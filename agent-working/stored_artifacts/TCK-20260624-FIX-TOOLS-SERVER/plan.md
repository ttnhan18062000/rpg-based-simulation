---
status: active
ticket_id: TCK-20260624-FIX-TOOLS-SERVER
artifact_type: plan
---

# Plan — TCK-20260624-FIX-TOOLS-SERVER

## Ordered Steps

1. **Fix 1 (cmd_build):** In `tools/knowledge_search.py`, change the ImportError branch in
   `cmd_build` from `print("Error: ...")` + `return 1` to `print("Warning: ...")` + `return 0`.

2. **Fix 1 (cmd_query):** Same change in the ImportError branch of `cmd_query`.

3. **Fix 2 (.mcp.json):** Change `"command"` from the absolute venv path to `"python3"`,
   add `"env": {"PATH": "/home/vboxuser/Work/venv/bin:/usr/local/bin:/usr/bin:/bin"}`.

4. **Fix 3 (server test):** In `test_health_503_when_not_ready` and
   `test_search_503_when_not_ready`, add `tmp_path` parameter and patch `_DB_PATH`
   and `_INDEX_DIR` to nonexistent paths BEFORE opening TestClient context.

5. **Verify:** Run `pytest tests/tools/ -m "not slow" -v --tb=short` — all must pass.

6. **Finalize:** Move ticket to done/, write working_log entry, move staging → stored,
   write monitoring entries, commit.
