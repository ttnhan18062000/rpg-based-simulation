---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260915-WORLDBUILDING-DUPLICATE-REGION-ID-ACROSS-MODULES
phase: done
date: 2026-09-15
tags: [world]
---

# TCK-20260915-WORLDBUILDING-DUPLICATE-REGION-ID-ACROSS-MODULES

## Title
Two world modules composed into the same world (`frontier_village_core`, `trading_company_hub`)
both define a region literally named `"hometown"` with different bounds — unclear whether the
compiler keeps them distinct, merges them, or one silently wins

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
Found while doing a static world-spec comparison for
`TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION`. `frontier_living_world`'s composition
includes both `frontier_village_core` (defines region `"hometown"`,
`grid_bounds: [10, 10, 40, 40]`) and `trading_company_hub` (defines region `"hometown"`,
`grid_bounds: [45, 10, 80, 45]`) — **two distinct region definitions sharing the same literal id**,
with materially different bounds (one in the map's far corner, the other overlapping
`bandit_road_trade_pressure`'s own `"bandit_road"` region and much closer to
`goblin_camp_conflict`'s `"goblin_camp"`).

It is not known from the content specs alone what `WorldCompiler` actually does when two modules
in one composition define the same region id: keep both as separate regions (in which case, which
one do entities from each module's own `population_recipes`/`spawn_region: "hometown"` actually
resolve to?), silently let the later-loaded module's definition override the earlier one (which
would relocate `frontier_village_core`'s own population, not just `trading_company_hub`'s), or
something else. This is a real question about durable world state — the answer determines whether
entities from two different modules end up in the same physical place or in two different ones
with the same name, which materially affects spatial-proximity-dependent mechanics (combat
engagement radius, region-scoped effects, etc.).

## Scope
- Read `WorldCompiler`'s own region-composition logic to determine, definitively, what currently
  happens when two composed modules define the same region id. Do not guess from the specs alone.
- Determine whether this is: (a) intentional behavior with a real resolution rule that just isn't
  obvious from reading the module YAMLs, (b) an unintentional but harmless collision (e.g. never
  actually occurs in a way that matters because nothing currently composes two same-named-region
  modules where it changes real behavior), or (c) a real bug producing incorrect entity placement.
- If (c): scope a fix — likely either requiring module authors to namespace region ids uniquely
  per module (a compile-time validation, similar in spirit to
  `TCK-20260915-WORLDBUILDING-DANGLING-REGION-REFERENCE-SILENT-FALLTHROUGH`'s own dangling-
  reference check), or an explicit, documented merge/override rule if same-named regions across
  modules are meant to compose (e.g. a hub town multiple modules all contribute population to).
- Audit whether other world compositions in the corpus have the same same-name-different-bounds
  collision, once the actual compiler behavior is understood.

## Out of Scope
- `TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION`'s own remaining scope — filed as its
  own defect, independent of whether it turns out to matter for that investigation's outcome.
- `TCK-20260915-WORLDBUILDING-DANGLING-REGION-REFERENCE-SILENT-FALLTHROUGH` (sibling ticket) — a
  related but distinct defect (a reference to a region that doesn't exist at all, not two regions
  sharing one name).

## Acceptance Criteria
- A definitive, evidence-backed statement of what `WorldCompiler` actually does with duplicate
  region ids across composed modules — not assumed from the specs.
- If it's a real bug: a scoped, reviewed fix (module-author-facing validation, or an explicit
  compose rule) — not built until the actual behavior is confirmed.
- If it's intentional/harmless: documented as such somewhere durable (this ticket's own closure,
  or a relevant doc), so the next person who notices this pattern doesn't re-investigate it from
  scratch.

## Related Tickets
- `TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION` (surfaced this while doing a static
  world-spec comparison)
- `TCK-20260915-WORLDBUILDING-DANGLING-REGION-REFERENCE-SILENT-FALLTHROUGH` (sibling — the other
  region-composition defect found in the same trace)

