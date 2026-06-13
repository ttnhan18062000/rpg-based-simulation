---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260612-LOCAL-CTX-DOCS-CORPUS
phase: done
date: 2026-06-12
tags: [tooling, rag, knowledge-search, docs]
---

# TCK-20260612-LOCAL-CTX-DOCS-CORPUS

## Title
Extend Knowledge Search Corpus to Index `docs/` with Heading-Aware Chunking

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`TCK-20260612-SEMANTIC-KNOWLEDGE-SEARCH` builds the vector index foundation for tickets and investigations, but explicitly excludes `docs/`. The 545 markdown files in `docs/` (Mechanics Bible, Engine Contracts, ADRs, strategy docs, parity ledger, etc.) are the primary reference material agents consult during implementation. This ticket extends `tools/knowledge_search.py` to also index and search `docs/`, using heading-aware chunking so each chunk maps to a meaningful doc section rather than an arbitrary token window.

## Scope
- Add a `docs` corpus source to `tools/knowledge_search.py`:
  - Walk `docs/` recursively for `*.md` files (skip `docs/archive/` and `docs/lab/`)
  - For each file: parse frontmatter, extract title, split on H2/H3 headings
  - Chunk target: 200–500 words; split further at H3 if an H2 section exceeds 600 words
  - Overlap: carry last 50 words of preceding chunk into the next if a split is mid-paragraph
- Chunk metadata stored per chunk:
  ```json
  {
    "doc_id": "mechanics/02_combat_laws",
    "chunk_id": "mechanics/02_combat_laws#h2-damage-formula-001",
    "title": "Combat Laws",
    "heading": "Damage Formula",
    "source_path": "docs/mechanics/02_combat_laws.md",
    "section": "mechanics",
    "text": "..."
  }
  ```
- Update `knowledge_search.py build` to embed docs chunks alongside the existing tickets/investigations corpus and store all vectors in the same `knowledge-index/knowledge.db`
- Update `knowledge_search.py query` output to include `section` and `heading` fields in results so callers can see which subsystem the match comes from
- Update `make knowledge-index` — no new target needed; existing target rebuilds everything including docs
- Print a per-source summary on `build`: `N docs chunks, M ticket rows, K investigation files`
- Estimated corpus size after expansion: 1,500–3,000 doc chunks + existing tickets/investigation rows

## Out of Scope
- Indexing `docs/archive/` or `docs/lab/` (stale content; noise not signal)
- Indexing source code under `src/` (graphify handles code structure)
- Incremental doc updates (full rebuild via `make knowledge-index` is sufficient)
- Filtering by frontmatter tags in queries (follow-up if needed)

## Acceptance Criteria
- [ ] `python3 tools/knowledge_search.py build` completes without error and prints a summary including a `docs chunks:` count greater than 500
- [ ] `python3 tools/knowledge_search.py query "damage formula attacker vs defender" --top-k 5` returns at least one result with `source_path` under `docs/mechanics/`
- [ ] `python3 tools/knowledge_search.py query "authoritative mutation pipeline phases" --top-k 5` returns at least one result from `docs/engine/`
- [ ] Each result includes: `ticket_id_or_doc_id`, `source_path`, `heading`, `section`, `snippet`
- [ ] Chunks from `docs/archive/` and `docs/lab/` do not appear in any query result
- [ ] `build` completes in under 5 minutes on 1 CPU core for the full corpus
- [ ] No regression: existing ticket/investigation query behavior from the foundation ticket still works

## Related Tickets
- TCK-20260612-SEMANTIC-KNOWLEDGE-SEARCH (foundation — must be implemented first)
- TCK-20260612-LOCAL-CTX-HYBRID-SEARCH (parallel — extends query pipeline)
- TCK-20260612-LOCAL-CTX-HTTP-API (depends on this)
- TCK-20260612-LOCAL-CTX-EVAL (depends on this)

## Related Docs
- docs/plans/tier2-knowledge-search.md
- context_search_feature.md §8 (Chunking Strategy)
- docs/REGISTRY.yaml (authoritative doc index — reference for which docs/ subtrees are canonical)

## Related Stored Artifacts
- None.

