---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260930-CORE-RPG-PILOT-NODE-CHARGE-ACCOUNTING
artifact_type: test_plan
tags: [testing]
---

# Test Plan

## Regression Surface
Impact report (`pilot/outputs/cap1_impact_d1_actual_paths.md`): `tests/integration/content/test_resource_region_coverage_corpus.py`, `tests/tools/test_done_checker_static.py`, `tests/tools/test_parity_index_baseline.py`. Also run: `tests/integration/pipeline/test_transaction_completion.py`, `tests/unit/resource/test_durability_repair.py`, `tests/unit/economy/test_gold_sink.py`, `tests/unit/resource/test_resource_contract.py`.

## New Tests Required
`tests/unit/resource/test_node_charge_accounting.py` (4), `tests/integration/kernel/test_node_charge_cross_actor.py` (1).

## Proof Plan
| AC | level | proof kind | oracle source | expected effect | selected commands |
|---|---|---|---|---|---|
| regular node harvest | unit | invariant | ch03 §3 Node Charges; parity `TOWN-122` (nearest entry) | `charges_delta == -1`, one item yielded | `pytest tests/unit/resource/test_node_charge_accounting.py` |
| loot node harvest | unit | invariant | ch03 §3 Node Charges; `TOWN-122` | `charges_delta == -remaining_charges` | same |
| reserved last charge, same tick | unit | invariant | ch03 §1, §3; `TOWN-122` | `SOURCE_DEPLETED`, no update emitted | same |
| two actors, one last charge | kernel_integration | invariant | ch03 §1, §3; `TOWN-122` | exactly one yield, node delta -1 | `pytest tests/integration/kernel/test_node_charge_cross_actor.py` |

Optional: negative cases are the two depleted-source tests; fixtures are `tests/helpers/{entities,resources}.py`; non-functional risk: none.

## Scoped Pytest Commands
`.venv/bin/python -m pytest tests/unit/resource/test_node_charge_accounting.py tests/integration/kernel/test_node_charge_cross_actor.py tests/integration/pipeline/test_transaction_completion.py tests/unit/resource/test_durability_repair.py tests/unit/economy/test_gold_sink.py tests/unit/resource/test_resource_contract.py -q` (54 passed). Manual scenario lane: `pytest tests/mechanic_scenarios -m "not slow and not extra_slow"` (53 passed).

## Anti-Drift Test Guards
The drill fault (`pilot/inputs/cap5_injected_fault.diff`) must fail 2 of the 5 new tests.
