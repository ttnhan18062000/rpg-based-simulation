---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260911-CAMPAIGN-SURVIVOR-RECONSTRUCTION-POSITION-COLLISION
phase: open
date: 2026-09-11
tags: [world, architecture, simulation-quality]
---

# TCK-20260911-CAMPAIGN-SURVIVOR-RECONSTRUCTION-POSITION-COLLISION

## Title
`CampaignOrchestrator._build_initial_state()`'s survivor-reconstruction branch places every
surviving entity at the identical `(0.0, 0.0)` default position — the other half of the position
gap `TCK-20260909-WORLD-ENTITY-SPAWNER-POSITION-RESOLUTION` fixed, never exercisable until now

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Found while re-verifying grief/nemesis event reachability
(`TCK-20260909-GRIEF-NEMESIS-CAMPAIGN-REVERIFICATION`) in a real multi-episode Campaign run.
`CampaignOrchestrator._build_initial_state()` has two branches: the episode-0/no-survivors branch
(catalog-native spawn via `WorldEntitySpawner`, which now gets real, de-conflicted positions per
`TCK-20260909-WORLD-ENTITY-SPAWNER-POSITION-RESOLUTION`) and the survivor-reconstruction branch
(episode N>0 with alive carry-forwards), which builds `EntityState` objects directly from
`EntityCarryForward` snapshots (`orchestrator.py:733-772`) and **never touches the catalog spawn
pipeline at all**. Every reconstructed survivor gets `EntityState(id=eid, kind="entity")`'s own
bare dataclass default position, `(0.0, 0.0)` — identical for every survivor, unconditionally.

**The existing comment describing this is actively misleading, not just silent.**
`orchestrator.py:733-736` reads: *"Fields not captured in EntityCarryForward (e.g. combat state,
position, current HP) are left at EntityState defaults — the scenario's `setup_tags` and
`world_composition` govern spawn placement."* The second clause is false for this branch: this
code path never calls into `WorldEntitySpawner`/`WorldCompiler.compile()`'s own entity placement
at all — nothing about `world_composition` governs survivor placement. A confident comment
describing a mechanism that doesn't actually run for this code path — the same shape as the
`invalidate_read_model` comment that sent an earlier investigation (part of this same session's
Dormant Mechanism Closure epic) to the wrong consumer. Do not trust it; correct or remove it as
part of this fix.

