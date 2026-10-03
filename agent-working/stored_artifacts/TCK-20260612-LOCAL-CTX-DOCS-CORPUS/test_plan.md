---
status: active
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260612-LOCAL-CTX-DOCS-CORPUS
artifact_type: test_plan
tags: [tooling, rag, knowledge-search, docs]
---

# Test Plan — TCK-20260612-LOCAL-CTX-DOCS-CORPUS

## Regression Surface

### Existing test file: tests/tools/test_knowledge_search.py

The foundation ticket produced 32 total tests: **24 non-slow** (run immediately) + **8 slow** (require `make knowledge-index`).

All 24 non-slow tests must pass without modification after this ticket's changes, with the following **one known required update**:

| Test | Change Required | Reason |
|---|---|---|
| `TestQueryHappyPath.test_query_result_format_tab_separated` | Update assertion `len(parts) == 3` → `len(parts) == 5` | Query output expands from 3 to 5 tab-separated fields (adding `heading`, `section`) |

All other 23 non-slow tests are unaffected:
- `TestBuildHappyPath` (4 slow) — build mechanics unchanged; per-source summary print gains a new line but existing assertions on `ticket`, `investigation`, `working log` remain valid.
- `TestGracefulDegradation` (3 non-slow) — no change to missing-index or missing-dep behavior.
- `TestMakeTarget` (4 non-slow) — Makefile `knowledge-index` target unchanged.
- `TestGitignore` (2 non-slow) — `.gitignore` entry unchanged.
- `TestCorpusScopeGuard` (2 non-slow) — `docs/extra.md` exclusion assertion remains valid; `test_collect_corpus_includes_all_three_sources` still asserts `ticket`, `investigation`, `working_log` source types (adding `doc` source type does not break this check).
- `TestPyprojectDeps` (3 non-slow) — pyproject.toml `knowledge` group unchanged.
- `TestExtractRequestSummary` (4 non-slow) — function unchanged.
- `TestExtractWorkingLogRows` (3 non-slow) — function unchanged.
- `TestCollectCorpus` (3 non-slow) — existing boundary assertions unchanged; new `doc` source type is additive.

---

## New Tests Required

All new tests go in `tests/tools/test_knowledge_search.py`, following the existing patterns (subprocess for CLI contract tests, direct function calls for unit tests).

### Group 8 — Docs corpus collection (unit tests, non-slow)

#### `TestDocsChunkExtraction`

**Test: `test_collect_docs_chunks_basic`**
- Setup: create `tmp_path/docs/mechanics/02_combat.md` with frontmatter + two H2 sections (~100 words each)
- Assert: `_collect_docs_chunks(tmp_path / "docs")` returns 2 chunks
- Assert: each chunk has keys `id`, `doc_id`, `path`, `text`, `source_type`, `heading`, `section`
- Assert: `source_type == "doc"` for all chunks
- Assert: `section == "mechanics"` for all chunks

**Test: `test_collect_docs_chunks_heading_text`**
- Setup: single file with `## The Damage Formula` as H2
- Assert: returned chunk has `heading == "The Damage Formula"`

**Test: `test_collect_docs_chunks_no_headings_fallback`**
- Setup: single file with frontmatter and body text but no H2/H3 headings
- Assert: returns exactly 1 chunk covering the full body text
- Assert: `heading == ""`

**Test: `test_collect_docs_chunks_frontmatter_stripped`**
- Setup: file with YAML frontmatter block `---\nstatus: authoritative\n---` + body
- Assert: returned chunk `text` does not contain `status: authoritative` or `---`

**Test: `test_collect_docs_chunks_empty_body_skipped`**
- Setup: file with only frontmatter and no body content
- Assert: returns 0 chunks (empty body guard)

**Test: `test_collect_docs_chunks_emoji_heading_slug`**
- Setup: file with heading `## 🏃 Phase 7: Locomotion Routing`
- Assert: the chunk `id` contains a valid ASCII-only slug (no emoji characters in `id`)
- Assert: `heading` field preserves the original text including emoji

