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
- Design real position resolution for survivor-reconstructed entities. The most direct option:
  reuse the same deterministic de-confliction mechanism
  `TCK-20260909-WORLD-ENTITY-SPAWNER-POSITION-RESOLUTION` already built
  (`_hash_point_in_bounds`/`_resolve_spawn_position` in `src/worldassembly/resolver.py`) — anchor
  survivors on a real region from the freshly-compiled `compiled_regions` (already available in
  `_build_initial_state()`'s own scope) rather than inventing a second mechanism. Confirm during
  Investigate whether that's directly reusable or needs its own variant (survivors don't have a
  `spawn_region` the way freshly-spawned populations do — decide what region a returning survivor
  should anchor to; e.g. their last-known region, or a fixed "return to town" region).
- Fix or remove the misleading `orchestrator.py:733-736` comment as part of this change.
- Real test evidence: a multi-episode Campaign run with multiple survivors (matching this
  investigation's own real 13-survivor case) must NOT trip `LAW-SPAWN-OCCUPANCY` in episode 1+,
  and episode 1+ must run to a plausible completion, not stall almost immediately.

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
  catalog spawn), only reachable once that ticket's own fix let real survivors exist.
- `TCK-20260909-GRIEF-NEMESIS-CAMPAIGN-REVERIFICATION` — origin of this finding; blocked by this
  bug for its own `nemesis_relation_formed`/episode-boundary-grief reverification, which needs a
  real multi-episode run this bug currently prevents.
- `TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING` — made Campaign mode's entities real in the
  first place, which is why survivors (and therefore this bug's real consequence) exist at all now.

## Related Docs
None yet.

## Related Stored Artifacts
None yet — standard tier, staging artifacts created when picked up.

## Related Code Areas
- `src/domains/campaigns/orchestrator.py` (`_build_initial_state()`'s survivor-reconstruction
  branch, lines ~733-772)
- `src/worldassembly/resolver.py` (`_hash_point_in_bounds`/`_resolve_spawn_position`, the existing
  de-confliction mechanism this fix should likely reuse)

## Assumptions / Open Questions
- What region a returning survivor should anchor to (last-known region from carry-forward data,
  vs. a fixed region such as the episode's own town/hometown region) is not decided here — real
  Investigate/Plan work for whoever picks this up.

## Implementation Notes
_(pending — filed, not yet picked up)_

## Test Summary
_(pending)_

## Files Changed
_(pending)_

## Completion Summary
_(pending)_
