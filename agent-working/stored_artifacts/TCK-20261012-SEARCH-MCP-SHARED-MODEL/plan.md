---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261012-SEARCH-MCP-SHARED-MODEL
artifact_type: plan
tags: [ai, mcp]
---

# Plan — TCK-20261012-SEARCH-MCP-SHARED-MODEL (Refs #520)

Investigation and plan only. No code until the planner approves. Unstaffed-seat exception for `tools/**`; `.mcp.json` is lead-owned. Evidence: `investigation.md`.

## Options

| | A. proxy to a shared server | B. idle unload | C. A plus auto-spawn |
|---|---|---|---|
| idea | `search_mcp` asks one shared server; both run ONE core function; in-process fallback | drop the model after N idle minutes; reload on demand | A, with the first session's launcher starting the server |
| identical results | yes, by construction | yes (nothing changes) | yes, by construction |
| memory with 9 active sessions | about 0.6 GB + 9 x 60 MB = about 1.2 GB | 9 x 606 MB = about 5.4 GB while all are active; frees only when idle, and `malloc_trim` does not reliably return torch memory | about 1.2 GB |
| first-query latency | about 0 s once the server is up | 6 s on every reload | about 6 s for the first session ever, about 0 s afterwards |
| moving parts | server lifecycle owned by the owner | none | lock, state file, idle exit |
| new setup per host | owner must start it | none | none |

**Recommendation: C**, as lead's steers require. B alone does not help when sessions are active at the same time, which is exactly the fleet case; A without auto-spawn needs a daemon nobody starts.

## Design (C)

1. **One core.** New `tools/search_core.py` holds the search: index resolution (moved from `search_mcp`), the lazy `_State` loader, and `search(query, top_k, section, mode)` (the current `_search` body). `search_mcp._search` becomes a call into it. The server calls the same function. Nothing else is a search path.
2. **The shared server.** `tools/search_shared_server.py`: stdlib `http.server.ThreadingHTTPServer`, no new dependency, runs under `.venv-knowledge`. `POST /search` takes `{query, top_k, section, mode}` and returns exactly what `search_core.search` returns. `GET /health`. Model access is serialised with a lock. It loads the model at start, not at the first query. The existing FastAPI `search_server.py` and its Docker image are untouched (a follow-up can point it at the same core; out of scope here).
3. **Bind and auth.** `127.0.0.1` only, port 0 (the OS picks it), a random 32-byte token required in an `Authorization` header, so another local user's process cannot query it.
4. **Where state lives, and the key.** `$XDG_RUNTIME_DIR/rpg-search/<key>/` (outside the repo, per user, mode 0700; fallback `${TMPDIR:-/tmp}/rpg-search-<uid>/<key>/` created 0700). `<key>` is the first 12 hex of sha256 of the resolved index DB path. Worktrees resolve to the main checkout's index, so they share one server; a worktree with its own built index gets its own. Files: `lock` (flock), `server.json` `{pid, port, token, db, started}` written atomically (write tmp, `os.replace`).
5. **Client.** In `search_mcp._search`, before the in-process path: read `server.json`, `POST` with a 2 s connect and a 15 s read timeout. Any failure (no file, refused, timeout, non-200, bad JSON) falls back to the in-process core for that call. The staleness warning stays client-side (`_ks.index_staleness`, no model needed), and `_run_health` is unchanged, so both keep working with the server down.
6. **Spawn.** If no live server answers, take the `flock` (non-blocking, then short wait), re-check, then start the server detached (`setsid`, `start_new_session=True`, stdout/stderr to `server.log` in the state dir, 0600) and wait up to 12 s for `server.json` and `/health`. If it is not ready by then, serve this call in-process and let the server keep starting. The spawn code lives in Python (`search_core`/a small `search_shared.py`), called by `search_mcp.py`, so `tools/start_search_mcp.sh` needs no change and **`.mcp.json` stays unchanged**.
7. **Races, spelled out.**
   - *Two sessions start at once:* both see no server; both try the flock; the winner spawns, the loser waits for the lock (max 15 s), re-reads `server.json`, finds a live server and attaches. Never two servers per key because the check-and-spawn is under the lock.
   - *Stale state file:* `server.json` is trusted only if the pid is alive AND `GET /health` with the recorded token answers with the same `db`. Otherwise, under the lock, it is removed and a new server is spawned. A reused pid cannot pass the health check.
   - *Port taken by a foreign process:* there is no fixed port. The OS assigns one at bind, so no collision. If `server.json` names a port now held by a foreign process, the health check fails the token check and the stale path above applies.
   - *Server dies mid-session:* the next call fails fast (refused), falls back in-process for that call, and the next call goes through spawn again; no session breaks.
   - *Index rebuilt:* the server records the DB mtime and reloads BM25 (and re-reads the DB per request, as today) when it changes; the model is index-independent.
8. **Idle shutdown.** The server exits after 30 idle minutes (configurable), removing its state files, so nothing lingers after the fleet exits. The next search spawns it again.

## Hard constraints and how each is met

