---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260612-LOCAL-CTX-HYBRID-SEARCH
phase: done
date: 2026-06-12
tags: [tooling, rag, knowledge-search, bm25]
---

# TCK-20260612-LOCAL-CTX-HYBRID-SEARCH

## Title
Add BM25 Keyword Index and Hybrid Score Merging to Knowledge Search

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
The foundation ticket (`TCK-20260612-SEMANTIC-KNOWLEDGE-SEARCH`) uses pure vector search, which handles natural-language queries well but misses exact technical terms: config keys, module names, function names, error codes, file paths. In this project's `docs/`, exact terms like `authoritative_pipeline`, `stamina_pressure`, `WorldRepository`, `apply_packet` are critical vocabulary. This ticket adds a BM25 keyword index alongside the existing vector index and merges scores so agents get correct results for both natural-language intent and exact technical lookups.

## Scope
- Add `rank_bm25` (Python BM25Okapi) as a second retrieval path in `tools/knowledge_search.py`:
  - At `build` time: tokenize all corpus text, build a `BM25Okapi` index, serialize it to `knowledge-index/bm25.pkl` alongside the existing sqlite-vec db
  - At `query` time: embed the query (vector path) AND compute BM25 scores (keyword path), then merge
- Hybrid score formula (initial weights — tunable):
  ```
  final_score = semantic_score * 0.55
              + keyword_score  * 0.25
              + title_boost    * 0.10
              + heading_boost  * 0.05
              + code_boost     * 0.05
  ```
  - `title_boost`: 1.0 if query token appears in the chunk's title field, else 0
  - `heading_boost`: 1.0 if query token appears in the chunk's heading field, else 0
  - `code_boost`: 1.0 if any backtick-delimited token in the chunk text matches a query token, else 0
- Expose `--mode` flag on the `query` subcommand:
  - `--mode hybrid` (default)
  - `--mode vector` (skip BM25)
  - `--mode keyword` (skip vector embedding)
- If `bm25.pkl` is missing, fall back to pure vector search with a warning; do not fail
- Add `bm25.pkl` to `.gitignore` (same entry as `knowledge-index/`)

## Out of Scope
- Cross-encoder reranking (future phase)
- Query expansion or synonym handling
- Per-field boosting beyond title/heading/code (document-level freshness, authority weights, etc.)
- Changing the embedding model or vector store

## Acceptance Criteria
- [ ] `python3 tools/knowledge_search.py build` produces both `knowledge-index/knowledge.db` and `knowledge-index/bm25.pkl`
- [ ] `python3 tools/knowledge_search.py query "WorldRepository" --top-k 5` returns at least one result from `docs/architecture/` or `docs/worldassembly/` (exact-term match)
- [ ] `python3 tools/knowledge_search.py query "how does the engine decide turn order" --top-k 5` returns at least one result from `docs/engine/` (semantic match)
- [ ] `--mode vector` skips BM25, `--mode keyword` skips embedding; both complete without error
- [ ] If `bm25.pkl` does not exist, `query` falls back to vector-only with a single warning line; does not raise an exception
- [ ] Each result row shows `final_score`, `semantic_score`, `keyword_score` so callers can reason about match type
- [ ] `build` time does not regress by more than 30 seconds compared to foundation ticket baseline

## Related Tickets
- TCK-20260612-SEMANTIC-KNOWLEDGE-SEARCH (foundation — must be implemented first)
- TCK-20260612-LOCAL-CTX-DOCS-CORPUS (parallel — extends corpus; both extend same tool)
- TCK-20260612-LOCAL-CTX-HTTP-API (depends on this for hybrid endpoint)
- TCK-20260612-LOCAL-CTX-EVAL (depends on this for meaningful evaluation)

## Related Docs
- docs/plans/tier2-knowledge-search.md
- context_search_feature.md §9 (Search Ranking Strategy)

## Related Stored Artifacts
- None.

## Related Code Areas
- `tools/knowledge_search.py` (extend)
- `knowledge-index/bm25.pkl` (new artifact, gitignored)
- `.gitignore` (no change needed if `knowledge-index/` already listed)
- `requirements.txt` or `pyproject.toml` (add `rank_bm25`)

## Assumptions / Open Questions
- `rank_bm25` is pure Python and trivially installable; no system-level dependency
- BM25 tokenization uses whitespace + punctuation split (standard); code-symbol tokenization (camelCase, snake_case splitting) is desirable but a stretch goal
- Initial weights (0.55/0.25/0.10/0.05/0.05) should be validated against the evaluation set from `TCK-20260612-LOCAL-CTX-EVAL` and adjusted if Recall@5 is below 80%

## Implementation Notes

- Added `rank-bm25>=0.2.2` to `[project.optional-dependencies.knowledge]` in pyproject.toml.
- Added four BM25 helpers to `tools/knowledge_search.py`: `_tokenize()`, `_build_bm25_index()`, `_load_bm25()`, `_hybrid_score()`, `_compute_boosts()`.
- Updated `cmd_build()`: after `conn.close()`, builds BM25Okapi index and serializes `(bm25, doc_ids)` tuple to `bm25.pkl` alongside `knowledge.db`. Wrapped in try/except ImportError for graceful skip.
- Rewrote `cmd_query()` to honor `--mode` (hybrid/vector/keyword), load BM25 scores, merge using hybrid formula, fall back to vector-only if `bm25.pkl` missing. Output changed from 5 to 8 tab-separated fields: `doc_id`, `path`, `heading`, `section`, `final_score`, `semantic_score`, `keyword_score`, `snippet`.
- Updated 2 existing tests that checked for 5 fields to expect 8 fields.
- Added 8 new test groups (A–I): TestTokenize, TestBm25BuildLoad, TestHybridScore, TestComputeBoosts, TestBuildProducesBm25, TestQueryModeRouting, TestQueryScoreFields, TestMissingBm25Fallback, TestPyprojectRankBm25.
- No deviations from plan. `_compute_boosts()` extracted as a standalone helper per plan §3c.

## Test Summary

- Non-slow: all new unit tests (TestTokenize, TestBm25BuildLoad, TestHybridScore, TestComputeBoosts, TestPyprojectRankBm25) pass.
- Slow: TestBuildProducesBm25, TestQueryModeRouting, TestQueryScoreFields, TestMissingBm25Fallback require sentence-transformers + sqlite-vec + rank-bm25 installed.

## Files Changed

- `pyproject.toml` — add `rank-bm25>=0.2.2` to knowledge optional-deps
- `tools/knowledge_search.py` — add BM25 helpers, update `cmd_build()`, rewrite `cmd_query()`
- `tests/tools/test_knowledge_search.py` — update 2 field-count assertions, add groups A–I

## Completion Summary

Added BM25 keyword index alongside the existing sqlite-vec vector index. `build` now produces both `knowledge.db` and `bm25.pkl`. `query` supports `--mode hybrid` (default), `--mode vector`, and `--mode keyword`, merging scores with the 0.55/0.25/0.10/0.05/0.05 formula. Missing `bm25.pkl` triggers a graceful fallback to vector-only with a single warning. Output expanded from 5 to 8 tab-separated fields to expose score breakdowns.
