---
status: active
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260612-LOCAL-CTX-DOCS-CORPUS
artifact_type: plan
tags: [tooling, rag, knowledge-search, docs]
---

# Implementation Plan — TCK-20260612-LOCAL-CTX-DOCS-CORPUS

## Dependency Map

```
Step 1 (_collect_docs_chunks helper)
  └─► Step 2 (schema + cmd_build INSERT/summary update)
        └─► Step 3 (cmd_query SELECT/print update)
              └─► Step 4 (wire into _collect_corpus)
                    └─► Step 5 (tests)
```

Steps 1–4 all touch `tools/knowledge_search.py` and must be applied in order:
- Step 2's INSERT must include `heading`/`section` columns before Step 4 wires in docs
  chunks that carry those keys.
- Step 3's SELECT must match the schema established in Step 2.
- Step 5 tests validate the full stack locked down in Steps 1–4.

---

## Step 1 — Add `_heading_slug()`, `_strip_frontmatter()`, and `_collect_docs_chunks()` to `tools/knowledge_search.py`

**File:** `tools/knowledge_search.py`

**Where to insert:** After `_collect_corpus()` (after line 191), before the `# sqlite-vec helpers`
comment block.

**Functions to add:**

### `_heading_slug(heading: str) -> str`

Generates an ASCII-safe slug from a heading string. Strips emoji and punctuation, lowercases,
replaces whitespace with hyphens, caps at 40 characters.

```python
def _heading_slug(heading: str) -> str:
    slug = heading.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)   # strip emoji and non-word characters
    slug = re.sub(r"\s+", "-", slug)
    return slug[:40]
```

### `_strip_frontmatter(text: str) -> str`

Removes the leading YAML frontmatter block (`--- ... ---`) from a markdown file.

```python
def _strip_frontmatter(text: str) -> str:
    return re.sub(r"^\s*---.*?---\s*", "", text, flags=re.DOTALL).strip()
```

### `_collect_docs_chunks(docs_root: Path) -> list[dict]`

Walks `docs_root` for `*.md` files and returns heading-aware chunks.

**Exclusions (hard-coded path prefix check):**
```python
if "docs/archive" in str(md_file) or "docs/lab" in str(md_file):
    continue
```

**Chunking algorithm:**
1. Strip frontmatter via `_strip_frontmatter()`.
2. If stripped body is empty after `.strip()`: skip file (`continue`), produce 0 chunks.
3. Extract `title`: from frontmatter `title:` field if present, else first `# H1` line, else file stem.
4. Extract `section`: the immediate subdirectory of `docs_root`
   (e.g. `docs_root/"mechanics"/"02.md"` → `section = "mechanics"`).
5. Split body on `## ` (H2) boundaries using `re.split(r"^(## .+)$", body, flags=re.MULTILINE)`.
6. For each H2 section:
   a. Count words. If `<= 600`: emit as one chunk with `heading = h2_heading_text`.
   b. If `> 600`: split on `### ` (H3) sub-headings.
      - Each H3 sub-section: if `<= 600 words`, emit as one chunk with `heading = h3_heading_text`.
      - Sub-section `> 600 words` after H3 split: hard-split at 500-word boundary,
        carry last 50 words of chunk N into the start of chunk N+1.
      - If no H3 in an oversized H2 section: hard-split directly with 50-word overlap.
7. If no H2 or H3 headings found in body: emit entire body as one chunk, `heading = ""`.
8. Chunk `id` format: `"{section}/{stem}#{heading_slug}-{sequence:03d}"` (per-file monotonic counter).
   No-heading fallback: `"{section}/{stem}#body-000"`.
9. `doc_id` = `"{section}/{stem}"` (no chunk qualifier — the document-level identity).

**Returned dict keys per chunk:**
`id`, `doc_id`, `path`, `text`, `source_type` (always `"doc"`), `heading`, `section`

**Scope guards:**
- Must NOT read from any path outside `docs_root`.
- Must NOT produce a chunk with empty `text` field.
- Must NOT index `docs/archive/` or `docs/lab/` subtrees.

**ACs covered by this step:** AC-5 (archive/lab exclusion enforced at source).

---

## Step 2 — Extend `knowledge_docs` schema and update `cmd_build()` INSERT and summary print

**File:** `tools/knowledge_search.py`

### 2a. Schema extension (inside `cmd_build()`, lines 267–280)

Replace `CREATE TABLE knowledge_docs` DDL to add two new columns:

