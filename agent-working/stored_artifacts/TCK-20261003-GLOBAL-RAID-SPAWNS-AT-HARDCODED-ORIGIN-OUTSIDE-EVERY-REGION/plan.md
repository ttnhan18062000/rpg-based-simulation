---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20261003-GLOBAL-RAID-SPAWNS-AT-HARDCODED-ORIGIN-OUTSIDE-EVERY-REGION
artifact_type: plan
tags: [world, root-cause]
---

# Plan — retire the global world-clock raid

**Decision: RETIRE `RaidService.check_for_raid` and its call site. Owner-approved 2026-10-03, and
independently ruled the same way by the rule layer (`owner_decision_memo.md` row 9).**

This plan **replaces an earlier one that re-anchored the raid on a real settlement.** That version was
implemented, measured and withdrawn; `investigation.md` §6 records why in full. The withdrawal is the
substance of this ticket, so it is stated here rather than buried.

## Why retirement rather than the fix I had already built

The hard bug is *"it creates regionless, inert entities"*. The minimal fix for that is to stop creating
them. Re-anchoring instead **activates a behaviour the world has never had** — a raid converging on a
settlement every 500 ticks, in every world — which is a gameplay change with a balance footprint, the
class row 7 parks. Four measured facts made it indefensible:

1. **11 of 12 re-anchored spawns were still outside every region**: a radius-25 ring around a city
   centred in a 30-wide region necessarily lands outside it. My own AC-2 test passed only because its
   fixture used a 60-wide region — it asserted a property real worlds do not have.
2. **`tactical.py:141` `PANIC_RETREAT` overwrites the raider target with the same hardcoded `(0.0,
   0.0)`** within 15–38 ticks, so 10 of 12 raiders walked past the city to the world origin. The fix
   would have shipped a feature that still did not function. Filed separately as
   `TCK-20261003-TACTICAL-RETREAT-TARGETS-HARDCODED-WORLD-ORIGIN`.
3. **In `frontier_marches` the fix changed nothing measurable** — zero raider combat in both arms,
   bit-identical influence and ownership.
4. It made the `Bug Fix` rationale class wrong; activating a never-functional mechanic is an
   **Intentional Gameplay Change**.

Rule layer, same conclusion: **PLACE-01** (a bare coordinate is not a Place) rules out the region-centre
fallback; **CAUSE-01 / ID-04 / ORG-03** require a raid to have a real causal and organizational origin,
and a world clock is not one. The camp path satisfies all four.

## Steps

1. `src/world/raid.py` — delete `check_for_raid`, and the withdrawn `global_raid_anchor` /
   `city_places` helpers with it. Leave a comment block recording the retirement, the measurement, and
   the conditions under which world-clock raids could return. **Keep `spawn_raid`** — it is the camp
   path's composition logic.
2. `src/engine/world_dynamics.py` — step 3.5 contributes an empty update. Note the local-import quirk:
   `NewStateUpdate` is bound inside earlier conditional branches, so an unconditional use raises
   `UnboundLocalError`; import it locally.
3. `tests/unit/world/test_global_raid_retired.py` — new, 4 tests, including a **positive control**
   (`test_camp_triggered_spawn_raid_still_works`) proving the absence assertions pass because the
   cadence path is gone, not because raid composition broke.
4. Delete `tests/unit/world/test_raid_spawn_origin.py` — it tested the withdrawn fix.
5. Rebase the three tests that called `check_for_raid` onto `spawn_raid`
   (`test_calamity_raid.py` ×2, `test_guild_need_scorer.py` ×1) and invert
   `test_world_dynamics_raid_spawning` to assert retirement.
6. `test_phase9_stability::test_1000_tick_stability` — monster floor 2 → 1, **with the reason in the
   docstring**: that fixture declares no places, so no camp raid and no boss spawn, making the retired
   global raid its only monster source. The old floor was met by inert off-map raiders.
7. `docs/guidelines/intentional_divergences.md` §2.64 — rewritten for the retirement, class **Bug Fix**,
   explicitly noting the withdrawn version carried that class wrongly.
8. `docs/parity_ledger/world_dynamics.yaml` `WORLD-032` — restated to describe the camp path, with a
   real `test_path` (it was P0 with `test_path: null`).
9. Apply `world-rule-catalog-design`'s verbatim decision text (memo row 9, roadmap item 6 sub-bullet,
   §10 count and list). All four anchors re-verified unique at my HEAD before applying.

## Scope guards

- **Do not modify `spawn_raid`.** Its ring geometry, scatter grid and `max_active_projects=0` signal
  (TCK-20260913) are load-bearing for the camp path.
- **Do not touch `src/world/camp.py`.** It is the surviving mechanic.
- Do not fix `tactical.py`'s `(0,0)` literals here — separate ticket, and it needs a rule-layer answer
  first.
- Do not fold in `TCK-20260908-RAID-SIZE-FORMULA-DOC-CODE-MISMATCH`.
- Do not redesign the phase9 stress fixture; only its floor moves, with the reason recorded.

## Acceptance-criteria map

The ticket's original ACs were written for the *re-anchoring* fix. Three are now moot and say so
explicitly rather than being quietly dropped.

| AC (original) | Outcome |
|---|---|
| 1 — origin/target decision recorded with reasoning | **Met, by retirement.** This file + memo row 9 |
| 2 — raiders land inside a region, test fails on today's code | **MOOT** — no raiders are created at all. Superseded by `test_no_entity_is_created_at_the_world_origin_ring_on_the_cadence_tick`. Worth recording that the re-anchored version **failed** this in real worlds (11/12 off-region) while passing on my fixture |
| 3 — `region_id` not None for a fresh raider | **MOOT** — no fresh raider exists |
| 4 — camp path unchanged, asserted | **Met** — `camp.py` untouched; `test_camp_triggered_spawn_raid_still_works` is the positive control |
| 5 — behaviour change recorded with rationale class + ledger | **Met** — §2.64 (Bug Fix) + `WORLD-032` |
| 6 — post-fix measurement re-run and positions reported | **Met, and it is what reversed the decision.** 8 runs, `dropped_work_total == 0`, repeat byte-identical; results in `investigation.md` §6 |

## Known gaps, stated not glossed

1. **`tactical.py`'s three `(0,0)` literals remain live** for every entity that retreats, not just
   raiders. Filed, not fixed. Whether non-raider kinds reach those branches is **not measured**.
2. **The phase9 fixture now has no monster source at all.** Lowering its floor to 1 is honest for what
   the fixture can guarantee, but a richer fixture (one with a CAMP, as every corpus world has) would be
   the better long-term fix and is deliberately out of scope.
3. **One unexplained measurement divergence**: the post-fix agent's pre-fix arm saw 3 raiders move that
   the earlier probe reported inert. Spawn coordinates agreed exactly; the movement side diverged.
   Recorded in `investigation.md` §6a, unresolved, and not load-bearing for the retirement.
