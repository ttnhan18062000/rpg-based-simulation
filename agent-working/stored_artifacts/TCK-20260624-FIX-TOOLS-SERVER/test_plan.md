---
status: active
ticket_id: TCK-20260624-FIX-TOOLS-SERVER
artifact_type: test_plan
---

# Test Plan — TCK-20260624-FIX-TOOLS-SERVER

## Target Tests (5 must change from FAIL → PASS)

| Test | Fix |
|------|-----|
| `test_knowledge_search.py::TestGracefulDegradation::test_missing_sentence_transformers_build_exits_0` | Fix 1 |
| `test_knowledge_search.py::TestGracefulDegradation::test_missing_sqlite_vec_query_exits_0` | Fix 1 |
| `test_search_mcp.py::TestMcpJson::test_command_is_python3` | Fix 2 |
| `test_search_server.py::TestHealth::test_health_503_when_not_ready` | Fix 3 |
| `test_search_server.py::TestSearch::test_search_503_when_not_ready` | Fix 3 |

## Regression Guard

Run `pytest tests/tools/ -m "not slow"` — all 418 non-slow tests must pass.

## Verification Command

```
python3 -m pytest tests/tools/test_knowledge_search.py::TestGracefulDegradation \
    tests/tools/test_search_mcp.py::TestMcpJson::test_command_is_python3 \
    tests/tools/test_search_server.py::TestHealth::test_health_503_when_not_ready \
    tests/tools/test_search_server.py::TestSearch::test_search_503_when_not_ready \
    -v --tb=short
```

All 6 collected tests (including the already-passing `test_missing_index_warning_and_exit_0`)
must pass.
