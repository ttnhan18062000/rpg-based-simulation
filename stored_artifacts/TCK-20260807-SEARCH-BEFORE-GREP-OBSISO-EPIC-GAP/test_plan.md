---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260807-SEARCH-BEFORE-GREP-OBSISO-EPIC-GAP
artifact_type: test_plan
tags: [agent-monitoring, process-improvement]
---

# Test Plan — TCK-20260807-SEARCH-BEFORE-GREP-OBSISO-EPIC-GAP

This is a single agent-definition prompt-text change (`.claude/agents/investigator.md`) — no
Python code changes, so no new/updated pytest coverage is expected or warranted.

## Verification

1. Direct read confirming the new instruction is present, unambiguous, and placed where an
   investigator would actually see it (top of `## Inputs`, before the file-reading instructions
   it must precede).
2. `pytest tests/tools/test_workflow_meta_conformance.py -q` — confirms this edit doesn't disturb
   the existing skill/agent-doc conformance checks (regression guard only; this ticket doesn't
   touch phase names or workflow structure).
3. No real-kernel verification possible for a prompt-text change (would require dispatching a real
   investigator agent, which this session cannot do — subagent spawn cap reached). The fix's real
   effectiveness can only be confirmed in a future session's own real Investigate-phase runs.
