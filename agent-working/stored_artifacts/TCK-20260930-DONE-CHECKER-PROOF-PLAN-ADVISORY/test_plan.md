---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260930-DONE-CHECKER-PROOF-PLAN-ADVISORY
artifact_type: test_plan
tags: [testing]
---

# Test Plan

## Proof Plan
| AC | level | proof kind | oracle source | expected effect | selected commands |
|---|---|---|---|---|---|
| 1 | unit | regression | ticket AC1 | each missing mandatory field named, per criterion | `pytest tests/tools/test_proof_plan_advisory.py` |
| 2 | unit | regression | ticket AC2 | complete plan OK; hotfix/epic NA; one-line declaration OK | same |
| 3 | unit | architecture guard | ticket AC3 | precheck list unchanged, exit code 0, unreadable plan degrades to WARN | same + `tests/tools/test_done_checker_static.py` |
| 4 | unit | regression | ticket AC4 | both layouts, `oracle: unresolved`, read-only | same |
| 5 | unit | architecture guard | ticket AC5 | field list equals investigator.md's mandatory list | same |

## Scoped Pytest Commands
`.venv/bin/python -m pytest tests/tools/test_proof_plan_advisory.py tests/tools/test_done_checker_static.py -q`
