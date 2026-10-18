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
OPEN

## Tier
standard (re-tiered 2026-10-19: Scope 1 adds a new committed tool)

## Type
repair

## Priority
P1

## Request Summary
`tools/test_architecture/simq_reanchor.py::audit_values` takes its two rows per key as "isolated audit_mode runs" on trust. It checks that the two rows are complete and identical, but nothing checks that either one actually ran under audit_mode. Two unaudited runs that happen to agree would be accepted as anchors. Slow run 38532053464 showed what unaudited runs cost: 14 anchors that had been read as behaviour step-changes were host-speed noise.

rpg's TCK-20261014-UNAUDITED-RUNS-DEPEND-ON-HOST-SPEED-THROUGH-PHASE-BUDGETS-EVEN-WITH-THE-PINNED-NORMAL-GOVERNOR (rpg-next fef0ae77f) adds typed `audit_mode` and `signals_zeroed` fields to RunManifest and the replay manifest, plus `src/observability/reporting/run_determinism.py::require_host_independent_runs`, which raises `NonAuditRunError`. No comparison tool reads those fields yet, and rpg-planner left wiring them in to testing (2026-10-14).

## Scope
1. The rows that `simq_reanchor` reads carry the run manifest's `audit_mode` and `signals_zeroed`, copied from the manifest and never inferred from flags or file names. Investigation (testing-implementer, 2026-10-19) found that no committed producer of `rows.jsonl` exists: the #531 rows came from a session-local driver. So this ticket commits one, `tools/test_architecture/simq_audit_rows.py`. It runs each key x 2 under `--audit-mode` and reads `<run dir>/manifest.json` before deleting only the run ids it created. Its row shape is documented and pinned by a test. It decides nothing; the refusal stays in `simq_reanchor`.
2. `simq_reanchor`: before comparing the pair, refuse with `ReanchorRefused` (naming the key and the run) unless both runs have `audit_mode is True`. Anchors are an audit_mode contract (#531). A pinned-governor run counts as host-independent, but it does not count as an anchor run. Use `run_is_host_independent` / `require_host_independent_runs` for the zeroed-signal half, so there is one definition of "host-independent".
3. `simq_pillar_compare`: refuse a comparison unless the LIVE side's manifest records it as host-independent (`signals_zeroed is True`), through rpg's `require_host_independent_runs`. A missing field, or a missing manifest, counts as not recorded. The anchor side is not checked by manifest: committed anchors carry none, and their host-independence is a write-time guarantee (#531 provenance now, and from v1 on the refusal in Scope 2). Adding manifest fields to `grade_anchors.json` is an anchor-format change for the D77 rebuild (testing-planner ruling, 2026-10-19). Wire it in where `test_grade_regression` / `evaluate_simq` call `compare_report`.
4. The refusal says what to do: re-run under audit_mode. There is no `--allow-unaudited` escape hatch. If one is ever needed, it is a separate owner decision.

## Out of Scope
- Any change to rpg's manifest fields or helper (rpg-owned; ask rpg-planner).
- Wiring the check into the gate harness or other tools (`rpg_gate_run.py`, `rpg_gate_harness.py`). File separately if wanted.
- Anchor values, tolerances, bands (baseline_change_policy.md rules 6 and 8).

## Acceptance Criteria
- [ ] AC1: `tools/test_architecture/simq_audit_rows.py` writes `audit_mode` and `signals_zeroed` from the manifest. Unit tests use a fake run dir (manifest present, a field absent so the value is None, manifest missing) and run no simulation. It deletes only its own run ids.
- [ ] AC2: `simq_reanchor` refuses a pair where either run has `audit_mode` not True, naming key and run. Separate tests cover: both audit runs accepted; one live run refused; a pinned run (signals_zeroed True, audit_mode False) refused for anchors; an old row with no fields refused.
- [ ] AC3: `simq_pillar_compare` refuses when the live side is not recorded host-independent, with three negative cases on the live side (live run, old manifest with no fields, no manifest), and the callers pass the manifest. The anchor side is covered by the Scope 2 write-time refusal.
- [ ] AC4: the existing simq_reanchor / simq_pillar_compare tests pass unchanged except for fixtures that gain the two fields. No assertion is weakened.
- [ ] AC5: `docs/plans/test_architecture/reference/baseline_change_policy.md` states both halves (anchors are refused at write time, the live run is refused at compare time), citing this ticket and rpg's.

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
- UNBLOCKED 2026-10-19: rpg's fix is on main via #645 (3597c08d3, squash of rpg-next). `src/observability/reporting/run_determinism.py` (`NonAuditRunError`, `run_is_host_independent`, `require_host_independent_runs`), `src/engine/signal_source.py::ZeroedSignalSource` / `signals_are_zeroed`, and the `audit_mode` / `signals_zeroed` fields in `artifact_repository.py` are all present on main.
- Should land before the v1 re-anchor runs, so AC1 of TCK-20261014-SIMQ-SINGLE-REANCHOR-ON-BASELINE-V1 is mechanically checked.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
