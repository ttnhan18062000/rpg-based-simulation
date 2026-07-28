---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260728-EVAL-FIXTURE-REPAIR
phase: done
date: 2026-07-28
tags: [testing]
---

# TCK-20260728-EVAL-FIXTURE-REPAIR

## Title
Repair and Extend Offline Retrieval Evaluation Fixtures

## Status
DONE

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
- [x] Every expected_doc_id in queries.json resolves to a doc_id actually present in the live index (no docs/archive/ or docs/lab/ entries, no stale renamed paths)
- [x] queries.json is extended with the new category values and new required fields (allowable_alternatives, source_lifecycle_assumption, context_budget)
- [x] tests/tools/test_eval_search.py's test_required_keys and test_category_balance (and category-minimum assertions) are updated to assert the new fields/categories
- [x] eval_search.py computes at least one new metric distinct from Recall@5/MRR@10 (authority/freshness correctness, duplicate rate, or estimated injected-token cost), each unit-tested independently
- [x] Known-difficult/no-result queries produce graceful zero-result output (no crash) and are excluded from recall/MRR denominators, matching existing edge-case query handling
- [x] Decision recorded: new harder categories are tracked separately and do not change the existing 0.80 Recall@5 gate's pass/fail meaning

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

Followed `staging_artifacts/TCK-20260728-EVAL-FIXTURE-REPAIR/plan.md`'s 12 steps in order.

1-2. Repaired the 6 path-only stale `expected_doc_ids` strings (`engine/contracts/*` →
`engine/*`, `architecture/adr-00N-*` → `architecture/*`) and converted the
`progression_package` cross-section entry by dropping its dead second id, leaving
`["mechanics/01_entity_anatomy"]` only. No other field on those 7 entries was touched.

3. Added `test_no_stale_expected_doc_ids` plus a module-level `_KNOWN_STALE_DOC_IDS`
constant (7 strings) to `TestQueriesJson`.

4. Backfilled `allowable_alternatives` (`[]`), `source_lifecycle_assumption`
(`"current"`), and `context_budget` onto all 40 pre-existing entries.
`context_budget` was chosen per-entry by the target doc's first `expected_doc_ids`
prefix: `mechanics/*` → 1800, `engine/*`/`core/*`/`architecture/*` → 900,
`guidelines/*` → 700, empty (no-result/edge-case) → 400 — not a single global
constant, per Resolved Decision 5.

5. Extended `test_required_keys` with type/enum/positivity assertions for the 3 new
fields and added a dedicated `test_new_fields_present_all_entries`.

6. Appended 21 new entries (3 each across `doc/exact-id`, `policy-vs-superseded`,
`ticket-history`, `symbol-to-test`, `changed-path`, `provider/workflow/monitoring`,
`no-result`). For `policy-vs-superseded`, verified 3 genuine archived-vs-current doc
pairs by direct content comparison (`docs/archive/combat/combat_movement_rulebook.md`
→ `docs/combat/combat_movement_overhaul_spec.md`; `docs/archive/engine_contracts/support_matrix.md`
→ `docs/engine/contracts/supported_gameplay_surface.md`; `docs/archive/engine_contracts/unsupported_register.md`
→ `docs/engine/legacy_replacement_ledger.md`) rather than using the plan's suggested
`progression_package`/`attribute_progression_contract` pairing, which the plan itself
gated on verification — reading both docs showed `progression_package.md` is about
Phase-5 resource-engine-loop certification, not XP/attribute progression, so the
content match does not hold. The `progression_package` concept instead became one of
the 3 `no-result` entries (query themed on its real content: resource-engine
phase-5 certification/support-matrix), with `source_lifecycle_assumption: "archived"`
and notes stating this models the real archived doc's permanent exclusion by design.
`symbol-to-test`/`changed-path` entries are proxies targeting `tickets/done/TCK-*`
doc_ids whose Request Summary text names the relevant function/module/path
(`TCK-20260711-EVAL-SEARCH-DOCID-ANCHOR-FIX`, `TCK-20260713-MONITORING-SQLITE-INDEX`,
`TCK-20260713-MONITORING-QUERY-INDEX-MIGRATE`), each with an explicit proxy
disclaimer in `notes` per the plan's anti-drift guard. Total entries: 61
(40 existing + 21 new), 11 distinct category values.

