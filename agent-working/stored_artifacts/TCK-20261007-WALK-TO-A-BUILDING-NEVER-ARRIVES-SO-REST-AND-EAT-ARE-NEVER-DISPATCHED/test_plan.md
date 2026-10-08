---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261007-WALK-TO-A-BUILDING-NEVER-ARRIVES-SO-REST-AND-EAT-ARE-NEVER-DISPATCHED
artifact_type: test_plan
tags: [combat, bug]
---

# Test plan

New: `tests/unit/movement/test_arrival_beside_unenterable_target.py`. Existing, rerun: `tests/unit/movement`, the CI jobs' directory lists, `tests/integration/campaigns`. Gates: code-health ratchet, parity-ledger schema, mypy baseline, frontmatter and registry clean-export check.

## Proof Plan
- **Level**: unit (the movement ladder and the tactical dispatch) and corpus (before and after).
- **Proof kind**: regression test with a disabling control (neutralising the arrival check fails three tests and shows the jitter); before and after measurement on one tree.
- **Oracle source**: world rule MOV-07 (adjacency is orthogonal) and #385's completion guard (arriving within reach ends the walk); the stated purpose of the tactical building branch (dispatch the service when within reach).
- **Expected effect**: a walker beside an unenterable building tile stops; the tactical pass dispatches `REST` or `EAT` within one brain cadence; no other walks change.
- **Selected commands**: `pytest tests/unit/movement tests/unit/strategic tests/unit/engine`; the CI directory lists; `pytest tests/integration/campaigns`; `measure_arrival.py` before and after; `arrival_corpus.py` over the 24 worlds.
