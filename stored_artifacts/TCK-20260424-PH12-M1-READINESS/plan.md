# Phase 12 Milestone 1 Execution Plan

## 1. Surface Freezing
- Audit `docs/engine/phase12_cutover_allowed_surface.md` and `docs/engine/phase12_cutover_constraints.md`.
- Verify these documents are consistent with the `LEG-RPG-*` and `LEG-SYS-*` entries in `legacy_replacement_ledger.md`.
- Create a "frozen" snapshot of the allowed surface in `investigation.md`.

## 2. Scope Separation
- Explicitly list all logic categories that are **excluded** from cutover (e.g., XP, Levels, Economy breakthroughs).
- Ensure `V2EngineManager` is configured to reject or ignore unsupported calls.

## 3. Consumer/Workflow Definition
- Identify the specific CLI commands and API endpoints that will be prioritized for cutover in Milestone 2.
- Define the "Primary Supported Workflow" (e.g., Headless CLI simulation with Replay).

## 4. Rollback Readiness
- Document the process for switching back to legacy `src` if a cutover failure is detected.
- Confirm that `BROKER_DISABLED` and `TELEMETRY_DISABLED` flags are stable for fallback.

## 5. Entry Publication
- Publish the `phase12_entry_package.md` once all tasks are complete.