7. Rewrote `test_category_balance` around an 11-entry `_CATEGORY_MINIMUMS` dict
(existing 4 minimums unchanged: 15/15/5/5) plus an unregistered-category-value guard.

8. Fixed the Recall@5/Recall@10 denominator in `evaluate()`: moved
`queries_with_expected` above the recall computation and divide `hits5`/`hits10` by
it instead of `total`, mirroring MRR@10's existing pattern. `total` is unchanged and
still used for the `"Queries: {total}"` print line. The `--threshold` default (0.80)
and the `return 0 if recall5 >= threshold else 1` gate were not touched.

9. Added `test_no_result_queries_excluded_from_recall_denominator` (3 answerable + 2
no-result queries, all answerable hit → asserts `recall_at_5`/`recall_at_10` == 1.0
via the saved report JSON, not `3/5`) and `test_threshold_default_unchanged` (calls
the real `main()` with `evaluate` monkeypatched to capture the `threshold` argument
it's invoked with, proving the CLI's argparse default is still 0.80). Confirmed all
5 pre-existing `TestEvaluateExitCode` methods still pass unchanged (they use
fully-populated `expected_doc_ids`, so `queries_with_expected == total` for them —
the denominator change is a no-op there, as predicted, not assumed).

10. Added `_duplicate_rate(results)` next to `_reciprocal_rank`/`_hit`: fraction of
retrieved results that are duplicates of an earlier result after `_strip_anchor`
reduction. Wired into `evaluate()`'s per-query loop (`duplicate_rate` per query,
`avg_duplicate_rate` averaged across all `total` queries, independent of whether an
expected answer exists) and added to the print summary line and `_save_report`'s
`metrics` dict as `"avg_duplicate_rate"`. No new dependency added.

11. Added `TestDuplicateRate` (4 pure-function tests, no mocking) and
`test_avg_duplicate_rate_in_saved_report` (new `TestEvaluateExitCode` method,
existing methods left untouched) asserting the key's presence and value in the
saved report.

12. AC6 decision, recorded here as required: **the 0.80 Recall@5 threshold value is
unchanged; only the doc_ids being scored against (Steps 1-2) and the denominator
population (Step 8) changed.** The 7 new query categories added in Step 6 are
measured and reported (per-query and in the category-balance test) but do not fold
into the existing Recall@5 pass/fail gate's meaning — that gate continues to mean
exactly what it meant before this ticket: "≥80% of queries with a non-empty
`expected_doc_ids` return a correct top-5 hit." Manual baseline run: see Test Summary
below for the new Recall@5/Recall@10/MRR@10/avg_duplicate_rate numbers, explicitly
distinct from the prior 0.53 baseline (which was measured under both the stale-id
bug and the pre-fix denominator bug simultaneously). No `.github/workflows/*.yml` or
`Makefile` changes were made — `eval_search.py` remains a manual-only target.

No `tools/knowledge_search.py` changes were made anywhere in this ticket.

13. **Post-Implement Verify correction (index staleness, AC1):** the first Verify
pass found 4 of the 21 new entries (2 `symbol-to-test` + 2 `changed-path`, all citing
`TCK-20260713-MONITORING-SQLITE-INDEX` / `TCK-20260713-MONITORING-QUERY-INDEX-MIGRATE`)
did not resolve in `knowledge-index/knowledge.db` — not because the fixture data was
wrong, but because that index (last built 2026-07-28 11:46) predated those two ticket
files being committed (commit `fdd946bf`, 2026-07-28 17:25:59) and `tools/eval/queries.json`
itself was authored assuming a rebuilt index. Ran `make knowledge-index-update`
(incremental, gitignored `knowledge-index/knowledge.db`, no `src/`/`docs/` content
changed) — both doc_ids now resolve exactly (confirmed via direct SQLite query) and
both entries score a real top-1 hit (`MRR: 1.0`) in the re-run baseline below. No
`queries.json`/`eval_search.py`/test code changed as part of this correction; this was
purely a stale-derived-artifact rebuild, not a fixture edit.

