# Investigation — TCK-20260612-LOCAL-CTX-HYBRID-SEARCH
## Add BM25 Keyword Index and Hybrid Score Merging to Knowledge Search

PHASE_TS: 2026-06-12T14:52:28Z

---

## 1. Existing State of tools/knowledge_search.py

### 1.1 File structure (as of investigation)

The file is 668 lines, well-structured with five logical zones:

| Zone | Lines | Description |
|---|---|---|
| Module docstring + imports | 1–35 | argparse, csv, re, sqlite3, struct, sys, pathlib |
| `_check_deps()` | 41–55 | soft-import guard for sentence-transformers + sqlite-vec |
| Corpus extraction helpers | 59–198 | `_extract_request_summary`, `_extract_working_log_rows`, `_collect_corpus` |
| Docs corpus helpers | 201–433 | `_heading_slug`, `_strip_frontmatter`, `_collect_docs_chunks` |
| sqlite-vec helpers | 437–442 | `_serialize_f32` |
| `cmd_build()` | 449–544 | Builds vector index only; no BM25 |
| `cmd_query()` | 551–603 | Vector-only query; `--mode` flag exists in parser but is ignored in logic |
| CLI `_build_parser()` | 610–655 | Argparse setup; `--mode` already declared with `choices=["hybrid","vector","keyword"]` |

### 1.2 Key observations

**`--mode` flag is already declared in `_build_parser()` (line 649–653)** but `cmd_query()` never reads `args.mode`. The help text reads "only vector is implemented in this version". This ticket completes the implementation.

**`cmd_build()` insertion point** for BM25: after line 540 (`conn.close()`), before line 543 (the print of documents embedded). Specifically, after the vector DB is written and closed, add:
- `_build_bm25_index(corpus, db_path.parent / "bm25.pkl")`

**`cmd_query()` insertion point** for BM25: after query embedding (line 578), load BM25 if `--mode` is not `vector`, then merge scores.

**Output format change**: currently 5 tab-separated fields (`doc_id`, `path`, `heading`, `section`, `snippet`). The AC requires `final_score`, `semantic_score`, `keyword_score` to appear. This means the output format must expand — see §5 below.

### 1.3 `rank_bm25` status in pyproject.toml

Current `knowledge` group (lines 34–37):
```toml
knowledge = [
    "sentence-transformers>=2.7.0",
    "sqlite-vec>=0.1.1",
]
```
`rank_bm25` is **not present** — must be added.

---

## 2. BM25 Index Construction (build time)

### 2.1 Tokenization

Standard BM25Okapi tokenization: split on whitespace + punctuation. The ticket states camelCase/snake_case splitting is a stretch goal — exclude from this ticket.

Proposed `_tokenize(text: str) -> list[str]`:
```python
import re as _re
def _tokenize(text: str) -> list[str]:
    return _re.findall(r"[a-zA-Z0-9_]+", text.lower())
```
This handles `authoritative_pipeline` as a single token (preserves underscores), and also tokenizes `WorldRepository` as `worldrepository` (single lowercased). Sufficient for initial implementation per ticket scope.

### 2.2 Index construction

```python
from rank_bm25 import BM25Okapi
tokenized = [_tokenize(doc["text"]) for doc in corpus]
bm25 = BM25Okapi(tokenized)
```

### 2.3 Serialization

```python
import pickle
bm25_path = db_path.parent / "bm25.pkl"
with open(bm25_path, "wb") as f:
    pickle.dump(bm25, f)
```
`pickle` is stdlib — no new import needed at module level. Import inside the function is fine.

### 2.4 Where in cmd_build()

After `conn.close()` (currently line 541), before the final print:

```python
# --- BM25 index ---
try:
    _build_bm25_index(corpus, db_path.parent / "bm25.pkl")
    print(f"BM25 index → {db_path.parent / 'bm25.pkl'}")
except Exception as exc:
    print(f"Warning: BM25 index build failed (non-fatal): {exc}", file=sys.stderr)
```

Wrapping in try/except ensures BM25 failure never breaks the vector build (defensive, non-fatal pattern consistent with existing corpus warnings).

---

## 3. BM25 Scoring (query time)

### 3.1 Loading with graceful fallback

```python
def _load_bm25(bm25_path: Path):
    """Load BM25Okapi from pickle. Returns (bm25_obj, doc_ids_list) or (None, []) on failure."""
    if not bm25_path.exists():
        print("Warning: bm25.pkl not found — falling back to vector-only search", file=sys.stderr)
        return None, []
    try:
        import pickle
        with open(bm25_path, "rb") as f:
            return pickle.load(f)
    except Exception as exc:
        print(f"Warning: could not load bm25.pkl: {exc} — falling back to vector-only", file=sys.stderr)
        return None, []
```

The BM25 pickle must store both the BM25Okapi object AND the ordered list of `doc_id`s (to map BM25 row indices back to vector DB rowids). This means `_build_bm25_index` must serialize `(bm25, doc_ids)`.

