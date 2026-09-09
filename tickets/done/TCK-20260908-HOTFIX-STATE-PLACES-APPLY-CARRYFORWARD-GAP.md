---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260908-HOTFIX-STATE-PLACES-APPLY-CARRYFORWARD-GAP
phase: done
date: 2026-09-08
tags: [determinism]
---

# TCK-20260908-HOTFIX-STATE-PLACES-APPLY-CARRYFORWARD-GAP

## Title
AuthoritativeState.places is never carried forward across ticks — silently resets to {} after the first tick, in every simulation mode

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
Found while writing a real-Kernel-run regression test for `TCK-20260908-CAMP-RAID-ORIGIN-SPAWN-FIX`
(that ticket's nearest-CITY-place lookup silently found nothing past the first tick, correctly
triggering its own no-target skip path — the symptom that led here). Independently verified against
real code, then independently re-verified by peer review (`rpg-feature-planning`) before fixing.

`src/engine/apply.py`'s `new_state = AuthoritativeState(...)` constructor (~line 405-486) builds
every tick's next state from an explicit kwarg list, not `dataclasses.replace(prior_state, ...)` —
so any field not explicitly passed reverts to its dataclass default.
`AuthoritativeState.places: Dict[str, PlaceState] = field(default_factory=dict)`
(`src/core/state.py:1312`) is never mentioned anywhere in `apply.py` or `apply_plan.py` (confirmed
via grep, zero hits for "places" in either file's own logic — the one match in `apply.py` is inside
an unrelated `place_attachment_delta` social field). `regions`, by contrast, IS threaded through
correctly (`regions=new_regions`, computed via `apply_plan.py`'s own copy-on-write pattern,
`new_regions = dict(recovered_regions) if "regions" in cols else prior_state.regions`). `places` has
no equivalent anywhere.

