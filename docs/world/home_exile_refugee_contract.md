---
status: authoritative
layer: world
authority: P2
audience: agent
last_verified: 2026-09-06
tags: [world, faction]
---

# Home, Exile & Refugee Contract

**Ticket:** TCK-20260905-HOME-EXILE-REFUGEE-THREADS (M6 ideas 59 + 65, `TCK-20260823-EPIC-RPG-M6-POLITICAL-IDENTITY`).

**Status**: AUTHORITATIVE — both the write-side primitive (idea 59) and its first real, live
producer (idea 65).

No Mechanics Bible chapter for social/political mechanics exists yet
(`TCK-20260905-SOCIAL-MECHANICS-BIBLE-CHAPTER` tracks authoring one). This doc is the
minimum-viable contract for the mechanism described below until that chapter lands.

---

## Write-Path Contract (Idea 59: Home, Exile & Return)

`StrategicComponent.home_region_id: Optional[str]` (`src/core/state.py:874`) is durable
per-entity state. The only authoritative way to set it is:

```
StrategicUpdate.home_region_id_set: Optional[str]   (src/core/updates.py)
    -> StrategicPatch.apply()                       (src/engine/patches.py)
    -> ApplyPath                                     (src/engine/apply.py)
```

`home_region_id_set` is deliberately the **reverse** of every other `_set` field on
`StrategicUpdate`: the already-durable value wins over a proposed update, not the other way
round.

```python
home_region_id=new_strat.home_region_id if new_strat.home_region_id is not None else u_strat.home_region_id_set
```

A refugee's `home_region_id` must keep pointing at their *original* home through any number of
subsequent displacements — it is set once, by whichever producer reaches it first, and never
overwritten after that.

## Producer 1: Birth (Idea 59)

`HumanoidReproductionService.process_reproduction()` (`src/world/reproduction_humanoid.py`)
already resolves the birth position's region via `SpatialQueryService.get_region_at()` for its
own `population_young_births_delta` nudge. This ticket reuses that same, already-computed
`region` and passes `region.id` (or `None` if unresolved) into
`EntityGenerator.spawn_humanoid_offspring()`'s new `home_region_id` parameter
(`src/systems/world_systems/generator.py`), which applies it via
`.strategic(home_region_id=home_region_id)` on the entity builder at construction time — this is
a plain constructor value, not a `StrategicUpdate`, since the entity doesn't exist yet.

**Why the caller resolves the region, not the generator itself**: `src/systems/` may not import
`src/engine/` outside a pinned exception list
(`tests/architecture/test_phase18_import_boundaries.py::test_systems_do_not_import_engine_outside_pinned_exceptions`),
and region resolution (`SpatialQueryService`/`LegalityServiceV2`) lives under `src/engine/`.
`src/world/reproduction_humanoid.py` has no such restriction and already imports
`SpatialQueryService`, so it is the architecturally correct place to do the resolution once and
pass the plain result down.

## Producer 2: Calamity Displacement (Idea 65: Named Refugee Threads)

`DisplacementService.compute_displacement()` (`src/world/displacement.py`) is a pure function:
reads `AuthoritativeState`, returns a `StateUpdate`. Every tick, for every region whose
`calamity_intensity >= DisplacementService.DISPLACEMENT_THRESHOLD` (0.6), every living entity
(`entity.lifecycle.active and entity.combat.alive`) currently resolved into that region is
relocated to its lowest-`calamity_intensity` adjacent region (ties broken by region id), via
`EntityUpdate.new_position` — the same field `src/engine/movement.py` already uses for teleport,
applied through `NavigationPatch.apply()` -> `ApplyPath._fast_replace_navigation`.

If the entity's `home_region_id` is still unset at the moment of displacement, the struck region
is recorded as their home via `StrategicUpdate(home_region_id_set=region.id)`. If it is already
set, no `StrategicUpdate` is attached to that entity's `EntityUpdate` at all — the existing home
is left untouched, never re-proposed and re-rejected.

Adjacency reuses `RegionalPressureModel._are_adjacent()` (`src/domains/world_emergence/models.py`)
read-only — no new adjacency model was introduced. Struck regions and affected entities are both
iterated in `sorted(..., key=lambda x: x.id)` order for determinism.

Wired into `src/engine/world_dynamics.py` immediately after the existing "3.9 Creature Territory
Lifecycle" block (as "3.9b Calamity-Driven Displacement"), reading `region.calamity_intensity`
already updated earlier in the same cycle by `CalamityService`/`CalamityPressurePropagator`.
Merged into the tick's `StateUpdate` only if `not displacement_update.is_noop()`, following the
same `if not X_update.is_noop(): update = update.merge(X_update)` pattern already used for every
other optional per-tick sub-update in that file.

`DisplacementService.DISPLACEMENT_THRESHOLD` (0.6) is a new, independent constant, deliberately
one tier above `CalamityService.apply_calamity_consequences()`'s existing `hazard_level > 0.5`
threshold — that threshold gates calamity_intensity *growth*, this one gates its *consequence*
(displacement). They are distinct events on the same underlying signal, not a shared threshold.

## Replay Fingerprint Coverage

Both `home_region_id` (`src/core/state.py:874`, already covered in
`EntityState.to_canonical_dict()`) and `navigation.position`
(`src/replay/fingerprint.py:61`, already covered by `StateFingerprinter`) were already covered by
both fingerprint mechanisms before this ticket — no gap existed here, unlike the two sibling M6
tickets (idea 39, idea 56), which each found and fixed a real fingerprint coverage gap.

## Out of Scope Here

- Rival-faction selection or any faction/loyalty mutation on displacement — idea 39's and idea
  56's scope, unrelated to this ticket's political-*identity* (home/origin) mechanism.
- Narrative/naming generation for a "named" refugee thread — the ticket's "Named Refugee Threads"
  framing describes the mechanism (a durable, traceable home-origin thread per entity), not a
  narrative-text-generation feature; no such subsystem is introduced here.
- Bridging the per-tick `AuthoritativeState` displacement signal into episode-boundary
  `CampaignState` — no such bridge existed for idea 56's loyalty-drift signal either (disclosed
  gap there); this ticket's displacement mechanism is fully wired live within a tick and needs no
  equivalent bridge, since it writes durable per-entity state directly, not a campaign-level
  aggregate.

## Related

- `TCK-20260823-EPIC-RPG-M6-POLITICAL-IDENTITY` — parent epic.
- `TCK-20260905-AFFILIATION-MUTATION-PRIMITIVE` — idea 39, sibling ticket (`docs/world/affiliation_mutation.md`).
- `TCK-20260905-DRIFTING-LOYALTY-SIGNAL` — idea 56, sibling ticket.
- `docs/parity_ledger/world_dynamics.yaml` (`WORLD-DISPLACE-001`), `docs/parity_ledger/strategic_cognition.yaml` (`STRAT-271`).
