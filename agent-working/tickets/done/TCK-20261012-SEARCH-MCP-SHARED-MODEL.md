---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261012-SEARCH-MCP-SHARED-MODEL
phase: done
date: 2026-10-12
tags: [ai, mcp]
---

# TCK-20261012-SEARCH-MCP-SHARED-MODEL

## Title
One shared embedding model for the fleet's search_docs sessions

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Refs #520. Each Claude session spawns its own `tools/search_mcp.py`, and each loads about 600 MB of embedding model on its first query; 5 loaded sessions hold about 3.2 GB of a 9.9 GB host. Unstaffed-seat exception: `tools/**` belongs to agent-working, whose seat is unstaffed; codebase takes this at the planner's request. `.mcp.json` is lead-owned.

## Scope
Investigation and plan (approved by the planner and lead, option C), then the implementation: `tools/search_shared.py` (shared server and client), a thin wrapper in `tools/search_mcp.py`, tests, and docs. Unstaffed-seat exception for `tools/**`; `.mcp.json` and `tools/start_search_mcp.sh` unchanged.

## Out of Scope
The FastAPI `search_server.py` and Docker path, `.mcp.json`, the `start_search_mcp.sh` u24desktop candidate (#517).

## Acceptance Criteria
1. `investigation.md` answers the four questions with numbers; `plan.md` compares A/B/C and meets lead's steers (all done).
2. Parity gate: the same top-k from the shared server and in-process (done: 5 of 5 byte-identical through the MCP tool).
3. Search never breaks because of the server; kill switch; no test spawns a real detached server; no server left running.
4. Nine-session before/after numbers recorded here.

## Related Tickets
- #520, #517

## Related Docs
- docs/guidelines/agent_working_environment.md
- docs/plans/codebase_health/mypy_pin_and_search_shared_model_brief.md (committed on branch mypy-dev-pin)

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261012-SEARCH-MCP-SHARED-MODEL/

## Related Code Areas
- tools/search_mcp.py
- tools/search_server.py
- tools/start_search_mcp.sh

## Assumptions / Open Questions
Approved: option C, 30-minute idle default, stdlib server, FastAPI server untouched. **Follow-up for agent-working:** point `tools/search_server.py` (and its Docker image) at the same core search path; today its `/api/search` returns different results.

## Implementation Notes
No separate `search_core.py`: `search_mcp._search` already is the one core function; the server calls it (`serve(_reloading(mcp)...)`), the client is `_search_shared_or_local` in `search_mcp`. Code-version hash covers `search_mcp.py`, `search_shared.py`, `knowledge_search.py`, `hybrid_retrieval.py`. State in `$XDG_RUNTIME_DIR/rpg-search/<sha256(resolved index DB path)[:12]>/` (0700; `server.json` 0600, atomic). Kill switch `RPG_SEARCH_SHARED=0`. A bug found by the new tests: `mkdir(parents=True)` made the intermediate directory 0755; each level is now created 0700. A second: health checks waited the full read timeout on a foreign listener that never answers; they now use the 2 s timeout.
Measured (host `ubuntu`, main index, 9 stdio MCP sessions): in-process, 2 sessions measured: 630 and 632 MB RSS each (482 and 483 MB PSS), total 1,262 MB RSS, extrapolated to 9 about 5.7 GB RSS / 4.3 GB PSS; shared, 9 sessions measured: 65 MB RSS (48 MB PSS) per session plus the server at 630 MB RSS (489 MB PSS), total 1,220 MB RSS / 919 MB PSS, 0 of 9 sessions holding an in-process model, MemAvailable drop 731 MB (902 MB for 2 in-process sessions). First `search_docs`: in-process cold 10.6 and 11.3 s (two concurrent loads); shared: 8.3 s for the first session (spawns the server and waits for the model), 1.8 to 3.4 s for the other 8 queried at once. Parity: 5 of 5 queries byte-identical `search_docs` output. Nine in-process sessions were not run (about 5.7 GB would not fit beside the other sessions).

## Test Summary
`tests/tools/test_search_shared.py` 20 passed (a stub server in a tmp XDG_RUNTIME_DIR, torn down by a fixture, none left running); `tests/tools/test_search_mcp.py` 4 new wiring tests. Whole `tests/tools` plus `tests/static` (kill switch on): 4900 passed, 29 skipped, 1 xfailed; the one failure was the registry drift check before the registry was regenerated (re-run after: see Completion Summary). Ruff clean on the new module.

## Files Changed
- tools/search_shared.py (new)
- tools/search_mcp.py (import and `_search_shared_or_local` wrapper)
- tests/tools/test_search_shared.py (new), tests/tools/test_search_mcp.py (4 tests), tests/tools/conftest.py (kill switch)
- docs/guidelines/agent_working_environment.md
- agent-working/stored_artifacts/TCK-20261012-SEARCH-MCP-SHARED-MODEL/ (investigation, plan, test plan)

## Completion Summary
One shared embedding model per index for the whole fleet: first session's search starts a detached stdlib server, later sessions attach, any failure searches in-process, identical results by construction and by test. Nine sessions hold about 1.2 GB instead of about 5.7 GB. Unstaffed-seat exception (`tools/**`). Follow-up for agent-working: point `search_server.py` at the same core.
