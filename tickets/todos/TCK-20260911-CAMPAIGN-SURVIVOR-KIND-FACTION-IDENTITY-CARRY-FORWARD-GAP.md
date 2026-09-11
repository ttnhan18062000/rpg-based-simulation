---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260911-CAMPAIGN-SURVIVOR-KIND-FACTION-IDENTITY-CARRY-FORWARD-GAP
phase: open
date: 2026-09-11
tags: [world, architecture, simulation-quality]
---

# TCK-20260911-CAMPAIGN-SURVIVOR-KIND-FACTION-IDENTITY-CARRY-FORWARD-GAP

## Title
Every survivor reconstructed after episode 0 loses its real `kind` and `identity.faction` — carries the campaign-completion acceptance bar forward from `TCK-20260911-CAMPAIGN-SURVIVOR-RECONSTRUCTION-POSITION-COLLISION`

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Found while verifying `TCK-20260911-CAMPAIGN-SURVIVOR-RECONSTRUCTION-POSITION-COLLISION`'s own
real 3-episode acceptance run. That ticket's position fix is confirmed correct with direct
evidence — episode 1's 13 survivors and episode 2's 9 survivors both reconstruct on fully distinct,
legal tiles, zero `LAW-SPAWN-OCCUPANCY` violations either time (`HardLawMonitor.
check_initial_placement()`). But episode 2 still stalled at tick 52 (`STALL_THRESHOLD=50`
consecutive zero-event ticks) despite the position fix — a different failure, not a recurrence.

Dumping episode 2's reconstructed entities found the real, confirmed gap:
`CampaignOrchestrator._build_initial_state()`'s survivor-reconstruction branch
(`orchestrator.py:746` area) builds every entity as `EntityState(id=eid, kind="entity")` — the
literal string `"entity"`, not the entity's real archetype (`"human"`, `"goblin"`, etc.) — and never
sets `identity.faction` from anything, so it stays at `IdentityComponent`'s bare default. Both
fields are entirely absent from `EntityCarryForward` (`entity_id`, `level`, `xp`, `equipment`,
`reputation`, `alive`, `last_position` — no `kind`, no `faction`). Confirmed directly: all 9 of
episode 2's reconstructed entities had `kind="entity"` and `identity.faction=0` uniformly.

**Confirmed downstream consequence, not inferred**: `src/content_semantics/faction.py`'s
`get_faction_id_str(entity)` reads `identity.properties["faction_id"]` first (never set for a
reconstructed survivor), falling back to `identity.faction` (an int/enum, stuck at the bare
default) — so every reconstructed survivor, regardless of their real original faction, resolves to
the identical faction string. Any hostility/cooperation/diplomatic logic keyed on faction identity
would see a uniformly single-faction population from episode 1 onward.

**What this is NOT (yet) confirmed to be**: the cause of episode 2's tick-52 stall specifically.
Peer review flagged a real complication in that story before this ticket assumed it: **episode 1's
survivors were reconstructed by the exact same branch, with the exact same faction-0 defect, and
episode 1 completed its full 150-tick length without stalling.** "Uniform faction → no hostility →
no combat/cooperation events → stall" therefore cannot be the whole mechanism on its own, or
episode 1 should have stalled too — unless something else (cast size, some other event source
still generating activity in episode 1 but not episode 2, cumulative effect across two
reconstructions rather than one) is also part of the real explanation. This is the ticket's own
open question, not a foregone conclusion to build the fix around.

## Scope
- Confirmed finding (not to be re-litigated, just fixed): thread `kind` and `identity.faction`
  (and check for any other identity/archetype fields silently dropped the same way — a fresh,
  careful audit of what `EntityState`'s own construction path sets vs. what the survivor-
  reconstruction branch sets, not an assumption that only these two are missing) through
  `EntityCarryForward`, extraction, and reconstruction, the same way this ticket's predecessor
  added `last_position`.
