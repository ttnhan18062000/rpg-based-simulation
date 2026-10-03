---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260908-CAMP-RAID-ORIGIN-SPAWN-FIX
artifact_type: plan
tags: [world, content]
---

# Plan — TCK-20260908-CAMP-RAID-ORIGIN-SPAWN-FIX

All open questions from `investigation.md` resolved via peer review (`rpg-feature-planning`),
independently re-verified before implementing:

## Decisions

1. **Fallback with no `PlaceKind.CITY` place**: skip the raid entirely (no raiders, no cost). The
   doc (`raid_boss_camp_contract.md:18,141`) already confirms "nearest settlement" targeting and
   flags `(0,0)` as a known anchor gap, not an intentional design — this closes an acknowledged gap
   rather than inventing new behavior. **Critical trap flagged by review, must hold**: the skip path
   must NOT apply `maturity_delta=-20.0` or `last_raid_tick_set` — those only apply when raiders are
   actually emitted. A skip-that-still-charges-cost would silently rebuild this exact ticket's bug.
2. **`raid_size` stays on `state.maturity`, unchanged.** Doc says `3 + camp.maturity`, but at the
   real trigger threshold (`camp.maturity>=80`) that formula yields 83+ raiders against a
   `monster_cap` of 8 resident monsters (`camp.py:70`, `max(2, int(camp.maturity/10))`) —
   internally inconsistent, a balance question, not an implementation call. Out of Scope explicitly
   excludes raid balance. File the doc/code mismatch as its own separate ticket, don't resolve which
   is "correct" here.
3. **Fix shape approved as proposed**: extract raid composition (spawn N raiders at an explicit
   `origin`, target an explicit `target` position) into a new `RaidService` method taking no
   internal cadence gate. `check_for_raid()` keeps its exact existing signature/behavior for the
   global (non-camp) caller — gates first, then delegates to the new method with `origin=(0,0)`* and
   the resolved target (see below), so its own output is unchanged. The camp-triggered site in
   `camp.py` calls the new method directly, using the camp's own `maturity>=80` +
   `last_raid_tick` cadence as its gate (bypassing `check_for_raid()`'s tick%500 check entirely,
   since that check does not apply to this call site).
   \* the global path's own "town" concept still has no addressable settlement lookup wired to it
   in this ticket — Out of Scope forbids touching its observable behavior, so its target/origin
   stay exactly as today (spawn position formula unchanged, `target=(0,0)`) even after extraction.
4. **Verification additions from review**: (a) assert the global path's output is byte-identical to
   pre-refactor for the same `(state, generator)` inputs — the Out-of-Scope guarantee, cheap to
   test directly; (b) prove the camp-triggered raid via *observed movement* toward the CITY place in
   a real multi-tick run, not merely asserting `navigation.target` was assigned.

## Implementation Steps

1. `src/world/raid.py`: add `RaidService._spawn_raid(state, generator, origin, target, raid_size)`
   (or similarly named private/internal composition helper) — the body of today's `check_for_raid()`
   from the `raid_size = ...` line onward, parameterized on `origin`/`target`/`raid_size` instead of
   hardcoding `(0,0)` for both spawn-position basis and destination. `check_for_raid()` keeps its
   gate (`state.tick % raid_interval_ticks`), then calls the new helper with the same `state.maturity`
   sizing and `(0,0)`-anchored origin/target it uses today — output must be identical to pre-change.
2. `src/world/camp.py`: replace the raid-trigger `else:` branch's discard stub. Resolve nearest
   `PlaceKind.CITY` place in `state.places` by squared Euclidean distance from `camp.position`. If
   none found: apply no `camp_updates` entry for this camp this tick (or an update carrying no
   maturity/cost change — confirm exact `CampUpdate` no-op shape during implementation) and emit no
   entities. If found: call the new `RaidService` helper with `origin=camp.position`,
   `target=<nearest CITY place's position>`, `raid_size` computed the same way `check_for_raid()`
   does today (`RAID_BASE_SIZE + state.maturity`), append the returned raiders to `entities_add`,
   and apply the existing `-20.0`/`last_raid_tick_set` `CampUpdate` only in this branch.
3. Tests: a no-CITY-world case (maturity unchanged, no raiders, no cost applied); a real-world case
   proving raiders spawn at the camp and are observed moving toward the CITY place over several
   ticks (not just a `navigation.target` assertion); a byte-identical-output assertion for the
   global (non-camp) path pre/post refactor; existing camp/raid suites stay green.
4. Update `docs/world/raid_boss_camp_contract.md`: the "Known gap" note and the raid-composition
   "Target: ... currently hardcoded to (0,0)" line both become false for the camp-triggered path —
   correct them, and record the change in the parity ledger via `tools/parity_ledger_writer.py`.
5. File the separate `raid_size` doc/code mismatch ticket (P2, `layer: world`) per decision 2 above
   — do not resolve it, just capture both halves (doc formula vs. code, and the internal
   inconsistency against `monster_cap`) for a future balance decision.
