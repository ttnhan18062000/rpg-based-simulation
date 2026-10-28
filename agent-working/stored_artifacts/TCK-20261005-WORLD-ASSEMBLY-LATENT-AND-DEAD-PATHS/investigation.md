---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20261005-WORLD-ASSEMBLY-LATENT-AND-DEAD-PATHS
artifact_type: investigation
tags: [world, investigation]
---

# Investigation

Commit measured: origin/main 3b5fab1e9 (branch base). Raw rows: `latent_paths_results.jsonl`, produced by `latent_paths_probe.py` in this folder over the 24 `data/worlds/*/world.yaml` compositions, through the resolver's own loaders (`load_composition_spec`, `WorldModuleAuthoringNormalizer`, `topological_sort_modules`).

## Sites re-derived (the ticket's lines were taken at 405cbd77b)
- (d) `src/worldassembly/resolver.py` (not `src/worldbuilding/`): `graph_map[ref.module_id] = module` and `ref_by_id[ref.module_id] = ref` in the enabled-refs loop, about L299-306. The claim "a module composed multiple times (e.g. multiple town instances)" is the comment at about L815.
- (e) `src/worldmodules/utils.py`: `if req in modules_map` silently skips a dangling `requires` (L18); the alphabetical zero-in-degree sort overrides the authored order (the `.sort()` calls). `src/worldgeneration/generator.py` still skips a missing `requires` target silently (cited at :513-515 in the mechanisms registry; to be re-checked if that item stays).
- (g) `resolver.py` ASM-COMP-001: loops `composition.module_refs` (about L135) while `graph_map` holds only enabled refs.
- (i) `WorldProceduralGenerator` is `generator.py:59-370`.

## Per-check counts over the 24 compositions
| check | count | worlds |
|---|---|---|
| (d) module id listed twice in `module_refs` | 0 | none |
| (g) ref with `enabled: false` | 0 | none |
| (e) dangling `requires`, absent from the repository | 0 | none |
| (e) dangling `requires`, in the repository but not composed | 2 | wilderness_survival (`wolf_den_near_forest`->`frontier_village_core`, `undead_battlefield`->`frontier_village_core`) |
| (e) refs that set `order` explicitly | 72 of the refs | 11 worlds |
| (e) refs with a non-zero `order` | 61 | 11 worlds |
| (e) authored sequence differs from the executed (topologically sorted) sequence | 14 of 24 worlds | crowded_frontier, frontier_extended, frontier_living_world, frontier_marches, generated_frontier_3_42, hero_guild_routing, highland_traverse, lifecycle_full_coverage_world, quest_dense_frontier, simq_routing_test, simq_scale_stress_seed42, swamp_border_world, urban_political, wilderness_survival |

## Reading
- (d) and (g) stay latent: zero on all 24.
- (e) `order` is NOT latent: it is authored on 72 refs in 11 worlds and the executed sequence differs from the authored one in 14 worlds. Honouring it would change the module merge order of those worlds; whether that changes a resolved world is not yet measured. Under the ticket's rule this item leaves the ticket.
- (e) dangling `requires` is NOT latent either: wilderness_survival composes two modules whose `requires` names a module it does not compose. Each is skipped silently today. Under the ticket's rule this item leaves the ticket.
- (i) is not dead by the ticket's own test: `tests/unit/worldgeneration/test_generator.py` constructs it. `docs/world/generator_contract.md` and parity entries WORLD-GEN-003/004 and SUBSTRATE-NEW-002 record it as an intentionally preserved legacy path. A string-dispatch search found no further reference.

## Experiment: would honouring `order` move resolved worlds? (`order_experiment.py`)
Re-resolving each of the 24 compositions with the topological sort's ties broken by the authored order instead of alphabetically (read-only, monkeypatched, nothing written): the rendered `world.resolved.yaml` text differs in 14 of 24 worlds (the same 14 as the authored-vs-executed list above). So honouring `order` changes resolved worlds; deleting the field would mean editing the `order:` keys in 11 worlds under `data/worlds/`, which the released scope excludes (the schema is `extra="forbid"`).
