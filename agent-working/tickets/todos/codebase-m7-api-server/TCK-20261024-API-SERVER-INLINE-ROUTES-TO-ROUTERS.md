---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261024-API-SERVER-INLINE-ROUTES-TO-ROUTERS
phase: open
date: 2026-10-24
tags: [architecture, api-design]
---

# TCK-20261024-API-SERVER-INLINE-ROUTES-TO-ROUTERS

## Title
The 16 remaining inline routes in create_v2_app move into routers under src/api/routes/ and the function-local imports go to module top

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P2

## Request Summary
M7 batch 1, ticket 3 of 3. User approval 2026-10-24, logged at https://github.com/ttnhan18062000/rpg-based-simulation/issues/715#issuecomment-6384147652. rpg-planner cleared the file on #697.

After ticket 2, `create_v2_app` still defines 16 routes inline:
- `/metrics` and `/health`;
- `/api/v1/observability/live/status`, `/snapshot`, `/entities/{entity_id}`, `/health` and `/stream-health`;
- `/api/v1/state` and `/api/v1/inspect`;
- `/api/v1/entities` and `/api/v1/entities/{entity_id}`;
- `/api/v1/control/pause` and `/api/v1/control/resume`;
- `/api/v1/test/publish_event`;
- `/api/v1/observability/history/runs/{run_id}/report`.

It also imports inside the function (34 `PLC0415` rows). When this ticket is done, `create_v2_app` is a short app factory: middleware, lifespan and `include_router` calls.

## Scope
1. **Move each inline route into an `APIRouter` module under `src/api/routes/`**, grouped by concern; plan.md settles the grouping.
   - First find out what `src/api/routes/state.py`, `control.py` and `health.py` are. They exist, but `create_v2_app` does not include them.
   - If they are dead code or duplicate the inline routes, record it and tell codebase-planner. Do not delete or merge them in this ticket without that answer: they are rpg's code.
2. **Keep each route's surface**: path, methods, endpoint function name, `response_model`, `response_class`, dependency list, and **registration order** relative to every other route (ticket 1 pins it). The `include_router` calls for the new modules take the inline definitions' positions.
3. **Move function-local imports in `server.py` to module top** (`PLC0415`) wherever no import cycle results.
   - Where a local import guards a real cycle or an optional dependency, keep it with `# noqa: PLC0415  # <reason>` (ruff 0.17 form) and list it in plan.md.
   - Check for cycles with `lint-imports`; the import-linter contracts are blocking.
4. **Fix in passing only what the move touches**:
   - `F401`, `I001`, `ANN202` on moved handlers, and `D100` (module docstring);
   - `BLE001` and `e3-silent-except` (lifespan) only if the fix is behaviour-identical; otherwise leave them and say why.
5. **The `set_quality_persistence` mypy `arg-type` row**: fix it only if the fix is behaviour-identical (for example, an explicit `None` guard that matches today's path). Otherwise leave it.
6. **Ratchet** all of `src/api/server.py`'s rows in `codebase/baselines/code_health_exceptions.jsonl`, and the mypy and Pyrefly baselines, to the new values through their sync targets. New router modules add no rows.
7. **For rpg, on the PR.** Two spots will move, and the implementer records their new file:line in this ticket; codebase-planner puts them on the PR:
   - the wildcard CORS block, today `server.py:109` (`TCK-20261019-SEMGREP-BASELINE-FINDINGS-IN-SRC-TRIAGE`);
   - the `/metrics` route behind `require_admission`, today `server.py:176` (`TCK-20261021-WATCHDOG-POLLS-AN-ADMISSION-GATED-METRICS-ENDPOINT`).

## Out of Scope
- Renaming `create_v2_app`. The `n4-version-marker-name` row stays; the user chose not to rename in this batch.
- Any change to behaviour, paths, auth or response shapes, and any change to existing router modules beyond adding the moved routes.
- Reshaping handlers that return raw dicts through presenters or schemas. That is an api-design follow-up and rpg's call.

## Acceptance Criteria
- Ticket 1's characterization tests pass with the fixture unchanged.
- `create_v2_app` has no nested route functions. `server.py` has no `PLC0415` left except the listed, justified `noqa` lines.
- `lint-imports` passes and the code-health gate reports 0 new and 0 worse.
- Every `server.py` baseline row is at or below its new measured value, and mypy and Pyrefly report 0 new.
- `tests/api`, `tests/architecture/test_api_read_model_guard.py`, `tests/codebase` and `tests/static` pass.
- Per roadmap section 9, the determinism and replay suites that import the API also pass. Find them with `graphify query "create_v2_app"`.
- The ticket records the new file:line of the CORS block and of the `/metrics` route.

## Related Tickets
- Previous: `TCK-20261024-API-SERVER-OBSERVABILITY-UI-STATIC-PAGE`
- rpg tickets that will rebase onto this: `TCK-20261019-SEMGREP-BASELINE-FINDINGS-IN-SRC-TRIAGE`, `TCK-20261021-WATCHDOG-POLLS-AN-ADMISSION-GATED-METRICS-ENDPOINT`

## Related Docs
- `docs/plans/codebase_health/python_code_craft_roadmap.md` (M7 row, decision 7 amendment, section 9)
- `docs/guidelines/python_code_standard.md`

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20260623-TYPE-CHECKER/investigation.md` (route inventory, with older line numbers)

## Related Code Areas
- `src/api/server.py`, `src/api/routes/`
- `src/api/dependencies.py`, `src/api/admission_control.py`, `src/api/auth.py`
- `codebase/baselines/`

## Assumptions / Open Questions
- Open: where the moved routes go when their names match the existing, unregistered modules (Scope 1).

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
