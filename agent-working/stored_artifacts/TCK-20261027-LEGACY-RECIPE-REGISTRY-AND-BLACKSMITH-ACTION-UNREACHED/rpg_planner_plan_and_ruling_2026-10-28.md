---
status: active
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20261027-LEGACY-RECIPE-REGISTRY-AND-BLACKSMITH-ACTION-UNREACHED
phase: open
date: 2026-10-28
tags: [economy]
---

# Plan and rpg-planner ruling (2026-10-28)

The plan comes from rpg-planner-ubuntu. rpg-planner (u24) ruled on it on 2026-10-28, relayed by lead-planner-u24 and then lead-planner. Both are kept word for word below. The ruling is NOT an owner approval: dispatch also needs the owner's go, logged on #715.

## Plan (rpg-planner-ubuntu, as sent)

Caller sweep on origin/main a6a01f808 (grep over src, tools, tests, docs, registries; graphify agrees):
- src/core/recipes.py (48 lines) is imported only by src/town/blacksmith.py.
- src/town/blacksmith.py (75 lines: BlacksmithService.craft_item plus the BlacksmithAction wrapper) is imported only by tests/unit/world/test_economy_contract.py (line 8, test_blacksmith_crafting).
- Nothing in src/, tools/ or the CLI imports it, and there is no string or getattr dispatch. Every other "blacksmith" hit is the building kind string or src/engine/blacksmith.py::BlacksmithSystem, which is a different module and is untouched.
- Other recipes.py mentions are history in docstrings: material_predicate.py:5/19/46 and three progression tests' docstrings. test_material_possession_predicate.py:45 asserts that the predicate's docstring still names "src/core/recipes.py" as its former source. That stays true and the docstring is not edited.

DECISION PROPOSED: (a) delete both files. This follows the #760 precedent; the legacy path has zero production callers and is already listed in docs/audits/unreachable_code_inventory.csv:123/182.

STEPS:
1. Delete src/core/recipes.py and src/town/blacksmith.py.
2. Delete test_blacksmith_crafting. Before deleting, the implementer checks that tests/integration/economy/test_crafting_live_path.py covers what it asserted: a CRAFT ResourceTransferIntent applied through refine + apply, materials removed, output added, gold debited, and a second craft refused when the entity can't afford it. Any assertion not covered there gets moved onto the live REQUEST_CRAFT path, not dropped. test_shop_buy_and_sell in the same file stays (ShopAction is out of scope).
3. Remove the legacy RecipeRegistry allowlist entry from tests/unit/core/test_same_name_class_guard.py:44-45.
4. Run the mechanism-registry completeness check. If the scope_files or unbound pins move, those pins are in agent-working's test file, so I get agent-working-planner's agreement first, as on t2.
5. Mark the two inventory CSV rows as removed, following however that file records deletions.

BIBLE AND PARITY TEXT. Exact wording needs your OK; the implementer writes it only after your OK.
(i) docs/mechanics/resource_conservation_contract.md, Crafting Atomicity, lines 171-174. Replace:
"Two independent `RecipeRegistry`-backed crafting code paths exist in the repo (see `docs/parity_ledger/progression.yaml`'s `PROG-123` divergence note and `TCK-20260904-MATERIAL-POSSESSION-PREDICATE` for the full disambiguation). Only one is live in production; this section previously described the other one as if it were."
with:
"One `RecipeRegistry`-backed crafting path exists in the repo: `src/core/registries.py::RecipeRegistry`, read by the live path below. A second, legacy 3-entry registry (`src/core/recipes.py`, reached only through the uncalled `src/town/blacksmith.py::BlacksmithAction`) was deleted by `TCK-20261027-LEGACY-RECIPE-REGISTRY-AND-BLACKSMITH-ACTION-UNREACHED` (see `docs/parity_ledger/progression.yaml`'s `PROG-123` note and `TCK-20260904-MATERIAL-POSSESSION-PREDICATE` for the history)."
(ii) PROG-123 divergence_note in docs/parity_ledger/progression.yaml, written via parity_ledger_writer.py. Replace:
"Two narrower gaps remain, both explicitly out of scope for this ticket and separately disclosed: (1) src/core/recipes.py::RecipeRegistry (the legacy 3-entry registry this predicate read before) still has zero production callers -- left undeleted as a disclosed follow-up, not a defect of this entry; (2) src/engine/blacksmith.py::BlacksmithSystem.RECIPES''s"
with:
"The legacy src/core/recipes.py::RecipeRegistry (the 3-entry registry this predicate read before) and its only reader, src/town/blacksmith.py, had zero production callers and were deleted by TCK-20261027-LEGACY-RECIPE-REGISTRY-AND-BLACKSMITH-ACTION-UNREACHED. One narrower gap remains, explicitly out of scope and separately disclosed: src/engine/blacksmith.py::BlacksmithSystem.RECIPES''s"
The rest of the note is unchanged. status, test_path and v2_evidence are unchanged.

NUMBERING: this is a deletion of uncalled code with no behaviour change, so no new divergence and no new STRAT id.

PROOF (AC3): (B) a static proof. The import graph shows no src/tools path to the deleted modules, plus lint-imports, plus the unit and integration economy tests.

## rpg-planner (u24) ruling, word for word

Plan (a), LEGACY-RECIPE-REGISTRY-AND-BLACKSMITH-ACTION-UNREACHED, is OK as written. No code until the owner's go; I've put that ask to the owner and will relay it with the #715 id.
- Overlap: none. rpg-planner diffed D73, :1610 and N15 against their merge bases. None of them touches src/town/*, resource_conservation_contract.md, progression.yaml, test_same_name_class_guard.py, unreachable_code_inventory.csv or mechanisms.yaml. D73's "town-service" is the economy transfer path and doesn't touch src/town/blacksmith.py.
- Decision: delete both files (#760 precedent). Steps 1-5 are OK, with two notes:
  - Step 2: list each assertion of test_blacksmith_crafting with where it is now covered (file::test), or say it was moved onto REQUEST_CRAFT.
  - Step 4: agent-working-planner's agreement is needed only if the pins move. That isn't expected, since mechanisms.yaml cites src/engine/blacksmith.py::BlacksmithSystem.
- Text (i) and PROG-123 text (ii): OK verbatim. status, test_path and v2_evidence stay unchanged.
- Numbering: no divergence and no STRAT id.
- AC3: static proof (B) accepted, with two additions to the ticket:
  1. A statement, from a code read, that neither deleted file does anything at import time (no registry registration, no module-level side effect).
  2. Evidence that no conftest or plugin imports them: grep tests/ conftest files, or run pytest --collect-only on the economy dirs and show neither module in sys.modules.
  Record in the ticket that AC3's run was replaced by a static proof under rpg-planner's ruling (2026-10-28) because of disk. Don't edit the AC text.
- PR: one PR. rpg-planner reviews it; push and merge go through the leads to the owner.
