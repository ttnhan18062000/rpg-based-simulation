---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260930-SKILL-PATH-MONITORING-NULL-TS-AND-VERDICT-STRICTNESS
artifact_type: test_plan
tags: [ai]
---

# Test Plan

## Proof Plan
| AC | level | proof kind | oracle source | expected effect | selected commands |
|---|---|---|---|---|---|
| 1 | prose | n/a | ticket AC1 | both decisions recorded with reasoning | (read) |
| 2 | unit | regression | ticket AC2 (the quoted failing input) | strict without the flag; fills only missing ts with it; no rescue of other fields | `pytest tests/tools/test_record_events.py` |
| 3 | prose | n/a | ticket AC3 | no gate loosened | (read) |

## Scoped Pytest Commands
`.venv/bin/python -m pytest tests/tools/test_record_events.py -q`
