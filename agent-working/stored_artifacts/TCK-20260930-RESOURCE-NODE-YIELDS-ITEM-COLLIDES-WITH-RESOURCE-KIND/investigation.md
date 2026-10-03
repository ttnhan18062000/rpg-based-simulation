---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260930-RESOURCE-NODE-YIELDS-ITEM-COLLIDES-WITH-RESOURCE-KIND
artifact_type: investigation
tags: [world]
---

# Investigation — TCK-20260930-RESOURCE-NODE-YIELDS-ITEM-COLLIDES-WITH-RESOURCE-KIND

## Root cause
`resource_type` means "resource kind" in module authoring (`herb_patch`) and was read as "item to yield" at
`src/worldbuilding/compiler.py` (step 4, compile resources): `yields_item=res_spec.resource_type`. The correct
resolution (`runtime_kind or resource_type` of the catalog resource definition -> `herb`) already existed at
`src/core/registries.py` (`CatalogToResourceRegistryAdapter`) and `src/world/ecology.py`, which is why ecology-spawned
nodes were right and compile-time nodes were wrong.

## Where the right value already lives
`WorldResolver` already calls `repo.get_resource(res_spec.resource_type)` to fill `required_ticks`. Recording
`yield_item` on `ResolvedResourceProfile` there puts the resolution beside the existing one, and the compiler just
consumes the context. Chosen over a local mapping in the compiler because that would duplicate the catalog rule a
third time, and over patching `frontier_village_core.yaml`, which fixes one symptom and leaves the collision for the
next module author. No-context compiles (e.g. `test_population_stability`, which calls `load_world` + `compile(spec, seed)`
with no context) fall back to `ResourceRegistry`.

## wood_node / iron_vein
Same static shape; fixed by the same change. Compiled nodes now yield `wood` / `iron_ore` (verified per node in the
probe output and pinned by test). Not measured to be *harvested* in the sampled 400-600 tick windows (no entity
completed a wood or iron harvest there), so "fixed and statically verified", not "observed completing".
`ResourceNodeState.kind` is a resource kind and was correct; unchanged.

## Measurement (production loader, real Kernel, PROD_SMALL, seed 42; same probe both sides)
Probe: `WorldRepository.load_world_with_context` + `WorldCompiler.compile`, `Kernel.tick_once`, wrapping
`src.core.items.ItemRegistry.get` (positive control: a bogus id incremented the counter before reset); harvest = sum of
`max_charges - remaining_charges` by node kind at end, cross-checked against item totals in inventories.
| world (ticks) | before: misses | before: charges spent / herb held | after: misses | after: charges spent / herb held |
|---|---|---|---|---|
| frontier_living_world (600) | 104 | 0 / 0 | 0 | 5 / 5 |
| crowded_frontier (400) | 72 | 0 / 0 | 0 | 5 / 5 |
| quest_dense_frontier (400) | 0 | 0 / 0 | 0 | 0 / 0 |
Probe conditions matter: the same probe with `flags={}` gave 134 / 69 before; the ticket's own earlier harness gave
109 / 45. Counts vary run to run (wall-clock tick-budget aborts), so the robust claim is nonzero -> zero, not any one
number. The presence claim is stronger than the absence claim: 0 -> 5 harvested herb in both worlds, charges and
inventory agreeing.

## Behaviour shift (not neutral)
Herb harvesting completes for the first time. Corpus baselines taken before this batch are not comparable to ones
taken after. Slow-tier SimQ anchor check: 16 `test_corpus_diversity.py` tests fail with the fix; the same 16 on
untouched origin/main 73cbf116b: 11 fail too (pre-existing). Of the 5 that failed only with the fix, re-run alone: 2 pass;
`urban_political_seed123_500t` is a per-test TimeoutError; `frontier_marches` population_stability is noise
(5 trials each, fix tree final alive 46/36/47/41/43, untouched main 42/46/47/36/39, both straddling the 37.2 floor);
ONE is a real, tight, upward shift: `unit_selfmodel_pilot_seed42_1000t` ECONOMY 0.1465 -> ~0.287 (0.2886/0.2841/0.2886),
NARRATIVE 0.0 -> ~0.05 (marginal). Re-baseline deferred to its own ticket (regression_policy.md 9-11); anchors not edited.
