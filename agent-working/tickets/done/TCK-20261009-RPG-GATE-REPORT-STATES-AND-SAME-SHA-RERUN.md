---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261009-RPG-GATE-REPORT-STATES-AND-SAME-SHA-RERUN
phase: done
date: 2026-10-09
tags: [testing, regression, simulation-quality]
---

# TCK-20261009-RPG-GATE-REPORT-STATES-AND-SAME-SHA-RERUN

## Title
The rpg gate report evaluates validity exactly and outcomes paired against both baselines, reruns the same SHA on non-pass, and reports six states

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Child 4 of TCK-20261009-RPG-GATE-REPORT-TESTING-INFRA-EPIC. States (the metric set v1, adopting outcome neutrality): pass / fail (VALIDITY only) / drift (OUTCOME only: "trace the cause") / unstable / stale / no-data.

## Scope
1. Evaluation per metric id and group:
   - validity: `violations > 0` gives `fail`, with up to 5 examples; otherwise `pass`. `run`-scope metrics are judged per (world, seed); `pooled`-scope metrics are judged per world from the pooled document (harness step 5);
   - outcome: paired by `(id, group, key, tick)` across seeds; the per-seed difference against the LAST baseline and the milestone-FIRST baseline. `drift` when |mean diff| > k*SE AND > the metric's floor (k and floors from rpg's config; a floor keyed by `id` applies to every key and tick); otherwise `pass`. Report both references.
   - `stale` (child 2) and `no-data` (child 3) pass through; neither ever becomes pass.
