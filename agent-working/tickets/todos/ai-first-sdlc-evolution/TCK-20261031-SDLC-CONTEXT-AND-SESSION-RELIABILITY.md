---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261031-SDLC-CONTEXT-AND-SESSION-RELIABILITY
phase: open
date: 2026-10-31
tags: [ai, governance, delivery]
---

# TCK-20261031-SDLC-CONTEXT-AND-SESSION-RELIABILITY

## Title
Agents can trust the freshness and authority of search, graph and handover context.

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Phase 5 (plan section 39). It needs no owner decision, is independent of the other phases, and can run in parallel.

## Scope
1. Fix the search staleness root; the stale flag is correct in worktrees.
2. Add an authority field and history down-weighting.
3. Mark branch content as not indexed.
4. Rebuild the graph on a schedule and print its build SHA.
5. A handover header and a write-time cap.
6. A canonical session path to fix the memory split.
7. Provenance labels on injected content.
8. Run E3 (plan section 45) and report.

## Out of Scope
- Search engine replacement.
- Editing the user's memory content.
- Thresholds the plan leaves to the owner: propose after the baseline; do not set them.

## Acceptance Criteria
1. The stale flag is correct in worktrees, with a test.
2. E3 baseline and after-numbers are recorded over 20 authority queries; the owner sets the share.
3. No handover over the cap without a write-time warning.
4. `tests/tools/` passes in a lead slot.

## Related Tickets
- TCK-20261031-EPIC-AI-FIRST-SDLC-EVOLUTION

## Related Docs
- docs/plans/agent_infrastructure/AI_FIRST_SDLC_ARCHITECTURE_EVOLUTION_PLAN.md
- docs/plans/agent_infrastructure/AI_FIRST_SDLC_DECISION_SUMMARY.md

## Related Stored Artifacts
- none

## Related Code Areas
- tools/knowledge_search.py, tools/search_mcp.py, tools/hybrid_retrieval.py
- tools/sessions/session_start_hook.py, tools/graphify_*

## Assumptions / Open Questions
- Owner condition #715 6528807751: credential details from either host stay out of committed files, tickets and public comments unless a decision needs them; they go to the owner directly.
- No credential or ruleset change is authorised by the epic; each gets its own owner ask, by ticket.
- Undecided, and not to be written as decided: OD-4 to OD-9, OD-11 to OD-13, OD-16 to OD-21.

## Implementation Notes
(to be filled by the implementer)

## Test Summary
(to be filled by the implementer)

## Files Changed
(to be filled by the implementer)

## Completion Summary
(to be filled by the implementer)
