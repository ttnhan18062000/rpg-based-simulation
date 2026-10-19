---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261014-SIMQ-COMPARE-TOOLS-REFUSE-RUNS-NOT-RECORDED-HOST-INDEPENDENT
phase: done
date: 2026-10-14
tags: [testing, simulation-quality, determinism]
---

# TCK-20261014-SIMQ-COMPARE-TOOLS-REFUSE-RUNS-NOT-RECORDED-HOST-INDEPENDENT

## Title
`simq_reanchor` and `simq_pillar_compare` refuse a run whose manifest does not record it as host-independent

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
`tools/test_architecture/simq_reanchor.py::audit_values` takes its two rows per key as "isolated audit_mode runs" on trust. It checks that the two rows are complete and identical, but nothing checks that either one actually ran under audit_mode. Two unaudited runs that happen to agree would be accepted as anchors. Slow run 38532053464 showed what unaudited runs cost: 14 anchors that had been read as behaviour step-changes were host-speed noise.

rpg's TCK-20261014-UNAUDITED-RUNS-DEPEND-ON-HOST-SPEED-THROUGH-PHASE-BUDGETS-EVEN-WITH-THE-PINNED-NORMAL-GOVERNOR (rpg-next fef0ae77f) adds typed `audit_mode` and `signals_zeroed` fields to RunManifest and the replay manifest, plus `src/observability/reporting/run_determinism.py::require_host_independent_runs`, which raises `NonAuditRunError`. No comparison tool reads those fields yet, and rpg-planner left wiring them in to testing (2026-10-14).

## Scope
1. The rows that `simq_reanchor` reads carry the run manifest's `audit_mode` and `signals_zeroed`, copied from the manifest and never inferred from flags or file names. Investigation found NO committed producer of `rows.jsonl` (it was a session-local driver), so the ticket is re-tiered STANDARD (testing-planner ruling 2026-10-19) and adds the committed producer `tools/test_architecture/simq_audit_rows.py` (reads `run_manifest.json` through `RunArtifactRepository.resolve_path` before deleting the run dir; deletes only its own run ids). `calibrate_simq` also writes the sidecar `quality_report.run_determinism.json` (`run_id`, `audit_mode`, `signals_zeroed`, verbatim from the same run's manifest) beside the report it writes, for the live-side check; the reader/writer is `tools/test_architecture/simq_run_record.py`.
2. `simq_reanchor`: before comparing the pair, refuse with `ReanchorRefused` (naming the key and the run) unless both runs have `audit_mode is True`. Anchors are an audit_mode contract (#531). A pinned-governor run counts as host-independent, but it does not count as an anchor run. Use `run_is_host_independent` / `require_host_independent_runs` for the zeroed-signal half, so there is one definition of "host-independent".
3. `simq_pillar_compare`: refuse a comparison unless the LIVE side is recorded host-independent (`signals_zeroed is True`), through rpg's `require_host_independent_runs`, translating `NonAuditRunError` into `HostIndependenceRefused` (original kept as `__cause__`). A missing field or a missing manifest counts as not recorded. The anchor side is not checked by manifest: committed anchors carry no manifest and can only be written by `simq_reanchor` (testing-planner ruling 2026-10-19; an anchor-format change belongs to the D77 v2 anchor shape). Wired into `test_grade_regression` and `evaluate_simq`; a caller with no manifest is a refusal, not a skip.
4. The refusal says what to do: re-run under audit_mode. There is no `--allow-unaudited` escape hatch. If one is ever needed, it is a separate owner decision.

## Out of Scope
- Any change to rpg's manifest fields or helper (rpg-owned; ask rpg-planner).
- Wiring the check into the gate harness or other tools (`rpg_gate_run.py`, `rpg_gate_harness.py`). File separately if wanted.
- Anchor values, tolerances, bands (baseline_change_policy.md rules 6 and 8).

## Acceptance Criteria
- [x] AC1: a rows producer (`simq_audit_rows`) writes `audit_mode` and `signals_zeroed` from the manifest. A unit test shows it copies them, including the field-absent case (None).
- [x] AC2: `simq_reanchor` refuses a pair where either run has `audit_mode` not True, naming key and run. Separate tests cover: both audit runs accepted; one live run refused; a pinned run (signals_zeroed True, audit_mode False) refused for anchors; an old row with no fields refused.
- [x] AC3: `simq_pillar_compare` refuses when the live side is not recorded host-independent (the anchor side is covered by the reanchor write-time refusal, per the testing-planner ruling of 2026-10-19), with the three negative cases on the live side, plus the sidecar-with-nulls case.
- [x] AC4: the existing simq_reanchor / simq_pillar_compare tests pass unchanged except for fixtures that gain the two fields. No assertion is weakened.
- [x] AC5: `docs/plans/test_architecture/reference/baseline_change_policy.md` states both halves (anchors refused at write time, the live run refused at compare time), citing this ticket and rpg's.

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
See plan.md and investigation.md in stored_artifacts (producer finding, CI blast-radius table, campaign mode). Separate item for review: the `tools/calibrate_simq.py` diff (5 lines: the sidecar write after the report) falls under tools/**; agent-working-planner has no objection.

## Test Summary
`tests/unit/tools tests/simulation_quality tests/tools/test_score_ceilings.py tests/architecture tests/static -m "not slow"`: 1692 passed, 64 skipped, 27 deselected. New: `test_simq_audit_rows.py` (13), reanchor refusal cases, `compare_report` live-manifest cases (incl. no default), sidecar-with-nulls and no-sidecar cases in `test_grade_regression.py` and `test_anchors_audit_mode.py` (real 5-tick `calibrate_simq` runs write the sidecar: audit True/True, and not-audit without the flag). Smoke run: `simq_audit_rows --key sandbox_world_seed42_200t`, 2 runs in 7.7 s, both `audit_mode` True and `signals_zeroed` True, run dirs deleted by id, rows accepted by `simq_reanchor`; the same rows with one `audit_mode` set False are refused naming the key and run id.

## Files Changed
- tools/test_architecture/simq_audit_rows.py (new), tools/test_architecture/simq_run_record.py (new)
- tools/test_architecture/simq_reanchor.py, tools/test_architecture/simq_pillar_compare.py
- tools/calibrate_simq.py (sidecar write), tools/evaluate_simq.py (refusal)
- tests/simulation_quality/test_grade_regression.py, test_anchors_audit_mode.py, tests/tools/test_score_ceilings.py, tests/unit/tools/test_simq_audit_rows.py (new), test_simq_reanchor.py, test_simq_pillar_compare.py
- docs/plans/test_architecture/reference/baseline_change_policy.md

## Completion Summary
Done. A run that is not recorded host-independent can no longer be an anchor (`simq_reanchor`, write time) or be compared against one (`simq_pillar_compare` / `test_grade_regression` / `evaluate_simq`, compare time); the committed rows producer `simq_audit_rows` records the fields from each run's own manifest. Open for the owners: the corpus-diversity guards are not wired (they run audit_mode in-process); a v2 anchor format with a manifest is the D77 rebuild's.
