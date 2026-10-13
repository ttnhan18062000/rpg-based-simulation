---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20261014-EVERY-COMPILED-LIVING-BODY-RESOLVES-TO-A-DECLARED-DIET-OR-THE-WORLD-DOES-NOT-COMPILE
phase: open
date: 2026-10-14
tags: []
---

# TCK-20261014-EVERY-COMPILED-LIVING-BODY-RESOLVES-TO-A-DECLARED-DIET-OR-THE-WORLD-DOES-NOT-COMPILE

## Title
Every compiled living body resolves to a declared diet, or the world does not compile (the diet slice of SURV-05 provenance; prerequisite of the free-meal removal).

## Status
INPROGRESS

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
The gate's V1 found the free meal feeding "undeclared" kinds. Measured (compile of every data world, seed 42): kind groups with no declared diet are bodies with NO species at all: `hero` (10 worlds), `merchant` (4), `scout` (1), spawned from world-module population recipes that name only a role and a faction (data/content/world_modules/trading_company_hub.yaml, hero_adventurers.yaml, and the scout module), so `resolver.py` takes the no-archetype branch (`resolved_entity` with no `species_id`) and `entity_spawner._spawn_legacy_guard` builds the body with `species_id=None`. `can_use_inn_meal` and `can_eat_item` then read `body is None` as "missing data gates nothing" and every food is allowed: a silent free meal (and, once the free meal is removed, a silent starvation). Two other groups are not gaps: `none` (guardian/spirit, sentinel/undead) are DECLARED empty diets. Owner ruling D73 / the rule "a missing property is a gap, not a default" (relayed by rpg-planner 2026-10-14): the body gets its kind's diet in content (a human's, for these), and a body with no declared diet is a CONTENT ERROR at compile.

## Scope
1. Content: the world-module recipes that spawn `hero`, `merchant` and `scout` bodies name the species of their kind (human, from the existing `traveling_merchant` / hero archetypes' species), by the smallest declaration the schema allows: an `archetype_id` on the recipe if an archetype exists for the role+faction (traveling_merchant exists), else a `species` field on the recipe, carried through `PopulationSpec`/`ResolvedEntityProfile` to the body's `species_id` (check the recipe schema, `src/worldmodules/schema.py`, before choosing; a new schema field is a state-model change: ask rpg-planner).
2. Compile check: after assembly every living entity resolves `get_kind_properties(species_id)` to a body whose `diet` is declared (a list, possibly empty). A body with no species, an unknown species, or a body model with `diet is None` raises a content error naming the world, population and recipe. One check, in the compiler or the content validator (`src/content/validator.py:142` already lists "properties a species and its body model leave undeclared": reuse it), never a default.
3. The `appraisal` fallbacks that read "no body or no diet = eats anything" (`can_eat_item`, `kind_can_eat_item`, `can_use_inn_meal`) stay for non-compiled test entities but are no longer reachable from a compiled world; say so in the code comments.

## Out of Scope
The free-meal removal itself (TCK-20261007-EAT-BESIDE-THE-INN-FEEDS-A-SUBJECT-THAT-CANNOT-PAY-FREE-MEAL, lands after baseline v1); the rest of SURV-05 provenance (need and drive profiles), which stays its own ticket: this takes ONLY the diet part (TCK-20261007-COMPILED-ENTITIES-GET-DEFAULT-NEED-AND-DRIVE-PROFILES-WITH-VISIBLE-PROVENANCE).

## Acceptance Criteria
- Compile of every data world: zero entities with an undeclared diet (the gate's `undeclared` group is empty); a constructed world with a recipe lacking a species fails to compile with a message naming it.
- Measured alone and paired against main, 5 seeds x 3 worlds, 1500 and 5000 ticks, two-run digests: V1's undeclared group goes to nothing; report what changes for the converted kinds (merchants now use the inn gate, the "prepared" diet, and the human body's other properties: size, edibility; check hero/scout stats do not move: species body only adds properties).
- Divergence entry: a content gap closed before the free-meal removal (named in the step-4 divergence).

## Related Tickets
TCK-20261007-EAT-BESIDE-THE-INN-FEEDS-A-SUBJECT-THAT-CANNOT-PAY-FREE-MEAL (step 4, after this); TCK-20261007-COMPILED-ENTITIES-GET-DEFAULT-NEED-AND-DRIVE-PROFILES-WITH-VISIBLE-PROVENANCE (SURV-05; this is its diet slice); TCK-20261009-RPG-REGRESSION-METRICS-COMPUTED-FROM-TYPED-RECORDS (V1).

## Related Docs
docs/world_rules/life-body/survival-needs.md (SURV-05, SURV-06).

## Related Stored Artifacts
None yet.

## Related Code Areas
data/content/world_modules/*.yaml (population_recipes), src/worldmodules/schema.py, src/worldassembly/resolver.py (the no-archetype branch ~1090), src/worldassembly/entity_spawner.py (_spawn_legacy_guard), src/worldbuilding/compiler.py, src/content/validator.py, src/engine/appraisal.py.

## Assumptions / Open Questions
- Whether the `hero`/`scout` bodies' stats come from the legacy guard's explicit stats (they do) and must stay exactly as they are: the species only supplies `species_id` (diet, edibility, size, power, wits), not stat profiles; to verify with a paired digest before and after, since a species also feeds hunger/need rates (`need_rates`) and perception.
- The legacy guard builds the body with `kind(profile.species_id or "human")`: after the change the kind name of these bodies may move from role-named to species-named; check what reads `entity.kind` (the gate's kind groups read the diet, not the kind).

## Implementation Notes
Built: `PopulationRecipeSpec.species_id` (typed, optional) carried by the resolver to the resolved profile's `species_id` (an unknown species is a ResolverError); `worldbuilding/diet_declaration.py` (`require_declared_diet`, called by the compiler: a body with no species, an unknown species or a body model with no diet is an InvalidWorldSpecError naming world, population, role, faction; a declared empty diet is valid; `require_known_recipe_species` for the resolver); the hero_adventurers, trading_company_hub and scalable_bandit_camp recipes name `human` (the species of the adventurer_hero, traveling_merchant and bandit_scout archetypes; an archetype was NOT used because it also brings its stat profile and inventory); the 14 worlds that use them are re-resolved (`python -m src.worldbuilding.cli resolve <world>`; the report files reorder terrain warnings, the compile_context.json change is the species). The appraisal fallbacks that read "no body or no diet = eats anything" are marked hand-built-only, and a slow corpus test proves no compiled data world reaches them.

Measured (all scratch, pinned governor, audit mode, seeds 42-46, 1500 ticks):
- Compile, 51 converted bodies in 14 worlds, seed 42: every canonical field, stats, inventory and need_rates IDENTICAL to main; only identity.properties.species_id moves (None -> human). The "undeclared" kind group is empty in every data world (it was hero in 10 worlds, merchant in 4, scout in 1).
- Paired runs, main vs branch, 3 worlds x 5 seeds: outcomes (alive, dead, starvation, alive by kind) identical in 9 of 15 (all 5 urban_political, 4 of 5 crowded_frontier); they differ in 6 (crowded_frontier s46 and all 5 frontier_living_world seeds), all worlds with wolves and predators. Starvation 0 in all 30. State digests differ in all 15 (species_id is in the state).
- Ablation, frontier_living_world s46: with the 3 converted merchants built species-less the run equals main exactly (33 alive, 25 dead); re-enabling all readers equals the branch exactly (30 alive, 32 dead). By reader alone: engine/hostility.py 31/30 and engine/appraisal.py 33/27 CHANGE behaviour; legality, serves.keeps_coin, perception signals, tactical_rest, opening_steps and carcass changed nothing in this run. Both are the readers D46/D47/D63 intend (a person's body is seen and judged as a person's); no role or name path found. Per kind (alive, main -> branch): guard 3 -> 2, worker 6 -> 3, blacksmith 1 -> 0, wild_creature 2 -> 3, wolf 0 -> 1; dead 25 -> 32.

## Test Summary
tests/unit/worldbuilding/test_every_compiled_body_has_a_declared_diet.py (6, incl. the slow corpus test); worldbuilding, worldassembly, content, worldmodules, engine and world unit suites pass (1941 non-slow); gates: code health 0 new/0 worse, mypy clean, import contracts 17 kept/0 broken, pin test 339/251.

## Files Changed
src/worldbuilding/{recipe,compiler,diet_declaration}.py; src/worldassembly/resolver.py; src/content/common_knowledge_seed.py (warmed_catalog); src/engine/appraisal.py (comments); data/content/world_modules/{hero_adventurers,trading_company_hub,scalable_bandit_camp}.yaml; data/worlds/*/resolved/* (14 worlds); tests as above and two hand-built profiles that now name a species.

## Completion Summary
TBD

## Designer ruling D74 (SURV-06, memo row 74)

G1 hero_adventurers, G2 trading_company_hub merchants and G3 scalable_bandit_camp scouts each take their role archetype species, `human`; one species per recipe, no distribution, no per-body draw; other species come later as separate recipes. Paired runs with the per-kind cause-of-death split: `agent-working/stored_artifacts/TCK-20261014-EVERY-COMPILED-LIVING-BODY-RESOLVES-TO-A-DECLARED-DIET-OR-THE-WORLD-DOES-NOT-COMPILE/paired_cause_of_death_1500t.tsv`. Divergence 2.120 records the drift (ungraded, untuned).
