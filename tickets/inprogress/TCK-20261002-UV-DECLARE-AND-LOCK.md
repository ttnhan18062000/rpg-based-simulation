---
status: active
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20261002-UV-DECLARE-AND-LOCK
phase: open
date: 2026-10-02
tags: [setup]
---

# TCK-20261002-UV-DECLARE-AND-LOCK

## Title
M2a: Declare dependencies once in pyproject.toml, refresh uv.lock, generate requirements.txt

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Finish the declaration half of the half-done uv adoption. Today dependencies are declared in three places (pyproject.toml, requirements.txt and a stale uv.lock) and the Python version is stated inconsistently (CI runs 3.13 while pyproject.toml says >=3.11 and mypy targets 3.11). Wanted outcome: dependencies declared once in pyproject.toml with dev tooling in a dependency group, a refreshed uv.lock, requirements.txt kept as a generated export until every CI job has been moved, the Python version statement aligned, and docs/guidelines/agent_working_environment.md updated. It must keep the knowledge-search stack split (TCK-20260702-CI-REQUIREMENTS-SPLIT) and the CI static tests green. This matters because pyproject.toml today under-declares what CI installs (yaml, duckdb, pyarrow, jsonschema are only in requirements.txt), so a uv sync from it would fail on import. The shared constraints apply: no src/ edits, no simulation behaviour change, no tests/ changes beyond tests for new tooling, no edits to governing files or the agent-working domain.

## Scope
- Classify every pin in requirements.txt as direct or transitive, and declare every direct third-party package in pyproject.toml (at minimum PyYAML, duckdb, pyarrow, jsonschema, mcp, plus the existing fastapi/pydantic/redis set)
- Move test/dev tooling (pytest, httpx, hypothesis, mypy, pytest-asyncio, coverage) into a [dependency-groups] dev group in pyproject.toml
- Refresh uv.lock from pyproject.toml, keeping torch, sentence-transformers, sqlite-vec and rank-bm25 out of the default resolution that CI and the export use
- Regenerate requirements.txt as a uv export from the lock with a documented command, in a shape plain 'pip install -r requirements.txt' still accepts and that keeps name==version lines
- Align the Python version statement across requires-python, [tool.mypy] python_version, test.yml python-version and the Prerequisites row of the environment doc, documenting which one is the source
- Update the Prerequisites and First-Time Setup sections of docs/guidelines/agent_working_environment.md for the uv-based install (including --system-certs on this machine) and state that requirements.txt is a generated export

## Out of Scope
- Any change to .github/workflows/test.yml install steps (TCK-20261002-UV-FIRST-CI-JOB)
- Changing the Makefile install-py recipe (pinned verbatim by tests/tools/test_dashboard_makefile_targets.py)
- Removing requirements.txt or requirements-knowledge.txt; changing the .venv-knowledge setup in substance
- Making mypy blocking or otherwise changing the mypy gate (M4; pinned by INFRA-TYPE-001)
- Adding ruff, complexipy or other M3 tools to the dev group (TCK-20261002-CODE-HEALTH-TOOL-CONFIG)
- Any file under src/, any existing test file under tests/, CLAUDE.md, .claude/settings.json, hooks, .claude/agents/, .claude/workflows/, .claude/skills/
- Updating docs/guides/delivery_process.md and docs/testing/migration_ci_lanes.md pip instructions (still accurate while jobs are unmigrated)

## Acceptance Criteria
- [ ] Every third-party package that requirements.txt pins today and that the repo imports (at minimum PyYAML, duckdb, pyarrow, jsonschema, mcp, pytest-asyncio, coverage, plus the existing fastapi/pydantic/redis set) is declared in pyproject.toml, with test/dev tooling (pytest, httpx, hypothesis, mypy, pytest-asyncio, coverage) in a [dependency-groups] dev group; a check comparing the two name sets reports no package present in requirements.txt but unreachable from pyproject.toml
- [ ] The ticket records, for every pin in the pre-change requirements.txt, whether it is direct or transitive
- [ ] 'uv lock --check' exits 0 against the committed uv.lock, and the lock's rpg-based-simulation entry lists the same dependencies and groups as pyproject.toml
- [ ] requirements.txt is reproducible from the lock: re-running the documented 'uv export' command yields no diff against the committed file, the file contains no torch, sentence-transformers, sqlite-vec or rank-bm25 line, and 'pytest tests/static/test_ci_requirements_no_ml_stack.py' passes
- [ ] 'pip install -r requirements.txt' into a clean Python 3.13 environment succeeds with the generated file, so unmigrated CI jobs keep working
- [ ] 'pytest tests/static/ tests/tools/test_dashboard_makefile_targets.py tests/tools/test_ci_workflow_test_coverage.py' passes with no edit to any existing test file under tests/
- [ ] requires-python in pyproject.toml, [tool.mypy] python_version, the python-version in test.yml and the Prerequisites row of docs/guidelines/agent_working_environment.md name the same version or a mutually consistent floor, with one of them documented as the source; pyproject.toml still has a [tool.mypy] section and 'make typecheck-py' output on src/ is not made blocking
- [ ] docs/guidelines/agent_working_environment.md's Prerequisites and First-Time Setup sections describe the uv-based install (including --system-certs) and state that requirements.txt is a generated export; requirements-knowledge.txt and the .venv-knowledge instructions are unchanged in substance
- [ ] 'git diff --stat <base>...HEAD' lists no path under src/, no path under .claude/ and not CLAUDE.md

