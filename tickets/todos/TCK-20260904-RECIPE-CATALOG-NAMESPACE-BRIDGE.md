---
status: active
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20260904-RECIPE-CATALOG-NAMESPACE-BRIDGE
phase: open
date: 2026-09-04
tags: [content, economy]
---

# TCK-20260904-RECIPE-CATALOG-NAMESPACE-BRIDGE

## Title
Bridge the three disjoint recipe-shaped catalogs so material-possession/crafting checks reach real production data

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
`TCK-20260904-MATERIAL-POSSESSION-PREDICATE`'s own architecture-review cycle discovered — and
independently re-verified twice — that this codebase has **three** disjoint recipe-shaped catalogs
with zero id overlap between them:
1. `src/core/recipes.py::RecipeRegistry` — legacy, 3 entries (`iron_sword`, `iron_shield`,
   `health_potion`). Confirmed to have **zero production callers of its own** (its two readers,
   `CraftingSystem.craft()` and `BlacksmithService.craft_item()`, are each themselves unreachable
   from any live code path).
2. `src/core/registries.py::RecipeRegistry` — catalog-bootstrapped, 25 entries. Confirmed to be the
   **actually-live** crafting-execution path, read by `src/engine/intent/action_intent.py`'s
   `REQUEST_CRAFT` branch (both pre-flight `Requirement` gating and the real commit via
   `ResourceTransferIntent` → `conservation.py`'s `CRAFTING` branch).
3. `src/engine/blacksmith.py::BlacksmithSystem.RECIPES` — 14 `craft_*`-prefixed entries. This is the
   **actual, unconditionally-wired** source that populates `entity.identity.known_recipes` in
   production (via wholesale-learning on a blacksmith-tile visit) — and shares **zero ids** with
   either of the two `RecipeRegistry` classes above.

The practical consequence: any check keyed on "does this entity know a recipe for material X"
(including `TCK-20260904-MATERIAL-POSSESSION-PREDICATE`'s new `recipe_materials()` predicate, and by
extension anything `TCK-20260904-FACTION-EXPAND-DIRECTIVE`'s `EXPAND_TERRITORY` directive might one
day want to consult) is structurally near-inert against real, organically-populated
`known_recipes` state, because the id namespace it can query (`recipes.py`'s 3 or `registries.py`'s
25) never matches what real entities actually learn (`blacksmith.py`'s 14 `craft_*` ids).

## Scope
- Investigate and decide the real fix: either (a) migrate `BlacksmithSystem.RECIPES`'s wholesale-learn
  step to populate `known_recipes` with ids drawn from the actually-live `registries.py::RecipeRegistry`
  catalog instead of its own private 14-entry `craft_*` list (closing the gap at the population side),
  or (b) extend `registries.py::RecipeRegistry`'s 25-entry catalog to include `blacksmith.py`'s 14
  `craft_*` recipes as first-class entries and have `known_recipes` continue to be populated from
  `BlacksmithSystem.RECIPES` but keyed consistently with the live registry, or (c) another design this
  ticket's own investigation surfaces. This is a real architecture decision — do not default to the
  smallest textual diff without evaluating gameplay/balance impact (`BlacksmithSystem.RECIPES`'s 14
  entries and `registries.py`'s 25 entries are not simply the same data under different names; check
  for real content differences before merging).
- Once bridged, verify `recipe_materials()` (from `TCK-20260904-MATERIAL-POSSESSION-PREDICATE`) or its
  replacement is genuinely reachable against organically-populated `known_recipes` in a real simulation
  run — not just a hand-constructed test fixture.
- Update the two disclosed-limitation regression tests
  (`test_material_possession_predicate_craft_prefixed_known_recipes_do_not_match`,
  `test_growth_gap_craft_prefixed_known_recipes_produce_no_material_gap`) to reflect the new, real
  reachability — they currently pin the OLD (inert) behavior as correct; once this ticket lands, that
  pinned behavior becomes stale and these tests need updating, not silent divergence.
- Update `docs/mechanics/resource_conservation_contract.md`, `docs/simulation/domains/progression_contract.md`,
  and the `PROG-123`/relevant `docs/parity_ledger/` entries to reflect the bridged state.

## Out of Scope
- Renaming either `RecipeRegistry` class (the naming collision itself is confirmed real but is a
  separate, lower-priority cosmetic issue — not blocking, not this ticket's job unless trivial
  alongside the real bridging work).
- Any change to `TCK-20260904-FACTION-EXPAND-DIRECTIVE`'s deliberate decision not to hard-gate
  `EXPAND_TERRITORY` on the material-possession predicate — that decision was correct given the
  predicate's state at the time and does not need revisiting as part of this ticket, though a future
  ticket could reconsider it once this bridge lands.
- Rebalancing crafting difficulty/materials — if bridging surfaces real content differences between
  the 14 and 25-entry catalogs, resolve them by choosing one as canonical (per the Scope's option
  a/b/c decision), not by inventing new balance values.

## Acceptance Criteria
- A single, real architecture decision is made and documented (in plan.md) for how the three catalogs
  are bridged, with the two rejected alternatives' tradeoffs named.
- After the bridge, a real simulation run (not a synthetic fixture) demonstrates an entity's
  organically-learned `known_recipes` producing a non-empty result from the material-possession
  predicate (or its successor).
- The two existing disclosed-limitation regression tests are updated to reflect the new reachable
  state, with a clear before/after note in their docstrings/comments.
- No regression in existing crafting/blacksmith test coverage
  (`tests/unit/world/test_economy_contract.py`, `tests/unit/core/test_hardcoded_regression_guard.py`,
  and the full `tests/unit/domains/progression/` suite).

## Related Tickets
- TCK-20260904-MATERIAL-POSSESSION-PREDICATE
- TCK-20260904-FACTION-EXPAND-DIRECTIVE

## Related Docs
- docs/mechanics/resource_conservation_contract.md
- docs/simulation/domains/progression_contract.md
- docs/parity_ledger/progression.yaml (PROG-123)
- docs/brainstorm/rpg_feature_atlas.html
- docs/brainstorm/rpg_expected_schemas.html
- docs/brainstorm/rpg_simulation_wiring_map.html

## Related Stored Artifacts
- stored_artifacts/TCK-20260904-MATERIAL-POSSESSION-PREDICATE/

## Related Code Areas
- src/core/recipes.py
- src/core/registries.py
- src/engine/blacksmith.py
- src/engine/intent/action_intent.py
- src/domains/progression/material_predicate.py
- src/domains/progression/possession.py
- src/domains/progression/gaps.py

## Assumptions / Open Questions
- Which of options (a)/(b)/(c) is correct depends on real content-parity analysis between
  `BlacksmithSystem.RECIPES`'s 14 entries and `registries.py::RecipeRegistry`'s 25 entries — not yet
  done, this ticket's own investigation phase must do it.
- Whether `src/core/recipes.py::RecipeRegistry` (confirmed to have zero production callers on either
  side) should be deprecated/removed entirely once the bridge lands is a real question this ticket
  should surface but not necessarily resolve — flagged for the plan phase to decide scope on.

## Implementation Notes
(To be filled during implementation.)

## Test Summary
(To be filled during implementation.)

## Files Changed
(To be filled during implementation.)

## Completion Summary
(To be filled on completion.)
