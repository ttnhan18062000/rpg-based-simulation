---
status: historical
layer: ai
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261004-SUBAGENT-STOP-GUARD-COUNTS-PARENT-SESSION-SUBSCRIPTIONS
date: 2026-10-05
tags: [ai, hooks, process-improvement]
---

# Test Plan: TCK-20261004-SUBAGENT-STOP-GUARD-COUNTS-PARENT-SESSION-SUBSCRIPTIONS

Existing guard tests stay green. New tests per the ticket's Test Summary.

## Proof Plan

- Level: unit (subprocess drive of the hook script).
- Proof kind: executable tests against a real captured payload.
- Oracle source: the ticket's acceptance criteria and the captured payload.
- Expected effect: `pytest tests/tools/test_subagent_stop_background_guard.py` passes; the captured payload exits 0, each blocking variant exits 2.
- Selected commands: `pytest tests/tools/test_subagent_stop_background_guard.py`.