**Test: `test_collect_docs_chunks_large_section_split`**
- Setup: single H2 section with >600 words and two H3 subsections (~300 words each)
- Assert: returns 2 chunks (one per H3), not 1 oversized chunk

**Test: `test_collect_docs_chunks_hard_split_overlap`**
- Setup: single H2 section with >600 words and no H3 headings (no sub-split possible)
- Assert: returns multiple chunks
- Assert: each chunk text length does not exceed 800 words (reasonable hard-split bound)
- Assert: the last 50 words of chunk N appear at the start of chunk N+1 (overlap verification)

#### `TestDocsCorpusScopeGuard`

**Test: `test_archive_excluded_from_collect_corpus`**
- Setup: `_make_minimal_corpus(tmp_path)` + create `tmp_path/docs/archive/old_doc.md` with content
- Call: `_collect_corpus(tmp_path)`
- Assert: no returned dict has `path` containing `docs/archive`

**Test: `test_lab_excluded_from_collect_corpus`**
- Setup: `_make_minimal_corpus(tmp_path)` + create `tmp_path/docs/lab/experimental.md` with content
- Call: `_collect_corpus(tmp_path)`
- Assert: no returned dict has `path` containing `docs/lab`

**Test: `test_collect_corpus_includes_doc_source_type`**
- Setup: `_make_minimal_corpus(tmp_path)` + create `tmp_path/docs/mechanics/test.md` with one H2 section
- Call: `_collect_corpus(tmp_path)`
- Assert: `"doc"` in `{d["source_type"] for d in corpus}`

**Test: `test_collect_corpus_existing_sources_unaffected`**
- Setup: `_make_minimal_corpus(tmp_path)` + add a docs file
- Call: `_collect_corpus(tmp_path)`
- Assert: `{"ticket", "investigation", "working_log", "doc"}` all present in source_types
- Assert: the ticket and investigation docs have identical text to what `_make_minimal_corpus` produced

### Group 9 — Build with docs corpus (slow, require deps)

**Test: `test_build_prints_docs_chunks_count`**
- Setup: `_make_minimal_corpus(tmp_path)` + `tmp_path/docs/mechanics/test.md` (2 H2 sections)
- Run `build` subcommand via subprocess
- Assert: stdout contains `"docs chunks"` or `"doc chunks"`
- Assert: the reported docs count is >= 1

**Test: `test_build_summary_includes_all_four_sources`**
- Setup: same as above
- Run `build` via subprocess
- Assert: stdout contains all of: `"ticket"`, `"investigation"`, `"working log"`, `"docs"` (or `"doc"`)

### Group 10 — Query with docs results (slow, require live index against real docs/)

**Test: `test_query_returns_docs_mechanics_result`**
- Precondition: skip if live `knowledge-index/knowledge.db` absent
- Run: `python3 tools/knowledge_search.py query "damage formula attacker vs defender" --top-k 5`
- Assert: at least one result line has a `path` containing `docs/mechanics/`
- Matches AC: *"returns at least one result with source_path under docs/mechanics/"*

**Test: `test_query_returns_docs_engine_result`**
- Precondition: skip if live `knowledge-index/knowledge.db` absent
- Run: `python3 tools/knowledge_search.py query "authoritative mutation pipeline phases" --top-k 5`
- Assert: at least one result line has a `path` containing `docs/engine/`
- Matches AC: *"returns at least one result from docs/engine/"*

**Test: `test_query_result_has_five_fields`**
- Precondition: skip if live `knowledge-index/knowledge.db` absent
- Run any query with `--top-k 1`
- Assert: output line splits into exactly 5 tab-separated fields: `doc_id`, `path`, `heading`, `section`, `snippet`
- Matches AC: *"Each result includes: ticket_id_or_doc_id, source_path, heading, section, snippet"*

**Test: `test_query_no_archive_results`**
- Precondition: skip if live `knowledge-index/knowledge.db` absent
- Run several diverse queries (e.g. 5 different topic queries) with `--top-k 10`
- Assert: no result line has a `path` containing `docs/archive/`
- Assert: no result line has a `path` containing `docs/lab/`
- Matches AC: *"Chunks from docs/archive/ and docs/lab/ do not appear in any query result"*

