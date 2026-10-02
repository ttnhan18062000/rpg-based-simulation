---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20261002-UV-DECLARE-AND-LOCK
artifact_type: plan
tags: [setup]
---

# Plan — TCK-20261002-UV-DECLARE-AND-LOCK

## Steps

1. `pyproject.toml`: add the undeclared direct runtime packages to `[project] dependencies`; replace the `dev` extra with `[dependency-groups] dev` (plus opt-in `profiling`); keep the `knowledge` and `search-mcp` extras.
2. Lock with the old pins as temporary constraints, remove the constraints, re-lock; confirm `uv lock --check`.
3. Regenerate `requirements.txt` with the documented export command; compare name and version sets with the old file.
4. Update Prerequisites and First-Time Setup in `docs/guidelines/agent_working_environment.md`; add a "Changing a dependency" subsection.
5. Verify: clean 3.13 `pip install -r requirements.txt`, the pinned tests, export reproducibility, `uv sync`.

## Scope guards

No `src/`, `.claude/`, `CLAUDE.md`, `Makefile`, `.github/workflows/` or existing `tests/` file. `requirements-knowledge.txt` untouched. mypy gate untouched.

## Acceptance-criteria map

| Criterion | Step |
|---|---|
| Every imported pin declared; dev group; name-set check | 1, 3 |
| Direct/transitive classification recorded | ticket Implementation Notes |
| `uv lock --check` exits 0; lock entry matches pyproject | 2 |
| Export reproducible, no ML stack, no-ML test passes | 3, 5 |
| Clean 3.13 pip install succeeds | 5 |
| Static and tools tests pass, no test edited | 5 |
| Python version statements consistent, source documented | 4 |
| Environment doc updated, knowledge setup unchanged | 4 |
| No `src/`, `.claude/`, `CLAUDE.md` in diff | 5 |
