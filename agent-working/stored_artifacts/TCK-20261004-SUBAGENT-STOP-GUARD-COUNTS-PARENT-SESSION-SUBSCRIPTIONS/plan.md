---
status: historical
layer: ai
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261004-SUBAGENT-STOP-GUARD-COUNTS-PARENT-SESSION-SUBSCRIPTIONS
date: 2026-10-05
tags: [ai, hooks, process-improvement]
---

# Plan: TCK-20261004-SUBAGENT-STOP-GUARD-COUNTS-PARENT-SESSION-SUBSCRIPTIONS

Filter two shapes in `subagent_stop_background_guard.py` for `SubagentStop` only; freeze the captured payload as a `.jsonl` fixture; add tests for the allow case and three block cases (own shell task, another monitor, main-session Stop).
Scope guard: no weakening for shell, monitor or workflow tasks; no CLAUDE.md edit; no silencing workaround.
