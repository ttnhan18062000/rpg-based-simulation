---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260728-EVAL-FIXTURE-REPAIR
phase: open
date: 2026-07-28
tags: [testing]
---

# TCK-20260728-EVAL-FIXTURE-REPAIR

## Title
Repair and Extend Offline Retrieval Evaluation Fixtures

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Audit and repair stale expectations in tools/eval/queries.json, and extend it with new query categories (doc/exact-id, policy-vs-superseded, ticket-history, symbol-to-test, changed-path, provider/workflow/monitoring, no-result). Each new query needs expected authoritative source IDs, allowable alternatives, source lifecycle assumptions, and a context budget.

## Scope
- Audit every expected_doc_id in tools/eval/queries.json against the live index; fix/replace stale entries (confirmed: engine/contracts/progression_package moved to docs/archive/engine_contracts/, permanently unmatchable there)
- Extend queries.json with the new category values: doc/exact-id, policy-vs-superseded, ticket-history, symbol-to-test, changed-path, provider/workflow/monitoring, no-result
- Add new required fields per query entry: allowable_alternatives, source_lifecycle_assumption, context_budget
- Update tests/tools/test_eval_search.py (test_required_keys, test_category_balance, and hardcoded category-minimum assertions) to match the extended schema and new categories
- Add at least one new metric to tools/eval_search.py distinct from Recall@5/MRR@10 (authority/freshness correctness, duplicate rate, or estimated injected-token cost), each unit-tested independently
- Ensure known-difficult/no-result queries produce graceful zero-result behavior (no crash) and are excluded from recall/MRR denominators, like existing edge-case queries

## Out of Scope
- Does not silently change the existing Recall@5 pass/fail gate (currently 0.80 threshold, current measured Recall@5 is 0.53); new harder categories are tracked/measured separately from that existing gate, not folded into its pass/fail meaning
- Does not wire eval_search.py into CI — remains a manual Makefile target, no automated regression safety net added by this ticket
- Does not build new doc frontmatter status/authority infrastructure beyond what's minimally needed to compute the new authority/freshness metric

## Acceptance Criteria
- [ ] Every expected_doc_id in queries.json resolves to a doc_id actually present in the live index (no docs/archive/ or docs/lab/ entries, no stale renamed paths)
- [ ] queries.json is extended with the new category values and new required fields (allowable_alternatives, source_lifecycle_assumption, context_budget)
- [ ] tests/tools/test_eval_search.py's test_required_keys and test_category_balance (and category-minimum assertions) are updated to assert the new fields/categories
- [ ] eval_search.py computes at least one new metric distinct from Recall@5/MRR@10 (authority/freshness correctness, duplicate rate, or estimated injected-token cost), each unit-tested independently
- [ ] Known-difficult/no-result queries produce graceful zero-result output (no crash) and are excluded from recall/MRR denominators, matching existing edge-case query handling
- [ ] Decision recorded: new harder categories are tracked separately and do not change the existing 0.80 Recall@5 gate's pass/fail meaning

## Related Tickets
- TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC

## Related Docs
None.

## Related Stored Artifacts
None.

## Related Code Areas
- tools/eval/queries.json
- tools/eval_search.py
- tests/tools/test_eval_search.py

## Assumptions / Open Questions
- Whether new harder categories count toward the existing 0.80 Recall@5 gate is resolved as: track separately, do not silently change the existing gate's pass/fail meaning (per investigator recommendation)
- New authority/freshness metric requires doc frontmatter status/authority lookup wiring that doesn't fully exist yet — scoped minimally to what's needed for the metric
- eval-search has no CI wiring today (manual Makefile target only); this ticket does not add one

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