**Test: `test_build_docs_chunk_count_exceeds_500`**
- Precondition: skip if deps not available
- Run `build` with `--corpus-root .` against the real repo
- Assert: the printed `docs chunks:` count is > 500
- Matches AC: *"build completes without error and prints a summary including a docs chunks: count greater than 500"*

**Test: `test_build_completes_under_five_minutes`**
- Precondition: skip if deps not available; mark `@pytest.mark.slow`
- Time the full `build` subprocess call with `--corpus-root .`
- Assert: elapsed < 300 seconds
- Matches AC: *"build completes in under 5 minutes on 1 CPU core for the full corpus"*

**Test: `test_existing_ticket_query_still_works`**
- Precondition: skip if live `knowledge-index/knowledge.db` absent
- Run: `python3 tools/knowledge_search.py query "player fatigue during extended combat" --top-k 5`
- Assert: returncode == 0
- Assert: at least one result with a `path` containing `tickets/done/` or `stored_artifacts/`
- Assert: query completes within 2 seconds
- Matches AC: *"No regression: existing ticket/investigation query behavior still works"*

### Group 11 — Updated regression test for 5-field format (non-slow)

**Test: `test_query_result_format_tab_separated` (UPDATE existing)**
- Change assertion from `len(parts) == 3` to `len(parts) == 5`
- Change destructure from `doc_id, path, snippet = parts` to `doc_id, path, heading, section, snippet = parts`
- Add assertions: `isinstance(heading, str)` and `isinstance(section, str)` (may be empty strings for ticket results)

---

## Scoped Pytest Commands

### Non-slow unit tests only (run during implementation, no deps required)

```bash
pytest tests/tools/test_knowledge_search.py -v -m "not slow"
```

Expected: all 24 existing non-slow + all new non-slow tests pass. No network, no model download.

### Docs corpus unit tests only (new tests in groups 8, scope guard)

```bash
pytest tests/tools/test_knowledge_search.py -v -m "not slow" -k "Docs or docs"
```

### Full test suite minus slow (CI-equivalent gate)

```bash
pytest tests/tools/ -v -m "not slow"
```

### Slow integration tests (require `make knowledge-index` first)

```bash
make knowledge-index  # build index with docs corpus
pytest tests/tools/test_knowledge_search.py -v -m slow
```

### Domain-scoped regression guard (verify no other tools tests broken)

```bash
pytest tests/tools/ -v -m "not slow"
```

Expected: all tools tests pass, including `test_generate_registry.py`, `test_validate_frontmatter.py`, etc.

---

## Anti-Drift Test Guards

### Archive/lab exclusion guard (must not be removed)

`TestDocsCorpusScopeGuard.test_archive_excluded_from_collect_corpus` and `test_lab_excluded_from_collect_corpus` are the primary anti-drift guards against future corpus boundary violations. These are non-slow unit tests — they run on every `pytest -m "not slow"` invocation with no external deps.

These tests complement the existing `TestCorpusScopeGuard.test_collect_corpus_only_reads_defined_roots` which guards against `docs/extra.md` and `src/engine.py` leaking in generally.

### Output field count guard

`test_query_result_format_tab_separated` (updated to assert 5 fields) acts as an anti-drift guard: if the output format is modified (fields added or removed), this test fails immediately. This is critical because `create-tickets.js` Step 0 is a downstream consumer.

### Source type completeness guard

`test_collect_corpus_includes_doc_source_type` (new) and the existing `test_collect_corpus_includes_all_three_sources` together ensure all four source types (`ticket`, `investigation`, `working_log`, `doc`) remain present. If a refactor accidentally drops docs collection from `_collect_corpus()`, the first test catches it.

### Build summary string guard

`test_build_summary_includes_all_four_sources` (new, slow) asserts the `build` stdout includes the `"docs chunks"` label. This prevents silent regression where docs are collected but not counted in the summary print.

### Chunk count floor guard

`test_build_docs_chunk_count_exceeds_500` (slow, against real repo) is the definitive AC guard. If docs/ shrinks dramatically or the chunker silently breaks, this test fails. It should be run after any significant docs/ restructuring.
