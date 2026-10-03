---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260908-CAMP-RAID-ORIGIN-SPAWN-FIX
phase: done
date: 2026-09-08
tags: [world, content]
---

# TCK-20260908-CAMP-RAID-ORIGIN-SPAWN-FIX

## Title
CampService.process_camps()'s raid branch discards its own computed raiders — camps drain maturity for a raid that never spawns

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Found during `TCK-20260904-CAMP-CONTENT-AUTHORING-BRIDGE`'s follow-up pass. `CampService.
process_camps()`'s raid-reuse code (`src/world/camp.py`, the `else:` branch under "Trigger a raid
from this camp!") calls `RaidService.check_for_raid(state, generator)` and receives a real
`raid_update` with computed raider entities in `raid_update.entities_add` — but a pre-existing,
self-documented incomplete stub then discards them:

```python
for mob in raid_update.entities_add:
    # We can't easily mutate the update list, so we just add them
    # but in a real system we'd pass the origin.
    # For now, let's just mark the last_raid_tick.
    pass
```

`camp_updates[c_id]` still unconditionally gets `maturity_delta=-20.0, last_raid_tick_set=state.tick`
— the internal bookkeeping proceeds exactly as if a raid happened, but **zero raiders are ever
actually spawned by this code path**, regardless of maturity or timing. Confirmed real via a
510-tick `Kernel.tick_once()` run against a dedicated calibration world
(`data/worlds/camp_maturity_calibration_pilot/`): both camps' maturity dropped by the raid cost at
the expected tick with no corresponding raider entity appearing anywhere in `state.entities`.

Separately, this camp-triggered call is *also* gated a second time by `RaidService.
check_for_raid()`'s own independent `state.tick % raid_interval_ticks == 0` condition
(`raid_interval_ticks = 500`, the same constant `src/engine/world_dynamics.py`'s own unrelated,
global, camp-agnostic periodic raid trigger uses) — a second, narrower compounding gate even once
the discard bug is fixed.

**User-visible symptom**: camps are silently charged a real maturity cost for a raid that never
occurs — draining camp maturity for zero gameplay effect, not just inert dead code.

## Scope
**Scope extended 2026-09-08 (user decision) to cover raid *targeting*, not only spawn origin.**
Follow-up review found that fixing the spawn origin alone would not produce a working raid:
`RaidService.check_for_raid()` computes its spawn position relative to town center `(0,0)`
(`src/world/raid.py:36`) and hardcodes every raider's destination with
`navigation=replace(mob.navigation, target=(0, 0))` (line 63, comment: *"Raiders target the town
(0,0)"*). Camp-anchored raiders would therefore spawn correctly at the camp and then immediately
walk to the world origin — entities would exist, and the raid would still be meaningless. That is
the same built-but-not-observable failure this epic exists to close, so both halves are in scope
here rather than split.

- Fix the raid-reuse code so `raid_update.entities_add`'s computed raiders are actually appended to
  `process_camps()`'s own returned `entities_add`, positioned/anchored at the triggering camp (per
  the existing comment's own stated intent — "in a real system we'd pass the origin").
- Give camp-triggered raiders a real destination instead of the hardcoded `(0,0)` — most likely the
  nearest settlement to the originating camp. Decide the selection rule during Investigate, and
  confirm what happens when a world has no settlement, or none within a sensible range.
- Confirm whether the existing global (non-camp) raid path should keep its `(0,0)` assumption or
  share the same target-selection logic. The `(0,0)` hardcode encodes a single-settlement-at-origin
  world model that may no longer hold — note that `state.regions`/`state.places` are now populated
  in Campaign mode as of PR #148, where they previously were not.
- This likely needs `RaidService.check_for_raid()`'s own signature or return contract extended to
  accept/apply a real origin — investigate the minimal real change, not a rewrite of `RaidService`'s
  own targeting logic.
- Confirm the second compounding gate (`raid_interval_ticks` alignment) is intentional or also worth
  addressing in the same ticket — a real call to make during Investigate, not assumed here.
- Prove the fix with a real simulation run: a camp-triggered raid actually produces visible raider
  entities in `state.entities`, not just correct maturity bookkeeping.

## Out of Scope
- `RaidService`'s own global (non-camp) raid-trigger path (`src/engine/world_dynamics.py`) — already
  confirmed working correctly, not part of this bug.
- Any change to raid difficulty/reward balance — this ticket only makes the existing raid actually
  spawn, not tune it.
- The Camp/Nest/Lair content-authoring gap this bug was found alongside — already closed by
  `TCK-20260904-CAMP-CONTENT-AUTHORING-BRIDGE`.

## Acceptance Criteria
- [x] A camp-triggered raid actually spawns real raider entities in `state.entities`, confirmed via
      a real simulation run (not a hand-constructed unit test alone).
- [x] Those raiders are given a sensible target derived from the originating camp (the nearest real
      `PlaceKind.CITY` place), NOT the hardcoded world origin — proven both by asserting
      `navigation.target` resolves to the real settlement position AND by the entity's spawn
      position itself being anchored at the camp, not `(0,0)`. **Relaxed during implementation, by
      explicit peer-review agreement**: observed movement toward the target over further real ticks
      is NOT asserted — investigated directly and confirmed this is blocked by an unrelated,
      pre-existing issue in the adaptive governor's `RuntimeMode.DEGRADED`/`ScanPolicy.EXACT_DIRTY`
      policy (any non-urgent, freshly-spawned entity with no per-tick `EntityUpdate` is permanently
      excluded from movement candidacy under that policy — a starvation loop, not a defect in this
      ticket's own fix), filed separately as
      `TCK-20260908-DEGRADED-POLICY-NONURGENT-MOVEMENT-STARVATION`. "Spawned but walking to (0,0)"
      still does not satisfy this ticket — that specific failure mode is fully closed (raiders never
      target `(0,0)` after this fix); "spawned but not yet observed moving due to an unrelated
      governor policy" is the actual, narrower, honestly-recorded gap.
- [x] Camp maturity cost (`-20.0`) and `last_raid_tick_set` bookkeeping remain correct and only apply
      when a raid genuinely occurs — including the no-CITY-place case, where the raid is skipped
      entirely and neither cost nor cooldown-reset applies (a new regression test covers this
      specifically, per peer review flagging it as the one place this fix could regress into its
      own bug).
- [x] No regression in existing camp/raid test suites.

## Related Tickets
- `TCK-20260904-CAMP-CONTENT-AUTHORING-BRIDGE` (`tickets/done/` — found this bug during its own
  follow-up pass)
- `TCK-20260908-HOTFIX-STATE-PLACES-APPLY-CARRYFORWARD-GAP` — a real, separate blocker found while
  writing this ticket's own real-run test: `state.places` was silently reset to `{}` on every tick
  in every simulation mode (not just Campaign mode), so this ticket's nearest-CITY-place lookup
  found nothing past the first tick in any real multi-tick run. Fixed as its own hotfix before this
  ticket could be verified end-to-end.
- `TCK-20260908-DEGRADED-POLICY-NONURGENT-MOVEMENT-STARVATION` — the destination for this ticket's
  own deferred live-movement verification (see Acceptance Criteria above); a real, separate,
  pre-existing issue unrelated to this ticket's own fix.
- `TCK-20260908-RAID-SIZE-FORMULA-DOC-CODE-MISMATCH` — a real doc/code mismatch found during
  Investigate, deliberately scoped out (raid balance, not spawn/targeting correctness).

## Related Docs
- `docs/world/raid_boss_camp_contract.md`

## Related Stored Artifacts
None yet — created by this ticket's own Investigate/Plan phases once picked up for implementation.

## Related Code Areas
- `src/world/camp.py` (`CampService.process_camps()`)
- `src/world/raid.py` (`RaidService.check_for_raid()`)

## Assumptions / Open Questions
- Whether `RaidService.check_for_raid()`'s own signature should change to accept an origin
  parameter, or whether the fix belongs entirely in `camp.py`'s own post-processing of the returned
  update, is a real design call for this ticket's own Investigate/Plan phases — not resolved here.

## Implementation Notes

**Investigation** found two real blockers beyond the ticket's own original scope, both routed
through peer review before implementing, per this repo's standing decision-routing convention:

1. **The "second compounding gate" was real, not just a stylistic worry.**
   `RaidService.check_for_raid()`'s own internal `state.tick % raid_interval_ticks != 0` gate is a
   different condition than the camp-triggered call site's own `camp.maturity>=80` +
   `last_raid_tick` cadence — even after fixing the discard bug, the camp-triggered raid would have
   silently returned zero raiders on ~499/500 of the ticks it's actually eligible to fire on.
2. **Doc/code mismatch on `raid_size`** (`3 + camp.maturity` per the doc vs. `3 + state.maturity` in
   code) — investigated and found the doc's own literal formula is internally inconsistent against
   `monster_cap` (83 raiders from an 8-monster camp at the trigger threshold). Correctly kept out of
   scope per peer review (a balance question, not this ticket's job) and filed separately as
   `TCK-20260908-RAID-SIZE-FORMULA-DOC-CODE-MISMATCH`.

**Fix shape** (peer-approved before implementing): extracted raid composition (spawn N raiders at
an explicit `origin`, target an explicit `target`, no internal cadence gate) into a new
`RaidService.spawn_raid()`. `check_for_raid()` keeps its exact existing gate/signature/behavior for
the global (non-camp) caller — confirmed byte-identical via a new test computing the expected spawn
position independently from the same RNG call and asserting exact equality. The camp-triggered site
in `camp.py` calls `spawn_raid()` directly, resolving the nearest `PlaceKind.CITY` place in
`state.places` by squared Euclidean distance from the camp's own position as the real target,
bypassing `check_for_raid()`'s own unrelated cadence gate entirely (the camp's own
`maturity`/`last_raid_tick` cadence is the correct gate for this path).

**Fallback with no CITY place**: skip the raid entirely — no raiders, and critically, per peer
review flagging this as the one place the fix could regress into its own bug, no `maturity_delta`
or `last_raid_tick_set` either. A dedicated regression test proves both halves (no raiders spawned,
maturity unchanged at the plain growth-only delta).

**Blocked mid-implementation by a real, separate bug**: writing the real-multi-tick-run proof this
ticket's own Acceptance Criteria required surfaced that `state.places` was silently reset to `{}`
on every tick, in every simulation mode — not the already-fixed `CAMPAIGN-REGION-PLACE-CARRY`
Campaign-mode-construction bug, but the apply-path never carrying `places` forward tick-to-tick at
all. Fixed as its own hotfix, `TCK-20260908-HOTFIX-STATE-PLACES-APPLY-CARRYFORWARD-GAP`, before this
ticket could be verified end-to-end (see that ticket for the full investigation and fix).

**Further blocked, after the places fix landed, by a second, unrelated real finding**: with
`state.places` surviving correctly and raiders spawning/targeting correctly, the raiders still
showed zero net movement over 30 real ticks. Traced precisely (ruling out
`TCK-20260908-DIRTY-SET-PASSIVE-DECAY-CONSUMER-INVESTIGATION`'s own gap via direct
`should_run_phase()` tracing — `movement_routing` runs unconditionally on this path) to the adaptive
governor's `RuntimeMode.DEGRADED`/`ScanPolicy.EXACT_DIRTY` policy: `MovementCandidateSelector.
select()` skips all non-urgent candidates under that policy, and a freshly-spawned entity with a
static target and no active AI goal has no path to ever satisfy any of the 5 urgency conditions —
a genuine starvation loop (per peer review's sharper framing), not mere throttling, and a
newly-observed, more visible consequence of an already-known, deliberately-deferred Kernel
wall-clock throttle determinism issue. Filed separately, not fixed here or there:
`TCK-20260908-DEGRADED-POLICY-NONURGENT-MOVEMENT-STARVATION`. The Acceptance Criteria above were
amended (with explicit peer agreement) to drop the live-movement assertion this ticket cannot
control, while keeping the spawn/positioning/targeting correctness this ticket does own.

`docs/world/raid_boss_camp_contract.md` updated: the "Known gap" note and the raid-composition
"Target: ... currently hardcoded to (0,0)" line both corrected to describe the camp-triggered path's
real fix, while explicitly preserving the global (non-camp) path's own unchanged `(0,0)` behavior as
a deliberate Out-of-Scope choice, not a remaining gap.

## Test Summary
- `tests/unit/world/test_camp_lifecycle.py`: 3 existing tests updated to seed a real CITY place
  (previously implicitly relying on the discard bug never actually spawning anything to check
  against); 1 new regression test (`test_camp_raid_trigger_skips_entirely_with_no_city_place_no_cost_charged`).
  20 passed.
- `tests/unit/world/test_calamity_raid.py`: 1 new test proving the global path's exact spawn
  positions are byte-identical to before the `spawn_raid()` extraction (independently recomputed
  from the same RNG call). 4 passed.
- `tests/integration/world/test_camp_raid_targeting.py` (new): a real `Kernel` + `WorldCompiler`
  run against `camp_maturity_calibration_pilot`, proving a camp-triggered raid spawns real
  `goblin_raider` entities anchored at the camp (not `(0,0)`) and targeting the real nearest CITY
  place. 1 passed.
- All new/modified tests in `camp.py`/`raid.py` confirmed to fail against the pre-fix code (reverted
  via `git show`/temporary copy, reran, restored) before finalizing — same discipline applied to
  `state.places`'s own 3 new tests on the sibling hotfix ticket.
- Full `tests/unit/world/ tests/certification/ tests/unit/certification/
  tests/integration/certification/` sweep (part of the broader sweep run for the `state.places`
  hotfix, since both land together): clean, 0 failures attributable to either change.

## Files Changed
- `src/world/raid.py` — `check_for_raid()` now delegates to new `spawn_raid(origin, target,
  raid_size)`; global-path behavior unchanged.
- `src/world/camp.py` — raid-trigger branch: discard bug fixed, nearest-CITY-place targeting added,
  no-CITY skip added (with correct cost/cooldown conditionality).
- `docs/world/raid_boss_camp_contract.md` — "Known gap" and raid-target sections corrected.
- `tests/unit/world/test_camp_lifecycle.py`, `tests/unit/world/test_calamity_raid.py` — updated/new
  tests (see Test Summary).
- `tests/integration/world/test_camp_raid_targeting.py` (new).
- `tickets/todos/TCK-20260908-RAID-SIZE-FORMULA-DOC-CODE-MISMATCH.md` (new, filed not implemented).

## Completion Summary
`CampService.process_camps()`'s raid-trigger branch discarded its own computed raiders — camps were
silently charged a real maturity cost for a raid that never spawned anyone. Fixed at the root,
along with a second, previously-undetected compounding gate (`check_for_raid()`'s own unrelated
tick-cadence check) that would have made the discard-only fix appear to work in a narrow test while
still failing in the overwhelming majority of real ticks. Raiders now spawn anchored at the
triggering camp and target the real nearest settlement (`PlaceKind.CITY` place), closing an
acknowledged, documented gap rather than inventing new behavior — with the no-target case correctly
skipping the raid entirely rather than defaulting to the old fabricated `(0,0)` anchor. Two real,
separate, pre-existing bugs were found and (in one case) fixed along the way: `state.places` never
survived past the first tick of any simulation (fixed as its own hotfix, a genuine blocker for this
ticket's own verification), and freshly-spawned non-urgent entities can permanently stop moving
under the adaptive governor's degraded-mode policy (filed separately, not a defect in this fix). A
doc/code mismatch on raid sizing was found and deliberately left as a separate balance question. All
real decisions in this ticket were routed through peer review before implementing, each
independently re-verified against real code — the discard bug, the compounding gate, the targeting
fallback, the `raid_size` scope boundary, and both of the deeper findings that blocked this ticket's
own end-to-end verification.
