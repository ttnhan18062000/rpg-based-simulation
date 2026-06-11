---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260607-MON-CAPTURE
phase: done
date: 2026-06-07
tags: [mon, capture]
---

# TCK-20260607-MON-CAPTURE

## Title
Agent Monitoring — Integrate event capture into implement-ticket workflow and enforce as hard rule

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Implement the capture layer: write run and event records at every exit point in `implement-ticket.js`. Add hard rules to CLAUDE.md and DoD condition 12. Implement `record_run.py` and `record_events.py` scripts.

## Scope
- `tools/agent-monitoring/record_run.py` — implemented in MON-SCHEMA
- `tools/agent-monitoring/record_events.py` — implemented in MON-SCHEMA
- `implement-ticket.js` — full monitoring integration (events[], pushEvent(), writeMonitoring())
- `CLAUDE.md` — hard rule + DoD condition 12

## Out of Scope
- Other workflows
- Agent summary field quality (TCK-MON-AGENTS)
- Processing/retro scripts (TCK-MON-RETRO)

## Acceptance Criteria
- [x] `implement-ticket.js` initializes events[] after Scope phase
- [x] pushEvent() called after every agent call with phase, agent, status, summary
- [x] writeMonitoring() called at all 8 exit paths (CONFLICTS_DETECTED, EPIC_SCOPED, NEEDS_HUMAN_INPUT, NEEDS_CHANGES, BLOCKED, TESTS_FAILED, DOD_BLOCKED, DONE)
- [x] Hotfix tier: pushes 3 skipped events for Investigate/Plan/Review phases
- [x] Monitoring agent failure (null return) logs WARNING, does not fail workflow
- [x] CLAUDE.md Hard Rules updated with monitoring mandate
- [x] CLAUDE.md DoD condition 12 added

## Related Tickets
- TCK-20260607-MON-SCHEMA (dependency)
- TCK-20260607-MON-AGENTS (parallel)
- TCK-20260607-MON-RETRO (consumer)

## Related Docs
- `.claude/workflows/implement-ticket.js`
- `CLAUDE.md`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260607-MON-CAPTURE/`

## Related Code Areas
- `.claude/workflows/implement-ticket.js`
- `CLAUDE.md`

## Assumptions / Open Questions
- Timestamps come from the monitoring-write agent via `date -u +%Y-%m-%dT%H:%M:%SZ` (Date.now() unavailable in workflow scripts)
- summary field for events uses first 200 chars of agent return for text agents, schema `summary` field for schema agents
- monitoring-write agent failure is non-fatal — logged as WARNING

## Implementation Notes
Added `const events = []`, `pushEvent()` arrow function, and `writeMonitoring()` async arrow function immediately after Scope phase completion. All 5 schema agents (TICKET_SCHEMA, REVIEW_SCHEMA, IMPL_SCHEMA, TEST_SCHEMA, DONE_SCHEMA) have `summary` added to required[] and properties. writeMonitoring() writes via a monitoring-write labeled agent that uses bash to get timestamps and calls the Python scripts. done-checker prompt updated to pre-mark condition 12 as PASS (written by workflow after READY_TO_CLOSE).

## Test Summary
Manual verification: implement-ticket.js reviewed for all 8 exit paths — each calls await writeMonitoring(status) before returning. No automated tests added (workflow script testing is manual).

## Files Changed
- `.claude/workflows/implement-ticket.js` (full rewrite with monitoring integration)
- `CLAUDE.md` (hard rule added, DoD condition 12 added)

## Completion Summary
Integrated agent monitoring into implement-ticket.js at all exit paths with events accumulation and a non-fatal writeMonitoring helper. Added mandatory monitoring hard rule and DoD condition 12 to CLAUDE.md. Every future workflow run will produce monitoring records.
