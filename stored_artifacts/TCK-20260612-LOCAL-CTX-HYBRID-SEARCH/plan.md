# Implementation Plan — TCK-20260612-LOCAL-CTX-HYBRID-SEARCH
## Add BM25 Keyword Index and Hybrid Score Merging to Knowledge Search

PHASE_TS: 2026-06-12T14:54:04Z

---

## Dependency Map

```
Step 1 (pyproject.toml) ─────────────────────────────────────┐
Step 2 (_tokenize + _build_bm25_index + cmd_build update) ──┐ │
Step 3 (_load_bm25 + _hybrid_score + cmd_query update) ─────┤ │
  └── depends on Step 2 (pkl format defined there)          │ │
Step 4 (tests) ──────────────────────────────────────────────┘ │
  └── depends on Steps 2+3                                      │
Step 5 (ticket close) ───────────────────────────────────────────┘
```

Steps 1 and 2 are independent (can be done in parallel); Step 3 depends on Step 2 (the pkl format); Step 4 depends on Steps 2+3.

---

## AC-to-Step Mapping

| AC | Step |
|---|---|
| AC1: `build` produces `knowledge.db` + `bm25.pkl` | Step 1, 2 |
| AC2: `query "WorldRepository"` returns `docs/architecture/` result | Step 3 |
| AC3: `query "how does the engine decide turn order"` returns `docs/engine/` result | Step 3 |
| AC4: `--mode vector`/`keyword` both complete without error | Step 3 |
| AC5: missing `bm25.pkl` falls back to vector-only, no exception | Step 3 |
| AC6: output rows show `final_score`, `semantic_score`, `keyword_score` | Step 3 |
| AC7: build time does not regress by more than 30 seconds | Step 2 (BM25 build is O(n*avg_len), trivially fast) |

---

## Step 1 — `pyproject.toml`: add `rank_bm25` to knowledge optional-dependencies

**File:** `pyproject.toml`

**Change:** Add `rank-bm25>=0.2.2` to `[project.optional-dependencies.knowledge]`.

```toml
knowledge = [
    "sentence-transformers>=2.7.0",
    "sqlite-vec>=0.1.1",
    "rank-bm25>=0.2.2",
]
```

**Scope guard:** Do NOT add to `[project.dependencies]` (core). Do NOT change `dev` group.

**Validation:** `pytest tests/tools/test_knowledge_search.py::TestPyprojectDeps -v` (existing group 7 tests will catch missing entries).

---

## Step 2 — `tools/knowledge_search.py`: add `_tokenize()`, `_build_bm25_index()`, update `cmd_build()`

**File:** `tools/knowledge_search.py`

### 2a. Add `_tokenize()` helper (new function, after `_serialize_f32`)

Location: after line 442 (after `_serialize_f32`), before `cmd_build`.

```python
def _tokenize(text: str) -> list[str]:
    """Tokenize text for BM25: lowercase, split on non-alphanumeric (preserving underscores).

    Preserves underscore-joined tokens (e.g. authoritative_pipeline stays as one token).
    CamelCase is NOT split (stretch goal excluded from this ticket's scope).
    """
    return re.findall(r"[a-zA-Z0-9_]+", text.lower())
```

### 2b. Add `_build_bm25_index()` helper (new function, after `_tokenize`)

```python
def _build_bm25_index(corpus: list[dict], bm25_path: Path) -> None:
    """Build a BM25Okapi index from corpus and serialize to bm25_path.

    Serializes a tuple: (BM25Okapi, list[str]) where the list contains
    the doc_id of each corpus entry in order (parallel to BM25 row indices).

    Raises: ImportError if rank_bm25 is not installed.
    """
    from rank_bm25 import BM25Okapi
    import pickle

    doc_ids = [d["id"] for d in corpus]
    tokenized = [_tokenize(d["text"]) for d in corpus]
    bm25 = BM25Okapi(tokenized)
    with open(bm25_path, "wb") as fh:
        pickle.dump((bm25, doc_ids), fh)
```

### 2c. Update `cmd_build()` to call `_build_bm25_index()`

**Insertion point:** After `conn.close()` (currently line 541), before the final print statement.

Add:
```python
    # --- BM25 keyword index ---
    bm25_path = db_path.parent / "bm25.pkl"
    try:
        from rank_bm25 import BM25Okapi  # noqa: F401
        _build_bm25_index(corpus, bm25_path)
        print(f"BM25 index ({len(corpus)} docs) → {bm25_path}")
    except ImportError:
        print(
            "Warning: rank-bm25 not installed — BM25 index skipped. "
            "Run: pip install -e '.[knowledge]'",
            file=sys.stderr,
        )
    except Exception as exc:
        print(f"Warning: BM25 index build failed (non-fatal): {exc}", file=sys.stderr)
```

