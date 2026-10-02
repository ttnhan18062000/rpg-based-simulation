---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20261002-CODE-HEALTH-TOOL-CONFIG
phase: done
date: 2026-10-02
tags: []
---

# TCK-20261002-CODE-HEALTH-TOOL-CONFIG

## Title
M3a: Configure and confirm code-health tools (ruff check, complexipy, jscpd, line-count script)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
First part of measuring the existing codebase's craft debt with no src/ edits. The author wants configuration for ruff check (no formatter), complexipy, jscpd, and a small line-count script for function, class and module length, because no existing tool offers that with a baseline, plus a make lint-py entry point. Each tool must be confirmed to work on this repo or be dropped with the reason recorded, because the versions and features in the roadmap came from web research and are not all verified. It depends on M2 (uv) for installing the tools. The shared constraints apply: no src/ edits, no autofix or reformat or inline suppression comments, no simulation behaviour change, tests/ changes limited to tests for the new tooling, no edits to governing files or the agent-working domain, new tooling in tools/code_health/ per docs/guidelines/repo_tooling_layout.md.

## Scope
- Add a [tool.ruff] lint configuration to pyproject.toml (check only, no formatter) with the roadmap Section 6.1 thresholds held in one config
- Add configuration for complexipy and jscpd (jscpd scoped to Python under src/ with generated files excluded), and record how jscpd is pinned given it is a Node tool outside uv.lock
- Add the pinned Python tools to the pyproject.toml dev dependency group and uv.lock
- Create tools/code_health/ as a real package (__init__.py, package imports, no sys.path.insert) containing the line-count script for function, class and module length with stable qualified symbol names for nested functions
- Add a 'make lint-py' target that runs 'ruff check' only, and add it to .PHONY
- Run each tool over src/ and record in the ticket the pinned version and result, or the reason the tool was dropped
- Add tests for the line-count script

## Out of Scope
- Adapters, the ratchet command, registries/code_health_exceptions.jsonl and 'make code-health' (TCK-20261002-CODE-HEALTH-RATCHET-REGISTRY)
- Snapshot metrics and the first snapshot (TCK-20261002-CODE-HEALTH-SNAPSHOT-METRICS)
- ruff format, --fix, or any autofix; any # noqa or # type: ignore added under src/
- CI gating, prek hooks, mypy changes (M4)
- A new dead-code detector (reuse tools/audit_unreachable_code.py)
- Moving the existing flat tools/codebase_health_*.py scripts
- Any file under src/, existing tests, CLAUDE.md, .claude/settings.json, hooks, .claude/agents/, .claude/workflows/, .claude/skills/

## Acceptance Criteria
- [x] For each of ruff, complexipy, jscpd and the line-count script the ticket records either the pinned version and a successful run over src/ (744 files at investigation time) or the reason it was dropped; pinned Python tools are in the pyproject.toml dev dependency group and uv.lock, and 'uv lock --check' exits 0
- [x] tools/code_health/ exists as a real package: it has __init__.py, is imported as 'from tools.code_health...', and contains no sys.path.insert
- [x] The line-count script reports function, class and module length against the roadmap Section 6.1 thresholds (function warn >50 / fail >80 lines, class >500, module >1,000), attributes nested functions to a stable qualified symbol name, and a test covers a nested function and a class method with the same name in one file
- [x] 'make lint-py' runs 'ruff check' only (the recipe contains no 'ruff format' and no '--fix') and is listed in .PHONY
- [x] The ruff configuration enables no formatter and the thresholds in config match roadmap Section 6.1 value for value: 50 statements, cyclomatic 10, 5 arguments, 12 branches, nesting 5; cognitive 15 is set in the complexipy configuration
- [x] pytest tests/tools/test_tools_orphan_check.py passes: every new file under tools/code_health/ has a live Makefile or import reference
- [x] pytest tests/static/test_ci_requirements_no_ml_stack.py tests/static/test_no_hardcoded_venv_interpreter_path.py tests/static/test_typecheck_gate_configured.py passes with those files unmodified
- [x] 'git diff --stat <base>...HEAD' lists no path under src/, the count of '# noqa' / '# type: ignore' lines under src/ is unchanged (23 at investigation time), and tests/ changes are confined to new test files for tools/code_health/
- [x] No path under .claude/ and not CLAUDE.md appears in the diff

## Related Tickets
- TCK-20261002-PYTHON-CODE-CRAFT-EPIC
- TCK-20261002-UV-DECLARE-AND-LOCK
- TCK-20261002-PYTHON-CODE-STANDARD-DOC
- TCK-20260929-TOOLS-ORPHAN-FILE-CHECK
- TCK-20260929-RETIRE-SCRIPTS-DIR
- TCK-20260916-MECHANISM-REGISTRY-TOOLS-PACKAGE
- TCK-20260909-UNREACHABLE-IMPLEMENTED-CODE-AUDIT
- TCK-20260702-CI-REQUIREMENTS-SPLIT
- TCK-20260623-TYPE-CHECKER

