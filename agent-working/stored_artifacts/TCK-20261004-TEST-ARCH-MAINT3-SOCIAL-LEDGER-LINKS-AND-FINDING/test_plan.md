---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261004-TEST-ARCH-MAINT3-SOCIAL-LEDGER-LINKS-AND-FINDING
artifact_type: test_plan
tags: [testing]
---

# Test Plan — TCK-20261004-TEST-ARCH-MAINT3-SOCIAL-LEDGER-LINKS-AND-FINDING

No test is added or changed. The change is ledger data and docs; the check is that the linked tests exist, pass and
assert the entry's claim, and that the ledger still validates.

## Proof Plan
| AC | level | proof kind | oracle source | expected effect | selected commands |
|---|---|---|---|---|---|
| linked tests pass | unit/arena | regression | the entry text in `docs/parity_ledger/social_narrative.yaml` | the 4 candidates pass; only matching ones linked | `pytest tests/arena/test_arena_stop_conditions.py::test_arena_stop_condition_wipe tests/arena/test_arena_stop_conditions.py::test_arena_stop_condition_timeout tests/unit/core/test_authoritative_state_contract.py::test_mutation_tripwire_during_decision tests/unit/core/test_p1_semantic_hardening.py::test_contract_outcome_consequences` |
| ledger stays valid | tool | regression | `docs/parity_ledger/schema.json` and `tools/parity_ledger_writer.py` | writer validates; diff is the two `test_path` lines | `pytest tests/tools/test_parity_ledger_writer.py tests/tools/test_parity_index.py` |
| counts reproducible | script | measurement | the committed YAML and `git grep` at the base SHA | same figures at two SHAs | scratch script, not committed |

## Scoped Pytest Commands

`pytest tests/tools/test_parity_ledger_writer.py tests/tools/test_parity_index.py` plus the four node ids above.
