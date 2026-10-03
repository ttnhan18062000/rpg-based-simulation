---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260728-EVAL-FIXTURE-REPAIR
artifact_type: test_plan
tags: [testing]
---

# Test Plan — TCK-20260728-EVAL-FIXTURE-REPAIR

## Regression Surface

All existing tests in `tests/tools/test_eval_search.py` must keep passing
(27 tests today, per `TCK-20260711-EVAL-SEARCH-DOCID-ANCHOR-FIX`'s completion
notes):

- unit — `TestQueriesJson`: `test_file_exists`, `test_has_40_entries`,
  `test_required_keys`, `test_category_balance` (the latter two will be
  *edited*, not left byte-identical, per the ticket's own AC — see New Tests
  Required; "must keep passing" here means the edited versions pass, not that
  the assertions stay unchanged).
- unit — `TestStripAnchor` (5 cases): anchor-stripping and hit-matching against
  the bare-vs-anchored doc_id scheme. Must not regress — this is the fix from
  the immediately preceding hotfix ticket.
- unit — `TestReciprocalRank` (5 cases), `TestHit` (4 cases): pure-function
  correctness for the two core metrics. Untouched by this ticket's scope,
  should not need edits.
- unit — `TestRunQuery` (3 cases): subprocess-output parsing, mocked, no live
  index required.
- integration (mocked subprocess, no live index) — `TestEvaluateExitCode`
  (5 cases): pins `evaluate()`'s exit-code contract. **At risk** from the
  Risk #2 denominator fix (recall5/10's `total` should become
  `queries_with_expected`-based) — every case in this class uses queries with
  fully-populated `expected_doc_ids` (no empty lists), so the fix should not
  change their results, but this must be verified by running the class after
  the change, not assumed.
- integration — `TestMainNoIndex` (1 case): no-index guard, unaffected by this
  ticket.

No other test file imports `tools/eval_search.py` or `tools/eval/queries.json`
(confirmed via graphify query — `eval_search.py`/`test_eval_search.py` sit in
graph community 151/62 respectively with no external edges into other test
modules). This is the complete regression surface; no arena-combat or broader
simulation test files are implicated (this ticket is pure agent-tooling).

## New Tests Required

Per the ticket's 6 acceptance criteria:

1. **Stale doc_id repair (AC1)**
   - Test name: `test_no_stale_expected_doc_ids` (or fold into
     `test_required_keys`)
   - Category: unit (schema/content check, no live index needed — asserts
     against a fixed list, not by shelling out)
   - Verifies: none of the 7 confirmed-stale strings
     (`architecture/adr-004-simulation-watchdog`,
     `architecture/adr-005-performance-optimization`,
     `engine/contracts/replay_contract`, `engine/contracts/scheduler_contract`,
     `engine/contracts/observability_contract`,
     `engine/contracts/infrastructure_overview`,
     `engine/contracts/progression_package`) appear anywhere in any entry's
     `expected_doc_ids` after the repair. This is a fast, deterministic,
     no-live-index-required regression guard against reintroducing the exact
     bug this ticket fixes.
   - Location: `tests/tools/test_eval_search.py`, `TestQueriesJson` class.
   - Note: a *stronger* version would assert every `expected_doc_ids` value
     resolves against the live `knowledge-index/knowledge.db`
     `knowledge_docs.doc_id` set (anchor-stripped) — but that requires the
     index to exist at test time (it's build-artifact, gitignored per
     `knowledge-index/` being a build output). Recommend keeping this as a
     `pytest.mark.skipif(not _DB_PATH.exists())`-guarded *optional* stronger
     check, with the fixed-blocklist test above as the always-runs baseline
     (mirrors `TestMainNoIndex`'s existing pattern of tolerating no-index
     environments).

2. **New required fields present (AC2, AC3)**
   - Test name: `test_required_keys` (extend in place) +
     `test_new_fields_present_all_entries`
   - Category: unit
   - Verifies: every entry has `allowable_alternatives` (list),
     `source_lifecycle_assumption` (str, non-empty), `context_budget`
     (numeric or str, per whatever type the Plan phase settles on — pin the
     exact type once decided).
   - Location: `tests/tools/test_eval_search.py`, `TestQueriesJson` class.

3. **New category values present with minimums (AC2, AC3)**
   - Test name: `test_category_balance` (rewritten)
   - Category: unit
   - Verifies: whatever category set the Plan phase settles (Risk #4 in
     investigation.md — 11-value additive set vs. consolidated set), each
     with an explicit minimum count, not just presence. Must not silently
     accept a category with 0 or 1 entries as "covered."
   - Location: `tests/tools/test_eval_search.py`, `TestQueriesJson` class.

