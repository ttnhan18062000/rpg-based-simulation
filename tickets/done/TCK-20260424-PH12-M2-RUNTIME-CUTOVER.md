# TCK-20260424-PH12-M2-RUNTIME-CUTOVER

## Title
Phase 12 Milestone 2: Supported Runtime Entrypoint Cutover

## Status
DONE

## Request Summary
Switch the default operational entrypoints (CLI, Serve) from the legacy `src` engine to the hardened `src` engine.

## Scope
- [x] Task 1: Implement delegation logic in `src/__main__.py` to point to `src` by default.
- [x] Task 2: Implement legacy fallback mechanism (e.g., `USE_LEGACY_SRC=1`).
- [x] Task 3: Verify CLI compatibility for `--ticks`, `--seed`, and `--entities`.
- [x] Task 4: Verify REST API cutover (FastAPI server delegation).
- [x] Task 5: Document any CLI argument drift or non-goals.

## Acceptance Criteria
- [x] Running `python3 -m src cli` executes the `src` engine.
- [x] Running `python3 -m src serve` starts the `src` API server.
- [x] Legacy execution is still possible via `USE_LEGACY_SRC=1`.
- [x] Basic smoke tests (Movement, Resource interaction) pass through the cutover entrypoint.

## Completion Summary
Milestone 2 is complete. `src/__main__.py` has been refactored as a thin delegator. V2 engine is now the default for `cli` and `serve` commands. Verified bit-identical results and server availability. Legacy fallback is preserved via `USE_LEGACY_SRC=1`.

## Implementation Notes
- `src/__main__.py` should remain the primary entrypoint but become a thin delegator.
- Non-supported legacy subcommands (like `inspect`) should either be delegated to `src` (if available) or kept in `src` with a warning.
