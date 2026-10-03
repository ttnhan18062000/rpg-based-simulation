---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20261003-GLOBAL-RAID-SPAWNS-AT-HARDCODED-ORIGIN-OUTSIDE-EVERY-REGION
phase: done
date: 2026-10-03
tags: [world, root-cause]
---

# TCK-20261003-GLOBAL-RAID-SPAWNS-AT-HARDCODED-ORIGIN-OUTSIDE-EVERY-REGION

## Title

The global tick-cadence raid spawns on a radius-25 ring around hardcoded `(0,0)`, placing every raider
outside every region where it is inert for the rest of the run — RETIRED, not re-anchored

## Status

DONE

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

**Outcome: the global world-clock raid is RETIRED.** `RaidService.check_for_raid` and its
`world_dynamics` step-3.5 call site are removed. `spawn_raid` survives as the camp path's composition
logic, and `src/world/camp.py` is untouched — camp-triggered raids are now the only raid mechanic.

**A re-anchoring fix was implemented, measured and WITHDRAWN.** It anchored on a `PlaceKind.CITY` with
a region-centre fallback, passed its unit tests, and was committed as `509009d41`. A post-fix corpus
measurement (8 runs, `audit_mode=True`, `max_tick_budget_ms=1e9`, `dropped_work_total == 0`, each world
repeated byte-identically, with a same-harness pre-fix control arm) then killed it on four counts:

1. **11 of 12 re-anchored spawns were still outside every region.** A radius-25 ring around a city
   centred in a 30-wide region necessarily lands outside it. **My own AC-2/AC-3 test passed only
   because its fixture used a 60-wide region** — it asserted a property real corpus worlds do not
   satisfy. That is the sharpest mistake in this ticket.
2. **`src/engine/tactical.py:141` `PANIC_RETREAT` overwrites a raider's target with the same hardcoded
   `(0.0, 0.0)`** within 15–38 ticks of spawn; 10 of 12 raiders walked *past* the city to the world
   origin and idled there. Re-anchoring would have shipped a feature that still did not work. Filed as
   `TCK-20261003-TACTICAL-RETREAT-TARGETS-HARDCODED-WORLD-ORIGIN`.
3. **In `frontier_marches` it changed nothing measurable** — zero raider combat in both arms, zero
   raider deaths, bit-identical final influence and ownership. In `crowded_frontier` it did come alive
   (raider-as-defender attacks 6 → 158, 3 raiders killed, `hometown` influence +15 of 200), but raiders
   killed nothing in any run and no region's owner changed in either arm.
4. **It activated a behaviour the world has never had**, which is an Intentional Gameplay Change parked
   by `owner_decision_memo.md` row 7 — and it made the `Bug Fix` rationale class wrong.

The rule layer ruled the same way independently (memo row 9): **PLACE-01** rules out a geometric region
centre as a destination (a bare coordinate is not a Place), and **CAUSE-01 / ID-04 / ORG-03** require a
raid to have a real causal and organizational origin, which a world clock is not. If world-clock raids
return, they do so as a declared feature with a settlement-Place predicate (SETT-01, **not** `== CITY`),
no coordinate fallback, and `PANIC_RETREAT` fixed first.

Also recorded: `NewStateUpdate` is bound inside earlier conditional branches in `world_dynamics`, so an
unconditional use of it raises `UnboundLocalError`; step 3.5 imports it locally.

## Test Summary

New: `tests/unit/world/test_global_raid_retired.py` (4 tests), including a **positive control**
(`test_camp_triggered_spawn_raid_still_works`) that proves the absence assertions pass because the
cadence path is gone rather than because raid composition broke. `test_global_world_clock_raid_surface_is_absent`
asserts the entry point is *removed*, not guarded, and that the withdrawn helpers do not linger.

Changed, each because it called or encoded the retired path, with reasons in §2.64:
`test_raid_spawn_origin.py` deleted (it tested the withdrawn fix); `test_calamity_raid.py` ×2 and
`test_guild_need_scorer.py` ×1 rebased onto `spawn_raid`; `test_world_dynamics_raid_spawning` inverted
to assert retirement; `test_phase9_stability::test_1000_tick_stability` monster floor 2 → 1.

**That floor change is a finding, not a relaxation.** The fixture declares no places, so no camp raid
and no boss spawn — the retired global raid was its *only* monster source, and the old floor of 2 was
being met by raiders that spawned outside every region and never moved or fought.

Scope: `tests/unit/world/` + `tests/integration/world/` + `tests/unit/engine` + `tests/unit/ai` =
**638 passed, 1 skipped**. Pre-existing `test_long_run_stability` deselected — `TimeoutError` on clean
`src/` too, reported not silenced.

## Files Changed

- `src/world/raid.py` — `check_for_raid` removed (and the withdrawn `global_raid_anchor`/`city_places`); retirement recorded in a comment block; `spawn_raid` untouched
- `src/engine/world_dynamics.py` — step 3.5 contributes an empty update
- `tests/unit/world/test_global_raid_retired.py` (new), `tests/unit/world/test_raid_spawn_origin.py` (deleted)
- `tests/unit/world/test_calamity_raid.py`, `tests/unit/world/test_world_dynamics.py`, `tests/unit/ai/test_guild_need_scorer.py`, `tests/integration/world/test_phase9_stability.py`
- `docs/guidelines/intentional_divergences.md` §2.64 (rewritten for retirement)
- `docs/parity_ledger/world_dynamics.yaml` `WORLD-032` (restated; was P0 with `test_path: null`)
- `docs/plans/systemic_world/owner_decision_memo.md` (row 9), `docs/plans/systemic_world/roadmap.md` (item 6 sub-bullet, §10 count and list) — `world-rule-catalog-design`'s verbatim text, all four anchors re-verified unique at HEAD
- `agent-working/staging_artifacts/TCK-20261003-GLOBAL-RAID-SPAWNS-AT-HARDCODED-ORIGIN-OUTSIDE-EVERY-REGION/`

## Completion Summary

Closed 2026-10-03. The global world-clock raid is retired; the camp-triggered path survives.

**This ticket's own fix was withdrawn after measurement, and that is the most useful thing in it.**
Three ACs (2, 3) are moot because no raiders are created at all, and they are marked moot in `plan.md`
rather than quietly dropped. AC-6 — the post-fix corpus measurement — is the AC that reversed the
decision, which is the argument for having required it.

Recorded gaps, none glossed:

1. **`tactical.py`'s three hardcoded `(0.0, 0.0)` retreat destinations remain live** for every entity
   that retreats, not just raiders. Filed as
   `TCK-20261003-TACTICAL-RETREAT-TARGETS-HARDCODED-WORLD-ORIGIN`. Whether non-raider kinds reach those
   branches is **not measured** and the ticket says so.
2. **The phase9 stress fixture now has no monster source at all.** Floor 1 is honest for what it can
   guarantee; a fixture with a CAMP would be better and is out of scope.
3. **One unexplained measurement divergence** between the two probe harnesses on whether three pre-fix
   raiders moved (`investigation.md` §6a). Both agree on 12/12 off-region at spawn, which is the
   load-bearing fact.
4. **Raiders killed nothing and no region changed owner in any arm.** Even a functioning raid moved
   `hometown` influence by 15 of 200 points. The influence/ownership channel remains essentially
   unresponsive to raids — relevant to the `regional_sovereignty` near-inert verdict and its expiry
   clause.
