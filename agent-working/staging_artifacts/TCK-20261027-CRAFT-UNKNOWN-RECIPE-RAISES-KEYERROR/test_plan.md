---
status: active
layer: economy
authority: P2
audience: agent
ticket_id: TCK-20261027-CRAFT-UNKNOWN-RECIPE-RAISES-KEYERROR
artifact_type: test_plan
tags: [economy, bug]
---

# Test plan

- New: unknown id in payload, unknown id via `opp_craft_`, no id. Each asserts no exception, no inventory or gold change, no resource transfer, and a `FAILED_REQUIREMENTS: unknown_recipe` trace.
- Existing six tests in `test_crafting_live_path.py` stay green.
- `pytest tests/unit/engine tests/integration/economy -m "not slow"`; ruff and lint-imports on changed files.
- Parity-ledger, registry and `tests/unit/tools` runs serially under `MemoryMax=3G`.
- Neutral paired proof, 1000t, 3 worlds, seed 42.
