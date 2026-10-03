---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260920-MECHANISM-COMPLETENESS-CHECK-SCOPE-GAP
artifact_type: test_plan
tags: [architecture]
---

# Test Plan

## Proof Plan
| AC | level | proof kind | oracle source | expected effect | selected commands |
|---|---|---|---|---|---|
| 1 | unit | regression | ticket Scope 1 (no AC in the ticket) | the wider tier is a repeatable, deterministic check | `pytest tests/unit/tools/test_mechanism_registry_completeness_check.py` |
| 2 | unit | architecture guard | ticket Scope 2 | any new wired candidate fails until dispositioned | same |
| 3 | unit | regression | registry invariants | 104 mechanisms validate; caller-check findings pinned; atlas/capabilities/views agree | `pytest tests/unit/tools -k "mechanism or registry"` |

## Scoped Pytest Commands
`.venv/bin/python -m pytest tests/unit/tools -q`
