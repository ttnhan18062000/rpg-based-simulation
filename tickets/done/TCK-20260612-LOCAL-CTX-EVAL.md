---
status: active
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260612-LOCAL-CTX-EVAL
phase: open
date: 2026-06-12
tags: [tooling, rag, knowledge-search, evaluation]
---

# TCK-20260612-LOCAL-CTX-EVAL

## Title
Search Quality Evaluation: Curated Query Set and Recall@5 / MRR@10 Measurement

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Without a ground-truth evaluation set there is no way to know whether search quality actually improved after tuning the hybrid weights, changing the chunking strategy, or upgrading the embedding model. This ticket creates a curated query set of 40 real agent-style questions drawn from this project's domain, and a `tools/eval_search.py` script that measures Recall@5 and MRR@10 against the live index. The evaluation can be run at any time with `make eval-search` to catch regressions before they reach production use.

## Scope
- New file: `tools/eval/queries.json` — 40 curated queries with expected document IDs:
  ```json
  [
    {
      "query": "what is the damage formula for attacker vs defender",
      "expected_doc_ids": ["mechanics/02_combat_laws"],
      "notes": "semantic — term 'damage formula' appears in heading"
    },
    {
      "query": "authoritative mutation pipeline phases",
      "expected_doc_ids": ["engine/authoritative_pipeline", "engine/authoritative_mutation_pipeline_contract"],
      "notes": "exact-term — tests BM25 path"
    }
  ]
  ```
  Query set must cover:
  - 15 semantic / natural-language queries (e.g., "how does the engine decide turn order")
  - 15 exact-term / technical queries (e.g., "WorldRepository", "apply_packet", "stamina_pressure")
  - 5 cross-section queries that should match docs from two different `section` values
  - 5 edge cases: very short queries, misspelled terms, queries with no good match
- New file: `tools/eval_search.py`
  - Loads `tools/eval/queries.json`
  - For each query: calls `knowledge_search.py query` (CLI path, not HTTP) with `--top-k 10`
  - Computes:
    - **Recall@5**: fraction of queries where at least one expected `doc_id` appears in top-5 results
    - **Recall@10**: same for top-10
    - **MRR@10**: mean reciprocal rank of first correct result in top-10
    - **Zero-result rate**: queries returning 0 results (should always be 0 for existing docs)
  - Prints a summary table and exits non-zero if Recall@5 < 0.80 (configurable via `--threshold`)
  - Saves full per-query results to `reports/eval_search_YYYYMMDD.json` (gitignored path)
- Add `make eval-search` target:
  ```makefile
  eval-search: ## Run search quality evaluation (requires knowledge-index)
      python3 tools/eval_search.py
  ```
- Add `reports/` to `.gitignore` if not already present

## Out of Scope
- Click-through rate or online evaluation (offline evaluation set is sufficient for now)
- Automated weight tuning (human reviews summary, adjusts weights in HYBRID ticket manually)
- User satisfaction scoring
- Evaluation of the HTTP API endpoint (CLI path is sufficient for regression detection)

## Acceptance Criteria
- [ ] `tools/eval/queries.json` exists with at least 40 entries spanning all four query categories
- [ ] `python3 tools/eval_search.py` completes without error when `knowledge-index/` is present
- [ ] Output includes a formatted table showing per-query: query text, expected doc, top-1 result, Recall@5 hit (Y/N), reciprocal rank
- [ ] Summary line shows: `Recall@5: X.XX | Recall@10: X.XX | MRR@10: X.XX | Zero-result: N`
- [ ] `make eval-search` runs successfully from project root
- [ ] Script exits 0 when Recall@5 >= 0.80, exits 1 when below threshold
- [ ] Evaluation report saved to `reports/eval_search_YYYYMMDD.json`
- [ ] `reports/` is listed in `.gitignore`
- [ ] If `knowledge-index/` does not exist, script prints an actionable error and exits 1 without a traceback

## Related Tickets
- TCK-20260612-SEMANTIC-KNOWLEDGE-SEARCH (foundation)
- TCK-20260612-LOCAL-CTX-DOCS-CORPUS (must be done — provides docs/ chunks to evaluate)
- TCK-20260612-LOCAL-CTX-HYBRID-SEARCH (must be done — hybrid weights being evaluated)
- TCK-20260612-LOCAL-CTX-HTTP-API (independent parallel)

## Related Docs
- context_search_feature.md §15 (Evaluation Plan)
- docs/testing/v2_test_taxonomy.md (test classification reference)

## Related Stored Artifacts
- None.

## Related Code Areas
- `tools/eval_search.py` (new file)
- `tools/eval/queries.json` (new file)
- `Makefile` (`eval-search` target)
- `.gitignore` (`reports/` entry)

## Assumptions / Open Questions
- `expected_doc_ids` match the `doc_id` field in the chunk metadata (relative path without extension under `docs/`), not the full source path — confirm this convention matches the implementation in DOCS-CORPUS ticket
- 40 queries is enough for an initial signal; expand to 100+ after first pass if false-positive rate is high
- The evaluation set itself should be reviewed by the project owner before `make eval-search` is treated as a gate

## Implementation Notes

- `expected_doc_ids` match the `doc_id` column value (`{section}/{stem}`) in knowledge_docs — not the chunk id which may include heading slug
- Edge-case queries with empty `expected_doc_ids` are excluded from Recall/MRR numerator; zero-result rate tracks them separately
- `_save_report` uses `relative_to(_REPO_ROOT)` with a ValueError fallback so tests patching `_REPORTS_DIR` to a tmp_path don't crash
- `reports/*` was already in `.gitignore` — no new entry needed

## Test Summary

- 21 tests in `tests/tools/test_eval_search.py`; all pass without a live index
- Covers: queries.json schema/balance, RR/Hit metrics, TSV parsing, exit codes, report save, no-index guard
- Full tools suite: 397 passed, 28 skipped

## Files Changed

- `tools/eval/queries.json` (new — 40 curated queries)
- `tools/eval_search.py` (new — evaluation runner)
- `tests/tools/test_eval_search.py` (new — 21 tests)
- `Makefile` (`eval-search` target added)

## Completion Summary

40-query evaluation set created (15 semantic, 15 exact-term, 5 cross-section, 5 edge-case). `tools/eval_search.py` computes Recall@5, Recall@10, MRR@10, and zero-result rate via subprocess calls to `knowledge_search.py`. `make eval-search` runs the full evaluation. 21 tests pass; no regressions.