2. Same-SHA rerun: when a report has any `fail` or `drift`, rerun the affected (world, seed) set once at the same SHA (fresh processes). If the rerun disagrees, mark those metrics `unstable` and route them to test infrastructure (roadmap §4.5, nondeterminism), not to the feature team.
3. Ownership (child 1's metric registry): an unowned `fail` fails the report; an owned one shows as known; an unowned `drift` is listed as "needs a trace ticket" (advisory); expired entries behave like the slow registry.
4. Output: a JSON report (machine) plus a markdown summary (step summary and rolling issue body): states per metric, both references, the examples, and the cited oracle per validity metric (from rpg's config).
5. The report's verdict, for CI: red only for an unowned or expired `fail`, or for `unstable`. Drift never makes the job red.

## Out of Scope
- Opening or updating the rolling issue (child 5).

## Acceptance Criteria
1. Unit tests for each state, from fixture documents, covering both references, the k*SE AND floor rule (one case inside SE but over the floor, one over SE but under the floor), owned/unowned/expired, and a rerun disagreement giving unstable.
2. The report cites each validity metric's oracle from the config, never from code constants.
3. Standard close.

## Related Tickets
- TCK-20261009-RPG-GATE-REPORT-TESTING-INFRA-EPIC; depends on TCK-20261009-KNOWN-REDS-REGISTRY-SHARED-MODULE, TCK-20261009-RPG-GATE-BASELINE-FORMAT-AND-STALENESS, TCK-20261009-RPG-GATE-PINNED-FRESH-PROCESS-HARNESS

## Related Docs
None.

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261009-RPG-GATE-REPORT-STATES-AND-SAME-SHA-RERUN/`

## Related Code Areas
None.

## Assumptions / Open Questions
None.

## Implementation Notes
- New `tools/test_architecture/rpg_gate_report.py` (rules in its docstring): `evaluate` (validity exact per (world, seed) for run scope and per world for pooled scope; outcome paired by `(id, group, key, tick)` across seeds against the LAST and milestone-FIRST baselines, drift when `|d| > k*se` AND `|d| > floor(id)`), `build_report` (same-SHA rerun once on a fail or drift, then ownership, then the verdict), `render_markdown`, and a CLI (`--fail-on-red`).
- Decisions where the ticket was silent (flagged to rpg-planner): a pooled outcome row has one value and no standard error, so it drifts on the floor alone (confirmed); an outcome needs at least two paired seeds for a standard error (otherwise no-data); any no-data seed stops outcome judgement for that world (a partial seed set would change what an outcome means); a stale reference gives `stale` for the outcome (validity is unaffected, it never uses a baseline); drift against either reference is drift, stale beats no-data beats pass; `stale`/`no-data` do not make the job red (visible in counts and the table).
- Rerun: a run-scope validity fail reruns its seed; everything else reruns every seed of its world; a finding whose state differs on the rerun becomes `unstable`, routed to test infrastructure, and makes the job red. The pooled document is recomputed only when every seed of the world was rerun.
- Ownership uses the shared registry (`state: fail` / `state: drift`, ids `<metric_id>` or `<metric_id>:<group>`): known / unowned / expired for a fail, traced / needs-trace-ticket / expired for a drift; stale mappings are listed per state.
- `known_reds.owner_of`, `classify` and `stale_mappings` now raise `ValueError` when the registry has entries with a `state` and no state is passed (testing-planner's note on #490). The slow registry has no states, so it is unaffected.
- Thresholds travel on the metric rows (rpg-planner and testing-planner, 2026-10-11): outcome rows carry `k` and `floor`, validity rows an `oracle`; the report reads only the documents and never imports `src/`; the config holds only the matrix, `stale_after_days` and the stop lines (no threshold keys, no default floor). A run outcome row without `k`/`floor` (a pooled one without `floor`) is a contract error: `no-data` with the reason. Rows of one `(id, group)` that disagree on `k`, `floor` or `oracle` across the run set give `no-data` "mixed metric module versions". Each outcome result shows "judged on n/m seeds". No-data findings carry the document's `reason` (`run_error`, `metric_error`, `harness_error`, `seed_no_data`) or `contract_error`; run errors are listed prominently in the markdown (an rpg defect) without turning the job red. Cosmetics from the #501 review: the stop-line docstring no longer lists validity rows, and a v1 owner ruling records `stop_lines_crossed` beside it.

## Test Summary
`pytest tests/unit/tools/test_rpg_gate_report.py` 28 passed (fixture documents): pass; validity fail per seed with 5 examples and the config oracle; pooled validity fail per world; drift needs k*SE AND the floor (one case inside SE but over the floor, one over SE but under the floor); both references reported and drift against either is drift; the floor applies to every key and tick; pooled outcome on the floor alone; stale never pass, validity unaffected, stale does not hide the other reference's drift; no-data for no baseline, a missing row, too few paired seeds, a no-data seed, a missing seed, a missing pooled document; owned / unowned / expired; a drift entry does not own a fail and a fail entry does not trace a drift; group ids; stale mappings; state-required registry calls; rerun disagreeing gives unstable and red, agreeing keeps the state and reruns every seed of the world, a vanishing drift is unstable; no rerun when nothing fails; markdown and JSON; the CLI; missing k or floor and mixed versions give no-data; the judged-seed count; the split no-data reasons and the prominent run error; validity judged from the seeds that have data. With the baseline, known-reds and slow report tests: 141 passed. An end-to-end run on the stub harness output (2 seeds, `sandbox_world`) produced the JSON and markdown.

## Files Changed
- new: `tools/test_architecture/rpg_gate_report.py`, `tests/unit/tools/test_rpg_gate_report.py`
- changed: `tools/test_architecture/known_reds.py` (state required), `tools/test_architecture/rpg_gate_baseline.py` (the two #501 cosmetics), `tests/unit/tools/test_rpg_gate_baseline.py`

## Completion Summary
The rpg gate report judges validity exactly, outcomes paired against both baselines with k*SE and a floor, reruns the same SHA once on a fail or drift to mark unstable, applies the ownership registry and gives a CI verdict that is red only for an unowned or expired fail or an unstable metric. Gaps stated: the choices listed in the Implementation Notes where the ticket was silent need rpg-planner's agreement; the rerun wiring through the harness is exercised by the stub only in the CLI path (the unit tests inject a fake rerun); real metrics wait for rpg's module.
