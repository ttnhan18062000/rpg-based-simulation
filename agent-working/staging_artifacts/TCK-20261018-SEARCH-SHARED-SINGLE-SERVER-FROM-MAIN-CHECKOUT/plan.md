---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261018-SEARCH-SHARED-SINGLE-SERVER-FROM-MAIN-CHECKOUT
artifact_type: plan
tags: [ai, mcp, bug]
---

# Plan — TCK-20261018-SEARCH-SHARED-SINGLE-SERVER-FROM-MAIN-CHECKOUT

Planner draft. The implementer refines it and records deviations here before coding.

## Order
1. **Code root.** Add `code_root()` in `search_shared.py`, which resolves the main checkout's `tools/` via git-common-dir from `_TOOLS_DIR`. Use the env override `RPG_SEARCH_SHARED_CODE_ROOT` (tests/dev); fall back to `_TOOLS_DIR` when resolution fails. `_server_argv()` and the client-side `code_version()` both use it. Move `_main_checkout_root` so `search_mcp` and `search_shared` share one implementation, without circular import trouble (both are loaded via `spec_from_file_location`).
2. **Server-held single instance.** In `_main` before `_ensure_loaded()`, `os.open(<dir>/server.lock)` and take `flock(LOCK_EX|LOCK_NB)`. On failure, print one line and exit 0. Then write a `starting` record (`{"pid", "state": "starting", "started"}`) atomically, load, and then `serve()` writes the ready record. Keep the fd open for the process's life.
3. **Client attach.**
   - `_alive` accepts `starting` while the pid lives and `now - started < START_GRACE` (180 s).
   - `_attach_or_spawn` never unlinks a live `starting` record and never spawns while one exists. It waits up to `SPAWN_WAIT_SECONDS`, then returns a distinct "starting" result → `try_search` returns `None` with reason `server starting`.
   - A stale record whose pid is dead is cleared as today.
4. **Fallback while starting.** Proposal: `search_mcp._search_shared_or_local` answers lexical-only (BM25, no model) when the reason is `server starting`, marks the result `degraded: "lexical_only_server_starting"`, and only loads the model in-process for other reasons (kill switch, unsafe dir, request failure). The planner decides at review.
5. **One-line transition log.** A module-level last-mode flag in `search_mcp`; log on change only.
6. **Docs.** The module docstring and the agent_working_environment.md section.

## Scope guards
- Ranking/results are unchanged on both paths; the existing parity test stays.
- No change to the state-dir location or key, token handling or the kill switch.
- Tests never spawn against the real `$XDG_RUNTIME_DIR` and never import sentence-transformers.
