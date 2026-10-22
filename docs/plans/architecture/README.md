---
status: active
layer: architecture
authority: P2
audience: agent
tags: [ai, governance]
---

# Architecture plans

Proposals and reviews from the advisory `architecture` session domain (seat `architecture-planner-u24`, owner decision
2026-10-22, logged on issue #715). This directory holds proposals only. Recorded decisions stay where they are: ADRs in
`docs/architecture/**` belong to lead-planner, code goes to rpg-planner or perf-planner.

## Contents

| file | what |
|---|---|
| `engine_execution_modes_proposal.md` | Fix the serial waste first, then five labelled execution modes (certified, fast test, parallel-deterministic, live, relaxed/distributed), the ports they need and what each gives up (2026-10-22) |
| `faster_feature_testing_draft_tickets.md` | Draft tickets for the proposal's steps 1 and 2 (H2, H3, H4, T1 to T3), for the owning planners to file after v1 (2026-10-22) |
