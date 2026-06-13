# Investigation — TCK-20260612-LOCAL-CTX-MCP

PHASE_TS: 2026-06-12T00:00:00Z

## Key findings

- `.claude/settings.json` exists with only `hooks` — needs `mcpServers` key added (merge, not overwrite)
- `mcp` Python package is NOT installed in the environment. Must handle ImportError gracefully in `search_mcp.py`
- `mcp` PyPI package (Anthropic MCP SDK) exposes `mcp.server.fastmcp.FastMCP`
- `agent_working_environment.md` already has a MCP Setup section (from HTTP-API ticket) — just needs updating to reflect the actual implementation
- CLAUDE.md Proactive Tool Use table already has the HTTP entry — need to update it to reference `search_docs` as primary with HTTP/CLI as fallbacks

## MCP server design

- `tools/search_mcp.py` — tries `from mcp.server.fastmcp import FastMCP`; if ImportError: prints error and exits 1
- `--test` mode: reads JSON from stdin, runs search, prints results to stdout — no MCP protocol needed; enables `make mcp-server-test` without an MCP client
- Lazy model loading: load model on first `search_docs` call (not at startup) for fast Claude Code spawn time
- Missing index: `search_docs` returns `{"error": "index not found", "action": "run make knowledge-index"}` without crashing

## .claude/settings.json merge

Current content: `{"hooks": {...}}`. Need to add `"mcpServers": {"knowledge-search": {...}}`.
