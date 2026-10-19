---
status: active
layer: testing
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261019-CI-RUNTIME-EPIC
phase: open
date: 2026-10-19
tags: [testing, workflows, performance]
---

# Test plan

## Proof Plan
| criterion | level | proof kind | oracle source | expected effect | selected commands |
|---|---|---|---|---|---|
| AC2 PR wait ≤ 6 min | CI measurement | 7-day window after child 1, same method as investigation.md | the epic's baseline | median successful-PR wall time ≤ 6 min, or the shortfall recorded | the investigation.md method (gh api runs + jobs) |
| AC3 no coverage lost | static + CI | per-job collect-only counts before and after (child 1); push-lane guard test (child 3) | test.yml as of 94ff6b0bc | counts equal; every non-informational lane runs on push | `pytest --collect-only -q` per job; `pytest tests/static -k push` |
| AC4 lead reviews | review | PR comment links | user ask 2026-10-19 | one lead-planner-u24 comment per child PR; lead-planner (ubuntu) on child 3 | n/a |
