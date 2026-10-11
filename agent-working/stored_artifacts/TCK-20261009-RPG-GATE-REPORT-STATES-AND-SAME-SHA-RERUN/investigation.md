---
status: historical
layer: testing
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261009-RPG-GATE-REPORT-STATES-AND-SAME-SHA-RERUN
phase: done
date: 2026-10-11
tags: [testing, regression, simulation-quality]
---

# Investigation
The ticket leaves open: pooled outcome comparison, a missing floor, paired-seed minimum, partial seed sets, and whether stale/no-data are red. Choices are recorded in the ticket's Implementation Notes and sent to rpg-planner. Registry calls without a state would let a drift entry own a fail, so they now raise.
