---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260808-AGENT-MONITORING-CLAUDE-VOCAB-REGISTRATION
phase: open
date: 2026-08-08
tags: [agent-monitoring, observability]
---

# TCK-20260808-AGENT-MONITORING-CLAUDE-VOCAB-REGISTRATION

## Title
`record_events.py`'s vocabulary-drift check does not recognize `"claude"` as a known agent
literal for the `implement-ticket` workflow, causing a spurious "unrecognized agent" warning on
every hand-orchestrated phase event

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
`tools/agent-monitoring/vocabulary.py`'s `WORKFLOW_AGENTS["implement-ticket"]` set is documented
as derived strictly by grepping `.claude/workflows/implement-ticket.js`'s own real
`pushEvent(...)`/subagent-dispatch call sites — but it already includes legitimate non-subagent
"orchestrator pseudo-agent" literals (`"implement-ticket-orchestrator"`) for cases where the
orchestrator logs an event with no delegated subagent. `"claude"` is the real, established literal
used when a session hand-orchestrates `implement-ticket.js` directly (no subagent dispatch —
e.g. after the subagent spawn cap is reached, a real, recurring, sanctioned mode this session used
throughout) — but it was never added to this set, so every such event triggers a harmless but
noisy `WARNING: unrecognized agent 'claude' for workflow 'implement-ticket'` on `record_events.py`
(confirmed non-blocking — warn-only, does not affect `cost_proxy_score`, which is driven by the
separate `agent-monitoring-index` rebuild, not this check — found and disclosed during this
session's own agent-monitoring retro review).

## Scope
1. **Investigate** (should be quick, hotfix tier): confirm `"claude"` is the only real
   hand-orchestration literal in current use (grep `agent-monitoring/events.jsonl` for other
   non-standard agent values that aren't drift/typos, to avoid registering `"claude"` while
   missing a sibling case).
2. **Implement**: add `"claude"` to `WORKFLOW_AGENTS["implement-ticket"]`, with a comment
   explaining it's a hand-orchestration literal (same category as the existing
   `"implement-ticket-orchestrator"` pseudo-agent, not a real `.claude/agents/*.md` subagent) —
   matching this file's own existing precedent and disclosure style, not silently added.

## Out of Scope
- Any change to `cost_proxy_score` computation itself, or the `agent-monitoring-index` rebuild
  cadence — this ticket is purely about the warning's own vocabulary set.
- Adding `"claude"` to other workflows' `WORKFLOW_AGENTS` sets unless Investigate finds real
  evidence it's used there too.

## Acceptance Criteria
- [ ] `WORKFLOW_AGENTS["implement-ticket"]` includes `"claude"`, with a real, evidenced rationale
      comment
- [ ] Re-running `record_events.py` with `agent="claude"` no longer prints the warning
- [ ] Scoped pytest passes (`tests/tools/test_validate_agent_monitoring.py` and any
      vocabulary-specific tests)

## Related Tickets
- None directly — found and disclosed during this session's own agent-monitoring retro review
  (`agent-monitoring/retro/RETRO-2026-W32.md`).

## Related Docs
- None requiring update — this is a code-only vocabulary-set fix, no behavior/contract change.

## Related Stored Artifacts
None yet.

## Related Code Areas
- `tools/agent-monitoring/vocabulary.py` (`WORKFLOW_AGENTS["implement-ticket"]`)
- `tools/agent-monitoring/record_events.py` (`warn_vocabulary_drift`, the call site that prints
  the warning)

## Assumptions / Open Questions
- Whether other hand-orchestration sessions used a different literal (e.g. a specific model name)
  instead of `"claude"` — not assumed; Investigate should grep real `events.jsonl` data before
  concluding `"claude"` is the only case needing registration.

## Implementation Notes
(To be filled during implementation.)

## Test Summary
(To be filled during implementation.)

## Files Changed
(To be filled during implementation.)

## Completion Summary
(To be filled during implementation.)