## Related Docs
- docs/plans/codebase_health/python_code_craft_roadmap.md
- docs/plans/codebase_health/python_code_craft_foundation_ticket_brief.md
- docs/guidelines/repo_tooling_layout.md

## Related Stored Artifacts
- stored_artifacts/TCK-20261002-CODE-HEALTH-TOOL-CONFIG/plan.md
- stored_artifacts/TCK-20261002-CODE-HEALTH-TOOL-CONFIG/investigation.md
- stored_artifacts/TCK-20261002-CODE-HEALTH-TOOL-CONFIG/test_plan.md

## Related Code Areas
- pyproject.toml
- uv.lock
- requirements.txt
- package.json
- Makefile
- tools/gate_checks/tools_orphan_check.py
- tools/audit_unreachable_code.py
- docs/guidelines/repo_tooling_layout.md
- docs/plans/codebase_health/python_code_craft_roadmap.md
- docs/plans/codebase_health/python_code_craft_foundation_ticket_brief.md

## Assumptions / Open Questions
- Hard dependency on TCK-20261002-UV-DECLARE-AND-LOCK: ruff, complexipy and jscpd are not installed (only uv, node and npx are on PATH) and none was run during investigation, so 'works on this repo' is unverified for all three
- jscpd is a Node tool: pinning it means a package.json/lockfile change or an unpinned npx fetch, and it is not covered by uv.lock; the choice is to be made and recorded here, and dropping jscpd with a reason is an acceptable outcome
- If requirements.txt is a generated export by then, adding dev tools regenerates it; the export must still exclude the knowledge stack and satisfy the pytest-cov/pytest-html ban
- The existing 'lint' Makefile target is frontend-only; 'lint-py' is a new, separate target
- Thresholds are roadmap values (ruff/pylint defaults and conventions) and are also stated in docs/guidelines/python_code_standard.md; the two must agree
- Whether ruff D (docstring) rules are enabled affects baseline size (1,143 public functions without a docstring per the roadmap's ad-hoc scan); the rule selection is settled here and feeds the registry ticket
- Layer is `misc`: no registered layer covers repo-wide Python code-health/dependency tooling; this matches the sibling TCK-20261002-UV-DECLARE-AND-LOCK. No new layer was registered.
- Source concern IDs: C4
- From the review of `TCK-20261002-PYTHON-CODE-STANDARD-DOC` (2026-10-02): `docs/guidelines/python_code_standard.md` rules E2 (`BLE001`) and M1 (`PLC0415`) express a justified exception as `# noqa: <code>` plus the reason, in new or changed code only; the ruff config must honour `noqa` for those codes, and existing `src/` violations stay in the external baseline. Rule S7 names `PLR1702`, a ruff preview rule, so the config needs preview or `explicit-preview-rules` for it, or S7's marker must change. Confirm every ruff code named in the standard and update the standard where a code is replaced.
- From the review of `TCK-20261002-UV-DECLARE-AND-LOCK` (2026-10-02): `pandas` (`src/observability/mining/dataset.py`) and `clickhouse_connect` (`src/observability/warehouse/clickhouse.py`) are optional function-level imports in `src/` and are undeclared in `pyproject.toml`. deptry will report them; decide here whether they become an opt-in dependency group or a deptry ignore.

## Implementation Notes
Hand-orchestrated by the `codebase-implementer` session in worktree `rpg-code-craft`, branch `python-code-craft`.

**Result per tool, run over `src/` (744 files, 125,791 lines):**

| Tool | Pinned version | Result |
|---|---|---|
| ruff | 0.16.10 (dev group, `uv.lock`) | Works. 5,422 findings with the configured rules: PLC0415 1063, D102 1003, I001 826, D100 410, BLE001 379, D101 346, C901 286, PLR0912 198, PLR0915 124, ANN001 122, ANN204 102, PLR1702 95, D103 90, ANN202 69, PLR0913 69, ANN201 66, B904 64, D104 59, N806 15, E722 9, ANN003 7, ANN205 6, ANN206 4, N814 2, N818 2, ANN002 2, B006 2, N817 1, N804 1. |
| complexipy | 8.0.1 (dev group, `uv.lock`) | Works. 3,015 functions, 384 over cognitive complexity 15; worst `EventExtractor::extract` at 789. |
| jscpd | 5.4.0 (Makefile `JSCPD_VERSION`, via `npx`; not in `uv.lock`) | Works. 97 exact clones, 1,392 duplicated lines (1.11%) in 656 files, at 8 lines / 70 tokens minimum. |
| line count (`tools/code_health/line_count.py`) | new in this ticket | Works, 0 unreadable files. 5,376 symbols: functions 251 fail / 212 warn / 2,645 ok; classes 21 flagged over 500 lines; modules 11 flagged over 1,000. Worst: `create_v2_app` 2,409 lines, nested `create_v2_app.<locals>.get_observability_ui` 2,094, `EventExtractor.extract` 1,586. |

No tool was dropped.

- **Configuration** is in `pyproject.toml`: `[tool.ruff.lint]` selects only the rules the standard names (this replaces ruff's default E/F set, so the baseline is about the standard); `[tool.ruff.lint.mccabe]` 10, `[tool.ruff.lint.pylint]` 5 args / 12 branches / 50 statements / 5 nested blocks; `[tool.complexipy]` 15; `[tool.code_health.size]` 50 / 80 / 500 / 1000. No formatter. `PLR1702` is a preview rule, enabled with `preview = true` plus `explicit-preview-rules = true`, so no other preview rule is on. `D` is limited to `D100` to `D104`; `ANN401` is ignored (T2 is a reviewer rule).
- **jscpd pin:** a single Makefile variable with `npx --yes jscpd@5.4.0`. The root `package.json` belongs to the graph viewer and was not touched. This pins the version but not the dependency integrity hashes.
- **`make lint-py`** runs `python3 -m ruff check src` only and exits 1 today because the 5,422 existing findings are not baselined; the ratchet ticket makes that usable as a gate. The other three targets are report-only and exit 0. They are extra to the ticket's one named target; they are what gives `line_count.py` its live Makefile reference and makes the jscpd pin live, and `TCK-20261002-CODE-HEALTH-RATCHET-REGISTRY` composes them into `make code-health`.
- **Dogfood:** `ruff check tools/code_health` found a missing `main()` docstring (`D103`) on the first run; fixed. mypy is clean on `line_count.py`.
- **Standard updated:** `docs/guidelines/python_code_standard.md` "planned" markers became "configured" (not gated), with the run commands and `D100` to `D104` and `ANN` except `ANN401`; its ownership row treats a stale "planned" as a staleness signal. `docs/guidelines/repo_tooling_layout.md` lists `code_health/`.
- **CI effect:** `requirements.txt` gains `ruff==0.16.10` and `complexipy==8.0.1`, so every pip-installing CI job installs them. Plain `pip install -r requirements.txt` into a clean 3.13 environment succeeds.
- The orphan checker reads tracked files only: `tools/code_health/` is invisible to it until staged.
- `make knowledge-index-update` was not run (worktree has no `knowledge-index/`; post-merge step is in the epic).

## Test Summary
- `pytest tests/tools/test_code_health_line_count.py`: 22 passed (nested function and same-named method distinct, decorators, async, nested classes, conditional definitions, function 50/51/80/81, class 500/501, module 1000/1001, empty module, unparseable file reported, stable order, CLI, config agreement, `lint-py` check-only).
- `pytest tests/static/ tests/tools/test_dashboard_makefile_targets.py tests/tools/test_ci_workflow_test_coverage.py tests/tools/test_tools_orphan_check.py tests/tools/test_code_health_line_count.py tests/tools/test_search_mcp.py tests/architecture/test_docker_compose_dependency_hygiene.py tests/tools/test_knowledge_search.py::TestPyprojectDeps`: 149 passed, no existing test file edited.
- `pytest tests/docs/`: 69 passed, 2 skipped, 1 xfailed.
- `uv lock --check`: exit 0; export re-run: no diff; orphan check: `tools/code_health/line_count.py` LIVE.
- `# noqa` / `# type: ignore` lines under `src/`: 23 before and after. Diff against 7dfd1349 has no `src/`, `.claude/` or `CLAUDE.md` path.
- Not run: the wider test suite.

## Files Changed
- pyproject.toml, uv.lock, requirements.txt (generated)
- Makefile, .jscpd.json
- tools/code_health/__init__.py, tools/code_health/line_count.py
- tests/tools/test_code_health_line_count.py (new)
- docs/guidelines/python_code_standard.md, docs/guidelines/repo_tooling_layout.md
- docs/REGISTRY.yaml (regenerated)
- stored_artifacts/TCK-20261002-CODE-HEALTH-TOOL-CONFIG/ (plan.md, investigation.md, test_plan.md)

## Completion Summary
ruff, complexipy, jscpd and a new line-count report are configured and run on all of `src/`, with thresholds held in `pyproject.toml` and matching the standard. Nothing is gated or baselined yet; that is `TCK-20261002-CODE-HEALTH-RATCHET-REGISTRY`.