```python
# OLD:
conn.execute(
    """
    CREATE TABLE knowledge_docs (
        rowid    INTEGER PRIMARY KEY,
        doc_id   TEXT NOT NULL,
        path     TEXT NOT NULL,
        text     TEXT NOT NULL,
        source_type TEXT NOT NULL
    )
    """
)

# NEW:
conn.execute(
    """
    CREATE TABLE knowledge_docs (
        rowid       INTEGER PRIMARY KEY,
        doc_id      TEXT NOT NULL,
        path        TEXT NOT NULL,
        text        TEXT NOT NULL,
        source_type TEXT NOT NULL,
        heading     TEXT NOT NULL DEFAULT '',
        section     TEXT NOT NULL DEFAULT ''
    )
    """
)
```

Note: `build` always drops and recreates the DB (`db_path.unlink()` on line 259). No ALTER TABLE
or migration is needed — the new schema takes effect on next `make knowledge-index` run.

### 2b. INSERT update (inside `cmd_build()`, lines 282–290)

Replace the INSERT statement inside the `for i, (doc, emb)` loop:

```python
# OLD:
conn.execute(
    "INSERT INTO knowledge_docs (rowid, doc_id, path, text, source_type) VALUES (?, ?, ?, ?, ?)",
    (i, doc["id"], doc["path"], doc["text"], doc["source_type"]),
)

# NEW:
conn.execute(
    "INSERT INTO knowledge_docs (rowid, doc_id, path, text, source_type, heading, section) "
    "VALUES (?, ?, ?, ?, ?, ?, ?)",
    (i, doc["id"], doc["path"], doc["text"], doc["source_type"],
     doc.get("heading", ""), doc.get("section", "")),
)
```

`doc.get("heading", "")` and `doc.get("section", "")` provide empty-string defaults for
ticket/investigation/working_log rows (which do not carry these keys). No change to their
collection code is required.

### 2c. Build summary print extension (lines 235–242)

```python
# OLD:
ticket_count = sum(1 for d in corpus if d["source_type"] == "ticket")
inv_count = sum(1 for d in corpus if d["source_type"] == "investigation")
wl_count = sum(1 for d in corpus if d["source_type"] == "working_log")
print(
    f"Corpus: {ticket_count} ticket summaries, "
    f"{inv_count} investigation files, "
    f"{wl_count} working log rows"
)

# NEW:
ticket_count = sum(1 for d in corpus if d["source_type"] == "ticket")
inv_count = sum(1 for d in corpus if d["source_type"] == "investigation")
wl_count = sum(1 for d in corpus if d["source_type"] == "working_log")
doc_chunk_count = sum(1 for d in corpus if d["source_type"] == "doc")
print(
    f"Corpus: {ticket_count} ticket summaries, "
    f"{inv_count} investigation files, "
    f"{wl_count} working log rows, "
    f"{doc_chunk_count} docs chunks"
)
```

**ACs covered by this step:** AC-1 (build prints docs chunks count > 500 — counter added here).

---

## Step 3 — Update `cmd_query()` SELECT and output to include `heading` and `section`

**File:** `tools/knowledge_search.py`

### SELECT query change (lines 338–354)

```python
# OLD SELECT and print:
rows = conn.execute(
    """
    SELECT d.doc_id, d.path, d.text, v.distance
    FROM knowledge_vec v
    JOIN knowledge_docs d ON d.rowid = v.rowid
    WHERE v.embedding MATCH ?
      AND k = ?
    ORDER BY v.distance
    """,
    (_serialize_f32(query_emb.tolist()), top_k),
).fetchall()
conn.close()

for doc_id, path, text, _dist in rows:
    snippet = text[:120].replace("\n", " ").replace("\t", " ")
    print(f"{doc_id}\t{path}\t{snippet}")

# NEW SELECT and print:
rows = conn.execute(
    """
    SELECT d.doc_id, d.path, d.heading, d.section, d.text, v.distance
    FROM knowledge_vec v
    JOIN knowledge_docs d ON d.rowid = v.rowid
    WHERE v.embedding MATCH ?
      AND k = ?
    ORDER BY v.distance
    """,
    (_serialize_f32(query_emb.tolist()), top_k),
).fetchall()
conn.close()

for doc_id, path, heading, section, text, _dist in rows:
    snippet = text[:120].replace("\n", " ").replace("\t", " ")
    print(f"{doc_id}\t{path}\t{heading}\t{section}\t{snippet}")
```

