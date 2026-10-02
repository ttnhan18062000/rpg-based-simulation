---
status: active
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20261002-CODE-HEALTH-TOOL-CONFIG
phase: open
date: 2026-10-02
tags: []
---

# TCK-20261002-CODE-HEALTH-TOOL-CONFIG

## Title
M3a: Configure and confirm code-health tools (ruff check, complexipy, jscpd, line-count script)

## Status
OPEN

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
- [ ] For each of ruff, complexipy, jscpd and the line-count script the ticket records either the pinned version and a successful run over src/ (744 files at investigation time) or the reason it was dropped; pinned Python tools are in the pyproject.toml dev dependency group and uv.lock, and 'uv lock --check' exits 0
- [ ] tools/code_health/ exists as a real package: it has __init__.py, is imported as 'from tools.code_health...', and contains no sys.path.insert
- [ ] The line-count script reports function, class and module length against the roadmap Section 6.1 thresholds (function warn >50 / fail >80 lines, class >500, module >1,000), attributes nested functions to a stable qualified symbol name, and a test covers a nested function and a class method with the same name in one file
- [ ] 'make lint-py' runs 'ruff check' only (the recipe contains no 'ruff format' and no '--fix') and is listed in .PHONY
- [ ] The ruff configuration enables no formatter and the thresholds in config match roadmap Section 6.1 value for value: 50 statements, cyclomatic 10, 5 arguments, 12 branches, nesting 5; cognitive 15 is set in the complexipy configuration
- [ ] pytest tests/tools/test_tools_orphan_check.py passes: every new file under tools/code_health/ has a live Makefile or import reference
- [ ] pytest tests/static/test_ci_requirements_no_ml_stack.py tests/static/test_no_hardcoded_venv_interpreter_path.py tests/static/test_typecheck_gate_configured.py passes with those files unmodified
- [ ] 'git diff --stat <base>...HEAD' lists no path under src/, the count of '# noqa' / '# type: ignore' lines under src/ is unchanged (23 at investigation time), and tests/ changes are confined to new test files for tools/code_health/
- [ ] No path under .claude/ and not CLAUDE.md appears in the diff

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
None.

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

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
