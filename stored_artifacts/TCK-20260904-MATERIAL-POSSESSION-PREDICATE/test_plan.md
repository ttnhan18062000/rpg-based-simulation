---
status: historical
layer: economy
authority: P2
audience: agent
ticket_id: TCK-20260904-MATERIAL-POSSESSION-PREDICATE
artifact_type: test_plan
tags: [economy, progression, cognition]
---

# Test Plan — TCK-20260904-MATERIAL-POSSESSION-PREDICATE

## Regression Surface

**Unit**
- `tests/unit/domains/progression/test_phase6_possession_understanding_service.py` — all 3 existing
  tests (`test_material_for_active_recipe_has_high_keep_priority`, `test_junk_item_has_sell_priority`,
  `test_better_weapon_gets_equip_priority`) must keep passing unmodified in outcome (keep/sell/equip
  priorities and `reason` text for `iron_ore`/`broken_mug`/`iron_sword`), even if the underlying
  implementation moves from hardcoded item-id checks to a `RecipeRegistry`-backed predicate — these
  three scenarios are exactly the cases the predicate must reproduce correctly through the new path.
- `tests/unit/domains/progression/test_phase6_growth_gap_evaluator.py` — must keep passing; in
  particular any test covering the `material_gap` key (`iron_sword`/`iron_ore`) must still produce
  the same gap if `GrowthGapEvaluator` is touched.
- `tests/unit/domains/progression/test_phase6_reward_interpretation_service.py`,
  `tests/unit/domains/progression/test_phase6_conversion_option_generator.py` — downstream
  consumers of `PossessionUnderstandingComponent`/`GrowthGapReport`; must not regress if either
  upstream service's output shape changes.
- `tests/unit/core/*` recipe/registry-adjacent guards: `tests/unit/core/test_hardcoded_regression_
  guard.py`, `tests/unit/core/test_registry_parity.py`, `tests/unit/core/test_registry_cross_
  reference.py`, `tests/unit/core/test_registry_bridge.py`, `tests/unit/core/test_registry_
  adapters.py` — must keep passing; none of these should need modification since
  `registries.py::RecipeRegistry` is out of scope.
- `tests/unit/strategic/test_registries.py`, `tests/unit/strategic/test_opportunities.py` — exercise
  `action_intent.py`'s `REQUEST_CRAFT` path against `registries.py::RecipeRegistry`; must not
  regress (confirms this ticket did not accidentally touch the catalog-bootstrapped registry).
- If the AmbitionProfile/`GrowthGapEvaluator` route is taken: `tests/unit/strategic/test_expanded_
  goals.py`, `tests/unit/strategic/test_goal_hysteresis.py`,
  `tests/unit/strategic/test_personality_goal_modifiers.py` (existing GoalScorer-adjacent
  regression coverage) should be re-run if any shared scoring utility is touched.

**Integration**
- `tests/integration/scenarios/test_phase6_progression_conversion_scenarios.py` — all 7 scenario
  tests (`test_scenario_6_1`...`test_scenario_6_7`), since they exercise the full
  `ProgressionConversionPhase.execute()` pipeline end-to-end (possession → gaps → interpretation →
  options → decision → resolved update), the exact chain this ticket's recommended production
  consumer sits inside.
- `tests/integration/domains/progression/test_phase6_progression_conversion_phase.py` — phase-level
  integration coverage for the same pipeline.
- `tests/unit/world/test_economy_contract.py::test_blacksmith_crafting` — the closest direct
  regression check for `recipes.py::RecipeRegistry`-backed crafting execution
  (`BlacksmithAction.craft`); must keep passing unmodified, confirming the predicate did not alter
  `CraftingSystem`/`BlacksmithService` behavior.

**Performance (budget guard)**
- `tests/perf/test_phase6_progression_conversion_budget.py` — confirms the predicate's added
  `RecipeRegistry` lookups per possession-evaluation pass don't blow the existing per-tick budget
  for `ProgressionConversionPhase`.

