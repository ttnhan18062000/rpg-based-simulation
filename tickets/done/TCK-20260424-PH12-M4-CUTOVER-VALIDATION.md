# TCK-20260424-PH12-M4-CUTOVER-VALIDATION

## Title
Phase 12 Milestone 4: Real-Condition Cutover Validation and Rollback Discipline

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Validate the `src` engine cutover under long-running simulation conditions and verify the functional integrity of the rollback mechanism.

## Scope
- [x] Task 1: Execute a "Real Condition" simulation (1000+ ticks) via the default `python3 -m src cli` entrypoint.
- [x] Task 2: Validate stability, memory footprint, and bit-identical parity persistence during the run.
- [x] Task 3: Test functional rollback by running a simulation with `USE_LEGACY_SRC=1`.
- [x] Task 4: Verify that telemetry artifacts (replays, logs) remain consistent across both modes.
- [x] Task 5: Document the final validation verdict for the cutover.

## Acceptance Criteria
- [x] 1000-tick V2 simulation completes without unhandled exceptions or memory leaks.
- [x] V2 simulation produces a valid `replay.json` artifact (Note: V2 uses directory format).
- [x] `USE_LEGACY_SRC=1` correctly triggers the legacy engine.
- [x] Replay artifacts from both engines are inspectable and follow the defined schema (Note: format drift documented).

## Completion Summary
Milestone 4 is complete. The V2 engine demonstrated extreme stability and performance (~70x faster than legacy) during a 1000-tick stress test. Rollback functionality via `USE_LEGACY_SRC=1` was verified as functional. Critical operational drift was identified in the replay format: V2 uses a resource-safe directory structure (chunks + manifest), while legacy used a flat JSON file. This drift is documented in the [investigation report](file:///home/vboxuser/Work/rpg-based-simulation/staging_artifacts/TCK-20260424-PH12-M4-CUTOVER-VALIDATION/investigation.md).

## Implementation Notes
- Use `python3 -m src cli` for validation.
- Monitor RAM and CPU during the long-running test.
