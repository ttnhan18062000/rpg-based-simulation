---
status: active
layer: simulation
authority: P2
audience: developer
title: World Density — Practitioner Guide
tags: [simulation-quality, world, corpus]
---

# World Density — Practitioner Guide

**Companion doc:** [`docs/world/density_metrics.md`](../world/density_metrics.md) (formulas,
derivations, real corpus ranges — read that first if you haven't). This guide is the practical
"how do I actually use this" counterpart.
**Ticket:** TCK-20260808-CORPUS-DENSITY-METRICS-AND-GUIDE

---

## Reading an existing world's density figures

Every corpus world's density is already computed — look it up, don't recompute by hand:

```bash
python3 -c "
import yaml
d = yaml.safe_load(open('config/simulation_quality/corpus_registry.yaml'))
print(d['_worlds']['sandbox_world']['density'])
"
```

This prints all 6 metrics (`entity_density_per_area`, `entity_density_per_region`,
`resource_density`, `quest_density`, `faction_density`, `building_density`) for that world,
computed fresh from real `world_compile_report.json` counts and `world.resolved.yaml` topology —
never hand-transcribed, so it's always current as of the last `make simq-corpus-registry` run.

## Computing density for a world you're authoring

If your world hasn't been added to `_WORLD_TIER` / calibrated yet (so it doesn't have a
`_worlds` entry), compute the same 6 ratios by hand using the identical formulas from
`docs/world/density_metrics.md`'s table — you need:

1. `entity_count`, `region_count`, `resource_node_count`, `quest_count`,
   `distinct_populated_factions`, `building_count` — from your world's own
   `world_compile_report.json` (produced by the world-compile step).
2. `topology.width` / `topology.height` — from your world's own `resolved/world.resolved.yaml`
   (only needed for `entity_density_per_area`; the other 5 metrics don't need topology).

Once your world is added to the anchors/calibration corpus and `make simq-corpus-registry` is
re-run, `tools/generate_corpus_registry.py::compute_density()` computes these automatically —
the by-hand computation above is only for a pre-calibration sanity check while authoring.

## Interpreting a value: is it high or low?

There is no universal "good" density — only "unusual relative to the rest of the corpus." Use
`docs/world/density_metrics.md`'s own real observed min/max/mean table as your anchor, not a gut
feeling. A few worked examples from the real corpus (as of 2026-08-08):

- **`resource_dense_basin`** has the corpus's highest `resource_density` (2.33 nodes/region,
  corpus mean 1.41) — this is *intentional*, authored specifically by
  `TCK-20260805-SIMQ-CORPUS-RESOURCE-DENSITY-DECOUPLE` to break the corpus's otherwise-flat
  1.3–1.75 range. If you see a new world land near this figure unintentionally, that's worth a
  second look — it wasn't previously reachable without deliberate authoring.
- **`quest_dense_frontier`** sits at both extremes simultaneously: highest `quest_density` (1.0,
  one quest per entity — corpus mean 0.36) AND lowest `entity_density_per_region`/
  `faction_density`. This is a real, deliberately narrow small-world case — a reminder that a
  world can be an outlier on one axis while being unremarkable, or even the opposite extreme, on
  another. Check the metric that answers YOUR actual question, not just one convenient number.
- **`unit_selfmodel_pilot`** has the corpus's highest `entity_density_per_region` (16.0),
  `faction_density` (3.0), and `building_density` (5.0) all at once — but it's a `unit`-tier
  world with only 1 region, so these ratios are naturally amplified by a tiny denominator. Always
  sanity-check a ratio against its own `region_count` before treating an extreme value as
  meaningful — a `unit`-tier world with `region_count=1` will produce more volatile ratios than an
  `end_to_end` or `stress`-tier world with 8+ regions.

## Spotting an outlier

A quick script to rank all 20 worlds by any one metric:

```bash
python3 -c "
import yaml
d = yaml.safe_load(open('config/simulation_quality/corpus_registry.yaml'))
worlds = d['_worlds']
metric = 'entity_density_per_area'  # swap for any of the 6
ranked = sorted(worlds.items(), key=lambda kv: kv[1]['density'][metric])
for name, w in ranked:
    print(f'{w[\"density\"][metric]:.6f}  {name} (tier={w[\"tier\"]})')
"
```

If a new or modified world lands well outside the existing min/max for a metric you care about
(not just slightly above the mean), that's the signal worth investigating — either it's a
deliberate new stress case (like `resource_dense_basin` above), or an authoring mistake worth a
second look before it's calibrated into the anchors.

## What this guide does NOT cover

- **Live/runtime density** during a simulation run (monster respawn targets, per-tick spawn
  cadence) — that's `src/world/spawn.py`'s own formula, a different, related concept documented
  in [`raid_boss_camp_contract.md`](../world/raid_boss_camp_contract.md), not this static
  world-compile-time registry.
- **Generation-time density-aware population sizing** for brand-new worlds — tracked separately
  by `TCK-20260808-WORLDGEN-AREA-AWARE-DENSITY` (not yet implemented as of this guide's writing).
  This guide is about measuring and reading density for worlds that already exist.
