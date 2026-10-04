---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261004-REVIEW-RUBRIC
artifact_type: plan
tags: [architecture, planning]
---

# Plan — TCK-20261004-REVIEW-RUBRIC

Docs-only ticket; the planner exempted it from the plan.md round trip, so this file was written at closure from what was done.
- Add Section 11 "Review rubric" to `docs/guidelines/python_code_standard.md` (old Section 11 "Related" becomes 12; no inbound references to the number): one table (Important, Nit, Pre-existing) and 5 bullets.
- Pin it in `tests/codebase/test_review_rubric.py`: the three categories, the sentence "Only Important blocks.", the correctness-bug clause, the length limit.
- Review fix applied: bullet 2 lets a correctness bug be Important by naming its concrete failure, so a plain bug is not downgraded to a Nit.
- Scope guards: no reviewer agent prompt edited; no examples in the rubric (they live in the `code-craft` skill); no src/ diff.