**Scope guard:** Do NOT modify any existing embedding, sqlite-vec, or corpus collection logic. Only add code after `conn.close()`.

**Validation:** After this step, `python3 tools/knowledge_search.py build` should produce `knowledge-index/bm25.pkl`.

---

## Step 3 — `tools/knowledge_search.py`: add `_load_bm25()`, `_hybrid_score()`, update `cmd_query()`

**File:** `tools/knowledge_search.py`

### 3a. Add `_load_bm25()` helper (new function, after `_build_bm25_index`)

```python
def _load_bm25(bm25_path: Path):
    """Load a serialized (BM25Okapi, doc_ids) tuple from bm25_path.

    Returns:
        (bm25, doc_ids) on success
        (None, [])      on missing file or any error — prints a single warning line

    Never raises.
    """
    if not bm25_path.exists():
        print(
            f"Warning: {bm25_path} not found — falling back to vector-only search",
            file=sys.stderr,
        )
        return None, []
    try:
        import pickle
        with open(bm25_path, "rb") as fh:
            return pickle.load(fh)
    except Exception as exc:
        print(
            f"Warning: could not load {bm25_path}: {exc} — falling back to vector-only",
            file=sys.stderr,
        )
        return None, []
```

### 3b. Add `_hybrid_score()` helper (new function, after `_load_bm25`)

```python
def _hybrid_score(
    semantic: float,
    keyword: float,
    title_boost: float,
    heading_boost: float,
    code_boost: float,
) -> float:
    """Compute the hybrid ranking score.

    Formula (initial weights — tunable post-evaluation):
        final = semantic * 0.55
              + keyword  * 0.25
              + title_boost   * 0.10
              + heading_boost * 0.05
              + code_boost    * 0.05

    All inputs are expected in [0.0, 1.0]; output is in [0.0, 1.0].
    """
    return (
        semantic    * 0.55
        + keyword   * 0.25
        + title_boost    * 0.10
        + heading_boost  * 0.05
        + code_boost     * 0.05
    )
```

### 3c. Add `_compute_boosts()` helper (new function, after `_hybrid_score`)

Extracting boost logic into its own function keeps `cmd_query()` readable.

