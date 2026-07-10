---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260710-STEP0-TS-ORCHESTRATOR-BASH
phase: open
date: 2026-07-10
tags: []
---

# TCK-20260710-STEP0-TS-ORCHESTRATOR-BASH

## Title
Move per-phase ts capture (agent-prompt Step 0 date -u) to orchestrator-side bash()

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Each agent prompt's "Step 0" asks the agent to run `date -u` and echo it back as the first line of its response, rather than the orchestrator capturing the timestamp itself, for the `events.jsonl` `ts` field. This is the same class of problem as the tool_call_count/cost_proxy_score sidecar issue, but lower risk today because `ts` is used for display/ordering only — `generate_retro.py`'s Slow Runs and Avg Duration sections read `runs.jsonl`'s `duration_s`, not per-event `ts`. This ticket implements the fix proposed in `docs/plans/agent_infrastructure/idea_agent_bookkeeping_determinism.md`: replace the `date -u` Step 0 prompt-text instruction with an orchestrator-side `bash()` capture, wired directly into `pushEvent`/`start_ts`, following the same precedent already used elsewhere in these files.

## Scope
- Replace every "Step 0" `date -u` prompt-text block across `.claude/workflows/implement-ticket.js` (12 sites: lines 56, 91, 347, 390, 453, 524, 595, 658, 809, 903, 968, 1025), `.claude/workflows/implement-epic.js` (3 sites: lines 66, 99, 124), and `.claude/workflows/create-tickets.js` (1 site: line 157) with an orchestrator-side `bash()` call whose captured value is wired directly into `pushEvent`/`start_ts`.
- Confirm (do not silently assume) the idea doc's open question — whether any Step 0 instance genuinely needs the agent's own wall-clock moment rather than the orchestrator's dispatch moment — is answered "no" for this narrow scope.
- Ensure `record_events.py`'s `ts` REQUIRED (non-nullable) check continues to pass unchanged.

## Out of Scope
- C1 (tool_call_count/cost_proxy_score sidecar registration) — separate ticket TCK-20260710-CURRENT-RUN-SIDECAR-BASH, higher priority, same files.
- C3 (verified_by provenance enforcement) — separate ticket TCK-20260710-MECHANICS-AUDITOR-ENFORCEMENT, different mechanism.
- The 4 "related, smaller ideas" from `docs/plans/agent_infrastructure/idea_agent_bookkeeping_determinism.md`: (1) asymmetric gate coverage beyond the security tag, (2) cross-retro trend detection, (3) duplicated tag-to-skill mapping logic consolidation, (4) working_log.csv malformed-row normalization backfill.
- Building a JS test harness for the workflow files generally (pre-existing structural gap, not introduced or required to be closed by this ticket).
- Any change to `record_events.py`'s `ts` validation/REQUIRED-field logic itself.

## Acceptance Criteria
- [ ] Every `date -u` Step 0 site across all 3 workflow files (16 total sites) is replaced by an orchestrator `bash()` call, with the value wired directly into `pushEvent`/`start_ts`.
- [ ] `record_events.py`'s REQUIRED check for `ts` still passes after the change.
- [ ] A live run's `events.jsonl` `ts` values are monotonically non-decreasing in `seq` order regardless of whether agent prose includes any timestamp.
- [ ] `docs/agent-monitoring/schema.md`'s `ts` field description is updated to state the field is orchestrator-captured, not agent-self-reported.

## Related Tickets
- TCK-20260710-AGENT-BOOKKEEPING-DETERMINISM-EPIC
- TCK-20260709-AGENT-MONITORING-DURATION
- TCK-20260708-AGENT-COST-OBSERVABILITY
- TCK-20260710-CURRENT-RUN-SIDECAR-BASH (sibling — shared Step 0/0b file overlap)
- TCK-20260710-MECHANICS-AUDITOR-ENFORCEMENT (sibling)

## Related Docs
- docs/plans/agent_infrastructure/idea_agent_bookkeeping_determinism.md
- docs/agent-monitoring/schema.md

## Related Stored Artifacts
None.

## Related Code Areas
- .claude/workflows/implement-ticket.js
- .claude/workflows/implement-epic.js
- .claude/workflows/create-tickets.js
- tools/agent-monitoring/record_events.py
- tools/agent-monitoring/generate_retro.py
- docs/agent-monitoring/schema.md

## Assumptions / Open Questions
- Assumes the idea doc's own open question ("does any Step 0 need the agent's OWN wall-clock moment") is answered "no" for this scope — must be explicitly confirmed during investigation/planning, not silently assumed.
- No automated JS test harness exists for these workflow files at all; this is a pre-existing gap this ticket does not need to close, but test verification will rely on live-run inspection of events.jsonl rather than unit tests.
- Coordination risk: shares Step 0/0b blocks in the same 3 files with C1 (TCK-20260710-CURRENT-RUN-SIDECAR-BASH) — recommend sequencing after C1 or careful diff coordination if implemented concurrently.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
