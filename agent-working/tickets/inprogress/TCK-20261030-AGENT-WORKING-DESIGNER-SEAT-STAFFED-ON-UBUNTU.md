---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261030-AGENT-WORKING-DESIGNER-SEAT-STAFFED-ON-UBUNTU
phase: open
date: 2026-10-30
tags: [process-improvement]
---

# TCK-20261030-AGENT-WORKING-DESIGNER-SEAT-STAFFED-ON-UBUNTU

## Title
The roster marks `agent-working-designer` as staffed on host ubuntu, ending the planner's interim hold on the seat.

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
Owner instruction #715 6525124859 (2026-10-30, recorded by lead-planner, read by me): the AI-first SDLC evolution work moves to host ubuntu and `agent-working-designer` is staffed there, reversing the 2026-10-18 "no designer on host ubuntu" note. The registry flip goes through the agent-working domain as a normal change. The seat is already running; its card still says "(unstaffed, held by agent-working-planner)". This instruction decides none of the plan's OD-1..OD-9.

## Scope
1. `registries/session_roles.yaml`, role `agent-working-designer`: `seat_status: unstaffed` -> `staffed`; remove `interim_holder` and the "no designer on host ubuntu" comment; add `card_note: "Host ubuntu; twin `-u24`."`.
2. `tests/tools/test_session_u24_twins.py::test_row7_seat_status`: the designer now asserts `("staffed", None)`, like the planner.
3. `tests/tools/test_session_roster.py:104`: the trailing comment says the designer is unstaffed; update it. The count of 32 does not change.
4. Regenerate the role cards and views with `tools/sessions/generate_agents.py` (plus any territory or cross-domain view the session tooling generates), so `.claude/agents/session-agent-working-designer.md` no longer says "held by".
5. Check whether `docs/plans/agent_infrastructure/session_layer_working_process.md:157-169` describes the designer as unstaffed; correct it only if it states the current seat (it is a plan, so history stays).

## Out of Scope
- `codebase-designer`'s `interim_holder: agent-working-designer`: unchanged. It stays valid and is a separate question.
- The SDLC evolution plan, its OD-1..OD-9 and moving its documents (the new seat's work).
- Any change to `accepts_dispatch_from` or `may_write`: the designer's values already match its `-u24` twin.

## Acceptance Criteria
1. `python3 -m tools.sessions.validate` is clean; the generated cards and views have no drift.
2. The designer's card has no "held by" and carries `Host ubuntu; twin `-u24`.`
3. Every registry-edit view is regenerated, and all of `tests/tools/` passes (a full run, not a -k subset, per the registry-edit rule). Take a lead slot, MemoryMax<=3G.
4. `tests/tools/test_agent_working_paths_guard*.py` passes before the push.

## Related Tickets
- TCK-20261025-RPG-UBUNTU-SEATS (the last seat change)

## Related Docs
- docs/plans/agent_infrastructure/session_layer_working_process.md

## Related Stored Artifacts
- none

## Related Code Areas
- registries/session_roles.yaml
- tools/sessions/generate_agents.py, tools/sessions/card.py
- tests/tools/test_session_u24_twins.py, tests/tools/test_session_roster.py
- .claude/agents/session-agent-working-designer.md

## Assumptions / Open Questions
- None. lead-planner asked for this citing the owner comment above; the push ask goes through lead-planner.

## Implementation Notes
(to be filled by the implementer)

## Test Summary
(to be filled by the implementer)

## Files Changed
(to be filled by the implementer)

## Completion Summary
(to be filled by the implementer)