**Confirmed at real scale, not a 2-entity edge case.** A real 150-tick `frontier_living_world`
episode 0 (post `TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING` +
`TCK-20260909-WORLD-ENTITY-SPAWNER-POSITION-RESOLUTION`) ended with 13 of 16 entities alive. All
13 reconstructed at the identical `(0.0, 0.0)` position in episode 1's initial state — confirmed
directly by inspecting `_build_initial_state()`'s own returned state. This trips a real
`LAW-SPAWN-OCCUPANCY` hard-law violation and derails the episode almost immediately (observed:
episode 1 and episode 2 both stalled at ~tick 52, close to `STALL_THRESHOLD=50`, versus episode
0's clean 150-tick completion).

**Why this was never seen before.** Campaign mode ran with zero entities in every episode until
`TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING` landed (this same follow-up batch). With zero
entities, there were never any survivors, so this branch's own position defaulting was never
exercised with real multi-entity data — the documented "known limitation" comment predates any
run that could have shown its real consequence. This is the sibling finding to
`TCK-20260909-WORLD-ENTITY-SPAWNER-POSITION-RESOLUTION`: that ticket fixed the episode-0 catalog
path; this is the other half (the survivor-reconstruction path), reachable only once the first was
fixed and real survivors started existing.

## Scope
- ~~Design real position resolution... reuse `_hash_point_in_bounds`/`_resolve_spawn_position`...~~
  **Superseded by pre-implementation investigation (2026-09-11) — see Assumptions/Open Questions.**
  `_resolve_spawn_position()` is not directly reusable: it requires a `spawn_region` string, and no
  survivor has one (`spawn_region` never reaches the live entity at all — see
  `TCK-20260911-ENTITYSPAWNCONTEXT-SPAWN-REGION-THREADING-GAP`, filed from this finding). The real
  fix: add `EntityCarryForward.last_position: Optional[Tuple[float, float]]`, populate it at
  extraction time from `entity.navigation.position` (the entity's real position when the episode
  ended), and reuse it at reconstruction — with a **validity check and fallback**, not a bare
  carry-through, since per-tile terrain/`blocked_tiles` are redrawn per episode's own seeded RNG
  even though region bounds stay authored/stable (confirmed: `compiler.py`'s `rng.weighted_choice`
  over `terrain_variants` and `rng.get_int(...)` for building placement both use
  `episode_seed = base_seed + episode_index`, different every episode). A carried position may land
  within its region's bounds but on now-blocked terrain — `blocked_tiles` is a real legality gate
  (`src/engine/legality.py:70-76`), not cosmetic. Deconfliction against *other* survivors can reuse
  `_DECONFLICT_PROBE_OFFSETS` directly (no region-bounds machinery needed for that part).
- **Corrected again (2026-09-11), per peer review, before implementation — locking in the real
  validity-check shape:**
  - `blocked_tiles` is one of three static gates checked by legality, not the gate.
    `LegalityServiceV2.verify_occupancy(pos, state_or_context, ignore_entity_id=None)`
    (`src/engine/legality.py:53-116`) already checks WALL terrain (`state.terrain`), `blocked_tiles`,
    buildings (`building_tiles`/`buildings`), transient claims, and dynamic entity occupancy —
    duck-typed on `state_or_context: Any` via `getattr`, so it accepts anything shaped enough like
    `AuthoritativeState` (terrain/blocked_tiles/buildings/entities). **Call this directly rather
    than hand-rolling a fourth copy of occupancy rules** — a private reimplementation is exactly the
    parallel-implementation pattern this whole batch has been deleting, and it would drift the first
    time someone adds a fourth gate to the real one. Confirmed during this investigation that its
    signature fits the reconstruction context cleanly (pass a context carrying `compiled_state`'s
    `terrain`/`blocked_tiles`/`buildings` plus the `entities` dict being incrementally built in the
    same reconstruction loop, for survivor-vs-survivor occupancy).
  - **One authority for entity-vs-entity collision, not two.** `verify_occupancy()`'s own "Dynamic
    Entities" branch already rejects an occupied tile by scanning the passed context's `.entities`
    — a separate claimed-set duplicates that rule. **Drop the claimed-set; `verify_occupancy()` is
    the single authority**, per peer review. But its dynamic-entity check has 3 sub-paths with
    different staleness behavior, and only one is safe to rely on across a reconstruction loop that
    mutates `.entities` in place on a *reused* context object:
    1. `state_or_context.occupancy_snapshot` if present/non-`None` — skip by never declaring this
       attribute on the reconstruction context.
    2. else `SpatialQueryService.get_occupancy_map(state_or_context)` — **dangerous**: it caches its
       result onto the context object itself via `object.__setattr__(state, "_occupancy_map_cache",
       mapping)`, keyed only by object identity, with no invalidation. Reusing one context object
       across the survivor loop would cache the occupancy map from whichever `.entities` state
       existed at the *first* call and silently return that stale map on every later call — **this
       was directly reproduced**, not just reasoned about: a plain context object's second
       `verify_occupancy()` call, checking a tile occupied by an entity added after the first call,
       returned `True`/`LEGAL` — a silently-approved occupied tile.
    3. else, on `AttributeError`/`TypeError` from path 2, a **direct, uncached scan of
       `.entities`** — the only path that reflects the dict as currently mutated.
    **Force path 3 deterministically**: define the reconstruction context as a `__slots__`-only
    class exposing exactly `terrain`, `blocked_tiles`, `buildings`, `building_tiles`,
    `transient_claims`, `entities` — no `occupancy_snapshot` slot (skips path 1), and no free
    attribute slot for `get_occupancy_map`'s `object.__setattr__(..., "_occupancy_map_cache", ...)`
    to land in, so that call raises `AttributeError`, propagates out of `get_occupancy_map`, and is
    caught by `verify_occupancy()`'s own `except (AttributeError, TypeError)` — landing on path 3
    every single call, regardless of whether the same context object is reused across the whole
    loop. **Verified directly** (not assumed): a `__slots__`-restricted context correctly rejected a
    tile occupied by an entity added to `.entities` *between* two `verify_occupancy()` calls on the
    *same* object, with `_occupancy_map_cache` never successfully written (confirmed via
    `getattr(ctx, "_occupancy_map_cache", "NOT_SET")` staying `"NOT_SET"` after multiple calls) —
    versus the plain-object version demonstrably going stale in the same scenario, above.
  - **This mechanism is correct but silently fragile — its correctness lives in an absence** (the
    slots list not containing `_occupancy_map_cache`) **and an exception path nothing at the call
    site names.** Someone later adding a field for an unrelated reason, or "tidying" what looks like
    an arbitrary attribute list, silently re-enables the cached path and the staleness bug returns
    with no visible cause. Two things the implementation must do, not just the test:
    1. Comment the `__slots__` declaration itself as **deliberately exhaustive** — this exact list,
       no more — because the uncached `.entities` scan (path 3) depends on `get_occupancy_map`'s
       `object.__setattr__` call failing, and any new slot risks making it succeed instead.
    2. Name the required staleness-regression test (see below) directly in that comment, so a future
       reader who's tempted to extend the slots list is pointed at the test that would catch it,
       not left to discover the mechanism by reading `spatial_query.py` from scratch.
  - **The fallback chain must never terminate at a shared default position** — that reproduces the
    original bug in a narrower, harder-to-notice form (several invalid carried positions all
    collapsing to the same fallback point). The chain: carried `last_position` → if
    `verify_occupancy()` rejects it (against the `__slots__` context, so entity-vs-entity is
    correctly live), deterministic outward probe reusing `_DECONFLICT_PROBE_OFFSETS`, checking
    `verify_occupancy()` again at each candidate (no separate claimed-set) → if the probe sequence
    is exhausted without finding a free tile, **expand the search rather than collapsing to a
    constant** (e.g. widen the probe radius, matching the spirit of `_resolve_spawn_position`'s own
    escalation, not its literal region-bounds mechanism). If genuinely exhausted, log a warning
    naming the entity and the region, mirroring `compiler.py:489-495`'s own `LAW-SPAWN-OCCUPANCY`
    exhaustion-warning precedent (`f"entity {id}
    ... could not be placed on a free tile in region '{region_id}' ... region is fully packed"`) —
    never a silent stack, which is the exact failure mode this whole ticket exists to eliminate.
- Fix or remove the misleading `orchestrator.py:733-736` comment as part of this change.
- Real test evidence: a multi-episode Campaign run with multiple survivors (matching this
  investigation's own real 13-survivor case) must NOT trip `LAW-SPAWN-OCCUPANCY` in episode 1+,
  and episode 1+ must run to a plausible completion, not stall almost immediately.
- Include a real test for the terrain-instability edge case specifically: a survivor whose carried
  position is valid in episode 0 and blocked in episode 1 — construct it by finding a real tile the
  two episode seeds disagree on (not by hand-placing a fixture), so the test exercises the actual
  mechanism rather than an idealized version of it. This is a distinct failure mode from the one
  this ticket was originally filed for, and needs its own coverage.
- Include a real test asserting the `__slots__` context takes path 3 deterministically, per peer
  review's own instruction not to assume this — mutate the context's `.entities` dict between two
  `verify_occupancy()` calls on the *same* context object and confirm the second call reflects the
  mutation (the exact scenario already reproduced during this ticket's own investigation; the test
  should encode that reproduction, not just cite it). Name it
  `test_reconstruction_context_slots_force_uncached_occupancy_scan` (or equivalent) and reference
  that exact name from the `__slots__` declaration's own comment (see above) — the test and the
  comment must point at each other, so extending the slots list is never a silent decision.

## Out of Scope
- `TCK-20260909-WORLD-ENTITY-SPAWNER-POSITION-RESOLUTION`'s own episode-0 catalog-spawn path —
  already fixed, not re-litigated here.
- `TCK-20260909-GRIEF-NEMESIS-CAMPAIGN-REVERIFICATION`'s own scope — blocked by this bug (multi-
  episode testing can't proceed reliably until this lands), but this ticket is about the position
  bug itself, not grief/nemesis event correctness.

## Acceptance Criteria
- [ ] Real per-survivor position resolution replaces the current unconditional `(0.0, 0.0)`
      default, with rationale recorded for which region/anchor a survivor resolves against.
- [ ] The misleading `world_composition governs spawn placement` comment is fixed to accurately
      describe what actually happens in this branch.
- [ ] A real multi-episode Campaign run with real survivors (13+, matching this investigation's
      own evidence) shows zero `LAW-SPAWN-OCCUPANCY` violations in episode 1+, and episode 1+
      completes without an early stall attributable to this bug.
- [ ] No regression in `tests/unit/domains/campaigns/`, `tests/integration/campaigns/`.

## Related Tickets
- `TCK-20260909-WORLD-ENTITY-SPAWNER-POSITION-RESOLUTION` — sibling finding, same underlying
  problem class (no real spatial placement), different code path (survivor reconstruction, not
  catalog spawn), only reachable once that ticket's own fix let real survivors exist. Its own
  `_resolve_spawn_position()` mechanism is NOT directly reusable here — see Scope.
- `TCK-20260909-GRIEF-NEMESIS-CAMPAIGN-REVERIFICATION` — origin of this finding; blocked by this
  bug for its own `nemesis_relation_formed`/episode-boundary-grief reverification, which needs a
  real multi-episode run this bug currently prevents.
- `TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING` — made Campaign mode's entities real in the
  first place, which is why survivors (and therefore this bug's real consequence) exist at all now.
- `TCK-20260911-ENTITYSPAWNCONTEXT-SPAWN-REGION-THREADING-GAP` — filed from this ticket's own
  pre-implementation investigation; the prerequisite if the narrative answer to D-07 (below) is
  ever "survivors return to their authored region" rather than "last known position."

## Related Docs
- `docs/plans/deferred_tuning_decisions_register.md` D-07 — the open narrative question (where
  survivors *should* reappear) this ticket's wiring fix answers pragmatically (last-known-position)
  without resolving; corrected 2026-09-11 to reflect this ticket's own investigation findings.

## Related Stored Artifacts
None yet — standard tier, staging artifacts created when picked up.

## Related Code Areas
- `src/domains/campaigns/orchestrator.py` (`_build_initial_state()`'s survivor-reconstruction
  branch, lines ~733-772; `_extract_entity_carry_forwards()`, lines ~510-548, needs the new
  `last_position` capture)
- `src/domains/campaigns/state.py` (`EntityCarryForward`, needs the new `last_position` field)
- `src/worldassembly/resolver.py` (`_hash_point_in_bounds`/`_resolve_spawn_position` — NOT directly
  reusable, requires a `spawn_region` no survivor has; `_DECONFLICT_PROBE_OFFSETS` IS reusable for
  probing candidate tiles, though the entity-vs-entity collision check itself is
  `verify_occupancy()`, not a separate claimed-set — see below)
- `src/engine/spatial_query.py:104-120` (`SpatialQueryService.get_occupancy_map()` — caches its
  result **onto the state/context object itself** via `object.__setattr__(state,
  "_occupancy_map_cache", mapping)`, keyed by nothing but object identity. Reused across a loop
  with a mutating `.entities` dict, this silently returns a stale map — confirmed by direct
  reproduction, not just read: a plain context object's second `verify_occupancy()` call on a tile
  occupied by an entity added *after* the first call returned `True`/`LEGAL`, silently approving an
  occupied tile.)
- `src/worldbuilding/compiler.py` (per-episode terrain/`blocked_tiles`/building generation — the
  source of the geometry-instability risk a validity check must guard against; lines 489-495 are
  the `LAW-SPAWN-OCCUPANCY` exhaustion-warning precedent to mirror, not just cite)
- `src/engine/legality.py:53-116` (`LegalityServiceV2.verify_occupancy()` — the real, existing
  occupancy check to call directly for the validity gate; do not hand-roll a copy)

## Assumptions / Open Questions
- ~~What region a returning survivor should anchor to... is not decided here~~ **Superseded by
  pre-implementation investigation (2026-09-11)**: not resolved by picking a region at all — the
  real fix carries the survivor's own last live position (`entity.navigation.position` at episode
  end), not a region anchor. See Scope and D-08's sibling entry, D-07, in
  `docs/plans/deferred_tuning_decisions_register.md` (corrected the same day, before this ticket's
  own implementation started).
- **New, confirmed before implementation**: region bounds are stable across episodes (authored,
  read verbatim from `RegionSpec.bounds`), but terrain and building placement inside those bounds
  are NOT — both draw from `DeterministicRNG(episode_seed)`, and `episode_seed` differs every
  episode (`base_seed + episode_index`). A carried `last_position` can be within-bounds but on
  newly-blocked terrain in the next episode. **Needs a validity check with fallback** (e.g., re-run
  a deconfliction/nearest-open-tile search when the carried position lands in `blocked_tiles`, or
  fall back to a `default_position` the way `WorldEntitySpawner.spawn_from_context()` already does
  when no better position is available) — do not ship a bare carry-through of `last_position`
  without this.
- Whether `EntityCarryForward.last_position` should be `Optional` (falling back to a sentinel like
  `None` for entities carried forward before this field existed, e.g. mid-flight save data) is a
  real implementation detail for whoever picks this up — not resolved here.
- **Adjacent finding, not this ticket's problem, worth a head start for whoever hits it next**:
  `SpatialQueryService.get_occupancy_map()` caches its result onto the passed context by **object
  identity alone**, with no invalidation — fine for the per-tick pipeline where contexts are
  short-lived, but a live trap for any future code that reuses one context object across a mutation
  of `.entities`, the way this ticket's own reconstruction loop does. Confirmed directly during this
  investigation (see the `__slots__` discussion above). Not fixed here — this ticket routes around
  it rather than changing `get_occupancy_map()`'s own caching behavior, which would be a much wider
  blast radius than this fix needs.

## Implementation Notes
_(pending — filed, not yet picked up)_

## Test Summary
_(pending)_

## Files Changed
_(pending)_

## Completion Summary
_(pending)_
