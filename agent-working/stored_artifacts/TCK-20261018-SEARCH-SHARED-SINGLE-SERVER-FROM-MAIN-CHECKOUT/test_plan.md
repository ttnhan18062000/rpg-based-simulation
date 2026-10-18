---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261018-SEARCH-SHARED-SINGLE-SERVER-FROM-MAIN-CHECKOUT
artifact_type: test_plan
tags: [ai, mcp, bug]
---

# Test plan — TCK-20261018-SEARCH-SHARED-SINGLE-SERVER-FROM-MAIN-CHECKOUT

All tests set `XDG_RUNTIME_DIR` to `tmp_path`, use the stub server command or fake embedder (which counts loads), and set `RPG_SEARCH_SHARED_ALLOW_TEST_SPAWN=1` only where a real child process is needed. None loads the real model or touches the live state dir.

| # | Test | Proves |
|---|---|---|
| 1 | `code_root()` from a temp git repo plus a linked worktree resolves the main checkout's tools; from a non-git dir → own dir; the env override wins | (a) resolution |
| 2 | Clients with differing worktree `tools/search_*.py` compute the main-root code_version and attach to one stub server; the fake embedder load count is 0 | AC1 |
| 3 | A slow stub server (sleeps > SPAWN_WAIT) with 3 concurrent clients → exactly one server process (count pids / `serve` invocations), every client gets `None` with reason "server starting" and zero embedder loads | AC2, cause 1 |
| 4 | A second `serve` on the same dir while the first holds `server.lock` exits 0 without calling the loader | (b) |
| 5 | SIGKILL the first `serve`, start another → it takes the lock and serves; no manual cleanup | (b) stale recovery |
| 6 | A `starting` record with a dead pid → treated as stale and cleared; one with a live pid younger than the grace → not unlinked and not respawned | (b) |
| 7 | The `search_mcp` transition log prints exactly one line per proxy↔in-process change over a 5-query sequence | (c) |
| 8 | The "server starting" fallback follows the decision in plan.md (lexical-only: no embedder load, and results flagged as degraded) | (c) |
| 9 | Regression: kill switch `RPG_SEARCH_SHARED=0`, the pytest no-spawn guard, and proxy/in-process result parity | unchanged |

Run: `.venv-knowledge/bin/python3 -m pytest tests/tools/test_search_shared.py tests/tools/test_search_mcp.py tests/tools/test_knowledge_search.py -q --basetemp=<own dir>`. This is light: no model and no full tools suite.

Post-merge (planner, not the implementer): one live repro on the real model with two clients from different worktrees, through lead-planner, alone, under `systemd-run --user --scope -p MemoryMax=…`. Expected: one server, both clients under 70 MB.

| 10 | A server on old code (stub reporting another code root) is terminated; exactly one new launch; the caller gets `server starting` (lexical-only, load count 0); racing 3 clients → still one new launch; a stuck old server keeping its lock is never raced by a second spawn | review: a pull must not make every client fat |
| 11 | A client whose own worktree tools differ never terminates a server matching the main checkout's; an own-index worktree client never touches the main-index server; a live pid whose recorded start time differs is never signalled (mutation-checked) | no kill loops, no recycled-pid kill |

## Proof Plan
- level: unit and process-level (real child processes with stub servers, tmp `XDG_RUNTIME_DIR`).
- proof kind: automated tests; the race test was mutation-checked (dropping the client's `starting` record yields three launches and fails).
- oracle source: the ticket's acceptance criteria and the 9 rows above; launch counts from a file the stub appends to, flock state, load counters on a fake embedder.
- expected effect: one server per index from the main checkout's code; no client loads a model during a slow start; one log line per transition.
- selected commands: `.venv/bin/python3 -m pytest tests/tools/test_search_shared.py tests/tools/test_search_mcp.py tests/tools/test_knowledge_search.py -q --basetemp=<own dir>` (211 passed, 35 skipped with test_session_cards).
