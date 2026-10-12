---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261012-SEARCH-MCP-SHARED-MODEL
phase: open
date: 2026-10-12
tags: [ai, mcp]
---

# TCK-20261012-SEARCH-MCP-SHARED-MODEL

## Title
One shared embedding model for the fleet's search_docs sessions

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Refs #520. Each Claude session spawns its own `tools/search_mcp.py`, and each loads about 600 MB of embedding model on its first query; 5 loaded sessions hold about 3.2 GB of a 9.9 GB host. Unstaffed-seat exception: `tools/**` belongs to agent-working, whose seat is unstaffed; codebase takes this at the planner's request. `.mcp.json` is lead-owned.

## Scope
Investigation and plan only until the planner approves: measured baseline, a server-vs-in-process parity check, server availability on this VM, lifecycle ownership, and a recommended option.

## Out of Scope
Any code. The FastAPI `search_server.py` and Docker path, `.mcp.json`, the `start_search_mcp.sh` u24desktop candidate (#517).

## Acceptance Criteria
1. `investigation.md` answers the four questions with numbers.
2. `plan.md` compares A/B/C, recommends one, meets lead's six steers.
3. Nothing is implemented before approval.

## Related Tickets
- #520, #517

## Related Docs
- docs/guidelines/agent_working_environment.md
- docs/plans/codebase_health/mypy_pin_and_search_shared_model_brief.md (committed on branch mypy-dev-pin)

## Related Stored Artifacts
- agent-working/staging_artifacts/TCK-20261012-SEARCH-MCP-SHARED-MODEL/

## Related Code Areas
- tools/search_mcp.py
- tools/search_server.py
- tools/start_search_mcp.sh

## Assumptions / Open Questions
Recommended option C needs the planner's and lead's approval, including the 30-minute idle default and the stdlib server.

## Implementation Notes
None yet.

## Test Summary
TBD

## Files Changed
- agent-working/staging_artifacts/TCK-20261012-SEARCH-MCP-SHARED-MODEL/ (investigation, plan, test plan)

## Completion Summary
TBD