## Related Tickets
- TCK-20261002-PYTHON-CODE-CRAFT-EPIC
- TCK-20261002-UV-FIRST-CI-JOB
- TCK-20260702-CI-REQUIREMENTS-SPLIT
- TCK-20260820-HOTFIX-REQUIREMENTS-TXT-MISSING-CORE-DEPS
- TCK-20260820-HOTFIX-PHANTOM-TESTCONTAINERS-DEPENDENCY
- TCK-20260817-HOTFIX-KGMCP-MISSING-JSONSCHEMA-DEPENDENCY
- TCK-20260914-VENV-NAMING-CI-PARITY-SWAP
- TCK-20260925-STATIC-CHECK-HARDCODED-VENV-INTERPRETER-PATH
- TCK-20260623-TYPE-CHECKER
- TCK-20260916-HEADROOM-TRIAL-ISOLATION-AND-REVERT

## Related Docs
- docs/plans/codebase_health/python_code_craft_roadmap.md
- docs/plans/codebase_health/python_code_craft_foundation_ticket_brief.md
- docs/guidelines/agent_working_environment.md
- docs/parity_ledger/infrastructure.yaml
- docs/guides/delivery_process.md
- docs/testing/migration_ci_lanes.md

## Related Stored Artifacts
None.

## Related Code Areas
- pyproject.toml
- requirements.txt
- requirements-knowledge.txt
- uv.lock
- docs/guidelines/agent_working_environment.md
- tests/static/test_ci_requirements_no_ml_stack.py
- tests/static/test_ci_step_summary_reporting.py
- tests/static/test_typecheck_gate_configured.py
- tests/static/test_no_hardcoded_venv_interpreter_path.py
- tests/tools/test_dashboard_makefile_targets.py
- src/observability/analytics/exporter.py
- src/observability/analytics/query.py
- src/observability/analytics/dataset.py
- src/observability/mining/dataset.py
- stored_artifacts/TCK-20260914-VENV-NAMING-CI-PARITY-SWAP/investigation.md

## Assumptions / Open Questions
- The src/ files listed are read-only evidence of undeclared imports (yaml, duckdb, pyarrow); they are not edited
- Open question: which Python version statement moves. requires-python '>=3.11' and CI on 3.13 are not contradictory; raising requires-python to >=3.13 would break installing into .venv-knowledge (3.12), and raising mypy python_version may change mypy output on frozen src/. Default assumption: keep a consistent floor and document CI's 3.13 as the tested version, unless the owner decides otherwise
- Some pins (cryptography, pyjwt, python-multipart, python-dotenv, pydantic-settings, httpx-sse) had no import found and are probably transitive; each was not traced during investigation
- uv.lock currently resolves torch and sentence-transformers through the 'knowledge' extra; this machine needs --system-certs and cannot reach the torch CPU wheel index, so the refresh may fail or resolve differently if that extra stays in the resolution. 'uv lock' was not attempted during investigation
- The uv export flags (hashes, markers, '-e .' line) need choosing so the file stays pip-installable; test_ci_requirements_no_ml_stack.py parses lines with split('==')
- Editing docs/guidelines/agent_working_environment.md is permitted: the brief defines the agent-working domain as .claude/agents, .claude/workflows and .claude/skills
- The CI path filters PERF_RE and MIG_RE trigger on requirements.txt but not pyproject.toml or uv.lock; while requirements.txt is regenerated with every dependency change this stays covered, and changing the filters is not part of this ticket
- Layer choice: `misc` — no registered layer covers dependency declaration / packaging / dev-environment tooling, and registering a new append-only layer was not warranted from a formatting-only step; the owner may register one (e.g. a build/tooling layer) and re-assign
- Source concern IDs from the pre-investigation: C3

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
