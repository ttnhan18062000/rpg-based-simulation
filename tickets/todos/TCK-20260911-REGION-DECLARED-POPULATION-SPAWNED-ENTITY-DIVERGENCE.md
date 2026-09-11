---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260911-REGION-DECLARED-POPULATION-SPAWNED-ENTITY-DIVERGENCE
phase: open
date: 2026-09-11
tags: [world, architecture, simulation-quality]
---

# TCK-20260911-REGION-DECLARED-POPULATION-SPAWNED-ENTITY-DIVERGENCE

## Title
`RegionState.population_cohorts` (declared population, feeds real demographics/migration/camp
logic) and `WorldEntitySpawner`'s actually-spawned entity count diverge whenever `PopulationSpec.count != 1`

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Found while designing the fix for `TCK-20260909-WORLD-ENTITY-SPAWNER-POSITION-RESOLUTION` (per
`rpg-feature-planning`'s review of that ticket's proposed approach — this is Finding 8 of that
investigation, filed as its own ticket rather than left as a footnote).

`WorldAssemblyResolver.resolve_module_contribution()` (`src/worldassembly/resolver.py:889-907`)
resolves each expanded archetype into exactly **one** `PopulationSpec` per (archetype, region)
combination, carrying `count: int` as a declared field:
```python
resolved_population_specs.append(PopulationSpec(
    id=f"{prefix}{pop_key}",
    count=count,
    ...
))
```
`WorldEntitySpawner.spawn_from_context()` (`src/worldassembly/entity_spawner.py:54-65`) then spawns
exactly **one** `EntityState` per `ctx.entities` dict entry — `count` is never read anywhere in
`ResolvedEntityProfile` (`src/worldassembly/models.py`, which has no `count` field at all) or in the
spawner's own loop. Confirmed structurally, not assumed: a population authored with `count=40`
produces exactly 1 spawned, individually-tracked `EntityState`.

Meanwhile `WorldCompiler.compile()` (`src/worldbuilding/compiler.py:267-277`) independently sums the
same `PopulationSpec.count` values per `spawn_region` into `region_declared_population`, and seeds
`RegionState.population_cohorts` from that sum via `_seed_population_cohorts()`
(`compiler.py:190-209`, `compiler.py:362`). The code's own comment (`compiler.py:270-272`) already
establishes that **multiple populations sharing one `spawn_region` is a normal, expected case**
("this must sum, not overwrite"), not an edge case.

**`population_cohorts` is not inert metadata — it drives real, live production logic:**
- `src/domains/demographics/cohort.py` — the full demographic migration cycle: scarcity-driven
  emigration keyed on `migration_threshold` (line 268), birth/mortality processing, and
  `total_pop = sum(c.count for c in region.population_cohorts.values())` (line 153).
- `src/world/camp.py:148-150` and `src/world/reproduction_humanoid.py:68-70` — both read
  `region.population_cohorts.get("young").migration_threshold` as a real gating condition.
- `src/engine/apply_plan.py:124-151` — applies `population_cohorts_set` updates through the
  authoritative mutation pipeline every tick.

So a region's **declared** population (what demographics/migration/camp logic reasons about) and its
**actual spawned entity count** (what combat/social systems and `WorldEntitySpawner`'s own consumers
see) are two independently-tracked numbers that can diverge arbitrarily — and do, for any
`count != 1` population or any region with more than one population group. This was not visible
before `TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING` made `WorldEntitySpawner` a live,
non-test-only consumer.

## Scope
- Determine whether this divergence is **intentional** (i.e. `population_cohorts` is meant to model
  an abstract, unnamed "background population" distinct from named/individually-tracked spawned
  entities — a legitimate and common simulation pattern) or **accidental** (someone expected spawned
  entity count to eventually match declared count and the gap was never closed). Investigate git
  history / design docs for `population_cohorts` and `WorldEntitySpawner` before concluding either
  way — do not assume.