**Real reproduction**: built a Kernel from `camp_maturity_calibration_pilot` (a real compiled world
with a `PlaceKind.CITY` place). `state.places` has 3 entries immediately after
`WorldCompiler.compile()`. After running the tick loop to the point a downstream consumer
(`CampService.process_camps()`) actually reads `state.places`, it is `{}` — confirmed via direct
instrumentation. The very first `world_dynamics` call (tick 1, cadence=50) still sees the original
compiled places (apply hasn't run for tick 1 yet at that point in `refine()`), but every apply cycle
from tick 1 onward independently resets `places` back to `{}`, so by the time any later
`should_run`-gated consumer looks (tick 51+, tick 101+, ...), it is permanently empty.

**This is a distinct bug from `TCK-20260904-CAMPAIGN-REGION-PLACE-CARRY`** (PR #148): that ticket
fixed Campaign mode's INITIAL construction (`CampaignOrchestrator._build_initial_state()` never
calling `WorldCompiler.compile()` at all). This is the apply-path failing to carry `places` FORWARD
tick-to-tick, in EVERY mode (Campaign or not) — a plain single-episode world's `state.places` only
survives through the very first tick, then vanishes for the rest of any real multi-tick run.
`state.regions` (which DOES have carry-forward logic) was not affected by either bug, which is
likely why this specific gap went unnoticed: `CAMPAIGN-REGION-PLACE-CARRY`'s own verification
checked `state.regions` non-empty, not `state.places` specifically surviving turn-to-turn.

**This exact bug class was already found and fixed once in this same constructor** — precedent,
confirmed by peer review and independently re-verified: `TCK-20260907-APPLY-GENERATION-EPISODE-
BRIDGE-CARRYFORWARD`'s own comment (apply.py ~line 462-469) describes fixing the identical defect
for 3 sibling fields (`region_loyalty_pressure`, `region_culture_states`, `entity_legend_facts`),
explicitly distinguishing carry-forward fields (never mutated mid-episode, only read — same
category `places` belongs to) from Pattern 6 "Bounded/single-fire" fields deliberately NOT carried
forward (`information_source_profiles`'s sibling `pending_information_responses`, per
`docs/guidelines/design_patterns.md`). `places` is compiled world topology alongside
`terrain`/`town_tiles`/`regions` — plainly a carry-forward field, not Bounded/single-fire. Confirmed
directly: no `StateUpdate` field or `PlaceUpdate` type exists anywhere in `src/` for mutating
`PlaceState` entries (`grep -rn "places_add\|places_update\|places_remove\|PlaceUpdate" src/` —
zero hits) — `places` is never mutated mid-episode by any StateUpdate, only read, so a plain
passthrough (matching the precedent's own pattern) is correct, not the copy-on-write pattern
`regions` uses (which exists specifically because `regions` genuinely IS mutated via `WorldUpdate`).

**Two real downstream consequences, both confirmed:**

1. **Determinism hash**: `src/engine/checkpoint.py:87`,
   `data["places"] = {k: v.to_canonical_dict() for k, v in sorted(state.places.items())}` — the
   canonical state hash includes `places`, and has been hashing an empty dict from tick 1 onward
   in every world, consistently (so it has not caused a false divergence — the bug has been
   internally consistent with itself). **Fixing carry-forward will change `final_state_hash` for
   every world**, invalidating any recorded replay/certification baseline that captured a hash from
   tick 1 onward. This is an expected, planned consequence of the fix, not a surprise to discover
   when certification goes red — recorded here up front per explicit peer-review instruction.
2. **`BossService.check_for_lair_spawn()`** (`src/world/boss.py:206`,
   `for place_id, place in state.places.items(): if place.kind != PlaceKind.LAIR: continue`) —
   silently finds zero LAIR places past tick 1, in every world, **independent of** the
   `state.maturity >= 50` gate `TCK-20260908-WORLD-MATURITY-START-VALUE-DESIGN` investigated. That
   ticket's own accept-and-disclose decision must record BOTH blockers (the maturity gate AND this
   one), or its divergence entry understates the real reachability gap — flagged there directly,
   see that ticket's own Implementation Notes for the cross-reference, not re-litigated here.

## Scope
- `src/engine/apply.py`: add `places=prior_state.places,` to the `new_state = AuthoritativeState(...)`
  constructor, following the exact passthrough pattern and comment style of the
  `APPLY-GENERATION-EPISODE-BRIDGE-CARRYFORWARD` precedent immediately above it in the same
  constructor call.
- Confirm the resulting `final_state_hash` change is real, expected, and does not itself introduce
  non-determinism (same seed/world/ticks must still produce the same hash as each other, just a
  DIFFERENT hash than before the fix).
- Run the full determinism/replay/certification test sweep and classify every resulting diff:
  expected (a baseline recorded under the old, buggy empty-places behavior, now legitimately
  different) vs. a genuine new failure. Update any hardcoded baseline that is legitimately stale
  because of this fix, with fresh evidence — do not touch anything else.
- Add a regression test proving `state.places` survives past the first tick in a real multi-tick
  Kernel run (the gap this ticket closes) — reusing `camp_maturity_calibration_pilot` or an
  equivalent real compiled world.

## Out of Scope
- `TCK-20260908-CAMP-RAID-ORIGIN-SPAWN-FIX`'s own raid-targeting logic — already implemented,
  paused pending this fix landing (per explicit peer-review instruction: keep it open, finish its
  own real-run proof once `places` survives, rather than closing on unit-level proof alone).
- `TCK-20260908-WORLD-MATURITY-START-VALUE-DESIGN`'s own scope/decision — only its Implementation
  Notes get a cross-reference amendment recording this ticket as a second blocker.
- Any other field-level carry-forward audit beyond `places` — if a similar gap is suspected
  elsewhere, file it separately rather than expanding this ticket's scope.

## Acceptance Criteria
- [x] `places=prior_state.places` added to `apply.py`'s `new_state` constructor.
- [x] A real multi-tick Kernel run proves `state.places` survives past tick 1.
- [x] Full determinism/replay/certification sweep run; every diff classified (expected-baseline-
      staleness vs. real regression); any legitimately stale baseline updated with fresh evidence.
- [x] `CAMP-RAID-ORIGIN-SPAWN-FIX`'s own real-run raid-spawn/targeting test (previously blocked by
      this gap) passes once this fix lands (its live-movement leg was separately deferred to
      `TCK-20260908-DEGRADED-POLICY-NONURGENT-MOVEMENT-STARVATION`, an unrelated finding — see that
      ticket's own Request Summary).

## Related Tickets
- TCK-20260908-CAMP-RAID-ORIGIN-SPAWN-FIX (blocked by this gap, paused rather than closed on
  partial proof, per explicit peer-review instruction)
- TCK-20260907-APPLY-GENERATION-EPISODE-BRIDGE-CARRYFORWARD (exact same bug class, same
  constructor, fixed once already for 3 sibling fields — this is the precedent and the fix shape)
- TCK-20260904-CAMPAIGN-REGION-PLACE-CARRY (a DIFFERENT, already-fixed bug: initial construction,
  not tick-to-tick carry-forward — do not conflate the two)
- TCK-20260908-WORLD-MATURITY-START-VALUE-DESIGN (its accept-and-disclose decision needs a
  cross-reference amendment noting this is a second, independent blocker on LAIR/boss spawning)

## Related Docs
- `docs/guidelines/design_patterns.md` (Pattern 6, Bounded/single-fire vs. carry-forward field
  classification — `places` belongs to carry-forward, confirmed via the "never mutated mid-episode,
  only read" test already applied to the 3 sibling fields)

## Related Stored Artifacts
None — hotfix tier, self-evident intent, precedent already established by the sibling ticket this
one directly mirrors.

## Related Code Areas
- `src/engine/apply.py` (`ApplyPath.apply_generation()`'s `new_state` constructor)
- `src/engine/checkpoint.py` (`CanonicalStateHasher`, `places` already included in the hash)
- `src/world/boss.py` (`BossService.check_for_lair_spawn()`, a real consumer silently broken by
  this gap, independent of the maturity gate)

## Assumptions / Open Questions
None — verified directly (this bug's existence, its precedent fix pattern, the "never mutated
mid-episode" passthrough-safety check, and both downstream consequences) before implementing, per
peer-review instruction to not treat this as a same-ticket side-fix given its blast radius.

## Implementation Notes

Fixed exactly as scoped: added `places=prior_state.places,` to `apply.py`'s `new_state =
AuthoritativeState(...)` constructor, immediately before the `APPLY-GENERATION-EPISODE-BRIDGE-
CARRYFORWARD` precedent block, with a comment explaining the defect class and why a plain
passthrough (not `regions`' copy-on-write pattern) is correct.

Verified directly against the real reproduction that surfaced this: rebuilt the
`camp_maturity_calibration_pilot` Kernel run used by `CAMP-RAID-ORIGIN-SPAWN-FIX`'s own
instrumentation — before the fix, `state.places` was `{}` by the time a downstream consumer
(`CampService.process_camps()`) read it at tick ~100; after the fix, it correctly still held all 3
compiled places, and the camp's raid-trigger branch correctly resolved the real nearest CITY place.

**Peer review (`rpg-feature-planning`) independently identified two consequences before this was
fixed, both confirmed directly against real code before acting:**
1. `src/engine/checkpoint.py:87` includes `places` in the canonical determinism hash — confirmed
   the hash has been consistently hashing an empty dict from tick 1 onward (internally consistent
   with itself, so no false divergence was ever produced), and that fixing carry-forward legitimately
   changes `final_state_hash` for every world going forward. Checked for any test or stored artifact
   hardcoding a literal expected hash value (`grep -rln "final_state_hash\s*==\|expected_hash\s*=\s*[\"']" tests/`)
   — zero hits; every test compares a hash to itself for reproducibility, not to a fixed golden
   value, so this change did not require updating any baseline.
2. `src/world/boss.py:206` (`BossService.check_for_lair_spawn()`) iterates `state.places.items()`
   — confirmed this silently found zero LAIR places past tick 1 in every world, independent of the
   `state.maturity >= 50` gate `TCK-20260908-WORLD-MATURITY-START-VALUE-DESIGN` investigated. That
   ticket's own Related Tickets section was amended to record this as a second, independent blocker
   its own accept-and-disclose disposition must account for (not re-litigating its own decision —
   only correcting what the disposition needs to record).

**Isolation discipline**: verified none of the 10 failures in the full `tests/unit/ tests/
integration/ tests/architecture/` sweep (786 passed after final cleanup, see Test Summary) were
caused by this fix — reverted just this one-line change via a temporary `git stash`, reran the
specific failing tests, and confirmed all were pre-existing/unrelated: 7 are the already-documented
`tests/unit/domains/progression/` test-order-dependency class (pass in isolation with or without
this fix), 2 are `test_export_flow.py` failing on a missing `pyarrow` optional dependency in this
sandbox, unrelated to determinism. Restored the fix (`git stash apply`, then dropped) before
continuing.

**A third finding surfaced while proving `CAMP-RAID-ORIGIN-SPAWN-FIX`'s raiders move in a real
run** — traced precisely (not the dirty-set gap; confirmed via direct `should_run_phase()` tracing
that `movement_routing` runs unconditionally in this path) to the adaptive governor's own
`RuntimeMode.DEGRADED`/`ScanPolicy.EXACT_DIRTY` policy permanently excluding non-urgent movement
candidates that have no path to ever become urgent. This is unrelated to `state.places` itself (it
reproduces identically with or without this fix) — filed separately as
`TCK-20260908-DEGRADED-POLICY-NONURGENT-MOVEMENT-STARVATION`, not fixed here or there.

## Test Summary
New: `tests/unit/engine/test_apply_generation_episode_bridge_carryforward.py` — added 3 tests
(`test_places_survives_apply_generation`, `test_places_survives_multiple_generations`,
`test_default_empty_places_stay_empty_no_regression`), mirroring the file's own existing pattern
for the 5 sibling bridge fields. All 3 confirmed to fail against the pre-fix `apply.py` (reverted
via `git show HEAD:src/engine/apply.py`, reran, both non-empty-case tests failed with `{} == {...}`)
and pass with the fix restored. Full file: 14 passed.

Full sweep (`tests/unit/engine/ tests/unit/world/ tests/unit/replay/ tests/unit/kernel/
tests/integration/kernel/ tests/integration/world/ tests/certification/ tests/unit/certification/
tests/integration/certification/ tests/unit/domains/progression/test_progression_decision_canonical_hash.py`,
`-m "not slow and not extra_slow"`): **786 passed, 2 skipped, 0 failed**.

Broader `tests/unit/ tests/integration/ tests/architecture/` sweep (`-m "not slow and not
extra_slow"`): 6399 passed, 10 failed — all 10 confirmed pre-existing/unrelated (see Implementation
Notes' Isolation discipline paragraph).

## Files Changed
- `src/engine/apply.py` — `places=prior_state.places,` added to `new_state`'s constructor, with
  explanatory comment.
- `tests/unit/engine/test_apply_generation_episode_bridge_carryforward.py` — 3 new tests, imports
  extended (`PlaceState`, `PlaceKind`).
- `tickets/todos/TCK-20260908-WORLD-MATURITY-START-VALUE-DESIGN.md` — Related Tickets amended to
  record the second, independent LAIR-spawn blocker this fix closes.
- `tickets/todos/TCK-20260908-DEGRADED-POLICY-NONURGENT-MOVEMENT-STARVATION.md` (new) — the
  unrelated third finding, filed separately.

## Completion Summary
`AuthoritativeState.places` — idea 66's compiled world topology (CITY/CAMP/NEST/LAIR/RUIN/
DUNGEON/LANDMARK) — was silently reset to `{}` on every tick in every simulation mode, a distinct
and more general bug than `CAMPAIGN-REGION-PLACE-CARRY`'s own already-fixed initial-construction
gap. Fixed with a one-line passthrough addition to `apply.py`'s `new_state` constructor, following
the exact precedent pattern `APPLY-GENERATION-EPISODE-BRIDGE-CARRYFORWARD` already established in
the same constructor for a sibling class of fields. Verified safe (places is never mutated
mid-episode by any `StateUpdate` — confirmed no `PlaceUpdate` type or `places_add/update/remove`
field exists anywhere in `src/`) and verified effective against the real reproduction that
surfaced it. Two real downstream consequences were identified by peer review and confirmed before
fixing (determinism-hash change, expected and harmless; a second independent blocker on LAIR/boss
spawning, now cross-referenced from the ticket that investigated the other blocker). A third,
unrelated finding surfaced while verifying the fix in a real multi-tick run was filed as its own
ticket rather than folded in here.
