---
status: historical
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20260904-RECIPE-CATALOG-NAMESPACE-BRIDGE
artifact_type: test_plan
tags: [content, economy]
---

# Test Plan — TCK-20260904-RECIPE-CATALOG-NAMESPACE-BRIDGE

## Normal flow
- `recipe_materials("craft_iron_sword")` returns `("iron_ore", "wood")` (a real `registries.py`
  recipe) instead of `()`.
- `BlacksmithSystem.enforce()`'s wholesale-learn step populates `known_recipes` with
  `registries.py::RecipeRegistry`'s real 25 ids on a blacksmith-tile visit.
- `PossessionUnderstandingService.evaluate()` reports `known_uses`/`craft_priority > 0` for a real
  possessed material matching a real known recipe.
- `GrowthGapEvaluator.evaluate()` raises a real `material_gap` when a known recipe's material is
  genuinely missing.

## Edge cases
- `recipe_materials()` on an unknown recipe id still returns `()`, not an exception (mirrors the
  old `.get_recipe()` None-on-miss contract, now built on top of `.contains()` guarding
  `registries.py`'s own `.get()`-raises-`KeyError` behavior).
- `known_recipes` containing a recipe id from neither registry (e.g. a stale/legacy id) still
  produces no match — not a crash.

## Failure modes
- `BlacksmithSystem.RECIPES`'s own crafting-execution branch (`craft_target`-gated) is confirmed
  unaffected — still dead in practice (no assignment path exists), verified by unchanged existing
  test coverage for that branch, not a new claim.

## Regression-prone paths
- The 2 disclosed-limitation tests must demonstrate the *opposite* of their old pinned assertion
  (from "does not match" to "genuinely matches") — a before/after docstring note makes this
  deliberate, not silent test-weakening.
- `src/core/recipes.py::RecipeRegistry` itself is untouched (no import changes) — confirmed via
  `git diff` showing zero changes to `src/core/recipes.py`.
- `tests/unit/world/test_economy_contract.py`, `tests/unit/core/test_hardcoded_regression_guard.py`
  must show zero new failures (per the ticket's own explicit AC).

## Commands
- `pytest tests/unit/domains/progression/ -v`
- `pytest tests/unit/world/test_economy_contract.py tests/unit/core/test_hardcoded_regression_guard.py -v`
- `pytest tests/unit/domains/progression/test_phase6_possession_understanding_service.py::test_material_possession_predicate_craft_prefixed_known_recipes_do_not_match -v` (renamed/rewritten — old name kept only if behaviorally still accurate, otherwise renamed to match its new assertion)
- New real-Kernel-tick test (name TBD during implementation) proving organic reachability.
