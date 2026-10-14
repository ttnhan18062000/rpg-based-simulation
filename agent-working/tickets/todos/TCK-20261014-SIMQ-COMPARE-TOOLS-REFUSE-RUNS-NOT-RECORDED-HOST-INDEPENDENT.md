---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261014-SIMQ-COMPARE-TOOLS-REFUSE-RUNS-NOT-RECORDED-HOST-INDEPENDENT
phase: open
date: 2026-10-14
tags: [testing, simulation-quality, determinism]
---

# TCK-20261014-SIMQ-COMPARE-TOOLS-REFUSE-RUNS-NOT-RECORDED-HOST-INDEPENDENT

## Title
`simq_reanchor` and `simq_pillar_compare` refuse a run whose manifest does not record it as host-independent

## Status
BLOCKED (on rpg's determinism fix reaching main; see Assumptions)

## Tier
hotfix

## Type
repair

## Priority
P1

## Request Summary
`tools/test_architecture/simq_reanchor.py::audit_values` takes its two rows per key as "isolated audit_mode runs" on trust. It checks that the two rows are complete and identical, but nothing checks that either one actually ran under audit_mode. Two unaudited runs that happen to agree would be accepted as anchors. Slow run 38532053464 showed what unaudited runs cost: 14 anchors that had been read as behaviour step-changes were host-speed noise.

rpg's TCK-20261014-UNAUDITED-RUNS-DEPEND-ON-HOST-SPEED-THROUGH-PHASE-BUDGETS-EVEN-WITH-THE-PINNED-NORMAL-GOVERNOR (rpg-next fef0ae77f) adds typed `audit_mode` and `signals_zeroed` fields to RunManifest and the replay manifest, plus `src/observability/reporting/run_determinism.py::require_host_independent_runs`, which raises `NonAuditRunError`. No comparison tool reads those fields yet, and rpg-planner left wiring them in to testing (2026-10-14).

## Scope
1. The rows that `simq_reanchor` and `simq_pillar_compare` read carry the run manifest's `audit_mode` and `signals_zeroed`, copied from the manifest and never inferred from flags or file names. Find which producer writes `rows.jsonl` (investigate first) and add the fields there.
2. `simq_reanchor`: before comparing the pair, refuse with `ReanchorRefused` (naming the key and the run) unless both runs have `audit_mode is True`. Anchors are an audit_mode contract (#531). A pinned-governor run counts as host-independent, but it does not count as an anchor run. Use `run_is_host_independent` / `require_host_independent_runs` for the zeroed-signal half, so there is one definition of "host-independent".
3. `simq_pillar_compare`: refuse a before/after comparison unless both sides are recorded as host-independent (`signals_zeroed is True`). A missing field, as in an older manifest, counts as not recorded, the same as in rpg's helper.
4. The refusal says what to do: re-run under audit_mode. There is no `--allow-unaudited` escape hatch. If one is ever needed, it is a separate owner decision.

## Out of Scope
- Any change to rpg's manifest fields or helper (rpg-owned; ask rpg-planner).
- Wiring the check into the gate harness or other tools (`rpg_gate_run.py`, `rpg_gate_harness.py`). File separately if wanted.
- Anchor values, tolerances, bands (baseline_change_policy.md rules 6 and 8).

## Acceptance Criteria
- [ ] AC1: a rows producer writes `audit_mode` and `signals_zeroed` from the manifest. A unit test shows it copies them, including the field-absent case (None).
- [ ] AC2: `simq_reanchor` refuses a pair where either run has `audit_mode` not True, naming key and run. Separate tests cover: both audit runs accepted; one live run refused; a pinned run (signals_zeroed True, audit_mode False) refused for anchors; an old row with no fields refused.
- [ ] AC3: `simq_pillar_compare` refuses when either side is not recorded host-independent, with the same three negative cases.
- [ ] AC4: the existing simq_reanchor / simq_pillar_compare tests pass unchanged except for fixtures that gain the two fields. No assertion is weakened.
- [ ] AC5: `docs/plans/test_architecture/reference/baseline_change_policy.md` states the refusal in one line, citing this ticket and rpg's.

## Related Tickets
- TCK-20261014-UNAUDITED-RUNS-DEPEND-ON-HOST-SPEED-THROUGH-PHASE-BUDGETS-EVEN-WITH-THE-PINNED-NORMAL-GOVERNOR (rpg; provides the fields and helper)
- TCK-20261014-SIMQ-SINGLE-REANCHOR-ON-BASELINE-V1 (its AC1 pairs should go through this check; land this first)
- TCK-20261011-SIMQ-GRADE-ANCHORS-RUN-UNDER-AUDIT-MODE (#531)
- TCK-20261014-SIMQ-PILLARS-COMPUTED-FROM-TYPED-RECORDS-WITH-SEED-SPREAD-D77 (the later harness should keep this refusal)

## Related Docs
- docs/plans/test_architecture/reference/baseline_change_policy.md

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261011-SIMQ-GRADE-ANCHORS-RUN-UNDER-AUDIT-MODE/

## Related Code Areas
- tools/test_architecture/simq_reanchor.py (`audit_values`)
- tools/test_architecture/simq_pillar_compare.py
- src/observability/reporting/run_determinism.py (rpg, read-only here)
- the `rows.jsonl` producer (to be located)

## Assumptions / Open Questions
- Blocked until rpg's fix (fef0ae77f on rpg-next) is on main. Unblock by moving Status to OPEN when the RPG PR carrying it merges.
- Should land before the v1 re-anchor runs, so AC1 of TCK-20261014-SIMQ-SINGLE-REANCHOR-ON-BASELINE-V1 is mechanically checked.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
