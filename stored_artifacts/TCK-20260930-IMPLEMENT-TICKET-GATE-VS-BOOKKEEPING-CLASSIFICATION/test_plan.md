---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260930-IMPLEMENT-TICKET-GATE-VS-BOOKKEEPING-CLASSIFICATION
artifact_type: test_plan
tags: [ai]
---

# Test Plan

## Proof Plan
| AC | level | proof kind | oracle source | expected effect | selected commands |
|---|---|---|---|---|---|
| 1 | unit | architecture guard | ticket AC1 | table rows == real call sites; grep over-count not used | `pytest tests/tools/test_implement_ticket_bash_site_classification.py` |
| 2 | unit | architecture guard | ticket AC2 | every row has class, route, risk; gate rows route attested with a real risk | same |
| 3 | measurement | probe | ticket AC3 | no non-agent shell path; evidence in `runtime_probe/` | (workflow probe, stored output) |
| 4 | prose | n/a | ticket AC4 | follow-up tickets filed | (read) |

## Scoped Pytest Commands
`.venv/bin/python -m pytest tests/tools/test_implement_ticket_bash_site_classification.py -q`
