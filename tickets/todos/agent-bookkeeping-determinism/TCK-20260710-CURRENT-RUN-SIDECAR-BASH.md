---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260710-CURRENT-RUN-SIDECAR-BASH
phase: open
date: 2026-07-10
tags: []
---

# TCK-20260710-CURRENT-RUN-SIDECAR-BASH

## Title
Move .claude/current_run sidecar registration from agent-prompt text to orchestrator-side bash()

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Today, the orchestrator embeds a free-text "Step 0b" instruction in every agent-call prompt telling the agent to write {"run_id": ..., "seq": N} to .claude/current_run as its literal first action — this is how tool_call_count/cost_proxy_score get attributed to an agent event in tools.jsonl. This was reproduced live in the same session: when the Step 0b instruction was omitted from 5 agent prompts during a manual run, tool_call_count/cost_proxy_score returned completely empty with no error. The fix, as proposed in `docs/plans/agent_infrastructure/idea_agent_bookkeeping_determinism.md`: the orchestrator should write the .claude/current_run sidecar itself via bash() immediately before each agent() invocation, mirroring the existing p0ScanOutput / Architecture-Verify static pre-check pattern already used in the same file — so correctness no longer depends on an LLM correctly reproducing a copy-pasted bash snippet.

## Scope
- Replace every Step 0b sidecar-write prompt-text instruction in .claude/workflows/implement-ticket.js (~12 confirmed call sites) with an orchestrator-side bash() call that writes .claude/current_run immediately before the paired agent() call, using run_id and events.length + 1 (seq) that the orchestrator already has in scope at that point.
- Follow the file's existing individually-quoted-argv convention (implement-ticket.js:757-763) — never JSON-embed in python3 -c strings.
- Explicitly resolve (not silently skip) whether implement-epic.js and create-tickets.js receive the same fix in this ticket or whether that is deferred with documented rationale (create-tickets.js currently has zero sidecar registration at all — a pre-existing null tool_call_count gap, separate from but related to this fix).
- Update docs/agent-monitoring/schema.md's sidecar-attribution section to describe the new orchestrator-side mechanism instead of the agent-self-report mechanism.

## Out of Scope
- C2 (per-phase Step 0 ts date -u capture) — separate ticket TCK-20260710-STEP0-TS-ORCHESTRATOR-BASH, same class of anti-pattern, different field.
- C3 (verified_by provenance enforcement for mechanics-auditor and other gates) — separate ticket TCK-20260710-MECHANICS-AUDITOR-ENFORCEMENT, different mechanism entirely.
- The 4 "related, smaller ideas" from docs/plans/agent_infrastructure/idea_agent_bookkeeping_determinism.md: (1) asymmetric gate coverage beyond the security tag, (2) cross-retro trend detection in generate_retro.py, (3) duplicated tag-to-skill mapping logic consolidation, (4) working_log.csv malformed-row normalization backfill.
- Any change to record_events.py's REQUIRED-field validation logic itself (out of scope — only the caller-side computation reliability is in scope).

## Acceptance Criteria
- [ ] Every agent() call site in implement-ticket.js with a Step 0b instruction has it replaced by an orchestrator-side bash() call issued immediately before the paired agent() call.
- [ ] Running implement-ticket.js end-to-end with Step 0b prompt text fully absent still produces non-empty tool_call_count/cost_proxy_score in events.jsonl.
- [ ] implement-epic.js and create-tickets.js either gain the same fix, or the ticket explicitly documents deferring it with rationale (including the create-tickets.js null tool_call_count gap).
- [ ] docs/agent-monitoring/schema.md's sidecar-attribution section is updated for doc/code parity with the new orchestrator-side mechanism.

## Related Tickets
- TCK-20260710-AGENT-BOOKKEEPING-DETERMINISM-EPIC
- TCK-20260709-AGENT-MONITORING-DURATION
- TCK-20260706-SCOPE-TAG-REGISTRY-CHECK
- TCK-20260706-MONITORING-REASON-CODE
- TCK-20260708-DATA-RUNS-CLEANUP-TIMING
- TCK-20260708-AGENT-MONITORING-SCHEMA-ENFORCEMENT
- TCK-20260710-STEP0-TS-ORCHESTRATOR-BASH (sibling — shared Step 0/0b file overlap)
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
- tools/agent-monitoring/post_tool_hook.py
- docs/agent-monitoring/schema.md

## Assumptions / Open Questions
- Assumes seq attribution (events.length + 1) can be safely computed by bash() timing relative to the events array mutation without drift — needs confirmation at investigation/plan time, not assumed here.
- Assumes implement-epic.js and create-tickets.js scope boundary can be decided within this ticket rather than requiring a separate follow-up ticket — open question to resolve during Scope phase.
- Coordination risk: shares Step 0/0b blocks in the same 3 files with C2 (TCK-20260710-STEP0-TS-ORCHESTRATOR-BASH) — recommend sequencing this ticket first (higher priority) or careful diff coordination if implemented concurrently.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