Output format change: 3 tab-separated fields → 5 tab-separated fields.

Field order: `doc_id`, `path`, `heading`, `section`, `snippet`.

Existing ticket/investigation/working_log rows produce `heading=""` and `section=""` — callers
parsing by field index 0 (doc_id) and 1 (path) are unaffected (confirmed: `create-tickets.js`
Step 0 reads only fields 0 and 1).

**ACs covered by this step:** AC-4 (each result includes heading, section, snippet — 5 fields total),
AC-2, AC-3 (docs results carry heading/section from their respective subsystems).

---

## Step 4 — Wire `_collect_docs_chunks()` into `_collect_corpus()` as the 4th source

**File:** `tools/knowledge_search.py`

### Docstring update for `_collect_corpus()`

Update the docstring to list all 4 corpus roots:

```
Corpus roots (relative to corpus_root):
  - tickets/done/TCK-*.md              → _extract_request_summary(content)
  - stored_artifacts/*/investigation.md → content[:500]
  - tickets/working_log.csv            → _extract_working_log_rows()
  - docs/ (excluding archive/, lab/)   → _collect_docs_chunks(docs_root)

ONLY these four paths are traversed — no src/, tests/, or other paths.
```

### 4th source block to add (after the working_log block, before `return docs`)

```python
# 4. docs/ — heading-aware chunks (excludes docs/archive/ and docs/lab/)
docs_dir = corpus_root / "docs"
if docs_dir.exists():
    docs.extend(_collect_docs_chunks(docs_dir))
```

The `docs_dir.exists()` guard ensures the function is safe when invoked against a minimal test
corpus with no `docs/` directory — produces 0 doc chunks without error.

**Scope guards:**
- `_collect_docs_chunks()` is the exclusive entry point for all docs corpus content.
- The existing `TestCorpusScopeGuard.test_collect_corpus_only_reads_defined_roots` test asserts that
  `docs/extra.md` does not appear in the corpus when the fake file is placed outside the expected
  docs tree. This guard remains valid — the new block only reads from `corpus_root / "docs"`.

**ACs covered by this step:** AC-1 (docs chunks routed through corpus and counted), AC-7 (no
regression — existing 3 sources unchanged; only additive extension).

---

## Step 5 — Update and extend `tests/tools/test_knowledge_search.py`

**File:** `tests/tools/test_knowledge_search.py`

### 5a. Update existing test (Group 11)

`TestQueryHappyPath.test_query_result_format_tab_separated`:
- Change `assert len(parts) == 3` → `assert len(parts) == 5`
- Change destructure `doc_id, path, snippet = parts` → `doc_id, path, heading, section, snippet = parts`
- Add `assert isinstance(heading, str)` and `assert isinstance(section, str)` (may be `""` for
  ticket/investigation rows; that is valid and expected behavior)

### 5b. New test class: `TestDocsChunkExtraction` (non-slow, Group 8)

8 unit tests using `tmp_path` fixtures with synthetic `.md` files. No sentence-transformers or
sqlite-vec required. Import `_collect_docs_chunks`, `_heading_slug`, and `_strip_frontmatter`
directly.

| Test | Setup | Assertion |
|---|---|---|
| `test_collect_docs_chunks_basic` | `tmp_path/docs/mechanics/02.md` with frontmatter + 2 H2 sections (~100 words each) | Returns 2 chunks; each has all required keys; `source_type=="doc"`; `section=="mechanics"` |
| `test_collect_docs_chunks_heading_text` | Single file with `## The Damage Formula` | Chunk `heading == "The Damage Formula"` |
| `test_collect_docs_chunks_no_headings_fallback` | File with frontmatter + body text, no H2/H3 | Returns exactly 1 chunk; `heading == ""` |
| `test_collect_docs_chunks_frontmatter_stripped` | File with `---\nstatus: authoritative\n---` + body | Chunk `text` does not contain `"status: authoritative"` or `"---"` |
| `test_collect_docs_chunks_empty_body_skipped` | File with only frontmatter, no body | Returns 0 chunks |
| `test_collect_docs_chunks_emoji_heading_slug` | File with `## 🏃 Phase 7: Locomotion Routing` | Chunk `id` is ASCII-only (no emoji); `heading` preserves original text including emoji |
| `test_collect_docs_chunks_large_section_split` | Single H2 >600 words, 2 H3 sub-sections ~300 words each | Returns 2 chunks (one per H3), not 1 oversized chunk |
| `test_collect_docs_chunks_hard_split_overlap` | Single H2 >600 words, no H3 headings | Returns multiple chunks; each <=800 words; last 50 words of chunk N appear at start of chunk N+1 |

