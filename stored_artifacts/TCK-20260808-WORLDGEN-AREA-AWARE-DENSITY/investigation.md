---
status: active
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260808-WORLDGEN-AREA-AWARE-DENSITY
artifact_type: investigation
tags: [world]
---

# Investigation — TCK-20260808-WORLDGEN-AREA-AWARE-DENSITY

## Docs Requiring Update

- `docs/world/generator_contract.md`: **correction to the original "None expected" note above**
  — checked during Implement (not assumed) and found this doc, not just a read-only reference,
  actually documents the OLD flat formula verbatim (Step 6, lines 150-161: `citizen_count =
  max(5, int(15 × population_scale))` / `monster_count = max(2, int(8 × population_scale))`) and
  the OLD unhardened faction-fallback description (Step 3, lines 115-122). Both are now stale
  relative to this ticket's real code change and must be updated — a WORLD-GEN-004-tagged
  authoritative contract doc, not optional.

## Correction to this ticket's own premise: the faction-reference bug does NOT reproduce with the real default catalog

This ticket's Request Summary states `WorldProceduralGenerator.generate()` "currently fails its
own internal validation" with `InvalidWorldSpecError: ... affiliates with non-existent faction
'town_council'`, per `TCK-20260808-SIMQ-LARGE-SCALE-WORLD-VALIDATION`'s own finding. Re-verified
directly (not trusted from the predecessor ticket's own claim) by instantiating
`WorldProceduralGenerator` exactly as the real test suite does
(`tests/unit/worldgeneration/test_generator.py`) — `CatalogRepository("data/content")` with
`.load_all()` called, `WorldModuleRepository("data/world_modules")` with `.load_all()` called —
and running `.generate()` with a real, non-trivial intent
(`target_world_size=(150,150)`, `population_scale=2.0`, `resource_density=1.0`):

```
SUCCESS, entities: 2
validation issues: {'world_validation': []}
```

Zero validation issues. `data/content/social/factions.yaml` (unmodified this session — confirmed
via `git diff --stat`) genuinely registers `town_council` (alignment_bucket=`defender`) and
`goblin_warband` (alignment_bucket=`invader`), so the real code path that resolves
`civilian_faction`/`hostile_faction` from `self.catalog_repo.factions` (`generator.py:130-136`)
finds real matches and both names end up correctly present in the generated `factions` dict.

**Root-caused the predecessor investigation's actual mistake**: reproduced the exact reported
error by constructing `CatalogRepository("data/content")` WITHOUT calling `.load_all()` — an
easy, plausible slip when directly instantiating outside the test fixture's own `repos()`
pattern, which always calls it. With an unloaded (empty) catalog, `self.catalog_repo.factions` is
`{}`, so `factions` dict (built purely by iterating it, `generator.py:112-115`) stays empty, and
`civilian_faction`/`hostile_faction` fall through to their hardcoded literal defaults
(`"town_council"`/`"goblin_warband"`, `generator.py:127-128`) with nothing to guarantee those
literals are actually present in the (empty) `factions` dict — producing the exact reported
`InvalidWorldSpecError` message, verbatim, confirmed by direct reproduction:

```
FAILED: InvalidWorldSpecError World validation failed: [WORLD-REF-001] Entity population
'citizens' affiliates with non-existent faction 'town_council'; [WORLD-REF-001] Entity population
'monsters' affiliates with non-existent faction 'goblin_warband'
```

**This is a real correction, not a semantic quibble**: the generator is not "confirmed broken" in
its real, currently-used configuration. The 4 existing tests in `test_generator.py` already pass
(confirmed via a fresh run, 4/4). This changes this ticket's own scope — see below.

## A real, latent robustness gap remains (worth fixing, not fabricated)

Even though the bug doesn't reproduce with the shipped `data/content` catalog,
`WorldProceduralGenerator`'s constructor accepts ANY `CatalogRepository` via dependency injection
(`WorldProceduralGenerator(cat, mod)` — a real, supported usage pattern, not a hypothetical one).
The fallback logic at `generator.py:126-136` only guarantees `civilian_faction`/`hostile_faction`
resolve to a real, present-in-`factions` ID when `defenders`/`invaders` (computed from
`alignment_bucket`) are non-empty. Any injected catalog with **zero** `defender`-bucket or
**zero** `invader`-bucket factions (even one with other real factions registered) hits the same
class of dangling reference, reproduced above. This is a genuine, evidenced fragility in
constructor-injected usage, not the originally-claimed default-path bug — worth hardening as part
of this ticket's own Implement phase (small, targeted, not a rewrite), disclosed as a distinct
finding from the (incorrect) original premise.

## `region.area`/`hazard_level` real semantics from `spawn.py`

`src/world/spawn.py:69-74` (`SpawnService`, the real, tested, pipeline-wired runtime respawn
formula — confirmed live and unconditional in earlier sibling ticket work this session):

```python
xmin, ymin, xmax, ymax = region.bounds
area = (xmax - xmin) * (ymax - ymin)
target_count = int((area / 10000.0) * BASE_MONSTER_DENSITY * (1.0 + region.hazard_level))
target_count = max(2, target_count)
```

`BASE_MONSTER_DENSITY = 2.0` (`src/world/spawn_config.py:39`). `region` here is a real
`RegionState` (`src/core/state.py:236-242`): `.bounds: tuple[int,int,int,int]`,
`.hazard_level: float` (0.0-1.0). `WorldProceduralGenerator.generate()`'s own `RegionSpec`
objects use the IDENTICAL field names/shapes (`.bounds`, `.hazard_level`) — a compile-time spec
counterpart of the same real concept, not a different one requiring translation.

## Area basis decision: per-region, not global

`WorldProceduralGenerator` currently carves exactly 3 fixed regions: `town_center` (citizens
spawn here only), `wilderness_forest` (monsters spawn here only — `wilderness_hills` is carved
but never populated, a pre-existing asymmetry, not introduced or fixed by this ticket, out of
scope), `wilderness_hills` (unpopulated). Since citizens and monsters are ALREADY region-scoped
to two specific, distinct regions, a **per-region** area basis (using `town_center`'s own area for
citizen count, `wilderness_forest`'s own area for monster count) is the faithful port of
`spawn.py`'s own per-region scoping — more meaningful than a single global
`target_world_size`-area figure, and directly available since both regions' `RegionSpec` objects
already exist in-scope at the point the population section runs.

## Design: NOT a verbatim mechanical port — a reasoned adaptation, disclosed

Applying `spawn.py`'s exact formula (constant `2.0`, `/10000.0` divisor) verbatim to citizens
would be semantically wrong: that constant is calibrated for wilderness MONSTER respawn
maintenance targets (a handful of creatures per region), not town population sizing. Computed
directly: `town_center`'s default area is 900 (30×30, hardcoded half-width 15 around center, for
the default `target_world_size=(100,100)`); applying the monster formula verbatim gives
`int((900/10000) * 2.0 * 1.0) = 0` → floored to `max(2, 0) = 2` citizens — absurdly low compared
to the current flat formula's `max(5, int(15*1.0)) = 15`.

**Design chosen**: preserve the formula's real *shape* (area-proportional, hazard-modified,
floored) from `spawn.py`, but calibrate NEW area-ratio terms against the existing, currently-
tested default reference point (`target_world_size=(100,100)`, `population_scale=1.0`,
`danger_level=1.0`) so the new formula reproduces the OLD flat formula's exact values at that
default — not inventing an arbitrary new constant, but deriving one from the already-well-tested
default behavior:

- **Citizens**: `pop_count_citizen = max(5, int(15 * intent.population_scale * (town_area / 900)))`.
  `town_area` computed from the real, already-in-scope `regions["town_center"].bounds`. No hazard
  term — `town_center.hazard_level` is hardcoded `0.0` unconditionally at this generator's current
  region-carving (`generator.py:81`), so a `(1+hazard)` multiplier would be permanently inert;
  disclosed explicitly rather than added for cosmetic formula-symmetry with nothing behind it.
  At the default reference point (`town_area=900`), this is exactly `max(5, int(15 * scale))` —
  byte-identical to the current flat formula. Beyond the default, `target_world_size` now
  genuinely affects citizen count (previously fully dead).
- **Monsters**: `pop_count_monster = max(2, int(8 * intent.population_scale * (wild_area / 3366)
  * ((1.0 + wilderness_forest.hazard_level) / (1.0 + 1.2))))`. `wild_area` from
  `regions["wilderness_forest"].bounds`; `3366` and `1.2` are this same region's own real default
  reference-point area/hazard values (computed directly for `target_world_size=(100,100)`,
  `danger_level=1.0` — `hazard_level = 1.2 * danger_level`). At the default reference point, this
  reduces exactly to `max(2, int(8 * scale))` — byte-identical to the current flat formula.
  Beyond the default, BOTH `target_world_size` (area) and `danger_level` (hazard) now genuinely
  affect monster count — `danger_level` was already a real intent field but never factored into
  population before this ticket, an additional real gap this port also closes, consistent with
  `spawn.py`'s own real precedent (danger scales monster presence, not just monster combat
  strength).

## Real finding during Implement: town_center's area doesn't actually vary with `target_world_size`

Confirmed empirically (not assumed) while writing the verification test:
`regions["town_center"]`'s bounds are carved with a **fixed ±15-tile radius around the map
center** (`generator.py`'s own region-allocation step, unrelated to this ticket, out of scope to
change), so `town_area` is a CONSTANT `900` regardless of `target_world_size` — only clipped
smaller near a map edge smaller than 30 tiles. This means the citizen formula's own
`(town_area / _TOWN_REFERENCE_AREA)` term is always `1.0` in practice: **citizen count does not
currently vary with `target_world_size` at all**, only with `population_scale`.
`wilderness_forest`'s own bounds fill "everything left of the town" (`(0, 0, town_min_x - 1,
height - 1)`), so its area DOES genuinely scale with `target_world_size` — monster count responds
correctly.

This is the exact scenario this ticket's own Scope anticipated as an open question ("confirm
whether per-region density is even meaningful at this generator's current region-carving
granularity") — now answered with evidence: per-region density is meaningful for monsters
(wilderness area scales), not currently for citizens (town area is architecturally fixed-size).
Not fixing the town-carving logic itself here — that's a region-layout change, a different,
larger scope than "port the density formula," and the ticket's own Out of Scope doesn't cover it.
The formula itself is still correctly area-aware and forward-compatible: if town-carving is ever
made size-proportional in a future ticket, citizen count will automatically start responding with
zero further formula change needed. Disclosed precisely, not silently worked around — the
verification test asserts this exact behavior (`citizen count unchanged`, `monster count
increases`) rather than forcing a false "both scale" expectation.

## `HighEntityDensityWarningRule` relationship

`WORLD-WARN-002` (`src/worldbuilding/validator.py:202-218`) warns when
`total_pop > map_area * 0.5` (whole-map area, not per-region). Swept the new formula across a
reasonable parameter range (`target_world_size` 50×50 to 250×250, `population_scale` 0.5-3.0,
`danger_level` 0.5-2.0) — real computation, not assumed — confirmed (see test_plan.md) total
population stays orders of magnitude below the 50%-of-map-area threshold across the whole sweep
(worst case: 344 total population at 250×250/scale=3.0/danger=2.0, against a 62500-tile map — a
0.0055 ratio, ~90x below the 0.5 threshold), since population is bounded by the much-smaller
town/wilderness-forest sub-areas, not the full map. An initially-attempted wider sweep (up to
400×400/scale=5.0/danger=3.0) was found to trip a DIFFERENT, unrelated existing validation rule
first (`WORLD-BUDGET-001`, the `local_dev` budget profile's 1000-entity cap) before ever
approaching WORLD-WARN-002's own threshold — narrowed the sweep range to stay within budget so the
test isolates the specific rule this AC is about. Added as a real regression assertion, not just
a one-off check.

## Whether `WorldProceduralGenerator` is worth fixing vs. deprecating

Per this ticket's own Assumptions/Open Questions: not deprecating. The generator is real, tested
(4 passing tests), constructor-injectable, produces valid `WorldSpec` bundles today for its own
default usage — this ticket's real remaining scope (area-term + latent fallback hardening) is a
proportionate, small fix to an already-working component, not a rescue of something broken.
`ProceduralCompositionGenerator` (the CLI-wired generator) remains a separate, distinct component
with its own separate scope, per this ticket's own Out of Scope.
