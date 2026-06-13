---
status: active
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260612-LOCAL-CTX-MCP
phase: open
date: 2026-06-12
tags: [tooling, rag, knowledge-search, mcp, agent-tool]
---

# TCK-20260612-LOCAL-CTX-MCP

## Title
MCP Server Wrapper for Agent-Native Context Search (`search_docs` tool)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
The FastAPI HTTP server (`TCK-20260612-LOCAL-CTX-HTTP-API`) serves human callers via `curl` and the browser. Agents (Claude Code) currently reach it through the `Bash` tool with `curl`, requiring CLAUDE.md to explicitly instruct the agent to run that command. An MCP server wrapper exposes the same search logic as a **native Claude Code tool** — `search_docs` appears in the agent's tool list automatically, no bash intermediary, no CLAUDE.md curl instructions needed. The MCP server shares retrieval logic directly with `tools/knowledge_search.py`; it does not proxy through the HTTP server.

## Scope

### 1. MCP Server

- New file: `tools/search_mcp.py`
- Transport: **stdio** (standard for local Claude Code MCP servers — Claude Code spawns it as a subprocess)
- Uses the `mcp` Python package (`pip install mcp`)
- Loads `knowledge-index/knowledge.db` and `knowledge-index/bm25.pkl` at startup by importing from `tools/knowledge_search.py` — no code duplication
- Exposes two tools: `search_docs` and `search_health`

### 2. Claude Code Registration

- `.mcp.json` (project root) with `mcpServers.knowledge-search` entry pointing to `tools/search_mcp.py`
- Add `make mcp-server-test` target

### 3. CLAUDE.md — Replace curl wiring with MCP reference

Proactive Tool Use table updated: `search_docs` MCP tool is primary; HTTP and CLI are fallbacks.

### 4. `implement-ticket` Workflow — Update Step 0

Step 0b added to new-ticket scope prompt: calls `search_docs` for context warm-start.

### 5. Update Setup Documentation

`docs/guidelines/agent_working_environment.md` MCP Setup section updated to reference `.mcp.json` (not `.claude/settings.json`).

## Out of Scope
- HTTP transport for MCP (stdio is correct for local Claude Code use)
- Removing or replacing the FastAPI HTTP server
- MCP resources or prompts (tools only)
- Authentication on the MCP server

## Acceptance Criteria
- [x] `.mcp.json` contains a `knowledge-search` MCP server entry pointing to `tools/search_mcp.py`
- [x] `search_docs` is implemented with query, top_k, section, mode args
- [x] `search_health` returns status/chunks/model dict
- [x] Missing index returns `{"error": "index not found", "action": "run make knowledge-index"}` without crashing
- [x] `make mcp-server-test` target added (uses `--test` mode, no HTTP server required)
- [x] CLAUDE.md Proactive Tool Use table references `search_docs` as primary
- [x] `implement-ticket` workflow Step 0b references `search_docs`
- [x] `docs/guidelines/agent_working_environment.md` MCP Setup section is accurate
- [x] `pyproject.toml` has `[search-mcp]` optional dep group with `mcp>=1.0.0`
- [x] FastAPI HTTP server unchanged — this ticket does not break it (verified: 130 passing tests)

## Related Tickets
- TCK-20260612-SEMANTIC-KNOWLEDGE-SEARCH (foundation)
- TCK-20260612-LOCAL-CTX-DOCS-CORPUS
- TCK-20260612-LOCAL-CTX-HYBRID-SEARCH
- TCK-20260612-LOCAL-CTX-HTTP-API
- TCK-20260612-LOCAL-CTX-OPS

## Related Docs
- docs/guidelines/agent_working_environment.md
- CLAUDE.md §Proactive Tool Use
- .claude/workflows/implement-ticket.js
- .mcp.json

## Related Stored Artifacts
- staging_artifacts/TCK-20260612-LOCAL-CTX-MCP/ → moved to stored_artifacts/

## Related Code Areas
- `tools/search_mcp.py` (new)
- `tools/knowledge_search.py` (imported — no changes to logic)
- `.mcp.json` (new — mcpServers entry)
- `Makefile` (`mcp-server-test` target)
- `CLAUDE.md` (Proactive Tool Use table)
- `.claude/workflows/implement-ticket.js` (Step 0b)
- `docs/guidelines/agent_working_environment.md` (MCP Setup section)
- `pyproject.toml` (`[search-mcp]` optional deps)
- `tests/tools/test_search_mcp.py` (new — 15 tests)

## Assumptions / Open Questions
- `.mcp.json` is the correct project-scoped MCP registration file for Claude Code (verified: `settings.json` schema does not allow `mcpServers` as a top-level field).
- `mcp` Python package is not installed in the dev environment; `search_mcp.py` handles ImportError gracefully (exits 1 with actionable message).
- Model loading is lazy (on first `search_docs` call) to keep Claude Code startup time fast.

## Implementation Notes
- `settings.json` was first attempted for MCP server registration but the schema rejected `mcpServers` as an unrecognized field. Switched to `.mcp.json` per Claude Code's actual project-scoped MCP config.
- Module-level stubs for `sentence_transformers` and `sqlite_vec` in `tests/tools/test_search_mcp.py` were kept off module level to avoid contaminating `_check_deps()` in `test_knowledge_search.py` — stubs are only applied inside test fixtures.

## Test Summary
- `tests/tools/test_search_mcp.py`: 15 tests, all passing
- Full `tests/tools/` suite: 418 passed, 28 skipped (0 failures — no regression introduced)
- Tests cover: .mcp.json schema, command/args shape, `_run_search` happy path, empty query, result key set, missing-index error dict with action hint, `_run_health` ok and unavailable, pyproject search-mcp optional dep, Makefile mcp-server-test target

## Files Changed
- `tools/search_mcp.py` — new MCP server (stdio, FastMCP, lazy model load, --test mode)
- `.mcp.json` — new project-scoped MCP server registration
- `pyproject.toml` — added `[search-mcp]` optional dep group with `mcp>=1.0.0`
- `Makefile` — added `mcp-server-test` target
- `CLAUDE.md` — updated Proactive Tool Use: `search_docs` as primary, HTTP/CLI as fallbacks
- `.claude/workflows/implement-ticket.js` — added Step 0b: context warm-start via `search_docs`
- `docs/guidelines/agent_working_environment.md` — updated MCP Setup section to use `.mcp.json`
- `tests/tools/test_search_mcp.py` — new test file (15 tests)

## Completion Summary
MCP server (`tools/search_mcp.py`) exposes `search_docs` and `search_health` as native Claude Code tools via stdio transport. Registration is in `.mcp.json`. The `mcp` package is an optional dep; the server handles ImportError gracefully. CLAUDE.md and `implement-ticket.js` now reference `search_docs` as the primary search path. All existing tests unaffected.
