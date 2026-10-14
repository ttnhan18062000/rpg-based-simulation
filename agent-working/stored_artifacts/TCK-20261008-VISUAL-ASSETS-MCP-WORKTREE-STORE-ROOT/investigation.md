---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261008-VISUAL-ASSETS-MCP-WORKTREE-STORE-ROOT
artifact_type: investigation
date: 2026-10-09
tags: [architecture, testing]
---

# Investigation

- `visual_assets/store/config.py` `_VISUAL_ASSETS = Path(__file__).resolve().parents[1]`; `start_mcp.sh` execs the module from the script's own checkout; `.mcp.json` registers `visual_assets/start_mcp.sh` relative to the session's project dir, which is the main checkout when a session works in a worktree via `cd`. The handoff workspace (`ASEPRITE_MCP_WORKSPACE`) is already shared in `~/.cache`.
- The server code of the main checkout may differ from the worktree's; the variable selects DATA (catalog, quarantine, review, drafts) only, the running code is still the launching checkout's. The label says so (`source`).
- Boundary test lets the server import `store.config` (allowed set includes `config`); the new code stays inside it. Path-free label because `store_*` results never carry absolute paths.
- Mutant runs that make the server ignore the variable stage a real intake into the REAL checkout's gitignored quarantine (one stray, `in-99648d0964800e3e`, was written and removed).