## Test Summary

`pytest tests/tools/test_eval_search.py -v` — 36 passed (27 pre-existing tests plus
9 new: `test_no_stale_expected_doc_ids`, `test_new_fields_present_all_entries`,
`test_no_result_queries_excluded_from_recall_denominator`,
`test_avg_duplicate_rate_in_saved_report`, `test_threshold_default_unchanged`, and
`TestDuplicateRate`'s 4 methods). 0 regressions; all 5 pre-existing
`TestEvaluateExitCode` methods pass byte-identical. Re-ran clean after the
`knowledge-index-update` rebuild (Implementation Notes step 13) — still 36/36.

Manual baseline (`python3 tools/eval_search.py`, run against the live
`knowledge-index/knowledge.db` **after** the Verify-phase index rebuild, 61 queries,
saved to `reports/eval_search_20260728.json`):
`Recall@5: 0.67 | Recall@10: 0.83 | MRR@10: 0.45 | Zero-result: 0` and
`Queries: 61 | With expected: 54 | Avg duplicate rate: 0.22`. `Threshold: Recall@5 >= 0.80 → FAIL`.
(An earlier pre-rebuild run measured 0.59/0.76/0.39/0.21 while the 4 AC1-violating
entries above could not yet resolve — that number is superseded by this one, not a
second independent baseline.) The FAIL is expected and does not block this ticket per
AC6/Resolved Decision 2: the 21 new harder-category queries (many deliberately probing
proxy/superseded/no-result cases the corpus was never designed to ace) are measured
and reported but are not required to pass the existing gate — the gate's 0.80
threshold and pass/fail mechanism are unchanged. Recall@5 at a real, bug-free 0.67 on
a harder, larger (40→61) query set, alongside Recall@10 at 0.83, indicates materially
better underlying retrieval quality than the old pre-ticket 0.53 figure (which was
measured under both the stale-id bug and the pre-fix denominator bug at once, so it
is not directly comparable). `reports/` and `data/runs/` were cleaned per the
Definition of Done after the run.

## Files Changed
- tools/eval/queries.json
- tools/eval_search.py
- tests/tools/test_eval_search.py
- tickets/inprogress/TCK-20260728-EVAL-FIXTURE-REPAIR.md
- staging_artifacts/TCK-20260728-EVAL-FIXTURE-REPAIR/plan.md (Deviations section)

## Completion Summary
Repaired the 7 confirmed-stale `expected_doc_ids` in `tools/eval/queries.json`
(6 corrected to the live index's actual doc_id scheme, 1 converted to a deliberate
`no-result` fixture), extended the fixture from 40 to 61 entries across 7 new
category values and 3 new per-entry fields, fixed the Recall@5/Recall@10 denominator
bug in `eval_search.py` so no-result queries are excluded the same way MRR@10 already
excludes them, and added a `duplicate_rate`/`avg_duplicate_rate` metric distinct from
Recall@5/MRR@10. The first Verify pass caught a real AC1 gap — 4 new entries citing
two just-committed tickets that predated the last `knowledge-index/knowledge.db`
build — resolved by rebuilding the (gitignored, derived-only) index via
`make knowledge-index-update`, no fixture/code change required; both doc_ids now
resolve exactly. The 0.80 Recall@5 gate's pass/fail meaning is unchanged; eval-search
remains a manual-only tool, not wired into CI. All 6 acceptance criteria satisfied
(verified against the rebuilt index), 36/36 scoped tests pass, no
`tools/knowledge_search.py` changes. One follow-up worth a separate ticket, flagged
but not fixed here (out of this ticket's Related Code Areas): `tools/knowledge_search.py`'s
`_collect_docs_chunks()` (lines 275-278) has a doc_id-derivation bug — `section = rel_parts[0]`
drops nested path segments under `docs/engine/contracts/`, `docs/architecture/`, etc.,
which is the root cause of 6 of the 7 originally-stale ids this ticket had to work around.