## Related Docs
_(none — no existing doc covers module composition's region-merge behavior yet)_

## Related Stored Artifacts
_(none yet — filed as a finding, not yet investigated)_

## Related Code Areas
- `data/content/world_modules/frontier_village_core.yaml` (`"hometown"`, `[10,10,40,40]`)
- `data/content/world_modules/trading_company_hub.yaml` (`"hometown"`, `[45,10,80,45]`)
- `src/worldbuilding/compiler.py::WorldCompiler` (the actual region-composition/merge logic)

## Assumptions / Open Questions
- Not yet known which of the three scenarios in Scope (intentional, harmless collision, or real
  bug) describes the actual current behavior — read the compiler before assuming.

## Implementation Notes
Disposition close — no code change. Scenario (a) of Scope: intentional behaviour with a real resolution rule.

- **Composition path** (`src/worldassembly/resolver.py` ~L345-360): each module ref's `namespace` becomes a
  `<namespace>_` prefix applied to that module's region ids *before* the merge. If two modules still contribute the
  same id, the merge raises `ValueError("Duplicate region ID collision '<id>' detected during assembly merge.")`.
  Nothing is merged, overridden, or silently won.
- **Direct `WorldSpec` path** (`src/worldbuilding/schema.py` ~L316-319): `validate_unique_identifiers` raises
  `Duplicate region ID found: '<id>'`.
- **The ticket's own example is resolved by authoring**, not by a collision: `data/worlds/frontier_living_world/world.yaml`
  composes `trading_company_hub` with `namespace: "trading"`, so the resolved world holds two distinct regions,
  `hometown` (`frontier_village_core`) and `trading_hometown` (`trading_company_hub`) — see
  `data/worlds/frontier_living_world/resolved/world.resolved.yaml`.
- **Corpus audit:** assembled all 24 `data/worlds/*/world.yaml` compositions with `WorldAssemblyResolver` against the
  real catalog and module repository (`load_all()` on both): 24 assembled, 0 collisions. The generator-side
  authoring of colliding compositions was already fixed by `_assign_region_namespaces`
  (`TCK-20261004-GENERATOR-AUTHORS-UNASSEMBLABLE-COMPOSITION-ON-REGION-ID-COLLISION`, #335).
- **Probe check:** a first audit run used the repositories without `load_all()` and reported 0/24 assembled
  ("module not found"), which showed the probe discriminates; the corrected run is the one reported above.
- **Known doc gap, not fixed here:** `docs/world/assembly_contract.md` documents the quest-id collision
  (`AssemblyCollisionError`) but not the region-id collision or the namespace-prefix rule. Handed to the planner as
  exact text rather than edited by me.

## Test Summary
No new tests: both fail-fast paths already have them and the corpus audit above is the new evidence.
- `tests/unit/worldassembly/test_assembly.py` (un-namespaced `hometown` across two modules raises
  `Duplicate region ID collision 'hometown' detected`)
- `tests/unit/worldbuilding/test_worldspec_schema.py` (`Duplicate region ID` on a direct `WorldSpec`)

## Files Changed
Ticket only (`todos/` -> `done/`); no source, test, or doc change.

## Completion Summary
Definitive answer: duplicate region ids across composed modules are never merged or overridden. A module author
disambiguates with `namespace` on the module ref; an un-namespaced duplicate is a fatal, tested error at assembly
time, and a duplicate inside one `WorldSpec` is a fatal, tested validation error. The frontier composition the ticket
cited uses `namespace: "trading"` and resolves to `hometown` + `trading_hometown`. All 24 corpus compositions
assemble. Remaining gap is documentation in `docs/world/assembly_contract.md`, routed to the planner.

## Disposition
STALE-PREMISE

## Disposition Rationale
The ticket's premise was that duplicate region ids across composed modules might merge, or one silently win. Neither
happens: `src/worldassembly/resolver.py:359` raises `ValueError("Duplicate region ID collision ...")` on an
un-namespaced duplicate, and `src/worldbuilding/schema.py:319` raises `Duplicate region ID found` inside one
`WorldSpec`. The cited example is authored apart: `data/worlds/frontier_living_world/world.yaml` gives
`trading_company_hub` `namespace: "trading"`, so the resolved world has `hometown` and `trading_hometown`. Corpus
audit through `WorldAssemblyResolver` (catalog and module repository `load_all()`ed): `24 0 0` (assembled, failed,
skipped) across all `data/worlds/*/world.yaml`.
