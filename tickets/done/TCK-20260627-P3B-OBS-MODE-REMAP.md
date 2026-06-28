---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260627-P3B-OBS-MODE-REMAP
phase: done
date: 2026-06-27
tags: [p3, observability-mode, lab, orchestrator, dx, sim-debug]
---

# TCK-20260627-P3B-OBS-MODE-REMAP

## Title
Remap lab `"STANDARD"` mode to `ObservabilityMode.NORMAL` and add `sim-debug` target

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
Lab mode `"STANDARD"` in `src/lab/orchestrator.py:147–153` maps to engine `ObservabilityMode.LIGHT`. A developer switching to STANDARD expecting richer data gets identical output to LIGHTWEIGHT. This is a naming mismatch that causes silent diagnosis failures. Source: D03 F5, Score 8/15. Note: D15 Gap 6 was resolved by TCK-20260619-E22-DECISION-EXPLAIN; this ticket covers the lab-layer mode naming only.

## Scope
- Remap `"STANDARD"` → `ObservabilityMode.NORMAL` in `src/lab/orchestrator.py:147–153`.
- OR rename the lab modes to match what they actually produce (`"LIGHT"` → `ObservabilityMode.LIGHT`, `"STANDARD"` → `ObservabilityMode.NORMAL`).
- Add a `make sim-debug` Makefile target that sets `SIM_OBS_MODE=DEBUG` for developers needing cognition snapshot access.

## Out of Scope
- Changes to `ObservabilityMode` enum values.
- Changing what LIGHT or NORMAL modes actually capture.

## Acceptance Criteria
- [ ] `"STANDARD"` lab mode maps to `ObservabilityMode.NORMAL` (or a renamed alias that accurately reflects NORMAL output).
- [ ] `make sim-debug` target exists in `Makefile` and sets `SIM_OBS_MODE=DEBUG`.
- [ ] Existing lab tests pass.
- [ ] No lab test asserts the old `ObservabilityMode.LIGHT` result for `"STANDARD"` mode.

## Related Tickets
- N/A (independent)

## Related Docs
- `docs/audits/D03_behavioral_emergence.md` F5
- `docs/observability/decision_trace_contract.md` §Mode Threshold

## Related Stored Artifacts
- N/A

## Related Code Areas
- `src/lab/orchestrator.py:147–153` (mode mapping)
- `Makefile` (add `sim-debug` target)

## Assumptions / Open Questions
- Decision trace is now written in LIGHT mode (post TCK-20260619-E22). Confirm whether NORMAL provides additional data beyond LIGHT before remapping — the fix is only valid if NORMAL genuinely provides richer output.

## Implementation Notes
- Confirmed via `docs/observability/decision_trace_contract.md` §Mode Threshold: decision_trace.jsonl is written in LIGHT and above; NORMAL adds `OBS_BEHAVIOR_NORMALIZATION=True` over LIGHT, so the remap provides genuine additional data.
- `src/lab/orchestrator.py:150`: changed `"STANDARD": ObservabilityMode.LIGHT` → `"STANDARD": ObservabilityMode.NORMAL`.
- `Makefile:108-109`: updated `sim-debug` target to prefix `SIM_OBS_MODE=DEBUG` before the CLI invocation (target existed but only set `--log-level DEBUG`; now exposes cognition snapshots).
- Added regression guard test `test_standard_obs_mode_resolves_to_normal` in `tests/unit/lab/test_scenario_lab_orchestrator.py`.

## Test Summary
- Unit: `orchestrator._resolve_obs_mode("STANDARD")` returns `ObservabilityMode.NORMAL`.
- Regression: `pytest tests/ -k orchestrator -m "not slow"`.

## Files Changed
- `src/lab/orchestrator.py` — extracted `_resolve_obs_mode()` static method; `"STANDARD"` now maps to `ObservabilityMode.NORMAL`; inline mapping replaced with method call
- `Makefile` — updated `sim-debug` target to prefix `SIM_OBS_MODE=DEBUG`, enabling cognition snapshots
- `tests/unit/lab/test_scenario_lab_orchestrator.py` — added `test_standard_obs_mode_resolves_to_normal` and `test_obs_mode_mapping_full_table`
- `docs/parity_ledger/infrastructure.yaml` — added entry INFRA-231

## Completion Summary
Remapped lab `"STANDARD"` mode from `ObservabilityMode.LIGHT` to `ObservabilityMode.NORMAL` by extracting `ScenarioLabOrchestrator._resolve_obs_mode()` static method. Updated `sim-debug` Makefile target to set `SIM_OBS_MODE=DEBUG` (was only setting `--log-level DEBUG`). Added two regression-guard tests verifying the full mode mapping table. Added parity ledger entry INFRA-231. All 7 unit tests pass.