### 5c. New test class: `TestDocsCorpusScopeGuard` (non-slow, Group 8 continued)

4 unit tests using `_make_minimal_corpus` + added docs files:

| Test | Setup | Assertion |
|---|---|---|
| `test_archive_excluded_from_collect_corpus` | `_make_minimal_corpus(tmp_path)` + `tmp_path/docs/archive/old_doc.md` | No returned dict has `path` containing `"docs/archive"` |
| `test_lab_excluded_from_collect_corpus` | `_make_minimal_corpus(tmp_path)` + `tmp_path/docs/lab/experimental.md` | No returned dict has `path` containing `"docs/lab"` |
| `test_collect_corpus_includes_doc_source_type` | `_make_minimal_corpus(tmp_path)` + `tmp_path/docs/mechanics/test.md` (1 H2 section) | `"doc"` in `{d["source_type"] for d in _collect_corpus(tmp_path)}` |
| `test_collect_corpus_existing_sources_unaffected` | `_make_minimal_corpus(tmp_path)` + a docs file | All four source types present; ticket and investigation text identical to what `_make_minimal_corpus` set |

### 5d. New slow tests — Group 9 (build with docs corpus, subprocess + tmp_path)

Both require `@pytest.mark.slow` and dep skip guard:

| Test | Setup | Assertion |
|---|---|---|
| `test_build_prints_docs_chunks_count` | `_make_minimal_corpus(tmp_path)` + `tmp_path/docs/mechanics/test.md` (2 H2 sections); run `build` via subprocess | stdout contains `"docs chunks"` and reported count >= 1 |
| `test_build_summary_includes_all_four_sources` | Same setup | stdout contains all of: `"ticket"`, `"investigation"`, `"working log"`, `"docs"` |

### 5e. New slow tests — Group 10 (live query, requires `knowledge-index/knowledge.db`)

All 7 tests require `@pytest.mark.slow` and skip if `knowledge-index/knowledge.db` absent:

| Test | Query / Action | Assertion | AC |
|---|---|---|---|
| `test_query_returns_docs_mechanics_result` | `"damage formula attacker vs defender" --top-k 5` | At least one result path contains `docs/mechanics/` | AC-2 |
| `test_query_returns_docs_engine_result` | `"authoritative mutation pipeline phases" --top-k 5` | At least one result path contains `docs/engine/` | AC-3 |
| `test_query_result_has_five_fields` | Any `--top-k 1` query | Output line splits into exactly 5 tab-separated fields | AC-4 |
| `test_query_no_archive_results` | 5 diverse queries `--top-k 10` | No result path contains `docs/archive/` or `docs/lab/` | AC-5 |
| `test_build_docs_chunk_count_exceeds_500` | `build --corpus-root .` against real repo | Printed docs chunks count > 500 | AC-1 |
| `test_build_completes_under_five_minutes` | `build --corpus-root .` timed | elapsed < 300 seconds | AC-6 |
| `test_existing_ticket_query_still_works` | `"player fatigue during extended combat" --top-k 5` | returncode==0; at least one result from `tickets/done/` or `stored_artifacts/`; completes < 2 s | AC-7 |

**Scope guards:**
- All non-slow tests must run without sentence-transformers or sqlite-vec: `pytest -m "not slow"`.
- All slow tests must skip gracefully if deps absent or `knowledge-index/knowledge.db` does not exist.
- Do not add docs corpus embedding to CI; `test_knowledge_index_not_in_test_target` must still pass.
- Expected non-slow count after Step 5: 24 existing + 1 updated + 12 new = 37.
- Expected slow count after Step 5: 8 existing + 9 new = 17.

---

## AC → Step Coverage Map

