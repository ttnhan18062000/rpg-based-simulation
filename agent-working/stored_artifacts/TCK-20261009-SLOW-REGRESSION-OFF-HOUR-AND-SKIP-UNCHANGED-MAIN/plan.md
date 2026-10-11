---
status: historical
layer: testing
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261009-SLOW-REGRESSION-OFF-HOUR-AND-SKIP-UNCHANGED-MAIN
phase: done
date: 2026-10-11
tags: [testing]
---

# Plan
Scope 1 moved the cron off the busy hour. Scope 2 added `slow_regression_gate.py`, the `gate` job in `slow-regression.yml`, and the same rule in the watchdog. Details and decisions are in the ticket's Implementation Notes (written when each scope was built).
