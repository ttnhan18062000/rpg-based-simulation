---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261009-PYTHON-FLOOR-3-12
phase: done
date: 2026-10-09
tags: [architecture, delivery]
---

# TCK-20261009-PYTHON-FLOOR-3-12

## Title
Raise the Python floor to 3.12 (amends roadmap decision 12)

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
Owner decision 2026-10-09: raise the Python floor from 3.11 to 3.12 now, and to 3.13 later once agent-working can move `.venv-knowledge`. This amends decision 12 of `docs/plans/codebase_health/python_code_craft_roadmap.md` ("keep the `>=3.11` floor; raising it would break the 3.12 knowledge-search venv"): 3.12 does not break that venv. Brief from codebase-planner.

## Scope
- `pyproject.toml`: `requires-python = ">=3.12"`, `[tool.mypy] python_version = "3.12"`, new explicit `[tool.ruff] target-version = "py312"` with a comment that it moves together with `requires-python`
- `uv.lock` re-locked with `uv lock` (not `--upgrade`): no package version changes for 3.13; only the <3.12 forks and markers go
- Docs: `README.md`, `docs/guidelines/agent_working_environment.md`, roadmap decision 12 amendment, `config/rendering/grade_thresholds.toml` comment
- Handoff to agent-working (`handoff_to_agent_working.md`, "Update 2026-10-09")

## Out of Scope
- Any file under `src/` (frozen). M7 candidates, left as is: `src/api/schemas.py`'s `typing_extensions` TypedDict import and `src/lab/results.py`'s now-dead fallback
- `tools/search/Dockerfile` (`python:3.11-slim`; agent-working's search server): theirs to align
- `tests/visual_assets/test_py311_fstrings.py` (asset domain): still valid, stricter than needed
- Raising the floor to 3.13 (waits on the knowledge venv)
- `tests/codebase/test_mypy_gate.py`'s `python_version = "3.11"`: a synthetic pyproject fixture, not the real config

## Acceptance Criteria
- [x] `requires-python`, mypy `python_version` and an explicit ruff `target-version` all say 3.12 (ruff's comment says it moves with the floor)
- [x] `uv.lock` has no package version change for 3.13: the `uv export --frozen --no-hashes --python 3.13` outputs differ only by a marker-excluded line (see Test Summary); resolution-marker counts reported
- [x] `make typecheck-py` 0 new; `make code-health` 0 new / 0 worse
- [x] Docs and the roadmap amendment updated
- [x] `tests/static` and `tests/codebase` pass
- [x] The three untouched files are named in the ticket; `git diff --stat` lists no path under `src/`

## Related Tickets
- TCK-20261008-BACKEND-IMAGE-BUILDS-FROM-UV-LOCK
- TCK-20261002-UV-DECLARE-AND-LOCK

## Related Docs
- docs/plans/codebase_health/python_code_craft_roadmap.md
- docs/guidelines/agent_working_environment.md
- docs/plans/codebase_health/handoffs/handoff_to_agent_working.md

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261009-PYTHON-FLOOR-3-12/

## Related Code Areas
- pyproject.toml
- uv.lock
- config/rendering/grade_thresholds.toml

## Assumptions / Open Questions
- Verified by codebase-planner 2026-10-09 on this machine: `.venv-knowledge` is Python 3.13.7 (`pyvenv.cfg`, created 2026-10-02) and `import torch, sentence_transformers, sqlite_vec` works; `agent_working_environment.md` still says 3.12.3 and a blocked torch index. The 3.13 floor waits on the other machine (question in the agent-working handoff); owner decision: ship 3.12 now, 3.13 as a later small ticket once agent-working confirms.

## Implementation Notes
- `pyproject.toml`: floor `>=3.12`; mypy `python_version = "3.12"`; new `[tool.ruff]` table with `target-version = "py312"` (previously ruff had no table and fell back to `requires-python`; the comment says to move the three together). The `[tool.ruff]` table sits just above `[tool.ruff.lint]`.
- `uv.lock` via `uv lock` (no `--upgrade`): 130 -> 127 packages. Removed: `async-timeout 5.0.1` (only for python < 3.11.3, via redis) and the `numpy 2.4.6` / `scipy 1.17.1` fork copies used on python < 3.12. Resolution markers: top-level list 7 -> 6 entries; packages carrying their own marker lists 4 -> 0; `requires-python` `>=3.11` -> `>=3.12`.
- Docs: README requirement line; `agent_working_environment.md` Python row (floor 3.12, why not 3.13 yet, `.python-version`/CI on 3.13); roadmap decision 12 amendment line plus a bracket note in the "Environment today" paragraph; `grade_thresholds.toml` comment.
- Handoff: `handoff_to_agent_working.md` "Update 2026-10-09". No test was edited, so no decision 8.11 notice to testing.
- Left alone on purpose: `docs/architecture/performance_optimization_decisions.md` (an ADR's evidence lines quoting `requires-python >=3.11` as history).

## Test Summary
- `uv export --frozen --no-hashes --python 3.13` before vs after: the only difference is `async-timeout==5.0.1 ; python_full_version < '3.11.3'` (and its `# via redis` comment), a line that never applies on 3.12 or 3.13, so the installed set for 3.13 is identical; same single-line diff for `--python 3.12`. numpy 2.5.0 and scipy 1.18.0 (the 3.13 versions) are unchanged. `uv lock --check` passes; `uv sync --locked --dry-run --python 3.13` resolves.
- `make typecheck-py`: no output, exit 0 (0 new errors). `make code-health`: `OK: 0 new, 0 worse, 57 improved, 15 gone, 3651 unchanged` (same as main). Run one at a time under the 2 GB cap.
- `tests/static` + `tests/codebase`: 544 passed, 2 skipped; the two known local 60 s make-target tests deselected.
- Not run: an independent 3.12 interpreter (this machine has no python3.12; mypy `python_version = "3.12"` type-checks `src/` against 3.12 semantics). `make knowledge-index-update` not run (times out under the cap).

## Files Changed
- `pyproject.toml`, `uv.lock`
- `README.md`, `docs/guidelines/agent_working_environment.md`, `docs/plans/codebase_health/python_code_craft_roadmap.md`, `config/rendering/grade_thresholds.toml`, `docs/plans/codebase_health/handoffs/handoff_to_agent_working.md`

## Completion Summary
The Python floor is 3.12 in `pyproject.toml`, mypy and ruff, the lock lost only its <3.12 forks, and the gates are unchanged. 3.13 follows once agent-working confirms both machines' knowledge venvs (this machine's is already 3.13.7); the question is in the handoff.
