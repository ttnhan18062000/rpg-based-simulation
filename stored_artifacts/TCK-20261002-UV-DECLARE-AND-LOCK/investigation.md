---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20261002-UV-DECLARE-AND-LOCK
artifact_type: investigation
tags: [setup]
---

# Investigation — TCK-20261002-UV-DECLARE-AND-LOCK

## Context scan

- `search_docs` ("uv lock requirements.txt pyproject dependencies CI requirements split"): `TCK-20260702-CI-REQUIREMENTS-SPLIT` (ML stack moved to `requirements-knowledge.txt` because the torch CPU wheel is not on PyPI) and `docs/guidelines/agent_working_environment.md` Prerequisites. No prior uv-migration ticket; no duplicate.
- `graphify query`: `tests/tools/test_knowledge_search.py::TestPyprojectDeps` pins the `knowledge` extra in `pyproject.toml`.

## Findings

1. **Tests that pin the dependency files** (none edited): `tests/static/test_ci_requirements_no_ml_stack.py` (no torch, sentence-transformers, sqlite-vec, rank-bm25 line in `requirements.txt`; parses with `split("==")`), `tests/tools/test_knowledge_search.py::TestPyprojectDeps` and `tests/tools/test_search_mcp.py` (the `knowledge` and `search-mcp` extras must stay under `[project.optional-dependencies]`), `tests/tools/test_dashboard_makefile_targets.py` (`install-py` recipe verbatim), `tests/static/test_typecheck_gate_configured.py` (`[tool.mypy]`), `tests/architecture/test_docker_compose_dependency_hygiene.py` (no broker clients in `pyproject.toml`).
2. **Imports versus declarations** (AST scan of `src/`, `tools/`, `tests/`). Imported and pinned in `requirements.txt` but not declared in `pyproject.toml`: `yaml`, `duckdb`, `pyarrow` (src); `starlette`, `typing_extensions` (src, reachable only through fastapi/pydantic); `coverage`, `websockets` (tools, tests); `jsonschema`, `mcp`, `pytest_asyncio` (tests). `mcp` was declared only as the `search-mcp` extra, which a default install does not include.
3. **Imported, not pinned anywhere, left undeclared:** `pandas` and `clickhouse_connect` (one `src/` import each) and `numpy` (knowledge tooling). CI does not install them today, so they are optional imports; declaring them would add packages CI has never had. Not changed here.
4. **`xxhash`, `sse-starlette`, `python-json-logger`** are declared but the scan found no import. Dropping a declaration is a behaviour risk and is deptry's job (roadmap 6.2); left as is.
5. **The old lock was stale in both directions**: fastapi 0.135.1 against the pinned 0.128.4, hypothesis 6.151.10 against 6.124.7, and it lacked coverage, duckdb, pyarrow and pytest-asyncio.
6. **Risk from the ticket did not occur.** `uv lock --system-certs` works on this machine. Locking only reads metadata from PyPI; it never contacts `download.pytorch.org`. The `knowledge` extra resolves torch from PyPI in the lock, and nothing installs it unless that extra is requested.
7. **Old `requirements.txt` was not a full pin set**: certifi, urllib3, charset-normalizer, httpcore, sortedcontainers and others were installed by CI unpinned. The export pins them.
8. **Parity ledger**: no entry covers dependency declaration; `INFRA-TYPE-001` (mypy gate) is untouched.

## Decisions

- Version preservation: the first `uv lock` ran with every old pin as a temporary `constraint-dependencies` entry, then the constraints were removed and the lock re-run, which keeps the locked versions. Result: all 47 old pins keep their exact version.
- `dev` moves from an extra to a `[dependency-groups]` group. `memray` goes to a separate opt-in `profiling` group so the export, and therefore CI, does not gain it.
- `mypy`, `jsonschema`, `mcp`, `websockets` join the `dev` group so the default export reaches them.
- Python version (owner decision 8.12): `requires-python >=3.11` is the source and floor, `[tool.mypy] python_version = "3.11"` follows it, CI's 3.13 is documented as the tested version. No value changed; the doc now states the relationship.
- Export command: `uv export --frozen --no-hashes --no-emit-project -o requirements.txt`. No `-e .` line, no hashes, `name==version` lines with environment markers where needed.
