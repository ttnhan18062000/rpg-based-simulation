---
status: historical
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261025-DROP-UNUSED-JSON-LOGGER-AND-SSE-STARLETTE-DEPENDENCIES
phase: done
date: 2026-10-25
tags: []
---

# TCK-20261025-DROP-UNUSED-JSON-LOGGER-AND-SSE-STARLETTE-DEPENDENCIES

## Title
Drop the unused python-json-logger and sse-starlette runtime dependencies from pyproject.toml

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
Owner approval, 2026-10-25 (#715 issuecomment-6398266862), following TCK-20261025-DROP-UNUSED-XXHASH-DEPENDENCY (#743), whose Out of Scope left the other three packages the codebase-health snapshot lists as unused (`sse-starlette`, `python-json-logger`, `pyyaml`) for their own check. That check found two of them unused and one a false positive.

## Scope
- Remove `sse-starlette>=3.3.0` and `python-json-logger>=2.0.7` from `[project].dependencies` in pyproject.toml.
- Re-lock with `uv lock`.

## Out of Scope
- `pyyaml`: kept. 28 files under src/ import it as `yaml`. The snapshot lists it only because `CORE_DEPENDENCY_IMPORT_OVERRIDES` in codebase/reports/codebase_health_baseline.py has no `pyyaml` -> `yaml` entry. That fix is codebase's; lead-planner sent codebase-planner a finding.
- Editing history: done tickets, stored artifacts, monitoring shards and codebase_health_history.jsonl keep their mentions.

## Acceptance Criteria
- pyproject.toml declares neither package.
- uv.lock has no python-json-logger package. It keeps sse-starlette, which `mcp` requires (the `search-mcp` extra and the dev group).
- The scoped tests pass with `import pythonjsonlogger` and `import sse_starlette` made to fail.

## Related Tickets
- TCK-20261025-DROP-UNUSED-XXHASH-DEPENDENCY
- TCK-20260929-RETIRE-SCRIPTS-DIR
- TCK-20260819-STANDARD-CODEBASE-HEALTH-BASELINE-TARGET
- TCK-20261002-UV-DECLARE-AND-LOCK

## Related Docs
- docs/guidelines/agent_working_environment.md

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261002-UV-DECLARE-AND-LOCK/investigation.md (item 4)

## Related Code Areas
- pyproject.toml; uv.lock

## Assumptions / Open Questions
- None.

## Implementation Notes
`git grep` on origin/main (0613ed19a) finds no import of `pythonjsonlogger` or `sse_starlette` in any tracked file, and no import string in a logging or server config. The project's JSON log formatter is its own (`src/logging/formatter.py` `JsonFormatter`). src/ serves no server-sent-events endpoint (no `EventSourceResponse`, no `text/event-stream`). The only code mentions are the health checker's own override map and its tests. TCK-20260929-RETIRE-SCRIPTS-DIR removed python-json-logger's last import, which was unreferenced.

`uv tree --invert`: nothing else depends on python-json-logger. sse-starlette is required by `mcp`, so it stays locked and installed wherever the `search-mcp` extra or the dev group is installed; only a plain base install loses it. `uv lock` resolved 152 packages and removed only python-json-logger v4.2.0; uv.lock loses 13 lines. Installed venvs drop python-json-logger at their next `uv sync --locked`.

## Test Summary
Ran tests/codebase, tests/architecture, tests/unit/core, tests/integration/kernel, tests/api, tests/unit/api and tests/logging (`-m "not slow and not extra_slow"`, `-n 2`, MemoryMax=3G, `.venv/bin` on PATH) with a sitecustomize that sets `sys.modules["pythonjsonlogger"]` and `sys.modules["sse_starlette"]` to None, so either import fails: 1354 passed, 1 failed. The failure, `tests/api/test_observability_websocket.py::test_observability_websocket_suite`, was a harness artifact: `tests/helpers/live_server.py` starts `python -m src` with the inherited environment, and a PYTHONPATH holding only the shim dir dropped the repo root, so the server never became ready. A control shim that blocks nothing failed the same way. With the repo root also on PYTHONPATH, the control and the blocked run both pass (1 passed each), and a child process confirms `import sse_starlette` is blocked there.

## Files Changed
pyproject.toml, uv.lock

## Completion Summary
python-json-logger and sse-starlette are no longer declared. Nothing imported either one, and the scoped tests pass with both imports blocked.