| Acceptance Criterion | Covered By |
|---|---|
| AC-1: build prints docs chunks > 500 | Step 2 (counter), Step 4 (wiring), Step 5 `test_build_docs_chunk_count_exceeds_500` |
| AC-2: query returns docs/mechanics/ result | Step 1 (chunker), Step 3 (output), Step 5 `test_query_returns_docs_mechanics_result` |
| AC-3: query returns docs/engine/ result | Step 1 (chunker), Step 3 (output), Step 5 `test_query_returns_docs_engine_result` |
| AC-4: result includes heading, section, snippet (5 fields) | Step 3 (SELECT + print), Step 5 `test_query_result_has_five_fields` + updated `test_query_result_format_tab_separated` |
| AC-5: no archive/lab results | Step 1 (exclusion), Step 5 `test_archive_excluded_from_collect_corpus`, `test_lab_excluded_from_collect_corpus`, `test_query_no_archive_results` |
| AC-6: build < 5 minutes | Step 5 `test_build_completes_under_five_minutes` |
| AC-7: no regression on ticket/investigation queries | Steps 2–4 (additive only, get-defaults), Step 5 `test_existing_ticket_query_still_works` |

---

## Files Changed (complete list)

| File | Change type | Summary |
|---|---|---|
| `tools/knowledge_search.py` | Modify | Add `_heading_slug()`, `_strip_frontmatter()`, `_collect_docs_chunks()`; extend `_collect_corpus()` docstring + 4th source block; extend `knowledge_docs` DDL (2 new columns); update INSERT (7-column with `get` defaults); extend build summary print; update SELECT + print loop (5 fields) |
| `tests/tools/test_knowledge_search.py` | Modify | Update 1 existing assertion (`len==3` → `len==5`); add ~21 new tests across Groups 8–10 (Group 11 is the updated test) |

No other files require changes:
- `Makefile`: `knowledge-index` target already covers full `build` invocation; no change needed.
- `pyproject.toml`: `[knowledge]` dep group unchanged; no new deps introduced.
- Parity ledger: no simulation mechanics changed; no entries to update or add.
- Docs: no behavioral change to simulation; no doc updates required for this tooling-only change.

---

## Deviations

| Step | Planned | Actual | Reason |
|---|---|---|---|
| Step 1 | `_collect_docs_chunks(docs_root)` signature (1 arg) | `_collect_docs_chunks(docs_root, corpus_root)` (2 args) | Investigation schema shows path = "relative path string from corpus_root" — `corpus_root` needed to derive the path |
| Step 1 | `source_type="doc_chunk"` (plan uses `"doc"` in Step 1 description but `"doc_chunk"` in Step 2c counter) | `source_type="doc_chunk"` consistently | More precise value; avoids collision; matches Step 2c counter logic |
| Step 4 | Wire call `_collect_docs_chunks(corpus_root / "docs")` | Wire call `_collect_docs_chunks(docs_dir, corpus_root)` | Matches 2-arg signature |
| Step 5 | `test_collect_corpus_only_reads_defined_roots` "remains valid" | Updated to accept `docs/extra.md` as valid `doc_chunk` source; still asserts `src/` excluded | docs/ is now a valid corpus root; the original guard (block non-corpus paths) is preserved with updated scope |

All other steps followed the plan exactly.

---

## Ordered Step List (summary)

1. Add `_heading_slug()`, `_strip_frontmatter()`, and `_collect_docs_chunks()` helper functions to `tools/knowledge_search.py` (after `_collect_corpus()`, before the sqlite-vec helpers section), implementing heading-aware chunking with exclusion of `docs/archive/` and `docs/lab/`, fallback for no-heading files, hard-split overlap, and the full chunk metadata schema.
2. Extend `knowledge_docs` DDL in `cmd_build()` with `heading TEXT NOT NULL DEFAULT ''` and `section TEXT NOT NULL DEFAULT ''`; update the INSERT to write 7 columns using `doc.get()` defaults for backward compatibility with existing non-doc rows; add `doc_chunk_count` to the build summary print including `{doc_chunk_count} docs chunks`.
3. Update `cmd_query()` SELECT to include `d.heading, d.section` (6 columns total) and update the print loop destructure and f-string to emit 5 tab-separated fields: `{doc_id}\t{path}\t{heading}\t{section}\t{snippet}`.
4. Wire `_collect_docs_chunks(corpus_root / "docs")` into `_collect_corpus()` as the 4th source block (after the working_log block, before `return docs`); update the docstring to list all 4 corpus roots.
5. Update `TestQueryHappyPath.test_query_result_format_tab_separated` (`len==3` → `len==5`, destructure + type assertions); add `TestDocsChunkExtraction` (8 non-slow unit tests), `TestDocsCorpusScopeGuard` (4 non-slow unit tests), Group 9 slow build tests (2), and Group 10 slow live-query AC tests (7) to `tests/tools/test_knowledge_search.py`.