- **Open question, must be investigated with real evidence before or alongside the fix, not
  assumed**: what actually causes episode 2's stall? Compare episode 1 (13 survivors, completed)
  against episode 2 (9 survivors, stalled at 52) directly — what event types occurred in episode 1
  that didn't in episode 2, what's different about the entity composition/roles beyond faction,
  whether smaller cast size alone is sufficient to explain it, whether the faction-0 defect
  compounds across two reconstructions in some way a single reconstruction doesn't. Real
  instrumentation (an event-stream listener, matching the pattern `tests/integration/campaigns/
  test_catalog_entity_spawn_wiring.py`'s own `_CollectingRecorder` already established), not
  guessing from static entity dumps.
- **The acceptance bar this ticket now owns, transferred explicitly from
  `TCK-20260911-CAMPAIGN-SURVIVOR-RECONSTRUCTION-POSITION-COLLISION`**: a real 3-episode
  `campaign_life_arc`-shaped run (`frontier_living_world`, matching that ticket's own test)
  completes all three episodes at their configured tick length, no early stall. If fixing
  `kind`/`faction` alone resolves it, done. If it doesn't — if a third defect is waiting behind
  this one — that defect gets found with the same discipline (real run, real evidence, no
  assumption) and the acceptance bar moves again to whichever ticket owns it. It must not quietly
  disappear into a pile of individually-true, individually-closed tickets that never add up to a
  working campaign.

## Out of Scope
- `TCK-20260911-CAMPAIGN-SURVIVOR-RECONSTRUCTION-POSITION-COLLISION`'s own position-resolution
  fix — confirmed correct and closed on its own narrower claim; not reopened here.
- Re-deriving the position fix's own `__slots__`/`verify_occupancy()` mechanism — reused as-is by
  whatever test infrastructure this ticket needs, not redesigned.

## Acceptance Criteria
- [ ] `kind` and `identity.faction` (and any other identity fields found missing during a real
      audit, not assumed to be only these two) are threaded through `EntityCarryForward`,
      extraction, and reconstruction.
- [ ] Real evidence (not inference) for what actually caused episode 2's stall — confirming,
      correcting, or replacing the "uniform faction" hypothesis, with episode 1's own completion
      accounted for rather than ignored.
- [ ] A real 3-episode `campaign_life_arc`-shaped run (`frontier_living_world`) completes all three
      episodes at their configured tick length (matching the predecessor ticket's own 150-tick
      test shape), with zero `LAW-SPAWN-OCCUPANCY` violations throughout (already covered by the
      predecessor's fix, re-verified here as part of the same real run).
- [ ] No regression in `tests/unit/domains/campaigns/`, `tests/integration/campaigns/`.

## Related Tickets
- `TCK-20260911-CAMPAIGN-SURVIVOR-RECONSTRUCTION-POSITION-COLLISION` (done — origin of this
  finding; the campaign-completion acceptance bar is transferred here explicitly from that ticket)
- `TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING` — the sibling episode-0 catalog-spawn path,
  where `kind`/`faction` ARE set correctly (via `WorldEntitySpawner`/`ArchetypeEntityFactory`),
  useful reference for what "correct" looks like
- `TCK-20260911-GRIEF-NEMESIS-CAMPAIGN-REVERIFICATION`-adjacent work — anything depending on real
  multi-episode faction/hostility behavior is also blocked by this gap, not just this ticket's own
  stall investigation

## Related Docs
None yet.

## Related Stored Artifacts
None yet — created by this ticket's own Investigate/Plan phases once picked up.

## Related Code Areas
- `src/domains/campaigns/state.py` (`EntityCarryForward` — needs `kind`/`faction` fields)
- `src/domains/campaigns/orchestrator.py` (`_extract_entity_carry_forwards()`,
  `_build_initial_state()`'s survivor-reconstruction branch — same locations
  `last_position` was added, `kind="entity"` hardcoded literal at the `EntityState(...)`
  construction call)
- `src/content_semantics/faction.py` (`get_faction_id_str()` — confirmed the real downstream
  consumer affected by the faction gap)
- `src/entities/archetype_factory.py`, `src/worldassembly/entity_spawner.py` — the episode-0 path's
  own correct `kind`/faction assignment, for comparison

## Assumptions / Open Questions
- Whether `kind`/`faction` are the *only* identity fields silently dropped, or whether a broader
  audit finds more (e.g. `identity.properties`, archetype-specific fields) — not assumed here, real
  Investigate work.
- **The central open question, deliberately not pre-answered**: does fixing `kind`/`faction` alone
  make episode 2 (and any further episode) complete at full length? Episode 1's own completion
  despite the identical faction-0 defect is real, confirmed counter-evidence against the simplest
  version of that story — worth having a real, tested explanation before claiming the fix worked,
  not just a plausible-sounding one. This same ticket arc has already had two plausible-sounding
  root-cause guesses turn out wrong once actually checked — `spawn_region` as the reusable fix
  basis for survivor placement (it isn't recoverable at all), and `docs/plans/
  deferred_tuning_decisions_register.md`'s own original D-07 entry favoring "authored region" as
  the defensible/deterministic option (same reason) — apply the same discipline here rather than
  trusting the first mechanism that sounds right.

## Implementation Notes
_(pending — filed, not yet picked up)_

## Test Summary
_(pending)_

## Files Changed
_(pending)_

## Completion Summary
_(pending)_
