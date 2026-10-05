---
status: historical
layer: ai
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261004-SUBAGENT-STOP-GUARD-COUNTS-PARENT-SESSION-SUBSCRIPTIONS
date: 2026-10-05
tags: [ai, hooks, process-improvement]
---

# Investigation: TCK-20261004-SUBAGENT-STOP-GUARD-COUNTS-PARENT-SESSION-SUBSCRIPTIONS

Report from rpg-feature-planning: a planner subagent was blocked twice by the SubagentStop guard on the parent's artifact subscriptions. The hook reads `background_tasks` unfiltered by design. A live capture (see the ticket) showed the subscription as a `monitor` task with an "(auto-armed on publish)" description and the subagent's own entry among the tasks, so both can be excluded by shape, for SubagentStop only.
