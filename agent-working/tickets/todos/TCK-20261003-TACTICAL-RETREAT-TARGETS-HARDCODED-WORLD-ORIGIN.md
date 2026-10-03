---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261003-TACTICAL-RETREAT-TARGETS-HARDCODED-WORLD-ORIGIN
phase: open
date: 2026-10-03
tags: [combat, world, root-cause]
---

# TCK-20261003-TACTICAL-RETREAT-TARGETS-HARDCODED-WORLD-ORIGIN

## Title

Three tactical retreat/wander branches send an entity to hardcoded world coordinate `(0.0, 0.0)`,
parking it outside every region permanently

## Status

OPEN

## Tier

standard

## Type

bug

## Priority

P1

## Request Summary

`src/engine/tactical.py` has **three** branches that set an entity's navigation target to the literal
`(0.0, 0.0)` as a "safe origin":

| line | reason tag | mode |
|---|---|---|
| 141 / 144 | `PANIC_RETREAT` | `MovementMode.RETREAT` |
| 247 / 250 | `SAFETY_PRESSURE_RETREAT` | `MovementMode.RETREAT` |
| 483 | *(untagged)* | `MovementMode.WANDER` |

The comment at `:138` reads *"PANIC: Move to safe origin"*. World coordinate `(0,0)` is not a safe
origin — in the corpus worlds it is **outside every region**. `frontier_marches`' nine region bounds
all start at ≥ 10.

**Measured, not inferred.** Found while measuring
`TCK-20261003-GLOBAL-RAID-SPAWNS-AT-HARDCODED-ORIGIN-OUTSIDE-EVERY-REGION`. Instrumented runs at
`509009d41` (`audit_mode=True`, `max_tick_budget_ms=1e9`, `LocalSequentialExecutor`,
`dropped_work_total == 0`, repeat-stable byte-identical): with raiders spawned at a real city and
correctly targeting it, **10 of 12 entered `PANIC_RETREAT` within 15–38 ticks of spawn**, had their
target overwritten with `(0.0, 0.0)`, walked **past** the city to the world origin, and **idled there
for the rest of the run** with `region_id=None`. `PANIC_RETREAT` fired 62–591 times per raider.

This is the same literal as the retired raid's spawn anchor, on the **flight** path instead of the
spawn path — which is why re-anchoring that raid would not have made it work, and part of why it was
retired instead (see §2.64).

**Scope caution, stated up front:** the measurement observed this for `goblin_raider` entities only.
Whether other entity kinds reach these branches, and how often, is **not measured**. The branches
themselves are kind-agnostic, so the suspicion is general — but that is inference, and this ticket
must not be written up as if the general case were measured.

## Scope

- Decide what "retreat to safety" should mean positionally, and record the decision. Candidates, none
  pre-judged: the entity's `strategic.home_region_id` centre; the nearest settlement Place; the
  nearest friendly-held region; the entity's own region's interior.
- Replace the three `(0.0, 0.0)` literals with that derivation.
- A test asserting a retreating entity's target is inside some region, so an out-of-world retreat
  cannot be reintroduced.
- Measure how often each of the three branches fires, and for which entity kinds, before changing
  behaviour — the fix's blast radius depends on it.

## Out of Scope

- The retired world-clock raid. `TCK-20261003-GLOBAL-RAID-SPAWNS-AT-HARDCODED-ORIGIN-OUTSIDE-EVERY-REGION`
  owns that and is done; do not revive it here.
- Re-introducing world-clock raids. If wanted they return as a declared feature, and this ticket is a
  prerequisite rather than part of it.
- Whether `is_fleeing` / safety-pressure thresholds are tuned correctly. Balance, parked by
  `owner_decision_memo.md` row 7.
- The `(0,0)` literal in any other module.

## Acceptance Criteria

1. The firing rate of all three branches is measured per entity kind, with `audit_mode=True` and a
   raised `max_tick_budget_ms`, **before** any behaviour change. Without that the blast radius is
   unknown.
2. A decision is recorded for what a retreat target should be, with reasoning, not silently adopting
   the first plausible option.
3. A retreating entity's target is inside some region. Asserted by a test that fails on today's code.
4. No entity ends a run parked at `(0.0, 0.0)` with `region_id=None` in a corpus run.
5. Any behaviour change is recorded in `docs/guidelines/intentional_divergences.md` with a rationale
   class, and the relevant `docs/parity_ledger/` entry updated.
6. The rule-layer question is put to `world-rule-catalog-design` before implementation: PLACE-01 says a
   bare coordinate is not a Place, which likely constrains what a legitimate retreat destination is.

## Related Tickets

- `TCK-20261003-GLOBAL-RAID-SPAWNS-AT-HARDCODED-ORIGIN-OUTSIDE-EVERY-REGION` (done) — same literal on
  the spawn path; its measurement is what found this. Read its §2.64 divergence entry first.
- `TCK-20260908-CAMP-RAID-ORIGIN-SPAWN-FIX` (done) — the first of this family, on the camp path.
- `TCK-20260920-VALUE-DIFFERENTIAL-VERIFICATION-INSTRUMENT-GAP` (open, moved into decision-7
  foundation scope) — "proves a mechanism executes, not that it matters" is exactly the shape of this
  defect class.

## Related Docs

- `docs/mechanics/02_combat_laws.md` — tactical modifiers and retreat
- `docs/mechanics/06_worldbuilding_foundation.md` — region bounds
- `docs/world_rules/places-culture/places.md` — PLACE-01, a bare coordinate is not a Place
- `docs/combat/combat_movement_overhaul_spec.md`

## Related Stored Artifacts

- `agent-working/stored_artifacts/TCK-20261003-GLOBAL-RAID-SPAWNS-AT-HARDCODED-ORIGIN-OUTSIDE-EVERY-REGION/`
  — its investigation records the trajectory measurement that found this.

## Related Code Areas

- `src/engine/tactical.py:137-146` — `PANIC_RETREAT`
- `src/engine/tactical.py:245-251` — `SAFETY_PRESSURE_RETREAT`
- `src/engine/tactical.py:483` — untagged `WANDER` branch

## Assumptions / Open Questions

- Whether all three branches should share one "where is safety" helper, or whether panic, safety
  pressure and stalemate-break legitimately differ, is open.
- Whether any consumer depends on a retreating entity being at `(0,0)` is unverified.
- The untagged branch at `:483` emits no `reason`, so it is invisible to reason-based
  instrumentation. Two `crowded_frontier` raiders got a `(35,35)` target from some non-reason-tagged
  branch that was not identified; that may be this one or something else.

## Implementation Notes

_To be completed by the implementer._

## Test Summary

_To be completed by the implementer._

## Files Changed

_To be completed by the implementer._

## Completion Summary

_To be completed by the implementer._
