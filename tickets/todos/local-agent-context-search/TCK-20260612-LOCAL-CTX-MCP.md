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
OPEN

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
- Exposes two tools:

**Tool 1: `search_docs`**
```python
@mcp.tool()
def search_docs(
    query: str,
    top_k: int = 8,
    section: str = None,   # e.g. "mechanics", "engine", "strategy"
    mode: str = "hybrid"   # "hybrid" | "vector" | "keyword"
) -> list[dict]:
    """
    Search project documentation, ticket history, and stored investigations
    by natural language or exact technical term.

    Returns ranked chunks with title, heading, source_path, section, score, and excerpt.
    Use this before answering any project-specific mechanics, architecture, or history question.
    """
```

**Tool 2: `search_health`**
```python
@mcp.tool()
def search_health() -> dict:
    """
    Check whether the knowledge index is loaded and ready.
    Returns index version, chunk count, and model name.
    Call this if search_docs returns no results unexpectedly.
    """
```

- If `knowledge-index/` does not exist at startup, server starts but `search_docs` returns a structured error: `{"error": "index not found", "action": "run make knowledge-index"}` — does not crash.

### 2. Claude Code Registration

- New file: `.claude/settings.json` entry (or update existing):
  ```json
  {
    "mcpServers": {
      "knowledge-search": {
        "command": "python3",
        "args": ["tools/search_mcp.py"],
        "description": "Local semantic search over project docs, tickets, and investigations"
      }
    }
  }
  ```
- Claude Code spawns the process on startup; the MCP server loads the index once and stays resident.
- Add `make mcp-server-test` target to verify the server starts and responds to a tool call:
  ```makefile
  mcp-server-test: ## Smoke-test the MCP server (requires knowledge-index)
      echo '{"query": "damage formula", "top_k": 3}' | python3 tools/search_mcp.py --test
  ```

### 3. CLAUDE.md — Replace curl wiring with MCP reference

The existing CLAUDE.md entries added by `TCK-20260612-LOCAL-CTX-OPS` that say "run `curl POST http://localhost:8765/api/search`" are superseded. Replace with:

```
| Answering project-specific mechanics, architecture, or history questions |
  Call the `search_docs` MCP tool directly — no curl or bash needed.
  Fall back to: python3 tools/knowledge_search.py query "<q>" --top-k 5
  if the MCP server is not registered.
```

The FastAPI HTTP server (`make search-server-docker`) is NOT removed — it still serves human callers and `make eval-search`. Only the CLAUDE.md agent wiring changes.

### 4. `implement-ticket` Skill — Update Step 0

Replace the curl-based Step 0 added by `TCK-20260612-LOCAL-CTX-OPS` with:

```
Step 0: Context search
  Call: search_docs(query="<ticket title + request summary>", top_k=5)
  (MCP tool — no bash needed)
  Fallback if MCP unavailable: python3 tools/knowledge_search.py query "..." --top-k 5
  Use results to warm-start investigation: note source_path and excerpt per result.
```

### 5. Update Setup Documentation

Update `docs/guidelines/agent_working_environment.md`:
- Add a **MCP Setup** section after the Command Reference table:
  - How Claude Code auto-discovers the tool via `.claude/settings.json`
  - How to verify: run `make mcp-server-test`
  - Explain that `search_docs` appears in the agent's tool list automatically — no CLAUDE.md curl wiring needed
  - Fallback: if MCP is not registered, use the CLI path
- Update the **Agent Usage Pattern** section to show the MCP call as primary, curl as secondary (human use), CLI as tertiary (no server)

## Out of Scope
- HTTP transport for MCP (stdio is correct for local Claude Code use)
- Exposing the MCP server to remote clients
- Removing or replacing the FastAPI HTTP server (it serves humans and `make eval-search`)
- MCP resources or prompts (tools only for now)
- Authentication on the MCP server (local stdio process, not network-exposed)

## Acceptance Criteria
- [ ] `.claude/settings.json` contains a `knowledge-search` MCP server entry pointing to `tools/search_mcp.py`
- [ ] After restarting Claude Code, `search_docs` appears in the available tool list (verify via `/tools` or equivalent)
- [ ] `search_docs(query="damage formula", top_k=5)` returns at least one result with `source_path` under `docs/mechanics/` (no bash, no curl)
- [ ] `search_docs(query="WorldRepository", top_k=3, mode="keyword")` returns at least one result from `docs/architecture/` or `docs/worldassembly/`
- [ ] `search_health()` returns `{"status": "ok", "chunks": N, "model": "..."}` when index exists
- [ ] If `knowledge-index/` does not exist, `search_docs` returns `{"error": "index not found", "action": "run make knowledge-index"}` without crashing
- [ ] `make mcp-server-test` passes from a clean terminal without the HTTP server running
- [ ] CLAUDE.md Proactive Tool Use table references `search_docs` tool call, not curl
- [ ] `implement-ticket` Step 0 references `search_docs` tool call, not curl
- [ ] `docs/guidelines/agent_working_environment.md` MCP Setup section exists and is accurate
- [ ] The FastAPI HTTP server (`make search-server-docker`) still works independently — this ticket does not break it

## Related Tickets
- TCK-20260612-SEMANTIC-KNOWLEDGE-SEARCH (foundation — provides index and model)
- TCK-20260612-LOCAL-CTX-DOCS-CORPUS (must be done — docs/ chunks in index)
- TCK-20260612-LOCAL-CTX-HYBRID-SEARCH (must be done — hybrid scoring in search logic)
- TCK-20260612-LOCAL-CTX-HTTP-API (parallel — HTTP server remains for human use)
- TCK-20260612-LOCAL-CTX-OPS (coordinate — CLAUDE.md curl wiring from OPS is superseded by this ticket; implement MCP ticket after OPS or merge the CLAUDE.md edits)

## Related Docs
- docs/guidelines/agent_working_environment.md (update target)
- CLAUDE.md §Proactive Tool Use (update target)
- .claude/skills/implement-ticket/SKILL.md (update target)
- .claude/settings.json (update target)

## Related Stored Artifacts
- None.

## Related Code Areas
- `tools/search_mcp.py` (new)
- `tools/knowledge_search.py` (import — no changes to logic)
- `.claude/settings.json` (mcpServers entry)
- `Makefile` (`mcp-server-test` target)
- `CLAUDE.md` (Proactive Tool Use table — replace curl with tool call)
- `.claude/skills/implement-ticket/SKILL.md` (Step 0 — replace curl with tool call)
- `docs/guidelines/agent_working_environment.md` (MCP Setup section)
- `requirements.txt` or `pyproject.toml` (add `mcp`)

## Assumptions / Open Questions
- `.claude/settings.json` is the correct registration path for project-scoped MCP servers in Claude Code; verify against current Claude Code docs if the file doesn't exist yet
- The `mcp` Python package is the Anthropic MCP SDK — confirm package name is `mcp` on PyPI (it is, as of 2026)
- Model loading at MCP server startup takes ~2–3 seconds; Claude Code's MCP timeout should be long enough — if not, lazy-load the model on first `search_docs` call instead
- If `.claude/settings.json` already exists with other entries, add `knowledge-search` without overwriting existing keys

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
