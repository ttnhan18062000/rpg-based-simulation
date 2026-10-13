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
OPEN (plan; build when rpg-planner says, measured alone, paired)

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
Measured with compile of all data worlds at seed 42 (kind, species, group): undeclared = hero (species None) in crowded_frontier, frontier_marches, hero_guild_routing and 7 more worlds; merchant in frontier_extended, frontier_living_world, swamp_border_world and 1 more; scout in dungeon_crawl. Declared-empty groups ("none"): guardian/spirit, sentinel/undead.

## Test Summary
TBD

## Files Changed
TBD

## Completion Summary
TBD
