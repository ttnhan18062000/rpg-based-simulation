---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260930-IMPLEMENT-EPIC-NATIVE-WORKFLOW-PORT
artifact_type: test_plan
tags: [ai]
---

# Test Plan

## Proof Plan
| AC | level | proof kind | oracle source | expected effect | selected commands |
|---|---|---|---|---|---|
| 1 | unit | regression | ticket AC1 | parses under the runtime's acorn options | `pytest tests/tools/test_implement_epic_native_port.py tests/tools/test_workflow_runtime_acorn_parse.py` |
| 2 | unit | architecture guard | ticket AC2 | no bash call sites, no Date.now/Math.random/argless new Date in code | same |
| 3 | unit | regression | ticket AC3 | existing implement-epic pins updated, not deleted; fail-open paths pinned | `pytest tests/tools -k "epic or step0 or execution_mode or summary_truncation"` |
| 4 | unit | regression | ticket AC4 | missing start_ts returns structured INVALID_ARGS before any work | test_implement_epic_native_port.py |
| 5 | measurement | probe | ticket AC5 | nested workflow() answered by measurement | `runtime_probe/` in the classification ticket's artifact |
| 6 | measurement | native run | ticket AC6 | one real native run, attribution of epic rows checked | run `wf_18d6fbaa-844` (see investigation.md) |

## Scoped Pytest Commands
`.venv/bin/python -m pytest tests/tools/test_implement_epic_native_port.py tests/tools/test_record_events.py tests/tools/test_workflow_runtime_acorn_parse.py -q`