## New Tests Required

Per Acceptance Criteria (predicate exists reusing `PossessionUnderstandingService`; names
`recipes.py::RecipeRegistry` explicitly; wires to a real production consumer; covers normal/edge/
failure-mode cases):

1. **`test_material_possession_predicate_recognizes_known_recipe_material`**
   - Category: unit
   - Verifies: entity possessing an item that is a required material for one of their
     `known_recipes` (looked up via `recipes.py::RecipeRegistry.get_recipe(recipe_id).materials`,
     not the hardcoded literal) is correctly identified as possessing/able-to-craft-toward that
     material — normal flow (positive case), generalized beyond the two hardcoded item ids
     (`iron_ore`, `wolf_fang`) already covered by the existing possession-service tests, e.g.
     `iron_shield`'s `iron_ore` requirement or `health_potion`'s `herb` requirement (both real
     `recipes.py` entries not currently exercised by any existing test).
   - Where: `tests/unit/domains/progression/test_phase6_possession_understanding_service.py` (if the
     predicate lives on/is called by `PossessionUnderstandingService`) or a new
     `tests/unit/domains/progression/test_material_possession_predicate.py` if it is extracted as an
     independently-callable unit.

2. **`test_material_possession_predicate_empty_inventory_returns_false_no_crash`**
   - Category: unit (edge case)
   - Verifies: an entity with zero inventory items (`entity.inventory.items == []`) evaluated
     against any known recipe's material returns a clean negative result — no exception, no
     `IndexError`/`AttributeError` from an empty list.
   - Where: same file as test 1.

3. **`test_material_possession_predicate_unregistered_material_returns_false_not_exception`**
   - Category: unit (failure mode)
   - Verifies: calling the predicate with a `recipe_id`/`material_id` not present in
     `recipes.py::RecipeRegistry` (confirmed behavior: `get_recipe()` returns `None`, never raises)
     produces a defined negative/false result, not an unhandled exception — this is the "RecipeRegistry
     lookup miss" failure mode named in the ticket's Acceptance Criteria. Must assert against the
     confirmed `None`-return contract of `recipes.py::RecipeRegistry.get_recipe()`, not the
     `KeyError`-raising contract of the unrelated `registries.py::RecipeRegistry.get()` — a test that
     accidentally imports the wrong `RecipeRegistry` and asserts `pytest.raises(KeyError)` would be
     silently testing the wrong class.
   - Where: same file as test 1.

4. **`test_recipe_registry_docstring_or_comment_disambiguates_the_two_classes`** (or equivalent
   static/introspective check)
   - Category: unit / architecture guard
   - Verifies: the predicate's implementation module contains an explicit code comment or docstring
     naming `src/core/recipes.py::RecipeRegistry` and distinguishing it from
     `src/core/registries.py::RecipeRegistry` — directly enforces AC #2 ("a code comment or
     docstring disambiguating the two by file path"). Can be a simple substring assertion against
     the module's `__doc__`/source, or a `code-review`-style manual check documented in the
     Implementation Notes if automated enforcement is impractical.
   - Where: `tests/unit/domains/progression/test_material_possession_predicate.py` (new file) or
     alongside test 1-3.

