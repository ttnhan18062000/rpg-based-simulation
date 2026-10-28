---
status: active
layer: economy
authority: P2
audience: agent
ticket_id: TCK-20261027-LEGACY-RECIPE-REGISTRY-AND-BLACKSMITH-ACTION-UNREACHED
artifact_type: plan
tags: [economy]
---

# Plan

Source: `rpg_planner_plan_and_ruling_2026-10-28.md` (plan by rpg-planner-ubuntu, ruling by rpg-planner u24 relayed via lead-planner-u24 and lead-planner; owner's go on #715 6473373689 and 6473439661). Followed as written.

1. Delete `src/core/recipes.py` and `src/town/blacksmith.py`.
2. Delete `test_blacksmith_crafting`; every assertion is mapped in investigation.md; the one not directly covered (a second craft refused after the first) is moved onto the live REQUEST_CRAFT path as a new test.
3. Remove the legacy `RecipeRegistry` row from the same-name guard.
4. Run the completeness check: no pin may move.
5. Record the two inventory rows 123 and 182 as deleted (see investigation.md for how that file records deletions).
6. Write text (i) in `resource_conservation_contract.md` and text (ii) in PROG-123 verbatim, (ii) through `parity_ledger_writer.py`.
