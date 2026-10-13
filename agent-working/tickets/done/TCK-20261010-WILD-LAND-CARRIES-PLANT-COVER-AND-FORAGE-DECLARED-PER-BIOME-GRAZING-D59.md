---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20261010-WILD-LAND-CARRIES-PLANT-COVER-AND-FORAGE-DECLARED-PER-BIOME-GRAZING-D59
phase: done
date: 2026-10-10
tags: []
---

# TCK-20261010-WILD-LAND-CARRIES-PLANT-COVER-AND-FORAGE-DECLARED-PER-BIOME-GRAZING-D59

## Title
Wild land carries plant cover that a grazing diet eats, and each biome declares its wild food (forage kinds plus fertility band) and grazing cover; camp forage, wild-edge forage and grazing all read the biome (owner memo row 59).

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Lane A's trace (2026-10-10): a plant-eater's ONLY food is berry nodes. frontier_living_world has ONE thicket (10 charges, +1 per 200 ticks) for 6 grazers plus the people, and there's no grass or plant-cover resource, so "graze" (D45) = forage on berries. That's a SURV-06 per-kind-way gap. Owner ruling (memo row 59, via rpg-designer): grazing = LAND COVER PER BIOME. Wild land carries plant cover (grass, browse) that a grazing diet can eat and people's diet can't, by diet and edible class (D46), not a flag. It regrows by the land's fertility band, is depleted by overgrazing, enters by growth and leaves by eating (conservation), from the land, never from nowhere. Food becomes a property of the LAND: each biome declares its wild food (its forage kinds and fertility band) and its grazing cover. Camp forage (D57), wild-edge forage (D35) and grazing read the biome; a module only adds specific features (a named thicket, a den). Coarse bands per D50 (low/medium/high fertility), no named plants.

## Scope
- Content: biome catalog entries declare a fertility band, forage kinds (food class) and grazing cover (food class "graze" or equivalent, in the diet/edible vocabulary of the hunting batch).
- Durable state for cover: engineering's choice of granularity (per region or coarse cell), owned by the land, with a lifecycle of growth by the fertility band and depletion by eating, inspectable via a presenter/debug view, and covered by conservation tests. Ask rpg-planner before adding the state field.
- A GRAZE way: an opening step / forage variant that eats cover where the subject stands or within range (way_in_range for range-bound kinds), via the diet gate.
- Migrate the per-module food lines (wild_edge_forage, the camp forage modules) to biome declarations; modules keep only named features.
- Bible 03 (economy/harvest, conservation), Bible 05 (ecology), SURV-06 evidence, parity entries, a divergence entry.
- Perf: profile the cover growth and grazing lookups (a per-tick cost), and report the tick-time delta pinned and paired.

## Out of Scope
- Spoilage (M3). Individual births (ECOL-03, its own ticket). Meat scale and meat-eater rates (in the hunting batch, owner row 60).

## Acceptance Criteria
- A grazer in a meadow eats cover without competing with people for a thicket; people can't eat cover (diet).
- Cover never goes negative; growth and eating balance from records alone (conservation).
- The validator: every biome a kind is placed in declares food that kind's diet can use, or the gap is reported by name.
- Paired measurement on top of sleep collapse and the need-wake: plant-eater survival, people/plant-eater competition, ways mix. No targets.

## Related Tickets
The hunting batch (rpg-hunting-diet-plant-eater); TCK-20261009-EACH-GOBLIN-AND-ORC-CAMP-HAS-WILD-FOOD-WITHIN-ITS-RANGE-D57 (Lane C; its module lines migrate here); TCK-20261009-PREY-POPULATION-CHANGES-BY-INDIVIDUAL-BIRTHS-AND-DEATHS-ECOL-03; sleep collapse (rpg-sleep-collapse).

## Related Docs
Designer memo rows 57, 59, 60; D33, D35, D45, D46, D50; world rule SURV-06; Bible 03, 05.

## Related Stored Artifacts
Lane A's T2 trace (in the hunting batch's probes).

## Related Code Areas
src/content/schema.py (biome definitions), src/ai/goals/opening_steps.py, the resource and ecology systems, src/engine/appraisal.py (diet), data/content/** biomes and world modules.

## Assumptions / Open Questions
- Lane: Lane A, after the sleep PR and before the hunting batch's re-measure.

## Implementation Notes
PR 1 of the owner-ruled split (the berry-line migration is PR 2, not here). Content: `regrowth_mode`/`bare_wait_ticks`/`fertility`/`density_per_1000_tiles`/`regen_per_check` on ResourceDefinition, `fertility`/`grazing_cover` on biomes, kinds `cover_patch_low|medium|high` (moderate bands, owner 2026-10-11), item `grass_cover` (food class `graze`, 20), plant-eater diet `[plant, graze]`. Code: `src/worldassembly/cover.py` (placement), `economy._record_depletion` (starts the bare wait), `world_dynamics._node_cooldown_updates` (a finished `regrow` wait adds nothing), `appraisal.kind_can_eat_item` (camp food and the need path report count only what a kind eats), validator CAT-COVER-001/002. Disclosed in divergence 2.107: the density-modifier floor, the latent `none`-path overshoot, the held-gatherer defect, the bare wait of berry/herb/wood left to a separate ruling.

## Test Summary
`tests/mechanic_scenarios/test_grazing_on_plant_cover.py` (LB-S22: compile counts, a grazer eats and a person takes none, bare wait then regrowth from zero), `tests/unit/world/test_resource_ecology.py` group D (the regrow lifecycle, canonical form), the camp-food, need-path and wild-food tests re-scoped to a person's food.

## Files Changed
See the branch diff against main.

## Completion Summary
Built as part of the hunting and grazing batch; measured once with hunting (see the batch ticket's artifacts).
