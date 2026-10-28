---
status: active
layer: economy
authority: P2
audience: agent
ticket_id: TCK-20261027-LEGACY-RECIPE-REGISTRY-AND-BLACKSMITH-ACTION-UNREACHED
artifact_type: investigation
tags: [economy]
---

# Investigation

## Caller sweep (origin/main a6a01f808)
Import statements only (`git grep` over src, tools, tests): `src/core/recipes.py` is imported by `src/town/blacksmith.py`; `src/town/blacksmith.py` is imported by `tests/unit/world/test_economy_contract.py:8`. No conftest, plugin, `importlib` or `__import__` reaches either. Other `recipes.py` mentions are docstrings/comments (material_predicate.py:5/19/46 and four progression tests' docstrings); `test_material_possession_predicate.py:45` asserts the predicate docstring still names `src/core/recipes.py` as its former source, which stays true. `src/engine/blacksmith.py::BlacksmithSystem` is a different module and untouched.

## test_blacksmith_crafting: each assertion and where it is covered
Legacy (hand-built blacksmith building, legacy 3-entry recipe, `BlacksmithAction.craft`), applied through `refine` + `apply_generation`:
1. A craft update exists (`craft_upd is not None`) -> `tests/integration/economy/test_crafting_live_path.py::test_craft_consumes_materials_and_gold_and_adds_the_product_together` (one CRAFTING resource transfer).
2. Gold debited (100 -> 50) -> same test (`gold == 60`; the live recipe costs 40).
3. Materials removed and the product added (inventory is exactly one `iron_sword`) -> same test (`_held(after) == {"iron_sword": 1}`).
4. A second craft refused: in the legacy test the second craft was refused because the materials were gone, not gold -> `test_craft_needs_every_material` covers the gate, and the exact sequence (craft, then craft again) is MOVED onto the live path as `test_a_second_craft_is_refused_once_the_first_has_consumed_the_materials`.
Not asserted by the legacy test and not carried: the blacksmith-proximity check (dist <= 2, functional building) lived only in the deleted `BlacksmithService`.
`test_shop_buy_and_sell` stays (ShopAction is out of scope).

## AC3: static proof instead of a run
AC3 (hash-neutral proof) was replaced by a static proof under rpg-planner's 2026-10-28 ruling because /data is under 10 GB and no run is allowed. The AC text is not edited.
1. Import-time behavior, from a code read: `src/core/recipes.py` defines a frozen dataclass `Recipe` and a class `RecipeRegistry` with a class-level dict; no registration, no I/O, no module-level call. `src/town/blacksmith.py` defines two classes and imports only `src.core.*`; its `ResourceTransferIntent` import is inside a function. Neither does anything at import time.
2. No conftest or plugin imports them: the import-statement `git grep` above (at the pre-deletion origin/main) shows only the pair blacksmith.py -> recipes.py and the one test; `pytest tests/unit tests/integration/economy --collect-only` after the deletion collects 8894 tests with exit 0 (a conftest or plugin import would have errored), and neither module is in `sys.modules` (trivially true once the files are gone; the collection result is the evidence).
3. Import graph: `make lint-imports` 17 kept, 0 broken.
4. Tests: tests/unit/world, tests/unit/domains/progression, tests/unit/core, tests/integration/economy, tests/integration/domains/progression: 832 passed.

## Inventory file
`docs/audits/unreachable_code_inventory.{json,csv}` are a point-in-time data record with no removal column; the prose file `.md` records later deletions in prose (BiologicalSystem precedent). Rows 123 (`BlacksmithAction`) and 182 (`RecipeRegistry.get_all`) are recorded as deleted in the `.md` Structured inventory section; the data files are not edited.

## Completeness-check pins moved (needs agent-working-planner's agreement before they are edited)
Measured on origin/main a6a01f808 vs this branch: scope_files 345 -> 343 (both deleted files were in scope), unbound_files 248 -> 246 (both were unbound), candidates 68 -> 67, wired 19 unchanged. The candidate that left is `src/town/blacksmith.py::BlacksmithService` (its name ends in "Service", one of the check's `_WIDER_SUFFIXES`), NOT `RecipeRegistry`: "Registry" is not in that suffix list, so the legacy `RecipeRegistry` never counted as a candidate. (My first message to rpg-planner-ubuntu named RecipeRegistry; rpg-planner-ubuntu caught it.) rpg-planner-ubuntu re-measured the three numbers independently and they match.

## Inventory precedent
The prose record of the two deleted rows follows the BiologicalSystem precedent in the same file (`TCK-20260908-BIOLOGICAL-SYSTEM-DEAD-CODE-DISPOSITION`, recorded in prose in `unreachable_code_inventory.md`; the `.csv`/`.json` are a point-in-time record and stay unedited). rpg-planner-ubuntu OK'd this.
