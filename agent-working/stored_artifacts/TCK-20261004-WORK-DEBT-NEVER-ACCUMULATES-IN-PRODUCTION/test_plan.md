---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261004-WORK-DEBT-NEVER-ACCUMULATES-IN-PRODUCTION
date: 2026-10-04
tags: [performance, determinism, testing]
---

# Test plan: TCK-20261004-WORK-DEBT-NEVER-ACCUMULATES-IN-PRODUCTION

| AC | Test | Proof |
|---|---|---|
| 1 | `test_work_debt_stays_empty_while_work_is_dropped[<scenario>]` for idle, movement, resource, strategic | `status.total_dropped_work > 0` (the run really shed work) and `state.work_debt == {}` after every tick |
| 1 | same test | the governor signal `work_debt_total` is 0 every tick, so every debt-derived branch is constant |
| 1 | control test | the same instrument sees debt when it is seeded (`inject_work_debt`), so an empty result is not a blind spot |
| 2 | reader inventory in the ticket | every `src/` reference classified |
| 3 | recommendation in the ticket | evidence from history, docs and the test |
