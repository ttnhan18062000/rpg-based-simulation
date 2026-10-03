---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20261003-GLOBAL-RAID-SPAWNS-AT-HARDCODED-ORIGIN-OUTSIDE-EVERY-REGION
phase: open
date: 2026-10-03
tags: [world, root-cause]
---

# TCK-20261003-GLOBAL-RAID-SPAWNS-AT-HARDCODED-ORIGIN-OUTSIDE-EVERY-REGION

## Title

The global tick-cadence raid spawns on a radius-25 ring around hardcoded `(0,0)`, placing every raider
outside every region where it is inert for the rest of the run

## Status

OPEN

## Tier

standard

## Type

bug

## Priority

P1

## Request Summary

`RaidService.check_for_raid` calls `spawn_raid(..., origin=(0, 0), target=(0, 0), ...)` with literal
zeros (`src/world/raid.py:41`). `spawn_raid` then places raiders on a ring of radius
`SANCTUARY_RADIUS + 10` = **25** around that origin. The `(0,0)` hardcode encodes a
single-settlement-at-origin world that the current multi-region corpus worlds are not.

**This answers a question an earlier ticket explicitly recorded and left open.**
`TCK-20260908-CAMP-RAID-ORIGIN-SPAWN-FIX` fixed the *camp-triggered* path and deliberately left this
caller byte-identical, stating in its own Open Questions: *"Confirm whether the existing global
(non-camp) raid path should keep its `(0,0)` assumption or share the same target-selection logic. The
`(0,0)` hardcode encodes a single-settlement-at-origin"*. `check_for_raid`'s docstring says the same
thing: it keeps *"the same (0,0)-anchored origin/target it always used"*. So the behaviour is known;
what was missing is evidence of its consequence. **This ticket supplies that evidence.**

**Measured, not inferred** — instrumented runs through the real pipeline at `958aa103d`, with
`audit_mode=True` and `max_tick_budget_ms` raised (`dropped_work_total == 0`, so no count is an
INFRA-273 throttle artifact), `LocalSequentialExecutor`, repeated with a byte-identical summary:

| world / seed | tick | spawned positions | nav target |
|---|---|---|---|
| `frontier_marches` / 42 | 500 | (4,-25) (5,-25) (6,-25) | (0,0) |
| `frontier_marches` / 42 | 1000 | (-21,12) (-20,12) (-19,12) | (0,0) |
| `crowded_frontier` / 7 | 500 | (13,19) (14,19) (15,19) | (0,0) |
| `crowded_frontier` / 7 | 1000 | (-25,0) (-24,0) (-23,0) | (0,0) |

All 12 raiders were confirmed present in the authoritative final state (`state.entities`,
`active=True`), so this is applied durable state and not a discarded update.

**The consequence, which is the actual defect:** `frontier_marches`' nine region bounds all start at
≥ 10 (`hometown` `(10,10,40,40)` … `swamp_border_territory` `(180,80,220,120)`). The raiders landed at
negative coordinates with `navigation.region_id = None` — **outside every region** — and had **not
moved at all** 100–600 ticks later (final position == spawn position, nav target rewritten to their own
position). They are inert, regionless entities in the playable world's authoritative state. In
`crowded_frontier`/7 the tick-500 raiders did walk to their `(0,0)` target, leaving entity 40 at
exactly `(0.0, 0.0)` at tick 1100.

So the global raid mechanic effectively **does not function** in multi-region worlds: it consumes
entity ids and state, produces no raid, and leaves permanent debris.

## Scope

- Decide what the global raid's origin and target should be, and record the decision. The adjacent
  camp path already answers the analogous question (`src/world/camp.py` passes `origin=camp.position`,
  `target=nearest_city.position`), so "share the camp path's target-selection logic" is the obvious
  candidate but is **not** assumed here.
- Replace the `(0,0)` literals in `check_for_raid` with the chosen derivation.
- Decide and record what happens to raiders that spawn outside every region — whether that should be
  representable at all, or clamped/rejected at spawn.
- A test asserting spawned raiders land inside some region, so a future regression cannot silently
  reintroduce an out-of-world spawn.

## Out of Scope

- The **camp-triggered** raid path. Already fixed by `TCK-20260908-CAMP-RAID-ORIGIN-SPAWN-FIX`; it
  passes a real origin and target and must not be changed here.
- The raid size formula — `TCK-20260908-RAID-SIZE-FORMULA-DOC-CODE-MISMATCH` owns that and is still
  open. Do not fold the two.
- Cleaning up raider debris in existing saved states. Separate concern if anyone wants it.
- Raid balance, frequency or difficulty. `owner_decision_memo.md` row 7 parks tuning.

## Acceptance Criteria

1. A decision is recorded for the global raid's origin and target, with the reasoning, rather than
   silently adopting the camp path's logic.
2. Raiders spawned by `check_for_raid` land inside a region. Asserted by a test that would fail on
   today's code.
3. `navigation.region_id` is not `None` for a freshly spawned raider.
4. The camp path's behaviour is unchanged, asserted.
5. Any behaviour change is recorded in `docs/guidelines/intentional_divergences.md` with a rationale
   class, and the relevant `docs/parity_ledger/` entry updated.
6. The measurement is re-run after the fix and the raider positions reported — on the same two worlds
   and seeds, with `audit_mode=True` and a raised tick budget, or the numbers are throttle artifacts.

## Related Tickets

- `TCK-20260908-CAMP-RAID-ORIGIN-SPAWN-FIX` (done) — fixed the camp path, deliberately left this one,
  and **recorded this exact open question**. Read its Open Questions before planning.
- `TCK-20260908-RAID-SIZE-FORMULA-DOC-CODE-MISMATCH` (open) — same service, different defect.
- `TCK-20260919-PERF-SCENARIO-METROPOLIS-SPAWN-COLLISION` (open) — adjacent spawn-placement concern;
  check for overlap before scheduling.

## Related Docs

- `docs/mechanics/05_world_evolution.md` — calamities and world evolution
- `docs/mechanics/06_worldbuilding_foundation.md` — region topology and bounds
- `docs/parity_ledger/world_dynamics.yaml`

## Related Stored Artifacts

- None yet. The measurement supporting this ticket was a bounded probe run under work-order item 4; its
  numbers are reproduced in full in this ticket's Request Summary rather than kept in a separate file.

## Related Code Areas

- `src/world/raid.py:41` — `check_for_raid`, the hardcoded `origin=(0, 0), target=(0, 0)`
- `src/world/raid.py` — `spawn_raid`, the radius-25 ring (`SANCTUARY_RADIUS + 10`)
- `src/world/camp.py` — the already-fixed caller, the contrast case
- `src/engine/world_dynamics.py:188` — the calling site inside `resolve_dynamics`
- `src/engine/pipeline.py:348` — `world_dynamics` phase

## Assumptions / Open Questions

- Whether a single global raid should target a settlement at all, or whether the mechanic is better
  expressed as per-region raids, is a design question this ticket does not pre-judge.
- The camp-triggered path **never fired** in either world within 1100 ticks (it needs
  `camp.maturity >= RAID_MATURITY_THRESHOLD`), so there is **no measured comparison** of a correct
  raid's coordinates — only the in-repo code. If a correct-path baseline is wanted, that gate has to
  be reached or forced first.
- Whether any consumer already depends on raiders being at `(0,0)` is unverified.

## Implementation Notes

_To be completed by the implementer._

## Test Summary

_To be completed by the implementer._

## Files Changed

_To be completed by the implementer._

## Completion Summary

_To be completed by the implementer._
