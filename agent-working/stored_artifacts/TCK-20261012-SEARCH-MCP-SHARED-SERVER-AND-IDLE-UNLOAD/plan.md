---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261012-SEARCH-MCP-SHARED-SERVER-AND-IDLE-UNLOAD
artifact_type: plan
tags: [ai, mcp, process-improvement]
---

# plan — TCK-20261012-SEARCH-MCP-SHARED-SERVER-AND-IDLE-UNLOAD

## Order (as dispatched)
1. One ranking path: `tools/search_core.py` holds `rank()`, `resolve_index_dir`, `main_checkout_root`, `index_fingerprint`, `derive_title`. `search_mcp._search` and `search_server./api/search` both call `rank()`. The server also gains the worktree index fallback and an optional `stale` block.
2. Proxy: `search_mcp._run_search` asks `_proxy_search` first. It forwards only when `/api/health` is `ok` and its `index_fingerprint` equals this session's `knowledge.db` fingerprint (size:mtime_ns, independent of path so a container's bind mount matches). Health verdict cached 15 s; any failure returns None and the in-process path runs. Staleness is computed in the session on both paths.
3. Idle unload: a daemon `threading.Timer` reset by each in-process query; the callback re-checks the idle time under a lock and unloads (drops model/bm25/doc ids, `gc.collect`, `malloc_trim`). Injectable clock and timer factory. `SEARCH_MCP_IDLE_UNLOAD_S`, default 600, 0 = never.
4. `search_health` adds `path` and `model_loaded`.

## Decisions
- Fingerprint, not path, as index identity: a Docker server's path differs from the host's, so a path compare would never proxy there.
- The server's excerpt is now the MCP's (`text[:200]`); `_make_excerpt` and its tests are removed. This is what makes the two answers identical.
- `.mcp.json` untouched: the proxy lives inside the existing launch command.