5. **Production-consumer behavior-change test** (exact name/location depends on which route
   `plan.md` selects — see investigation.md Risks):
   - If **Route A (GrowthGapEvaluator/ConversionOptionGenerator chain)**:
     `test_growth_gap_material_gap_uses_real_recipe_lookup_not_hardcoded_literal` — unit test in
     `tests/unit/domains/progression/test_phase6_growth_gap_evaluator.py` asserting a `material_gap`
     is correctly raised/suppressed for a recipe *other than* the hardcoded `iron_sword`/`iron_ore`
     pair (e.g. `health_potion`/`herb`), proving the hardcoded literal was actually replaced by the
     shared predicate, not merely wrapped.
   - If **Route B (AmbitionProfile)**: a test asserting a concrete, non-default-constructed
     `AmbitionProfile.strategic_value_targets` value changes real downstream behavior (per AC #3:
     "a test asserting production behavior changes based on the predicate's output, not just that
     the field gets set") — e.g. a `GrowthGap`'s `severity`/`candidate_resolution_tags` differs
     between an entity with an empty vs. populated `strategic_value_targets`. Must NOT be a test
     that only asserts `entity.identity.motivation.ambition.strategic_value_targets == (...)` with
     no behavioral assertion — that would reproduce the exact dead-field pattern this ticket exists
     to close.
   - Category: unit (behavioral), directly required by AC #3.
   - Where: matches whichever production file is actually touched.

## Scoped Pytest Commands

```bash
# Core possession/progression regression + new predicate tests
pytest tests/unit/domains/progression/ -v

# Progression pipeline integration scenarios (full 6-step chain)
pytest tests/integration/scenarios/test_phase6_progression_conversion_scenarios.py \
       tests/integration/domains/progression/test_phase6_progression_conversion_phase.py -v

# Crafting/blacksmith regression (recipes.py::RecipeRegistry live path)
pytest tests/unit/world/test_economy_contract.py -v

# registries.py::RecipeRegistry catalog path — must show zero change in behavior
pytest tests/unit/core/test_registry_parity.py tests/unit/core/test_registry_cross_reference.py \
       tests/unit/core/test_hardcoded_regression_guard.py tests/unit/strategic/test_registries.py -v

# Only if the AmbitionProfile/GoalScorer route touches goal-scoring:
pytest tests/unit/ai/goals/ tests/unit/strategic/test_expanded_goals.py \
       tests/unit/strategic/test_goal_hysteresis.py -v

# Progression conversion performance budget guard
pytest tests/perf/test_phase6_progression_conversion_budget.py -v
```

Never `pytest tests/` — scoped to `progression`/economy-crafting/registries/goal-scoring domains
per CLAUDE.md's Testing Rule.

## Anti-Drift Test Guards

- **`recipes.py` vs `registries.py` `RecipeRegistry` isolation**: any new test must import
  `from src.core.recipes import RecipeRegistry` explicitly (never `from src.core.registries import
  RecipeRegistry`) and, ideally, assert both classes remain independently importable with their
  documented differing miss-behavior (`None` vs. `KeyError`) — this catches an accidental silent
  substitution of the wrong registry at the source, not just at review time.
- **Hardcoded-literal regression guard**: a test parametrized over a *second* real recipe besides
  `iron_sword`/`iron_ore` (e.g. `health_potion`/`herb`, `iron_shield`/`iron_ore`) must pass — if the
  predicate still only recognizes the original two hardcoded item ids, this guard fails and proves
  the implementation didn't actually generalize past the mock.
- **`CraftingSystem`/`BlacksmithService` untouched guard**: `tests/unit/world/test_economy_
  contract.py::test_blacksmith_crafting` and any existing `CraftingSystem.craft()` gate-order tests
  must pass byte-identically — catches accidental modification of the authoritative 7-gate crafting
  sequence, which this ticket must never touch (read-only predicate, not a new crafting gate).
- **AmbitionProfile dead-field guard (only if Route B is chosen)**: a test must fail if
  `AmbitionProfile.strategic_value_targets` is populated by a production code path but no production
  code path *reads* it back into an observable behavior change — i.e. the test in "New Tests
  Required" item 5 (Route B) is itself the anti-drift guard against reproducing the exact
  `TCK-20260824-PERSONAL-ECONOMY-SCOPE-BLOCK`-class defect this ticket exists to avoid.
- **Determinism guard**: since `ProgressionConversionPhase` is a bounded authoritative engine phase,
  any predicate change must not introduce iteration-order-dependent or wall-clock-dependent behavior
  — existing scenario tests in `test_phase6_progression_conversion_scenarios.py` already assert
  fixed, reproducible outcomes for fixed seeds/state, so their continued pass is itself a determinism
  guard for this change.
