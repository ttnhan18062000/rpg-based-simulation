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
  - **The fallback chain must never terminate at a shared default position** — that reproduces the
    original bug in a narrower, harder-to-notice form (several invalid carried positions all
    collapsing to the same fallback point). The chain: carried `last_position` → if
    `verify_occupancy()` rejects it, deterministic outward probe reusing
    `_DECONFLICT_PROBE_OFFSETS`, checking `verify_occupancy()` (all gates) plus this reconstruction
    pass's own claimed-set at each step → if the probe sequence is exhausted without finding a free
    tile, **expand the search rather than collapsing to a constant** (e.g. widen the probe radius,
    matching the spirit of `_resolve_spawn_position`'s own escalation, not its literal region-bounds
    mechanism). If genuinely exhausted, log a warning naming the entity and the region, mirroring
    `compiler.py:489-495`'s own `LAW-SPAWN-OCCUPANCY` exhaustion-warning precedent (`f"entity {id}
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
  the lighter survivor-vs-survivor deconfliction pass)
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

## Implementation Notes
_(pending — filed, not yet picked up)_

## Test Summary
_(pending)_

## Files Changed
_(pending)_

## Completion Summary
_(pending)_
