---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260809-COMBAT-PURSUIT-NEVER-CLOSES-TO-MELEE-RANGE
artifact_type: test_plan
tags: [combat, simulation-quality]
---

# Test Plan — TCK-20260809-COMBAT-PURSUIT-NEVER-CLOSES-TO-MELEE-RANGE

No production code changed by this ticket (investigation-and-recommendation only, per plan.md).
No new tests added. Verification consists of:
1. `python3 tools/validate_frontmatter.py` on the ticket and all 3 staging artifacts.
2. No scoped pytest run required — `git status` confirms zero `src/`/`tests/` changes.

The follow-up ticket (`TCK-20260809-COMBAT-PURSUIT-PER-TICK-TRACE`) will carry its own real test
plan once its own investigation produces a confirmed, fixable root cause.