```python
def _compute_boosts(
    query_tokens: list[str],
    doc_id: str,
    heading: str,
    text: str,
) -> tuple[float, float, float]:
    """Return (title_boost, heading_boost, code_boost) for a chunk.

    title_boost:   1.0 if any query token appears in doc_id (lowercased)
    heading_boost: 1.0 if any query token appears in heading (lowercased)
    code_boost:    1.0 if any backtick-delimited token in text matches a query token
    """
    title_boost = 1.0 if any(tok in doc_id.lower() for tok in query_tokens) else 0.0
    heading_boost = 1.0 if any(tok in heading.lower() for tok in query_tokens) else 0.0

    # Extract backtick-delimited tokens from text
    code_tokens = set(re.findall(r"`([^`]+)`", text))
    code_boost = 1.0 if any(ct.lower() in query_tokens for ct in code_tokens) else 0.0

    return title_boost, heading_boost, code_boost
```

### 3d. Rewrite `cmd_query()` to support `--mode` and hybrid scoring

Replace the current `cmd_query()` implementation (lines 551–603) with a new version that:

1. Reads `args.mode` (default `"hybrid"` via argparse).
2. For modes `hybrid` and `vector`: performs vector search as before, gets top-k rows.
3. For mode `keyword`: performs a full-scan of `knowledge_docs` table and returns top-k by BM25 score only.
4. Computes and normalizes scores for each result row.
5. Prints 8 tab-separated fields: `doc_id`, `path`, `heading`, `section`, `final_score`, `semantic_score`, `keyword_score`, `snippet`.

**Pseudo-code for hybrid mode:**

```python
mode = getattr(args, "mode", "hybrid")

# --- Vector path ---
if mode in ("hybrid", "vector"):
    # embed query, run vec0 MATCH query as before → get rows with distance
    # semantic_score = 1.0 - (dist / 2.0), clamped to [0.0, 1.0]

# --- BM25 path ---
bm25_obj, bm25_doc_ids = (None, [])
if mode in ("hybrid", "keyword"):
    bm25_path = db_path.parent / "bm25.pkl"
    bm25_obj, bm25_doc_ids = _load_bm25(bm25_path)
    if bm25_obj is None:
        mode = "vector"  # graceful fallback

# For hybrid/vector: iterate vec rows, look up BM25 score by rowid (if available)
# For keyword: fetch all docs, rank by BM25, take top_k

# --- Merge scores and emit ---
for each result row:
    query_tokens = _tokenize(query_text)
    title_boost, heading_boost, code_boost = _compute_boosts(
        query_tokens, doc_id, heading, text
    )
    final = _hybrid_score(semantic, keyword, title_boost, heading_boost, code_boost)
    snippet = text[:120].replace(...)
    print(f"{doc_id}\t{path}\t{heading}\t{section}\t{final:.4f}\t{semantic:.4f}\t{keyword:.4f}\t{snippet}")
```

**BM25 score lookup for hybrid mode:**

The `bm25_doc_ids` list from the pickle maps BM25 row index → `doc["id"]`. The vector DB rows have a `rowid` that was set as `i` (0-indexed insertion order, same as corpus order). So:
- `bm25_raw = bm25_obj.get_scores(_tokenize(query_text))` → array of length N (corpus size)
- `bm25_max = bm25_raw.max() or 1.0`
- For each vector result with `rowid=i`: `keyword_score = float(bm25_raw[i]) / bm25_max`

This requires the BM25 pickle to store `(bm25, doc_ids)` AND the rowid-to-index mapping to be simply `rowid = i` (which it is — `cmd_build()` inserts with `rowid = i`).

**Scope guard:** Output format changes from 5 fields to 8 fields. This is intentional and required by AC6. Do not preserve the old 5-field format.

**Validation:** AC4, AC5, AC6 directly.

---

## Step 4 — Tests: update existing + add new tests

**File:** `tests/tools/test_knowledge_search.py`

### 4a. Update existing tests that check field count

| Test | Current assertion | New assertion |
|---|---|---|
| `test_query_result_format_tab_separated` (line 292) | `len(parts) == 5` | `len(parts) == 8` |
| `test_query_result_has_five_fields` (line 1113) | `len(parts) == 5` | `len(parts) == 8` |

Update destructuring lines too (add `final_score`, `semantic_score`, `keyword_score` fields).

### 4b. Add new test groups (append to file)

Add the following groups as described in `test_plan.md`:
- **Group A**: `TestTokenize` — unit tests for `_tokenize()`
- **Group B**: `TestBm25BuildLoad` — unit tests for `_build_bm25_index()` + `_load_bm25()`
- **Group C**: `TestHybridScore` — unit tests for `_hybrid_score()` + `_compute_boosts()`
- **Group D**: Extend `TestBuildHappyPath` with `test_build_produces_bm25_pkl`, `test_build_bm25_pkl_is_valid_pickle`
- **Group E**: New `TestQueryModeRouting` class (slow) — `test_query_mode_hybrid_default`, `test_query_mode_vector_skips_bm25`, `test_query_mode_keyword_skips_embedding`
- **Group F**: New `TestQueryScoreFields` class (slow) — `test_query_output_has_8_fields`, `test_query_output_score_fields_are_floats`, `test_query_hybrid_final_score_in_range`
- **Group G**: Extend `TestGracefulDegradation` with `test_query_missing_bm25_fallback_vector_only`, `test_query_missing_bm25_warning_text`
- **Group H**: Extend `TestLiveQueryDocsMechanics` with AC2/AC3 exact-term/semantic recall tests
- **Group I**: Extend `TestPyprojectDeps` with `test_knowledge_group_contains_rank_bm25`

---

## Step 5 — Ticket finalization (after implementation)

- Update ticket: fill `## Implementation Notes`, `## Test Summary`, `## Files Changed`, `## Completion Summary`; change `status: DONE`; change frontmatter `status: done`; change `phase: closed`
- Move ticket to `tickets/done/`
- Move staging artifacts to `stored_artifacts/TCK-20260612-LOCAL-CTX-HYBRID-SEARCH/`
- Append row to `tickets/working_log.csv`
- Write agent monitoring entries to `agent-monitoring/runs.jsonl` and `agent-monitoring/events.jsonl`
- Run: `rm -rf data/runs/* reports/release_proof/*`
- Commit with message: `TCK-20260612-LOCAL-CTX-HYBRID-SEARCH: Add BM25 keyword index and hybrid score merging`

---

## Scope Guards Summary

| Guard | Rule |
|---|---|
| No simulation code | All changes are in `tools/` and `tests/tools/` only |
| No HTTP API | `tools/knowledge_search.py` is a CLI tool; no Flask/FastAPI additions |
| No MCP | No MCP server changes |
| No camelCase splitting | `_tokenize()` does not split camelCase (stretch goal) |
| No per-field freshness/authority weights | Only title/heading/code boosts |
| No cross-encoder reranking | Future phase |
| `bm25.pkl` gitignored | `knowledge-index/` already in `.gitignore` — no `.gitignore` edit needed |
| `rank-bm25` in optional-deps only | Must NOT appear in `[project.dependencies]` |
| Output format 8 fields | Breaking change from 5 fields — acceptable; no downstream callers exist yet |
| Backward compat for `--mode` | argparse `default="hybrid"` already set; callers not passing `--mode` get hybrid |