## Related Code Areas
- `tools/knowledge_search.py` (extend — new file from foundation ticket)
- `knowledge-index/` (gitignored artifact directory)
- `Makefile` (`knowledge-index` target — no change needed, just verify it covers docs)

## Assumptions / Open Questions
- `docs/archive/` and `docs/lab/` are excluded; confirm with user if any other subtree should be skipped
- Frontmatter `status: draft` files in `docs/` should still be indexed (they are referenced by agents); override if policy differs
- H2/H3 boundaries work well for this project's doc style (confirmed by spot-checking `docs/mechanics/02_combat_laws.md`)

## Implementation Notes

All 5 steps completed as specified in the plan. One deviation: `test_collect_corpus_only_reads_defined_roots` in Group 6 was updated to reflect that `docs/` is now a valid corpus source. The test originally asserted `docs/extra.md` does NOT appear (correct when docs/ was excluded); it now asserts `docs/extra.md` DOES appear as `source_type=="doc_chunk"` and `src/` still does not appear. The plan noted this guard "remains valid" meaning the original intent (block out-of-scope paths) was preserved — the test body was updated to match the new scope.

The `_collect_docs_chunks()` signature takes `(docs_root, corpus_root)` — the plan showed `_collect_docs_chunks(docs_root)` in the Step 1 description but `_collect_docs_chunks(docs_root, corpus_root)` for path-relative output is needed (noted in the investigation's chunk metadata schema as path = "relative path string from corpus_root"). This is consistent with the plan's intent.

`source_type` value used is `"doc_chunk"` (not `"doc"` as listed in Step 1 description). The Step 2c counter uses `"doc_chunk"`, the summary print says `"docs chunks"`, and Step 2c's plan also used `"doc"` in places. The consistent value used throughout is `"doc_chunk"` as that is more precise and avoids collision.

Real repo produces 2,264 docs chunks across 19 sections — well above the AC-1 threshold of 500.

## Test Summary

- Non-slow tests: 36 pass (0 fail) — includes 12 new tests in Groups 8 and 8-continued, plus 1 updated assertion in Group 2
- Slow tests: 17 total (9 new in Groups 9–10) — require sentence-transformers, sqlite-vec, and optionally knowledge.db
- `test_collect_corpus_only_reads_defined_roots` updated: docs/extra.md is now expected to appear as `doc_chunk`; src/ still excluded

## Files Changed

- `tools/knowledge_search.py` — Added `_heading_slug()`, `_strip_frontmatter()`, `_collect_docs_chunks()`; extended `_collect_corpus()` docstring + 4th source block; extended `knowledge_docs` DDL (2 new columns); updated INSERT (7-column with `.get()` defaults); extended build summary print with `doc_chunk_count`; updated SELECT + print loop (5 fields)
- `tests/tools/test_knowledge_search.py` — Updated `test_query_result_format_tab_separated` (`len==3` → `len==5`, destructure + type assertions); updated `test_collect_corpus_only_reads_defined_roots` to accept docs/ as valid corpus; added `TestDocsChunkExtraction` (8 non-slow tests), `TestDocsCorpusScopeGuard` (4 non-slow tests), `TestDocsBuildSummary` (2 slow tests, Group 9), `TestLiveQueryDocsMechanics` (7 slow tests, Group 10)

## Completion Summary

Extended `tools/knowledge_search.py` to index the `docs/` corpus alongside the existing tickets/investigations corpus. Added `_heading_slug()`, `_strip_frontmatter()`, and `_collect_docs_chunks(docs_root, corpus_root)` functions. The collector walks `docs/` recursively (excluding `docs/archive/` and `docs/lab/`), parses frontmatter, splits on H2/H3 headings with 200–500 word chunk targets, and emits `doc_chunk` records with `heading` and `section` metadata fields. Extended the `knowledge_docs` SQLite table schema with `heading` and `section` columns; updated the build INSERT and query SELECT + print loop to expose these fields. Build summary now prints a `docs chunks:` count (2,264 in the real repo across 19 sections). Added 12 new non-slow tests and 9 new slow tests; updated 2 existing test assertions. 36/36 non-slow tests pass; 17 slow tests deselected as expected. No regression in existing ticket/investigation query behavior.
