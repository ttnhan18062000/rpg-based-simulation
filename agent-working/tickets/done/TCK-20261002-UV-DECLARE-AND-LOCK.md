---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20261002-UV-DECLARE-AND-LOCK
phase: done
date: 2026-10-02
tags: [setup]
---

# TCK-20261002-UV-DECLARE-AND-LOCK

## Title
M2a: Declare dependencies once in pyproject.toml, refresh uv.lock, generate requirements.txt

## Status
DONE

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
- [x] Every third-party package that requirements.txt pins today and that the repo imports (at minimum PyYAML, duckdb, pyarrow, jsonschema, mcp, pytest-asyncio, coverage, plus the existing fastapi/pydantic/redis set) is declared in pyproject.toml, with test/dev tooling (pytest, httpx, hypothesis, mypy, pytest-asyncio, coverage) in a [dependency-groups] dev group; a check comparing the two name sets reports no package present in requirements.txt but unreachable from pyproject.toml
- [x] The ticket records, for every pin in the pre-change requirements.txt, whether it is direct or transitive
- [x] 'uv lock --check' exits 0 against the committed uv.lock, and the lock's rpg-based-simulation entry lists the same dependencies and groups as pyproject.toml
- [x] requirements.txt is reproducible from the lock: re-running the documented 'uv export' command yields no diff against the committed file, the file contains no torch, sentence-transformers, sqlite-vec or rank-bm25 line, and 'pytest tests/static/test_ci_requirements_no_ml_stack.py' passes
- [x] 'pip install -r requirements.txt' into a clean Python 3.13 environment succeeds with the generated file, so unmigrated CI jobs keep working
- [x] 'pytest tests/static/ tests/tools/test_dashboard_makefile_targets.py tests/tools/test_ci_workflow_test_coverage.py' passes with no edit to any existing test file under tests/
- [x] requires-python in pyproject.toml, [tool.mypy] python_version, the python-version in test.yml and the Prerequisites row of docs/guidelines/agent_working_environment.md name the same version or a mutually consistent floor, with one of them documented as the source; pyproject.toml still has a [tool.mypy] section and 'make typecheck-py' output on src/ is not made blocking
- [x] docs/guidelines/agent_working_environment.md's Prerequisites and First-Time Setup sections describe the uv-based install (including --system-certs) and state that requirements.txt is a generated export; requirements-knowledge.txt and the .venv-knowledge instructions are unchanged in substance
- [x] 'git diff --stat <base>...HEAD' lists no path under src/, no path under .claude/ and not CLAUDE.md

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
- stored_artifacts/TCK-20261002-UV-DECLARE-AND-LOCK/plan.md
- stored_artifacts/TCK-20261002-UV-DECLARE-AND-LOCK/investigation.md
- stored_artifacts/TCK-20261002-UV-DECLARE-AND-LOCK/test_plan.md

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
- Hand-orchestrated by the `codebase-implementer` session in worktree `rpg-code-craft`, branch `python-code-craft`.
- **Classification of the 47 pins in the pre-change `requirements.txt`:**
  - Direct, runtime, already declared (11): fastapi, msgpack, prometheus-client, psutil, pydantic, python-json-logger, redis, requests, sse-starlette, uvicorn, xxhash.
  - Direct, runtime, newly declared in `[project] dependencies` (5): PyYAML, duckdb, pyarrow, starlette, typing_extensions.
  - Direct, test/dev, now in `[dependency-groups] dev` (8): pytest, pytest-asyncio, httpx, hypothesis, coverage, jsonschema, mcp, websockets.
  - Transitive (23): annotated-doc, annotated-types, anyio, attrs, click, colorama, cryptography, h11, httpx-sse, idna, iniconfig, jsonschema-specifications, packaging, pluggy, pydantic-settings, pydantic_core, Pygments, pyjwt, python-dotenv, python-multipart, referencing, rpds-py, typing-inspection. The six the ticket flagged as unverified (cryptography, pyjwt, python-multipart, python-dotenv, pydantic-settings, httpx-sse) all come from `mcp`, confirmed with `uv tree --invert`.