### 3.2 Score normalization

BM25Okapi `.get_scores()` returns raw TF-IDF-based scores (non-normalized, range 0..∞). To merge with cosine similarity scores (0..1), normalize BM25 scores by their max value:

```python
bm25_raw = bm25.get_scores(_tokenize(query_text))
bm25_max = bm25_raw.max() or 1.0
bm25_norm = bm25_raw / bm25_max  # -> [0, 1]
```

### 3.3 Semantic score from sqlite-vec

sqlite-vec returns `distance` (L2 distance on normalized embeddings). For all-MiniLM-L6-v2, embeddings are normalized, so L2 distance ∈ [0, 2]. Convert to similarity:

```python
semantic_score = 1.0 - (distance / 2.0)  # -> [0, 1]
```

### 3.4 Boost signals

- `title_boost`: 1.0 if any query token appears in `doc_id` (the chunk id includes doc stem / section) — actually more accurately: needs a separate `title` field. Current schema has `doc_id` (document-level id) and `heading`. The "title" in chunk context is the file stem/doc title. For simplicity: `title_boost = 1.0 if any(tok in doc_id.lower() for tok in query_tokens) else 0.0`.
- `heading_boost`: 1.0 if any query token appears in `heading.lower()`.
- `code_boost`: 1.0 if any backtick-delimited token in chunk `text` matches a query token.

### 3.5 Hybrid score formula

```
final = semantic * 0.55 + keyword * 0.25 + title_boost * 0.10 + heading_boost * 0.05 + code_boost * 0.05
```

### 3.6 Mode routing in cmd_query()

```python
mode = getattr(args, "mode", "hybrid")  # default hybrid for backward compat
if mode == "vector":
    # skip BM25 entirely: keyword_score = 0.0 for all rows
elif mode == "keyword":
    # skip embedding: query only BM25, rank by keyword score + boost terms
elif mode == "hybrid":
    # both paths
```

For `--mode keyword`: need to retrieve all docs from the DB (no vector filter), score via BM25, sort, return top_k. This is the most complex mode — requires a full-scan SQL query without the `MATCH` clause.

---

## 4. Output Format Change

Current output (5 fields):
```
doc_id\tpath\theading\tsection\tsnippet
```

New output required by AC (must show `final_score`, `semantic_score`, `keyword_score`):
```
doc_id\tpath\theading\tsection\tfinal_score\tsemantic_score\tkeyword_score\tsnippet
```

**This is a breaking change to the output format** (5 → 8 fields). Callers downstream (TCK-20260612-LOCAL-CTX-HTTP-API) do not exist yet — safe to change. Existing test `test_query_result_format_tab_separated` at line 291 checks for exactly 5 fields and will need updating.

---

## 5. rank_bm25 Dependency

`rank_bm25` is pure Python, available on PyPI. Version: `rank-bm25>=0.2.2`. This must be added to `pyproject.toml` under `[project.optional-dependencies.knowledge]`.

Note: the PyPI package name is `rank-bm25` (hyphenated) but the import is `from rank_bm25 import BM25Okapi`. Both must be handled correctly.

---

## 6. .gitignore

`knowledge-index/` is already present in `.gitignore` at the project root (covers `knowledge-index/bm25.pkl`). No change needed.

---

## 7. Test Impact Analysis

### Tests that need updating

| Test | File | Reason |
|---|---|---|
| `test_query_result_format_tab_separated` | line 291 | Checks `len(parts) == 5`; must become 8 |
| `test_query_result_has_five_fields` (Group 10) | line 1097 | Checks `len(parts) == 5`; must become 8 |
| `test_missing_sqlite_vec_query_exits_0` | line 391 | `args` namespace needs `mode='hybrid'` — already set |

### New tests needed

| Test | AC |
|---|---|
| `test_build_produces_bm25_pkl` | AC1 |
| `test_query_mode_vector_skips_bm25` | AC4 |
| `test_query_mode_keyword_skips_embedding` | AC4 |
| `test_query_missing_bm25_pkl_falls_back_vector` | AC5 |
| `test_query_output_has_score_fields` | AC6 |
| `test_pyproject_contains_rank_bm25` | anti-drift |
| `test_query_hybrid_scores_present` | AC6 |

---

## 8. Architecture Concerns

- Pure tooling: no simulation logic, no durable state mutation, no world/entity involvement.
- `bm25.pkl` is a derived artifact (rebuild-on-demand), gitignored. Pickle is acceptable for this use case (local tooling, not cross-machine serialization).
- The BM25 index is built in `cmd_build()` — a single clear ownership point.
- The `--mode` flag is backward-compatible: existing callers not passing `--mode` get `hybrid` (the new default). The parser already declares `default="hybrid"`.
- No HTTP API or MCP scope in this ticket.
