---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260923-MECHANISM-IMPLEMENTED-BY-RESIDUE-RESOLUTION
artifact_type: test_plan
tags: [architecture]
---

# Test Plan

## Proof Plan
| AC | level | proof kind | oracle source | expected effect | selected commands |
|---|---|---|---|---|---|
| 1 | unit | regression | ticket AC1 | gap mechanisms reported separately, coverage over non-gap; doc states the rule | `pytest tests/unit/tools/test_mechanism_registry_completeness_check.py` |
| 2 | corpus_run | differential | ticket AC2; registry `verified` schema | each of the 5 has a disposition with a runtime-instrument `verified` block | `python3 stored_artifacts/.../runtime_probe/call_counter_named_methods.py` |
| 3 | unit | regression | ticket AC3 | dependency ticket closed with its own criteria met | (read) |
| 4 | unit | architecture guard | ticket AC4 | convergence tests, atlas/capabilities check, views regenerated, caller-check findings pinned | `pytest tests/unit/tools -k "mechanism or registry"` |

## Scoped Pytest Commands
`.venv/bin/python -m pytest tests/unit/tools -q`