- `pyproject.toml`: the `dev` extra is replaced by `[dependency-groups] dev`; mypy joins it. `memray` moves to an opt-in `profiling` group so CI does not gain it. The `knowledge` and `search-mcp` extras stay, because existing tests pin them. `mcp` is in both the `search-mcp` extra and the dev group.
- `uv.lock`: refreshed. To keep versions, the first lock ran with the 47 old pins as temporary `constraint-dependencies`; the constraints were then removed and the lock re-run. All 47 old pins keep their exact version. The lock still resolves torch for the `knowledge` extra, from PyPI metadata only; no default install or export includes it.
- `requirements.txt`: now generated by `uv export --frozen --no-hashes --no-emit-project -o requirements.txt`. It gains 17 lines CI previously installed unpinned or not at all: certifi, urllib3, charset-normalizer, httpcore, sortedcontainers, cffi, pycparser (previously unpinned transitives); mypy, mypy-extensions, pathspec, librt, ast-serialize (mypy is now in the dev group); httptools, uvloop, watchfiles (from `uvicorn[standard]`, which `pyproject.toml` always declared but the old file did not honour); async-timeout and pywin32 (marker-gated, not installed on CI's Linux 3.13). The hand-written header comment is replaced by uv's generated header.
- **Behaviour change for CI to be aware of:** every job that installs `requirements.txt` now also gets mypy, uvloop, httptools and watchfiles. With uvloop installed, uvicorn's default loop setting selects uvloop where a server is started through uvicorn. The local runs below passed with these installed; the real check is the first PR run.
- Python version: no value changed. `requires-python = ">=3.11"` is documented as the source and floor, mypy's `python_version = "3.11"` follows it, CI's 3.13 is the tested version (owner decision 8.12).
- Not declared: `pandas`, `clickhouse_connect` (one `src/` import each) and `numpy` are imported but were never in `requirements.txt`; they stay optional. `xxhash`, `sse-starlette` and `python-json-logger` are declared with no import found; left for deptry.
- The ticket's lock risk did not occur: `uv lock --system-certs` works here, since locking does not contact the blocked torch wheel index.
- Not done: `make knowledge-index-update` (same reason as the standard-doc ticket; post-merge step is recorded in the epic). `docs/guidelines/agent_working_environment.md` still has a pre-existing wrong line in Troubleshooting saying the sqlite-vec minimum is in `requirements.txt`; out of scope.
- Layer stays `misc` per the ticket's own assumption.

## Test Summary
- `uv lock --check --system-certs`: exit 0.
- Old versus new `requirements.txt`: no package missing, no version changed, 17 new lines (listed above).
- Export re-run: no diff against the committed file.
- Clean Python 3.13.7 environment, `pip install -r requirements.txt`: exit 0.
- From that clean environment: `pytest tests/static/ tests/tools/test_dashboard_makefile_targets.py tests/tools/test_ci_workflow_test_coverage.py tests/tools/test_search_mcp.py tests/architecture/test_docker_compose_dependency_hygiene.py tests/tools/test_codebase_health_baseline.py tests/tools/test_knowledge_search.py::TestPyprojectDeps`: 126 passed.
- `uv sync --frozen --python 3.13 --system-certs` into a scratch environment: exit 0; yaml, duckdb, pyarrow, fastapi, mcp, jsonschema, coverage, pytest_asyncio import; torch and sentence_transformers absent.
- `pytest tests/api -m "not slow"` from the clean environment (to check the newly installed uvloop and httptools): run 1 used `-x` and stopped at `tests/api/test_live_entity_inspection.py::test_live_entity_inspection` (connection refused, port 8012); run 2, without `-x`, gave 149 passed and 1 failed, `tests/api/test_rest_parity.py::test_api_compression` (connection refused, port 8002). Both start a server subprocess and wait a fixed 3 seconds. Re-run alone in the new environment, `test_api_compression` passed 3 of 3 and `test_live_entity_inspection` passed once. In the main checkout's `.venv` (old dependency set), `test_live_entity_inspection` failed once of one run and `test_api_compression` failed 1 of 3. So this is a boot-timing flake that also occurs without the new export. No existing ticket covers it (only done tickets mention these tests); it is not fixed here because those are existing test files.
- The rest of the suite was not run against the new export.
- Diff against 7dfd1349: no `src/`, `tests/`, `.claude/`, `CLAUDE.md`, `Makefile` or workflow path.

## Files Changed
- pyproject.toml
- uv.lock
- requirements.txt (generated)
- docs/guidelines/agent_working_environment.md
- docs/REGISTRY.yaml (regenerated)
- stored_artifacts/TCK-20261002-UV-DECLARE-AND-LOCK/ (plan.md, investigation.md, test_plan.md)

## Completion Summary
Dependencies are declared once in `pyproject.toml`, `uv.lock` is current, and `requirements.txt` is a reproducible export that plain pip installs on 3.13 with every previously pinned version unchanged. CI still installs through pip; `TCK-20261002-UV-FIRST-CI-JOB` moves the first job to `uv sync`.