4. **New metric function(s) (AC4)**
   - Test name: e.g. `TestDuplicateRate` / `TestAuthorityFreshness` /
     `TestEstimatedTokenCost` (name depends on which metric(s) the Plan phase
     picks — ticket requires at least one of the three named in the source doc)
   - Category: unit
   - Verifies: the new metric function in isolation, with hand-constructed
     inputs (not the live index) — e.g. duplicate-rate: given a `results` list
     with repeated doc_ids, returns the correct fraction; authority/freshness:
     given a doc with a known frontmatter `status`/`authority` value (or a
     missing one), returns the correct classification without crashing on
     missing frontmatter; token-cost: given fixed-length snippet strings,
     returns a deterministic estimate.
   - Location: `tests/tools/test_eval_search.py`, new test class(es)
     mirroring the existing `TestStripAnchor`/`TestReciprocalRank`/`TestHit`
     pattern (pure function, no mocking needed).
   - Also needs: an `evaluate()`-level integration test (extend
     `TestEvaluateExitCode` or add a new class) confirming the new metric is
     computed and appears in the saved JSON report (mirrors
     `test_report_saved_to_reports_dir`'s existing pattern of asserting keys
     in the written report).

5. **Graceful no-result handling + denominator exclusion (AC5)**
   - Test name: `test_no_result_queries_excluded_from_recall_denominator`
   - Category: unit (pure function test on `evaluate()`, mocked `_run_query`
     returning `[]`)
   - Verifies: a query with `expected_doc_ids: []` (or explicitly categorized
     `no-result`) contributes 0 to `hits5`/`hits10` **and is excluded from
     the recall5/recall10 denominator** (Risk #2) — i.e. mixing N answerable
     queries (all hits) with M no-result queries should yield
     `recall5 == 1.0`, not `N/(N+M)`. This is the regression test that locks
     in the Risk #2 fix; write it to fail against the pre-fix `total = len(queries)`
     logic so it actually proves the change.
   - Also verify no crash: a `no-result` query whose live retrieval genuinely
     returns 0 results does not raise, and is counted in `zero_results`
     (existing behavior, L67-69 — should not regress).
   - Location: `tests/tools/test_eval_search.py`, extend `TestEvaluateExitCode`.

6. **Gate-meaning-unchanged decision recorded (AC6)**
   - Not a code test — a documentation/ticket-body requirement (the
     ticket body itself, or `plan.md`, must state the decision explicitly).
     No new pytest test is needed for this AC; it is satisfied by the ticket's
     own "Assumptions / Open Questions" section already stating the resolved
     decision (present in the ticket as written). Flag this at Verify time as
     a docs-only AC, not a code-coverage gap.

## Scoped Pytest Commands

```
pytest tests/tools/test_eval_search.py -v
```

If a new metric module or helper is factored into a separate file (e.g. a
`tools/eval_metrics.py`), scope to both:

```
pytest tests/tools/test_eval_search.py tests/tools/test_eval_metrics.py -v
```

Never `pytest tests/` — this ticket's blast radius is exactly
`tools/eval/queries.json`, `tools/eval_search.py`,
`tests/tools/test_eval_search.py` (per Related Code Areas); no other domain's
tests are implicated.

Manual (not part of the automated gate, matches ticket's "no CI wiring" Out of
Scope) — re-run the harness against the live index to record the new baseline
number after the Risk #2 denominator fix and the repaired doc_ids, for the
ticket's own `Test Summary` section:

```
python3 tools/eval_search.py
```

## Anti-Drift Test Guards

- **Threshold-unchanged guard**: an explicit test asserting
  `evaluate.__defaults__` (or the CLI's `--threshold` default) is still `0.80`
  — catches an accidental threshold edit smuggled in alongside the metric/
  category work. Cheap, deterministic, directly enforces AC6.
- **No-CI-wiring guard**: none needed as a pytest test (absence of CI wiring
  isn't something a test proves) — verify manually at Verify phase that no
  `.github/workflows/*.yml` or `Makefile` target was changed to invoke
  `eval_search.py` as a blocking check.
- **Stale-id blocklist guard** (see New Tests #1) doubles as an anti-drift
  guard against a future ticket accidentally reintroducing one of the 7 known-
  stale ids (e.g. by copy-pasting an old entry as a template for a new one).
- **Category-set drift guard**: `test_category_balance`'s per-category minimum
  assertions should use a single source-of-truth list/dict (not scattered
  magic strings) so that adding an 8th category later fails loudly (missing
  minimum) rather than silently passing with 0 coverage — matches the
  "Category semantics ambiguity" risk in investigation.md.
- **Denominator-consistency guard**: a test explicitly comparing
  `recall5`'s effective denominator against `mrr10`'s `queries_with_expected`
  denominator on the same query set, asserting they use the *same* count —
  prevents the two metrics from silently diverging again in the future (this
  is the exact inconsistency this ticket fixes; guard against it recurring
  when a future metric is added).
- **New-field-type guard**: a schema test that fails loudly (not just
  "missing key") if `context_budget`/`allowable_alternatives`/
  `source_lifecycle_assumption` are present but wrong-typed (e.g.
  `context_budget` as a string when the Plan phase picks numeric) — prevents
  silent type drift across future entries added by different contributors.
