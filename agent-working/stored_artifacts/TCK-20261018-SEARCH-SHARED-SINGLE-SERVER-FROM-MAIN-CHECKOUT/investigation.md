---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261018-SEARCH-SHARED-SINGLE-SERVER-FROM-MAIN-CHECKOUT
artifact_type: investigation
tags: [ai, mcp, bug]
---

# Investigation — TCK-20261018-SEARCH-SHARED-SINGLE-SERVER-FROM-MAIN-CHECKOUT

## Evidence (host ubuntu, 2026-10-18)
- #628 (lead-planner, ~14:10): two `search_shared.py serve` at ~570 MB, whose parents were the perf-implementer and asset-implementer `search_mcp.py` (~650 MB each). Every other client was 18–34 MB. Both sessions had been `/clear`ed; an incremental index rebuild ran at about 00:45; load was 35–75.
- At planner review, 18:59: one server, pid 464861 (631 MB), argv `.claude/worktrees/platform-planner/tools/search_shared.py serve`. Clients run from the main checkout `tools/`, `.claude/worktrees/{platform,platform-planner,agent-working,agent-working-planner}/tools/`.
- State dir `$XDG_RUNTIME_DIR/rpg-search/<key>/` holds `lock`, `server.json` and `server.log`. The log shows repeated "Loading weights" (one per server start).

## Code path (tools/search_shared.py at origin/main 760f5ac9d)
- `_TOOLS_DIR = Path(__file__).resolve().parent`, and `_server_argv()` runs **this client's** `search_shared.py`. So the spawning client's checkout serves.
- `code_version()` hashes `_CODE_FILES` from **this client's** `_TOOLS_DIR`. `try_search()` returns `None` ("server was started from different code") whenever the client's hash ≠ the server's, and `search_mcp` then searches in-process → loads the model. **Cause 2.**
- `_attach_or_spawn()`, under `<dir>/lock` (a flock held by the client, waiting up to 15 s):
  - reads server.json; if it isn't alive, it unlinks it, spawns, and `_wait_ready()` polls for up to `SPAWN_WAIT_SECONDS = 12`;
  - the server's `_main` calls `mcp._ensure_loaded()` (model + BM25) **before** `serve()` writes server.json;
  - under load the model load takes longer than 12 s, so the client returns `None` → in-process (fat client). The lock is released while the first server is still loading, the next client sees no server.json, and it spawns **a second server**;
  - other clients waiting on the lock for over 15 s also get `None` → in-process. When both servers finish, the later `_write_state` wins and the earlier one is unreachable until its 1800 s idle exit. **Cause 1. This matches #628 exactly: two servers, each parented by a fat client.**
- Nothing in `serve()` enforces one server per state dir. **Cause 3** is the capture by whichever checkout spawns first.

## Not the cause
- An index rebuild alone doesn't restart the server: `_reloading()` reloads BM25 in place.
- `/clear` doesn't restart MCP processes. It only made both sessions query at about the same time after the rebuild.

## Reuse
- `search_mcp._main_checkout_root()` already resolves the main checkout from `--git-common-dir`.
- The existing pytest guard `spawn_allowed()` / `ALLOW_TEST_SPAWN` and stub server command in `tests/tools/test_search_shared.py` (the "fake index file, the shared path switched on, and a stub server command" fixture).
