---
status: active
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260808-CORPUS-DENSITY-METRICS-AND-GUIDE
artifact_type: investigation
tags: [simulation-quality, world, corpus]
---

# Investigation — TCK-20260808-CORPUS-DENSITY-METRICS-AND-GUIDE

## Docs Requiring Update

- `docs/world/density_metrics.md`: new technical doc (Implement phase)
- `docs/guides/world_density.md`: new practitioner guide (Implement phase)
- `docs/simulation_quality/corpus_tier_taxonomy.md`: add a pointer to the new density docs
  (Implement phase)

## Data availability check

`config/simulation_quality/corpus_registry.yaml`'s `_worlds` section (20 worlds, built by
`TCK-20260808-SIMQ-CORPUS-WORLD-METADATA-REGISTRY`/`TCK-20260808-CORPUS-REGISTRY-PER-WORLD-VIEW`)
already carries per-world `scale`: `entity_count`, `region_count`, `building_count`,
`resource_node_count`, `quest_count`, `distinct_populated_factions`. Checked directly (not
assumed): all 20 worlds have non-zero `region_count` (min 1) and non-zero `entity_count` (min 6)
— no division-by-zero risk for any ratio metric.

Checked `data/worlds/{name}/resolved/world.resolved.yaml`'s `topology.width`/`.height` for all 20
worlds programmatically — **all 20 present**, no missing/stale resolved specs. The true
area-based metric is safe to compute for the full corpus, not just a subset.

## Metric selection — each with a real, stated purpose, none invented without one

1. **`entity_density_per_area`** = `entity_count / (topology.width * topology.height)`. Purpose:
   "how crowded is this world in absolute space" — the same denominator
   `HighEntityDensityWarningRule` (`WORLD-WARN-002`, `src/worldbuilding/validator.py:202-218`)
   uses for its own `total_pop > map_area * 0.5` warning threshold, so this metric is directly
   comparable to that real, existing validation rule (see the corpus-wide sanity check below).
   Also the same denominator shape as `src/world/spawn.py`'s real runtime monster-density formula
   (`target_count = int((area / 10000.0) * BASE_MONSTER_DENSITY * (1.0 + region.hazard_level))`)
   — the technical doc cross-references both.
2. **`entity_density_per_region`** = `entity_count / region_count`. Purpose: coarser than #1 (no
   area data needed, always available even for a world missing a resolved spec, though none
   currently are) — "how many entities does an average region carry," useful for spotting
   region-count outliers independent of raw map size.
3. **`resource_density`** = `resource_node_count / region_count`. Purpose: reuses the EXACT metric
   already established as a real corpus concept by `TCK-20260805-SIMQ-CORPUS-RESOURCE-DENSITY-
   DECOUPLE` (that ticket's own investigation found "node-per-region density is currently roughly
   flat (1.3-1.75) across the entire corpus" and authored `resource_dense_basin` specifically to
   break that pattern) — not reinvented, the same ratio, now surfaced in the registry instead of
   requiring a one-off `world_compile_report.json` scan.
4. **`quest_density`** = `quest_count / entity_count`. Purpose: reuses the EXACT metric already
   established by `TCK-20260805-SIMQ-CORPUS-QUEST-DENSITY-DECOUPLE` ("quest-def density decoupled
   from entity count") — same ratio, not reinvented.
5. **`faction_density`** = `distinct_populated_factions / region_count`. Purpose: "how factionally
   fragmented is the map" — precedented informally in `crowded_frontier`'s own authoring framing
   (its own registry entry: 6 factions / 4 regions), now made a first-class computed figure
   instead of an ad-hoc observation.
6. **`building_density`** = `building_count / region_count`. Purpose: "how much built
   infrastructure per region" — parallel construction to #3/#5, same real denominator, answers a
   distinct question (economy/service availability, not population or quest availability).

Deliberately NOT computing a single combined "density score" — the ticket's own Request Summary
and this session's own standing methodology (never fabricate a metric without a stated question)
both argue against collapsing 6 distinct real questions into one number.

## Corpus-wide sanity check (real assertion, not assumed)

Computed `entity_density_per_area` for all 20 worlds and compared against
`HighEntityDensityWarningRule`'s own `0.5` threshold:

```
max observed entity_density_per_area across all 20 worlds: 0.00297 (urban_political:
30 entities / 10100 tile area)
min observed: 0.000168 (wilderness_survival: 11 entities / 65536 tile area)
```

Every world's real value is roughly 2 orders of magnitude below the `0.5` warning threshold —
confirms no currently-anchored world breaches `WORLD-WARN-002`, a real, checked assertion (not
assumed true because "it should be"), and becomes a scoped pytest assertion in Implement.

## Cross-reference to `TCK-20260808-WORLDGEN-AREA-AWARE-DENSITY`

That sibling ticket (generation-time density formula for NEW worlds) has not yet landed as of
this ticket's own Implement phase — noted as a forward reference in the technical doc's own
cross-reference section, per this ticket's own Scope item 4, not blocking.
