# Phase 12 M1 Test Plan: Readiness Verification

## 1. Documentation Consistency Check
- **Task**: Cross-reference `phase12_cutover_allowed_surface.md` with `legacy_replacement_ledger.md`.
- **Expected**: Every "Allowed" item must be marked as `SUPPORTED` in the ledger.

## 2. Forbidden Assumption Test
- **Task**: Run a smoke test on `src_v2` attempting to access `XP` or `Level` logic.
- **Expected**: Logic should be missing, no-op, or explicitly rejected (not leaking from legacy `src`).

## 3. Rollback Procedure Validation
- **Task**: Verify the `BROKER_DISABLED` flag correctly switches the runtime to the in-memory `V2EngineManager` path.
- **Expected**: Toggling flags should cleanly switch between "Cutover" and "Legacy-Compatible" modes.

## 4. Entrypoint Audit
- **Task**: List all current entrypoints in `src_v2/cli/entry.py`.
- **Expected**: All endpoints must align with the "Allowed" surface.
