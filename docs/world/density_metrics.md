---
status: active
layer: simulation
authority: P2
audience: developer
last_verified: 2026-08-08
---

# World Density Metrics

**Source:** `tools/generate_corpus_registry.py` (`compute_density`)
**Data:** `config/simulation_quality/corpus_registry.yaml`'s `_worlds.<world_name>.density`
**Related docs:** [raid_boss_camp_contract.md](raid_boss_camp_contract.md) (runtime density
precedent), [docs/simulation_quality/corpus_tier_taxonomy.md](../simulation_quality/corpus_tier_taxonomy.md)
**Ticket:** TCK-20260808-CORPUS-DENSITY-METRICS-AND-GUIDE
**See also:** [../guides/world_density.md](../guides/world_density.md) for practical usage

---

## Why multiple metrics, not one

"How dense is this world?" is not one question. An author asking "will entities feel crowded on
this map" needs a different answer than one asking "does this world have enough quests per
entity to sustain progression." Collapsing these into a single composite score would hide which
specific dimension is unusual about a given world. Each metric below computes one real ratio,
answers one real question, and none was added without a stated purpose — see
`stored_artifacts/TCK-20260808-CORPUS-DENSITY-METRICS-AND-GUIDE/investigation.md` for the
selection reasoning.

## The 6 metrics

All 6 are computed once per unique world by `compute_density()`
(`tools/generate_corpus_registry.py`) from real `world_compile_report.json` counts (via the
`_worlds` scale sub-object) and real `world.resolved.yaml` topology — never hand-transcribed.

| Metric | Formula | Question it answers |
|---|---|---|
| `entity_density_per_area` | `entity_count / (topology.width * topology.height)` | How crowded is this world in absolute map space? |
| `entity_density_per_region` | `entity_count / region_count` | How many entities does an average region carry, independent of raw map size? |
| `resource_density` | `resource_node_count / region_count` | How resource-rich is an average region? |
| `quest_density` | `quest_count / entity_count` | Is there enough quest content per entity to sustain progression? |
| `faction_density` | `distinct_populated_factions / region_count` | How factionally fragmented is the map? |
| `building_density` | `building_count / region_count` | How much built infrastructure (services) does an average region have? |

## Cross-references to real engine mechanics

**`entity_density_per_area`** uses the exact same denominator (`topology.width *
topology.height`) as `HighEntityDensityWarningRule` (`WORLD-WARN-002`,
`src/worldbuilding/validator.py:202-218`), which warns at generation-validation time when
`total_pop > map_area * 0.5`. This makes the two directly comparable: a world's
`entity_density_per_area` value is exactly the ratio that rule checks against `0.5`. The same
denominator shape also appears in `src/world/spawn.py`'s real runtime monster-respawn density
formula (`target_count = int((area / 10000.0) * BASE_MONSTER_DENSITY * (1.0 +
region.hazard_level))`, per-region rather than whole-map, and floored at a minimum of 2 monsters
per active region) — see [raid_boss_camp_contract.md](raid_boss_camp_contract.md) for the full
runtime contract. `entity_density_per_area` is a **static, whole-world snapshot** at
world-compile time; `spawn.py`'s formula is a **live, per-region, per-tick** respawn target — related
concepts, not the same computation.

**`resource_density`** and **`quest_density`** are not new inventions — they reuse the exact
metric definitions already established by `TCK-20260805-SIMQ-CORPUS-RESOURCE-DENSITY-DECOUPLE`
("node-per-region density") and `TCK-20260805-SIMQ-CORPUS-QUEST-DENSITY-DECOUPLE` ("quest-def
density decoupled from entity count"). Those tickets computed these ratios by hand from
`world_compile_report.json` scans; this doc's registry extension makes them a standing, always-
current figure instead of a one-off measurement.

## Real corpus-observed ranges (as of 2026-08-08, 20 worlds)

| Metric | Min (world) | Max (world) | Mean |
|---|---|---|---|
| `entity_density_per_area` | 0.000168 (`wilderness_survival`) | 0.00297 (`urban_political`) | 0.0017 |
| `entity_density_per_region` | 2.0 (`quest_dense_frontier`) | 16.0 (`unit_selfmodel_pilot`) | 7.90 |
| `resource_density` | 0.6 (`highland_traverse`) | 2.33 (`resource_dense_basin`) | 1.41 |
| `quest_density` | 0.1875 (`unit_information_density`) | 1.0 (`quest_dense_frontier`) | 0.36 |
| `faction_density` | 0.33 (`quest_dense_frontier`) | 3.0 (`unit_selfmodel_pilot`) | 1.29 |
| `building_density` | 0.25 (`dungeon_crawl`) | 5.0 (`unit_selfmodel_pilot`) | 1.72 |

Every world's real `entity_density_per_area` sits roughly 2 orders of magnitude below
`HighEntityDensityWarningRule`'s own `0.5` warning threshold — checked directly (not assumed) and
enforced as a real regression assertion (`tests/tools/test_corpus_registry.py::
test_no_world_breaches_high_entity_density_warning_threshold`).

## Forward reference

`TCK-20260808-WORLDGEN-AREA-AWARE-DENSITY` (filed alongside this ticket, not yet implemented as
of this doc's writing) addresses a related but distinct gap: `entity_density_per_area` here
*measures* an already-generated world's density after the fact; that ticket's own scope is
*generation-time* population sizing with an area term, since the current initial-generation
population formula (`src/worldgeneration/generator.py`) has none. The two are complementary, not
duplicative — this doc's metrics are a good acceptance-check target for that ticket's own future
work, once it lands.
