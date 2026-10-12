---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261012-SEARCH-MCP-SHARED-SERVER-AND-IDLE-UNLOAD
phase: open
date: 2026-10-12
tags: [ai, mcp, process-improvement]
---

# TCK-20261012-SEARCH-MCP-SHARED-SERVER-AND-IDLE-UNLOAD

## Title
search_docs: use the shared search server when it answers, and release the in-process model when idle

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P2

## Request Summary
GitHub issue #520 (finding from lead-planner): each Claude session's `.mcp.json` starts its own stdio
`tools/search_mcp.py`, so the sentence-transformers model is loaded once per session. On host ubuntu with 9
sessions this measured about 1.9 GB RSS (up to about 630 MB per process once loaded) on a machine with 2.8 GiB
available. On u24desktop (2026-10-11) the 9 processes held only about 275 MB, because `_ensure_loaded()` loads
the model on the first query; once loaded it is never released.

A shared HTTP server already exists (`tools/search_server.py`, `make search-server-docker`, 127.0.0.1:8765), but
it does **not** return the same results as `search_docs`:
- it ranks with a vector top-k plus `_ks._hybrid_score`, while `search_mcp.py` uses
  `hybrid_retrieval.hybrid_fuse_and_filter` (RRF fusion with the authority/freshness filter);
- it has no staleness block (`with_staleness`, TCK-20261006-KNOWLEDGE-INDEX-STALE-WARNING);
- it reads only its own checkout's index (no `_resolve_index_dir` worktree fallback,
  TCK-20261010-SEARCH-MCP-WORKTREE-VENV-RESOLUTION).
So a plain proxy would silently change what every session's search returns. That is why this is standard tier,
not a two-line change.

## Scope
1. One search path. Move the ranking body of `search_mcp._search` (embed, `hybrid_fuse_and_filter`, the section
   filter, the result dict shape) into a function both callers use (a small shared module under `tools/`, or
   `knowledge_search.py` if it fits there). `search_server.py`'s `/api/search` calls it, so the server and the
   MCP return identical results for the same index. Keep the server's response model; add the staleness block to
   its response as an optional field.
2. Proxy first. `search_mcp.py` checks `GET http://127.0.0.1:8765/api/health` (short timeout, about 0.5 s; the
   result is cached for a short TTL so every query does not pay it). When the server answers `ok` **and** serves
   the same index file as this session would resolve (compare a value the health payload exposes, such as the
   index path or the manifest hash), `search_docs` forwards to `/api/search`. Otherwise it searches in-process
   exactly as today. Any proxy error (connection refused, timeout, non-200) falls back in-process for that call;
   a fallback never surfaces as a tool error.
3. Idle unload. In the in-process path, release the model (and BM25 state) after an idle period with no query
   (default 10 minutes, override by environment variable, `0` = never unload). The next query reloads it.
   Checking the idle time only when the next query arrives is not enough, because the point is to free memory
   while no query arrives; a daemon `threading.Timer` reset on each query is acceptable. State why the chosen design frees
   memory in practice (CPython returning freed arenas, `gc.collect()`, torch tensors), and measure it.
4. `search_health` reports which path is active (`shared-server` or `in-process`) and whether the model is
   loaded, so a session can see it.
5. Measure on u24desktop: RSS of one `search_mcp.py` before the first query, after a query (in-process), after
   the idle unload, and with the shared server up (the proxy path must not load the model at all). Record the
   numbers in the ticket.
6. Tests in `tests/tools/` for: the proxy path used when health matches; fallback on refused connection,
   timeout, 503, and an index mismatch; the shared ranking function giving the same results through the server
   and the MCP for a fixture index; idle unload releasing state and the next query reloading it (inject the
   clock and the model loader; do not load the real model in unit tests).
7. Update `docs/guidelines/agent_working_environment.md` (the MCP setup section): the shared server is now the
   preferred way to run several sessions on one host, plus the idle-unload variable.

## Out of Scope
- Changing `.mcp.json` (lead-owned). The launch command stays `bash tools/start_search_mcp.sh`. If a change to it
  turns out necessary, stop and ask lead-planner first.
- Starting the Docker server automatically from a session or from SessionStart.
- The Docker image build on u24desktop (blocked by the TLS block on the torch index; see
  TCK-20261009-SEARCH-SERVER-IMAGE-PYTHON-FLOOR). Test the proxy path against `make search-server` (uvicorn)
  on this host.
- Interpreter and path literals in `start_search_mcp.sh` (TCK-20261012-HOST-PATH-LITERALS-MAKEFILE-AND-MCP-LAUNCHERS).
- Index building (`make knowledge-index`).

## Acceptance Criteria
- AC1: For the same index and query, `/api/search` and in-process `search_docs` return the same doc ids in the
  same order (test with a fixture index).
- AC2: With the server healthy on the same index, a `search_docs` call does not load the model in the MCP
  process (test, and the RSS measurement in Scope 5).
- AC3: With the server down, slow, returning 503, or serving a different index, `search_docs` returns in-process
  results and no error (tests).
- AC4: After the idle period, the in-process model is released and the next query reloads it (test with an
  injected clock). Measured RSS after unload is recorded.
- AC5: `search_health` names the active path and whether the model is loaded.
- AC6: Staleness reporting (`stale` block) is unchanged on both paths.
- AC7: `pytest tests/tools/test_search_server.py tests/tools/ -k "search"` passes; existing search tests still pass.
- AC8: `.mcp.json` is unchanged.

## Related Tickets
- GitHub issue #520 (source).
- TCK-20261010-SEARCH-MCP-WORKTREE-VENV-RESOLUTION (worktree index fallback; keep it).
- TCK-20261006-KNOWLEDGE-INDEX-STALE-WARNING (staleness block; keep it).
- TCK-20261009-SEARCH-SERVER-IMAGE-PYTHON-FLOOR (Docker image; build unverified on u24desktop).
- TCK-20260612-LOCAL-CTX-MCP, TCK-20260612-LOCAL-CTX-HTTP-API (original MCP and server).
- TCK-20261012-HOST-PATH-LITERALS-MAKEFILE-AND-MCP-LAUNCHERS (same batch).

## Related Docs
- docs/guidelines/agent_working_environment.md (MCP setup)

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20260612-LOCAL-CTX-MCP/ (if present)

## Related Code Areas
- tools/search_mcp.py, tools/search_server.py, tools/knowledge_search.py, tools/hybrid_retrieval.py
- tests/tools/test_search_server.py, tests/tools/ (search_mcp tests)

## Assumptions / Open Questions
- `tools/search_mcp.py`, `tools/search_server.py` and `tools/start_search_mcp.sh` have no owner in
  `registries/session_roles.yaml`. agent-working-planner takes this work from issue #520 without changing the
  manifest; ownership is routed separately.
- Comparing the index: if the health payload has no stable index identity today, add one (the resolved db path
  and the manifest hash) as part of Scope 2.

## Implementation Notes
Planner (2026-10-12): issue #520 suggested a proxy or idle unload. Both are scoped, because the proxy alone does
nothing on a host where the server is not running (u24desktop today), and idle unload alone keeps N copies
loaded while sessions are active.

## Test Summary

## Files Changed

## Completion Summary
