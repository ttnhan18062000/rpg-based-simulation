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

## Implementer refinements and deviations (2026-10-18, before coding)
1. **Code root is per index, not global.** `code_tools_dir(db_path)`: override `RPG_SEARCH_SHARED_CODE_ROOT` (a checkout root; tools = `<root>/tools`) wins; else the main checkout's `tools/` from git-common-dir of the module's own path (never cwd), cached per process; else this module's own dir. **Exception:** when this checkout is a worktree and `db_path` lies inside it (it has built its own index), it keeps its own `tools/`. Reason: the server refuses a `--db` other than the one its code searches (existing test, kept), so a main-checkout server could never serve that index and every query would respawn a server and wait 12 s. `search_mcp._main_checkout_root` stays (its tests pin it) and delegates to the one implementation in `search_shared.main_checkout_root`.
2. **Single instance.** `_main` takes `flock(LOCK_EX|LOCK_NB)` on `<dir>/server.lock` as its very first act (the directory comes from `--db` alone, before importing search_mcp or loading anything), writes the `starting` record, loads, and `serve()` overwrites it with the ready record. The fd stays open for the process life (module global); the kernel drops it on death. A loser prints one line and exits 0. If the load fails, the starting record is removed.
3. **Starting record is separate from `_read_state`.** `_read_state` still means "a ready record" (needs port/token). New `_read_starting(dir)` reads `{pid, state: "starting", started}`. A starting record with a live pid is never unlinked and never respawned over. With the pid dead it is stale and cleared. Older than `START_GRACE` (180 s) with a live pid = wedged: the client falls back in-process (reason `server not responding`), without spawning (the lock is held, a spawn would only exit).
4. **API.** `try_search_ex(...) -> (answer | None, reason | None)` with no printing. `try_search` stays as a wrapper that prints `_note(reason)` (existing tests and callers unchanged). Reason `REASON_STARTING = "server starting"`. The transition log moves to `search_mcp` (one line per mode change: shared / lexical-only / in-process).
5. **Fallback while starting: lexical-only (my proposal, matches the planner default).** `search_mcp._search_lexical` ranks by BM25 only (loads only bm25.pkl, never the model), reads rows from sqlite without sqlite-vec, `semantic_score` 0. It returns `{"results": [...], "degraded": "lexical_only_server_starting"}` so the answer says it is degraded, and `_run_search` still adds the `stale` field. After the server is ready, the next query uses the shared path again (no sticky state). Cost to the owner: a first query during a cold start returns keyword-only ranking; benefit: no client ever loads a 600 MB model because of a slow start. All other reasons (kill switch, unsafe dir, code mismatch, request failure, wedged) keep today's in-process search.
6. **Client wait.** `SPAWN_WAIT_SECONDS` (12 s) stays: it bounds how long one query blocks. A `starting` server → `(None, REASON_STARTING)` after that wait (it returns immediately if the starting record already exists and the server is not ready, with a short poll of at most 2 s so a nearly-ready server is not missed).
7. Tests follow test_plan.md (9 rows); test 8 asserts lexical-only (no embedder, `degraded` flag). `test_the_server_refuses_to_serve_a_database_other_than_the_one_it_searches` is kept as is.

## Planner review conditions (2026-10-18) and how this plan meets them
- Condition 1 assumed the server retargets to the requested `--db`. Item 1 above chose the other way (keep the server's refusal of a foreign `--db`; a worktree that has its own index keeps its own `tools/` as code root). Both keep the state-dir key, `server.json` `db` and `/health` `db` equal to the requested db, and give one server per db. The test the planner asked for is kept: a main-checkout client and a worktree client with its own index → two servers (one per db), and neither respawns on repeat queries.
- Condition 2: grep for other importers of `try_search` done before the edit; `try_search` stays as a wrapper.
- Condition 3: lexical-only while `starting` within `START_GRACE`; in-process past the grace or for any other reason. Both branches tested with a fake embedder load counter (0 vs 1).
