---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261018-SEARCH-SHARED-SINGLE-SERVER-FROM-MAIN-CHECKOUT
phase: open
date: 2026-10-18
tags: [ai, mcp, bug, root-cause]
---

# TCK-20261018-SEARCH-SHARED-SINGLE-SERVER-FROM-MAIN-CHECKOUT

## Title
One shared search server per host, served from the main checkout's code. Clients that time out or see a code mismatch stop loading their own model.

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
GitHub #628, claimed on #634 (host ubuntu, approved by lead-planner on 2026-10-18).

On host ubuntu, two `search_shared.py serve` processes (~570 MB each) ran at once. The two `search_mcp.py` clients that spawned them were ~650 MB each, which means they had loaded the model in-process. That's about 2.4 GB on a 9.9 GB VM during a load spike (load 35–75), with a 37 s guest stall. Separately, the shared server on 2026-10-18 runs from `.claude/worktrees/platform-planner/tools/`, a worktree copy.

The root causes are in `investigation.md`. In short:
- (1) a slow model load under host load overruns `SPAWN_WAIT_SECONDS` (12 s). The waiting client falls back in-process and loads its own model. The lock is released while server.json doesn't exist yet, so the next client spawns a second server. The first server becomes an orphan until its 1800 s idle exit;
- (2) `code_version()` hashes the client's **own** `tools/` copy. Any worktree whose `tools/search_*.py` differs from the copy the server was spawned from falls back in-process on every query;
- (3) whichever client spawns first decides which checkout's code serves, so a worktree that is editing `tools/search_*.py` can capture the shared server.

## Scope
- **(a) Code root pinned to the main checkout.** The server argv and the client's comparison `code_version` both use the main checkout's `tools/`, resolved from `git rev-parse --git-common-dir` from the module's own path (never cwd), with the existing `search_mcp._main_checkout_root` logic reused or moved to one place.
  - If the main checkout can't be resolved, keep today's behaviour (own tools dir).
  - A worktree editing `tools/search_*.py` therefore neither spawns nor is served by its own copy, unless `RPG_SEARCH_SHARED_CODE_ROOT` (a test/dev override) says so.
- **(b) Single instance, held by the server.**
  - The server takes an exclusive, non-blocking flock on `<state dir>/server.lock` **before** loading the model and holds it for its whole life. A second `serve` that can't get it exits 0 immediately, without loading.
  - The kernel drops the flock when the pid dies, so a dead pid's lock recovers without manual cleanup. Test this with a killed child.
  - A spawn in progress counts as alive: the server writes a `starting` record (pid, `started`) under the lock before the load. While that pid lives and the record is younger than a bound (e.g. 180 s), a client waits for it or returns `None` without spawning. It never unlinks the record or spawns a second server.
- **(c) No silent fat clients.** When the shared path returns `None` because the server is still starting, `search_mcp` retries the shared path on the next query instead of staying in-process.
  - A client that fell back in-process keeps trying the shared path per query (as today) and frees its own model through the existing idle unload.
  - It logs exactly one stderr line when it moves between proxy and in-process (`[search_shared] using shared server` / `… in-process fallback: <reason>`), with no per-query spam.
  - Decide in plan.md whether the fallback on a "server starting" timeout should be a short-wait in-process search (today's behaviour) or a lexical-only answer while the server loads. The default is lexical-only, which never loads the model in the client; record the decision.
- Update the module docstring and `docs/guidelines/agent_working_environment.md` § "One shared search model for the whole fleet".
- **Tests** (`tests/tools/test_search_shared.py`, `tests/tools/test_search_mcp.py`):
  - They use an isolated tmp state dir (`XDG_RUNTIME_DIR` → tmp_path) and a stub/fake embedder or stub server command.
  - They **never touch the live server's state dir and never load the real model**.
  - The full list is in `test_plan.md`.

## Out of Scope
- Changing the index, ranking or results: results must stay byte-identical between the proxy and in-process paths.
- The HTTP `search_server.py` proxy (TCK-20261012-SEARCH-MCP-SHARED-SERVER-AND-IDLE-UNLOAD).
- Killing or restarting today's live servers: the owner does that with `/mcp` reconnect.
- The live two-client repro on the real model. It's done once by the planner after the merge, through lead-planner and under the memory cap, and isn't part of the implementer's test run.

## Acceptance Criteria
- Two clients from different worktrees whose `tools/search_*.py` differ, plus one from the main checkout, all reach **one** server whose code is the main checkout's. No client loads a model (proved with a fake embedder that counts loads).
- Concurrent spawn: N clients (≥3) racing to start against a server that is slow to load (stub sleeps longer than `SPAWN_WAIT_SECONDS`) end with exactly one server process, and no client loads the embedder.
- A second `serve` against the same state dir exits without loading. A `serve` started after the first holder was SIGKILLed takes the lock and serves.
- The proxy↔in-process transition logs one line per transition.
- `tests/tools/test_search_shared.py`, `tests/tools/test_search_mcp.py` and `tests/tools/test_knowledge_search.py` are green, and the existing kill switch and pytest no-spawn guard still hold.

## Related Tickets
- TCK-20261012-SEARCH-MCP-SHARED-MODEL (introduced search_shared)
- TCK-20261012-SEARCH-MCP-SHARED-SERVER-AND-IDLE-UNLOAD (idle unload, HTTP proxy)
- TCK-20261010-SEARCH-MCP-WORKTREE-VENV-RESOLUTION (main checkout index fallback)

## Related Docs
- docs/guidelines/agent_working_environment.md § One shared search model for the whole fleet

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261012-SEARCH-MCP-SHARED-MODEL/
- agent-working/stored_artifacts/TCK-20261012-SEARCH-MCP-SHARED-SERVER-AND-IDLE-UNLOAD/

## Related Code Areas
- tools/search_shared.py, tools/search_mcp.py, tools/start_*_mcp.sh (read only unless needed)

## Assumptions / Open Questions
- Lexical-only versus in-process fallback while the server starts: the implementer proposes in plan.md, and the planner decides at review.

## Implementation Notes
## Test Summary
## Files Changed
## Completion Summary
