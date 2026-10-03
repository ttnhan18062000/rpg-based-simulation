---
status: historical
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20260904-RECIPE-CATALOG-NAMESPACE-BRIDGE
artifact_type: plan
tags: [content, economy]
---

# Plan — TCK-20260904-RECIPE-CATALOG-NAMESPACE-BRIDGE

## Decision (see investigation.md for full rationale and evidence)

**Option (a)**: bridge both ends of the namespace mismatch through `src/core/registries.py::
RecipeRegistry` — the one registry independently confirmed real, live, catalog-backed, and
AI-reachable (`src/domains/adventure/resolver.py`'s `ACQUIRE_ITEM` → `REQUEST_CRAFT` dispatch →
`action_intent.py`).

1. **Population side**: `BlacksmithSystem.enforce()`'s wholesale-learn step
   (`src/engine/blacksmith.py:144`) switches from `list(BlacksmithSystem.RECIPES.keys())` to
   `list(RecipeRegistry.all().keys())` (the `registries.py` `RecipeRegistry`).
2. **Consumption side**: `recipe_materials()` (`material_predicate.py`) switches from reading
   `src/core/recipes.py::RecipeRegistry` (legacy, 3 entries) to `src/core/registries.py::
   RecipeRegistry` (25 entries), adapting for its different miss-behavior (`.get()` raises
   `KeyError` vs. `.get_recipe()` returning `None`) and field name (`requires_items` vs.
   `materials`).

**Rejected: Option (b)** (extend `registries.py` with `BlacksmithSystem.RECIPES`'s 14 entries as
first-class catalog content) — the real content-parity check found 13 of 14 output items and 11 of
15 required materials don't exist anywhere in the real catalog. Extending would mean inventing new
items/materials from nothing, directly forbidden by this ticket's own Out of Scope. Not a smaller
or safer alternative to (a); a larger, forbidden one.

**Rejected: leaving `recipe_materials()` reading `recipes.py`** — regardless of which registry the
population side uses, `recipes.py`'s 3 ids (`iron_sword`/`iron_shield`/`health_potion`) overlap
with neither `BlacksmithSystem`'s old 14 nor `registries.py`'s 25 — the predicate would stay fully
inert either way. Both ends of the bridge must point at the same real registry.

**`src/core/recipes.py::RecipeRegistry`** (now fully callerless): left in place, undeleted — a
disclosed, deliberate scope decision (dead-code removal is a separate concern from this ticket's
namespace-bridge scope), flagged as a real follow-up opportunity in Completion Summary.

**`BlacksmithSystem.RECIPES`'s own crafting-execution branch** (`blacksmith.py:154-246`, gated on
`entity.identity.craft_target`, confirmed separately dead since nothing in real AI ever sets
`craft_target`): untouched — a separate, deeper reachability gap explicitly outside this ticket's
namespace-bridge scope. Flagged, not silently dropped.

## Implementation steps

1. **`src/engine/blacksmith.py`**: import `RecipeRegistry` from `src/core/registries.py` (aliased
   to avoid ambiguity with the module-local `V2Recipe`/`RECIPES`); change the wholesale-learn
   step's `all_recipes` source. Update the "Parity with V1 RECIPES" comment block context (the
   wholesale-learn comment specifically, not the `RECIPES` dict's own docstring, which still
   correctly describes its own now-narrower role: crafting-execution lookups only, no longer the
   `known_recipes` population source).
2. **`src/domains/progression/material_predicate.py`**: redirect `recipe_materials()` to
   `registries.py::RecipeRegistry`, adapting for `.contains()`/`.get()`/`requires_items`. Rewrite
   the module docstring — its entire "why NOT registries.py" rationale is now backwards; the new
   docstring must explain why it reads `registries.py` specifically (the live path) and not
   `recipes.py` (legacy, dead) or `BlacksmithSystem.RECIPES` (not a registry, and its own
   crafting-execution consumers are separately dead).
3. **`src/domains/progression/possession.py`, `gaps.py`**: update their inline comments citing the
   old (now-reversed) rationale for which registry `recipe_materials()` reads.
4. **Tests**: rewrite the 2 disclosed-limitation pinning tests
   (`test_material_possession_predicate_craft_prefixed_known_recipes_do_not_match`,
   `test_growth_gap_craft_prefixed_known_recipes_produce_no_material_gap`) to demonstrate the new
   reachable state, using a real `registries.py` recipe id (`craft_iron_sword`, materials
   `{iron_ore: 2, wood: 1}`) instead of the old fictional `craft_steel_sword` — with a clear
   before/after docstring note per the ticket's own AC.
5. **New real-simulation test**: a real `Kernel` tick with an entity on a real `blacksmith`-tile,
   confirming (a) wholesale-learn populates real `registries.py` ids into `known_recipes`, and (b)
   `PossessionUnderstandingService` genuinely matches a real inventory material against them —
   satisfies the AC's explicit "not just a hand-constructed test fixture" requirement.
6. **Docs**: `docs/mechanics/resource_conservation_contract.md`,
   `docs/simulation/domains/progression_contract.md`, `docs/parity_ledger/progression.yaml`
   (PROG-123) updated to reflect the bridged, now-reachable state (via `doc-updater`-style direct
   edits and `tools/parity_ledger_writer.py` for the YAML, never hand-edited).

## Explicitly out of scope (per investigation.md + the ticket's own text)
- `src/core/recipes.py::RecipeRegistry`'s removal — left in place, disclosed as a follow-up.
- `BlacksmithSystem.RECIPES`'s own crafting-execution branch / `craft_target` reachability — a
  separate, deeper, pre-existing gap.
- Renaming either `RecipeRegistry` class.
- Any change to `TCK-20260904-FACTION-EXPAND-DIRECTIVE`'s `EXPAND_TERRITORY` gating decision.
- Inventing new balance values for `BlacksmithSystem.RECIPES`'s orphaned content.

## Acceptance-criteria map
| AC | Satisfied by |
|---|---|
| A single, real architecture decision is made and documented, with rejected alternatives' tradeoffs named | investigation.md + this plan.md |
| A real simulation run demonstrates organically-learned known_recipes producing a non-empty possession-predicate result | New real-Kernel-tick test (step 5) |
| The 2 disclosed-limitation tests updated with a before/after note | Step 4 |
| No regression in existing crafting/blacksmith test coverage | `tests/unit/world/test_economy_contract.py`, `tests/unit/core/test_hardcoded_regression_guard.py`, full `tests/unit/domains/progression/` suite re-run |
