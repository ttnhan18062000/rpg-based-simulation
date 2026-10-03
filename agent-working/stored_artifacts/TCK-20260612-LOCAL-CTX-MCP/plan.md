# Plan — TCK-20260612-LOCAL-CTX-MCP

PHASE_TS: 2026-06-12T00:00:00Z

## Steps

1. `tools/search_mcp.py` — MCP server with search_docs + search_health tools + --test mode
2. `.claude/settings.json` — add mcpServers.knowledge-search entry
3. `pyproject.toml` — add [search-mcp] optional dep group with `mcp>=1.0.0`
4. `Makefile` — add mcp-server-test target
5. `CLAUDE.md` — update Proactive Tool Use to reference search_docs as primary
6. `implement-ticket SKILL.md` — update Step 0 to use search_docs
7. `docs/guidelines/agent_working_environment.md` — already has MCP section; verify accuracy

## Scope guards

- Do NOT break existing HTTP server tests (test_search_server.py)
- Do NOT add mcp to core deps — optional only
- FastAPI HTTP server stays intact — MCP is additive
