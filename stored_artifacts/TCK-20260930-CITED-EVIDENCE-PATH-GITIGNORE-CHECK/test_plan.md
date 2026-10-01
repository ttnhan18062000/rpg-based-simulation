---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260930-CITED-EVIDENCE-PATH-GITIGNORE-CHECK
artifact_type: test_plan
tags: [ai]
---

# Test Plan

## Proof Plan
| AC | level | proof kind | oracle source | expected effect | selected commands |
|---|---|---|---|---|---|
| 1 | unit | regression | ticket AC1; `.gitignore:239` rule text | WARN names the ignored `.json` path and the rule | `pytest tests/tools/test_cited_evidence_advisory.py` |
| 2 | unit | regression | ticket AC2 | all-tracked paths yield OK, no WARN | `pytest tests/tools/test_cited_evidence_advisory.py` |
| 3 | unit | invariant | ticket AC3 | advisory is absent from precheck/finalize and cannot change exit code | `pytest tests/tools/test_cited_evidence_advisory.py tests/tools/test_done_checker_static.py` |

## Scoped Pytest Commands
`pytest tests/tools/test_cited_evidence_advisory.py tests/tools/test_proof_plan_advisory.py tests/tools/test_done_checker_static.py tests/tools/test_skill_usage_metric.py`
