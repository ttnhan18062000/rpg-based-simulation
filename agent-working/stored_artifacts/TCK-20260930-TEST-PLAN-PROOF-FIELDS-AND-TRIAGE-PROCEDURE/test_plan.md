---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260930-TEST-PLAN-PROOF-FIELDS-AND-TRIAGE-PROCEDURE
artifact_type: test_plan
tags: [testing]
---

# Test Plan

## Regression Surface
`tests/tools/test_wave1_agent_tools_frontmatter.py`, `tests/tools/test_delivery_ci_triage_classifier.py`, `tests/tools/test_skill_investigate_search_before_grep.py`.

## New Tests Required
`tests/tools/test_test_workflow_agent_prose.py` (8 text-level tests).

## Proof Plan
| AC | level | proof kind | oracle source | expected effect | selected commands |
|---|---|---|---|---|---|
| 1 | unit | architecture guard | roadmap §4.4; ledger n/a (process doc) | investigator lists mandatory + optional fields, oracle only cites | `pytest tests/tools/test_test_workflow_agent_prose.py` |
| 2 | unit | architecture guard | roadmap §4.4, principle 8 | checklist advisory, verdict vocabulary unchanged | same |
| 4 | unit | architecture guard | roadmap §4.5 | §13 has all classes; delivery_process links; §6 rule unchanged | same |

## Scoped Pytest Commands
`.venv/bin/python -m pytest tests/tools/test_test_workflow_agent_prose.py tests/tools/test_wave1_agent_tools_frontmatter.py tests/tools/test_delivery_ci_triage_classifier.py tests/tools/test_skill_investigate_search_before_grep.py -q`

## Anti-Drift Test Guards
`test_regression_policy_quarantine_row_unchanged_with_pending_pointer`, `test_architecture_reviewer_verdict_vocabulary_unchanged`.
