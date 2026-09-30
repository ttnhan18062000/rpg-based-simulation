---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260930-TEST-PLAN-PROOF-FIELDS-AND-TRIAGE-PROCEDURE
artifact_type: plan
tags: [testing]
---

# Plan

1. `regression_policy.md` §13 (evidence record, 8 classes, prohibitions, defects to feature team); one pending-decision pointer under §6; `delivery_process.md` CI triage step 3 links to §13. Appended as §13 so existing §-references do not renumber.
2. `investigator.md`: `## Proof Plan` section in `test_plan.md`; reads the epic's shared-fixture note.
3. `architecture-reviewer.md`: advisory diff-scoped checklist under Architecture-Verify; verdict vocabulary untouched.
4. `implement-epic.js`: one line in the request-mode epic-creation prompt seeds the subsection.
5. `tests/tools/test_test_workflow_agent_prose.py` pins all of the above.

Removed at review: a done-checker WARN and static presence function (enforcement is new gate tooling, not in the epic).
Not touched: CLAUDE.md, settings.json, ticket-scoper.md, §6's rule, any oracle-review step.
