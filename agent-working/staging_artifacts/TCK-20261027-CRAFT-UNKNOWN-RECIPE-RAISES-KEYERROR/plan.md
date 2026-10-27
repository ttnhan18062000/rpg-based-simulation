---
status: active
layer: economy
authority: P2
audience: agent
ticket_id: TCK-20261027-CRAFT-UNKNOWN-RECIPE-RAISES-KEYERROR
artifact_type: plan
tags: [economy, bug]
---

# Plan

1. `src/engine/intent/action_intent.py`, REQUEST_CRAFT requirement block: when the recipe id is missing or not in `RecipeRegistry`, append an `IntentTrace` with `execution_result="FAILED_REQUIREMENTS: unknown_recipe"` and return `{entity.id: EntityUpdate(entity_id=entity.id, readiness_delta=0.0)}`, the same shape as BUY_ITEM's `shop_unavailable`. `RecipeRegistry.get` is then only reached for ids the registry contains.
2. Three tests in `tests/integration/economy/test_crafting_live_path.py`: unknown id in `payload["recipe_id"]`, unknown id as `target_id="opp_craft_<unknown>"`, no id at all.
3. PROG-097 to `verified` via `tools/parity_ledger_writer.py`; checklist line and `resource_conservation_contract.md` match.
4. Reword the `src/ai/goals/scorers.py:316` docstring (comment only).
5. Proof: `paired --neutral`, 3 worlds, 1000t, same as #760. Not IDENTICAL means stop and report.
