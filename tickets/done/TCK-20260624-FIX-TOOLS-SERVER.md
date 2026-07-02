---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260624-FIX-TOOLS-SERVER
phase: done
date: 2026-06-24
tags: [tools, mcp, knowledge-search, graceful-degradation, server-tests]
---

# TCK-20260624-FIX-TOOLS-SERVER

## Title
Fix tools/search server tests — exit code contract violation, .mcp.json absolute path, lifespan timing

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
5 test failures in `tests/tools/`:

1. **`test_missing_sentence_transformers_build_exits_0`** and **`test_missing_sqlite_vec_query_exits_0`** — `tools/knowledge_search.py::cmd_build()` and `cmd_query()` now call `sys.exit(1)` when optional deps (`sentence_transformers`, `sqlite_vec`) are missing. The AC7 graceful-degradation contract specifies exit 0 with a warning. The implementation was hardened to fail-fast, breaking the contract.

2. **`test_command_is_python3`** — `.mcp.json` has `"command": "/home/vboxuser/Work/venv/bin/python3"` (absolute venv path, machine-specific). Test asserts `"python3"`. The portability contract requires the generic `python3` command with the venv activated via PATH/env rather than hardcoded.

3. **`test_health_503_when_not_ready`** and **`test_search_503_when_not_ready`** — `monkeypatch.setattr` runs before the test body but AFTER `TestClient.__enter__()` fires the FastAPI lifespan startup. The lifespan startup attempts to load `SentenceTransformer('all-MiniLM-L6-v2')` from HuggingFace (network + filesystem) before the "not ready" state patch takes effect. The mock never activates for the startup handler.

4. **`test_validate_frontmatter.py::TestEnumAntiDrift::test_enum_values_phase`** — no longer errors (passes cleanly in current state; the earlier ERROR was transient).

## Scope
- `cmd_build`/`cmd_query` dep-missing exit code: change `sys.exit(1)` → print `Warning: ...` to stderr + `return 0` in the missing-dep branches of both commands
- `.mcp.json`: change `"command"` from the absolute venv path back to `"python3"`; if the venv is needed, add it to the `"env": {"PATH": "..."}` key rather than hardcoding the interpreter path
- `test_health_503_when_not_ready` / `test_search_503_when_not_ready`: patch the app state or the model-loading call BEFORE opening the `TestClient` context, so the lifespan startup sees the mocked state

## Out of Scope
- Installing `sentence_transformers` or `sqlite_vec` in the test environment
- Changing the knowledge search algorithm or server behavior when deps ARE present

## Acceptance Criteria
- Both graceful-degradation tests pass (exit 0 with a warning message on stderr when dep is missing)
- `test_command_is_python3` passes (`.mcp.json` uses `"python3"`)
- Both server 503 tests pass
- No regression in other tools tests

## Related Tickets
None

## Related Docs
- AC7 graceful-degradation contract (wherever documented — check `docs/guidelines/` or `docs/compliance/`)

## Related Code Areas
- `tools/knowledge_search.py` — `cmd_build()`, `cmd_query()` — missing-dep branches
- `.mcp.json` — `command` field
- `tests/tools/test_knowledge_search.py` — graceful degradation tests
- `tests/tools/test_search_mcp.py::TestMcpJson::test_command_is_python3`
- `tests/tools/test_search_server.py` — `TestHealth`, `TestSearch` fixture setup
- `src/tools/search_server.py` or equivalent — FastAPI app lifespan

## Assumptions / Open Questions
- Confirm the AC7 contract specifies exit 0 (check `docs/compliance/checklist.md` or `gap_analysis.md`)
- For server tests: determine whether the FastAPI app's lifespan startup can be skipped in tests (use `app.router.lifespan_context = None`), or whether a separate fixture pre-loads the mocked state via `app.state.search_index = mock_index` before `TestClient.__enter__()`
- `.mcp.json` change: confirm the MCP server can find `python3` in PATH in the CI/dev environment without the absolute path

## Implementation Notes
Fix 1 (exit codes):
```python
# In cmd_build(), when sentence_transformers not installed:
print("Warning: sentence-transformers not installed. Skipping index build.", file=sys.stderr)
return 0  # was: sys.exit(1)
```

Fix 2 (.mcp.json):
```json
{
  "command": "python3",
  "env": {"PATH": "/home/vboxuser/Work/venv/bin:/usr/local/bin:/usr/bin:/bin"}
}
```

Fix 3 (lifespan timing):
```python
@pytest.fixture
def not_ready_client(app, monkeypatch):
    # Patch BEFORE opening TestClient so lifespan startup sees the mock
    monkeypatch.setattr(app.state, "search_index", None)
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client
```

## Test Summary
Run: `pytest tests/tools/ -v --tb=short`

## Files Changed
- `tools/knowledge_search.py` — cmd_build/cmd_query: `return 1` → `return 0`, `"Error:"` → `"Warning:"` in ImportError branches
- `.mcp.json` — `"command"` changed from absolute venv path to `"python3"`, venv added to `"env"."PATH"`
- `tests/tools/test_search_server.py` — test_health_503_when_not_ready, test_search_503_when_not_ready: added `tmp_path` param and patched `_DB_PATH`/`_INDEX_DIR` before TestClient context to prevent lifespan model loading

## Completion Summary
Fixed 5 failing tests in tests/tools/: 2 graceful-degradation exit-code tests (return 0 + Warning instead of return 1 + Error), 1 .mcp.json portability test (python3 command with venv PATH env), and 2 FastAPI lifespan timing tests (patch DB paths before TestClient opens to prevent real model loading). All 418 non-slow tools tests pass.