- If accidental: decide and implement the correct fix — options include (a) expanding
  `PopulationSpec.count` into `count` individually-spawned entities (interacts directly with
  `TCK-20260909-WORLD-ENTITY-SPAWNER-POSITION-RESOLUTION`'s own per-entity position work, since each
  expanded individual would need its own position too — check that ticket's landed state before
  starting), or (b) deriving `region_declared_population` from the actual spawned entity count
  instead of `PopulationSpec.count` once (a) exists, or (c) some other reconciliation.
- If intentional: document the split explicitly (a docs update, likely
  `docs/world/assembly_contract.md` or `docs/mechanics/`) so the next investigator doesn't
  rediscover this as a suspected bug, and confirm the demographics/camp/reproduction consumers listed
  above are correctly reasoning about the *declared* (not spawned) population by design.

## Out of Scope
- `TCK-20260909-WORLD-ENTITY-SPAWNER-POSITION-RESOLUTION`'s own scope (per-entity spatial placement)
  — related, may share groundwork if the resolution here is "expand count into individuals," but this
  ticket is about the declared-vs-spawned population *count* divergence, not spatial placement.
- Any change to `_seed_population_cohorts()`'s own young/adult/elder apportionment math (Hamilton
  apportionment, `_YOUNG_ADULT_ELDER_RATIO`) — out of scope unless the Scope investigation concludes
  the sourcing input itself (not the apportionment) needs to change.

## Acceptance Criteria
- [ ] An explicit, evidence-based determination (intentional vs. accidental) is recorded, not
      assumed.
- [ ] If accidental: implemented per the chosen option above, with real test coverage showing
      declared and spawned counts reconcile (or a documented, deliberate exception).
- [ ] If intentional: documented explicitly in the relevant doc, with the demographics/camp/
      reproduction consumers confirmed correct under that documented design.
- [ ] No regression in `tests/integration/worldassembly/`, `tests/unit/domains/campaigns/`,
      `tests/integration/campaigns/`, `tests/unit/domains/demographics/` (or equivalent).

## Related Tickets
- `TCK-20260909-WORLD-ENTITY-SPAWNER-POSITION-RESOLUTION` (sibling finding from the same
  investigation; both trace back through `PopulationSpec`/`WorldEntitySpawner`)
- `TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING` (made `WorldEntitySpawner` a live consumer,
  surfacing this divergence's real-world relevance for the first time)
- `TCK-20260909-UNREACHABLE-IMPLEMENTED-CODE-AUDIT` (adjacent pattern — implemented-but-diverged
  state, not implemented-but-unreachable code; related family of findings from the same batch)

## Related Docs
- `docs/world/assembly_contract.md`
- `docs/mechanics/` (demographics/population mechanics, if documented there)

## Related Stored Artifacts
None yet — created when this ticket is picked up.

## Related Code Areas
- `src/worldassembly/resolver.py` (`resolve_module_contribution()`, where `PopulationSpec.count` is
  set but not expanded)
- `src/worldassembly/entity_spawner.py` (`WorldEntitySpawner.spawn_from_context()`, spawns 1 entity
  per `ctx.entities` key regardless of `count`)
- `src/worldassembly/models.py` (`ResolvedEntityProfile` — has no `count` field)
- `src/worldbuilding/compiler.py` (`region_declared_population` aggregation, `_seed_population_cohorts()`)
- `src/domains/demographics/cohort.py`, `src/world/camp.py`, `src/world/reproduction_humanoid.py`
  (real consumers of `population_cohorts`)

## Assumptions / Open Questions
- Whether `population_cohorts` was ever intended to track named/spawned entities at all, or has
  always been a deliberately-abstract background-population model — not determined here, this is
  exactly what Investigate must establish first.

## Implementation Notes
_(pending — filed, not yet picked up)_

## Test Summary
_(pending)_

## Files Changed
_(pending)_

## Completion Summary
_(pending)_
