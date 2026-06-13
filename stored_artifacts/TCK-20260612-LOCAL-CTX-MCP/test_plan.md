# Test Plan — TCK-20260612-LOCAL-CTX-MCP

PHASE_TS: 2026-06-12T00:00:00Z

## Tests

| ID | What | How |
|---|---|---|
| T-SETTINGS-01 | settings.json has mcpServers.knowledge-search | json.load + assert |
| T-SETTINGS-02 | command is python3, args[0] ends in search_mcp.py | key checks |
| T-SEARCH-01 | _run_search returns list with required keys | mock index load |
| T-SEARCH-02 | Missing index returns error dict | monkeypatch _DB_PATH |
| T-HEALTH-01 | _run_health returns dict with status | mock state |
| T-PYPROJECT-01 | mcp in search-mcp optional deps | tomllib parse |
| T-MAKEFILE-01 | mcp-server-test target present | grep Makefile |

## Location

`tests/tools/test_search_mcp.py`
