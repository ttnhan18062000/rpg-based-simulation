---
status: historical
layer: world
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20260915-WORLDBUILDING-DANGLING-REGION-REFERENCE-SILENT-FALLTHROUGH
phase: done
date: 2026-10-05
tags: [world]
---

# investigation — TCK-20260915-WORLDBUILDING-DANGLING-REGION-REFERENCE-SILENT-FALLTHROUGH

## Premise check (the ticket's wording is partly stale)
- **`trade_road` is not a silent fallthrough.** `src/worldassembly/resolver.py` (population step) maps `trade_road` to
  `bandit_road` through `REGION_MIGRATION_MAP`, recorded as `compat_projected` in
  `data/content/compatibility/migration_map.yaml`. It then raises `ResolverError("region", ...)` for any
  `preferred_regions` entry absent from the module's own and required modules' regions. The spawn uses
  `preferred_regions[0]` after mapping, not the next listed preference.
- **Measured:** the resolved `frontier_living_world` places `merchant_caravan_traveling_merchant` and
  `merchant_caravan_frontier_guard` in `bandit_road`, not `hometown`. The ticket's "ends up in `hometown`" is wrong.

## The real defect (not in the ticket's framing)
`WorldCompiler.compile` guards each placement loop with `if region:` and has no `else`
(`src/worldbuilding/compiler.py`, resources / buildings / populations). A `PopulationSpec.spawn_region`,
`ResourceNodeSpec.region` or `BuildingSpec.region` naming an undefined region **drops the whole population, node or
building with no error and no warning**. `WorldSpec.validate_unique_identifiers` checks id uniqueness only, so a
directly authored `WorldSpec` (no assembly) is unguarded.

## Corpus measurement
All 24 `data/worlds/*/resolved/world.resolved.yaml` have 0 dangling placement references (positive control: the
probe reads 16 entities / 10 resources / 8 buildings / 8 regions from `frontier_living_world`).

## Decision: hard error, not warning
- The silent path discards authoritative state, so a report-only warning would still produce a wrong world.
- Cost is nil: 0 of 24 corpus worlds dangle.
- Consistent with the assembly path, which already raises for the equivalent module-level case.
- Quest `required_location_tags` stay warnings (`test_compiler_quest_referential_warnings`) because an unmatched
  tag drops no authoritative state.

## Out of scope / routed
Region bounds overlapping each other is a separate defect, filed by the planner as
`TCK-20261005-REGION-OVERLAP-VALIDATION-FLAG-HAS-NO-READER`.
