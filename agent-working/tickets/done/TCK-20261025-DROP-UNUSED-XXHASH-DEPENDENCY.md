---
status: historical
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261025-DROP-UNUSED-XXHASH-DEPENDENCY
phase: done
date: 2026-10-25
tags: []
---

# TCK-20261025-DROP-UNUSED-XXHASH-DEPENDENCY

## Title
Drop the unused xxhash runtime dependency from pyproject.toml and uv.lock

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
Owner approval, 2026-10-25 (#715 issuecomment-6396617829), following TCK-20261025-README-DETERMINISM-AND-ENTITIES-FLAG-CLAIMS (#741). `xxhash>=3.4.0` is a declared runtime dependency, but no file in src/, tools/, tests/, scripts or Dockerfiles imports it. The codebase-health snapshot has listed it under `unused_core_dependencies` since TCK-20260819-STANDARD-CODEBASE-HEALTH-BASELINE-TARGET. TCK-20261002-UV-DECLARE-AND-LOCK left it in place for a later deptry pass.

## Scope
- Remove `xxhash>=3.4.0` from `[project].dependencies` in pyproject.toml.
- Re-lock with `uv lock`.

## Out of Scope
- The other declared-but-unimported packages the snapshot lists (`sse-starlette`, `python-json-logger`, `pyyaml`). `pythonjsonlogger` and `yaml` may be loaded by import strings or tools; each needs its own check.
- Editing history: archived docs (docs/archive/pitch.md), done tickets, stored artifacts and the monitoring shards keep their mentions.

## Acceptance Criteria
- pyproject.toml declares no xxhash, and uv.lock has no xxhash package (no other package depended on it).
- The scoped tests pass with any `import xxhash` made to fail.

## Related Tickets
- TCK-20261025-README-DETERMINISM-AND-ENTITIES-FLAG-CLAIMS
- TCK-20261002-UV-DECLARE-AND-LOCK
- TCK-20260819-STANDARD-CODEBASE-HEALTH-BASELINE-TARGET

## Related Docs
- docs/guidelines/agent_working_environment.md

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261002-UV-DECLARE-AND-LOCK/investigation.md (item 4)

## Related Code Areas
- pyproject.toml; uv.lock

## Assumptions / Open Questions
- None.

## Implementation Notes
`git grep -i xxhash origin/main` (9a8ebd63a) finds no code, test, script, Dockerfile or requirements use. The only hits are history (tickets, stored artifacts, monitoring shards, codebase_health_history.jsonl) and docs/archive/pitch.md. `uv lock` resolved 153 packages and removed only xxhash v3.6.0; uv.lock loses 85 lines. Installed venvs keep xxhash until their next `uv sync --locked`, which removes it.

## Test Summary
Ran tests/codebase, tests/architecture, tests/unit/core and tests/integration/kernel (`-m "not slow and not extra_slow"`, `-n 2`, MemoryMax=3G) with a sitecustomize that sets `sys.modules["xxhash"] = None`, so any import fails: 1089 passed. The first run had one failure, `test_make_target_runs_successfully_end_to_end`. It was a local-environment artifact: `make` called /usr/bin/python3, which has no ruff, because the venv was not on PATH. It passes with `.venv/bin` on PATH, as in CI.

## Files Changed
pyproject.toml, uv.lock

## Completion Summary
xxhash is no longer declared or locked. Nothing imported it, and the scoped tests pass with the import blocked.