| constraint | how |
|---|---|
| identical top-k, proxy vs in-process | one `search_core.search`; plus a parity test as a guard |
| staleness warning keeps working | client-side, server not involved |
| worktree sessions keep working | index resolution moves into the core unchanged; key follows the resolved DB |
| `start_search_mcp.sh` u24desktop candidate (#517) | file not touched |
| search never breaks because of the server | every failure path falls back in-process; tested |
| no Docker in the critical path | stdlib server in the knowledge venv |

## `.mcp.json`

Unchanged. If review prefers the spawn in the launcher instead, the diff for lead would be: `tools/start_search_mcp.sh` only (add one `python3 tools/search_shared.py ensure` line before the final `exec`), still no `.mcp.json` edit.

## Measuring (recorded now; numbers recorded in the ticket at implementation)

Scripted 9-session equivalent: spawn 9 `search_mcp.py` stdio sessions (the MCP client in `.venv-knowledge`), each issuing one `search_docs`. Before (today's code) and after (C): per-process RSS and PSS and their sum (`/proc/<pid>/smaps_rollup`), plus `MemAvailable`; first-query latency in three cases: in-process (today, 6.05 s measured), proxied with the server already up, proxied with a cold spawn. Baseline already measured: 5 loaded sessions about 3.2 GB total, 606 MB per loaded process. Expected after: about 0.6 GB + 9 x 60 MB.

## Risks

- A detached process outliving its parent session: bounded by the idle exit and a PID check.
- Memory accounting on the host: the server counts against whichever cgroup spawned it; documented in the ticket.
- A second, stdlib server beside the FastAPI one: two entry points. Mitigated by the shared core and the follow-up to retire the divergent `/api/search` path.

## Out of scope

`search_server.py`/Docker, `.mcp.json`, the u24desktop candidate (#517), changing result quality.

## Approved additions (planner and lead, 2026-10-12) and what was built

- **(a) Code-version check.** `/health` and `server.json` carry `code_version`, a sha256 prefix over `search_mcp.py`, `search_shared.py`, `knowledge_search.py` and `hybrid_retrieval.py` (the files that decide a result). The client compares it with its own and searches in-process on a mismatch; it never spawns over a live mismatched server. Test: `test_a_server_from_different_code_is_never_used`, `test_code_version_follows_the_result_deciding_files`.
- **(b) Kill switch.** `RPG_SEARCH_SHARED=0` forces in-process search; `tests/tools/conftest.py` sets it for every test. Under pytest no server is spawned unless `RPG_SEARCH_SHARED_ALLOW_TEST_SPAWN=1`. The lifecycle tests run their servers in a tmp `XDG_RUNTIME_DIR` and a fixture tears them down.
- **(c) Fallback accounting.** A session whose 12 s spawn wait times out searches in-process for that call and still tries the server first on the next. The measurement counts sessions holding an in-process model by RSS above 300 MB.
- **Lead 1 (key).** `<key>` is sha256 of the index DB's resolved path, never its contents; test `test_state_dir_key_is_the_resolved_path_not_the_contents`. A rebuilt index reaches the same server, which reloads BM25 when the DB mtime changes (`test_the_server_reloads_bm25_when_the_index_is_rebuilt`).
- **Lead 2 (concurrency).** `encode()` is serialised behind a lock (`_LockedModel`); each request opens its own sqlite connection inside `_search` and nothing is shared across threads. Test: two parallel queries equal the same two run sequentially.
- **Lead 3 (secrets).** `server.json` is written 0600 inside the 0700 directory, atomically (tmp + `os.replace`); the client refuses a directory or file that is not owned by its uid or is group/other accessible, and falls back in-process. Tests for both.

### Deviations from the plan as first written (all disclosed)
1. **No new `search_core.py`.** `search_mcp._search` already is the one core function, so the server calls it directly (`serve(_reloading(mcp)...)`, wrapper only adds the BM25 reload) and the client sits in a thin `_search_shared_or_local` wrapper that `_run_search` calls. Moving the body would have broken tests that patch `search_mcp`'s own globals for no gain. A test pins that the server runs `mcp._search`.
2. **Timeouts.** Connect 2 s, read 8 s (a legitimate query takes about 1 s warm); health checks use the 2 s one, so a foreign listener that accepts and never answers costs 2 s, not 8.
3. **Real-index parity** is measured through the actual MCP tool with a real server (below), not as a CI test (CI has no knowledge index or model); CI covers the transport and the lifecycle with a stub server.

### Measured result (host `ubuntu`, main index, same code, 9 stdio MCP sessions each running `search_docs`)
| | in-process (today), 2 sessions measured | shared server (C), 9 sessions measured |
|---|---|---|
| RSS per session | 630 and 632 MB | 65 MB (all 9) + server 630 MB |
| PSS per session | 482 and 483 MB | 48 MB + server 489 MB |
| total RSS / PSS | 1,262 / 965 MB (2 sessions) | **1,220 / 919 MB (9 sessions)** |
| extrapolated to 9 sessions (linear) | about 5.7 GB RSS / 4.3 GB PSS | 1.2 GB / 0.9 GB |
| sessions holding an in-process model | 2 of 2 | **0 of 9** |
| MemAvailable drop | 902 MB for 2 sessions | 731 MB for 9 sessions |
| first `search_docs`, cold | 10.6 and 11.3 s (two concurrent cold loads) | 8.3 s for the very first session (it spawns the server and waits for the model); 1.8 to 3.4 s for the other 8 queried at once (serialised on one model) |
| parity | reference | **5 of 5 queries byte-identical** `search_docs` output, proxied vs in-process |

Nine in-process sessions were not run: about 5.7 GB would not fit beside the other sessions on a 9.9 GB host; the in-process cost is linear per session (606 to 632 MB measured four times).
