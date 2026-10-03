---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20261003-GLOBAL-RAID-SPAWNS-AT-HARDCODED-ORIGIN-OUTSIDE-EVERY-REGION
artifact_type: plan
tags: [world, root-cause]
---

# Plan — global raid anchored at `(0,0)`

**Decision: share the camp path's notion of a raidable settlement, with a region-centre fallback.
Owner-approved 2026-10-03** (AC-1).

## Why this shape and not the alternatives

The owner chose "share the camp path's target-selection" over retiring the global raid and over
per-region raids. Two amendments came out of implementation, both forced by measurement:

1. **Share the *definition*, not the *selection*.** `city_places()` is the shared "what counts as a
   raidable settlement" set. The two callers select within it differently and must: the camp path takes
   the city nearest its camp, while the global path has no anchor to be near. Forcing one selection
   function would have meant inventing an arbitrary reference point for the global path.
2. **A region-centre fallback is required.** Anchoring strictly on a city changes raid *frequency* in
   city-less worlds, which broke `test_phase9_stability::test_1000_tick_stability`. The defect is
   placement; frequency must not move. See `investigation.md` §3(a).

Rejected and why, recorded so it is not re-litigated: *retire the global raid* (the owner did not pick
it, and it is a scope question beyond a bug fix); *per-region raids* (a design change, which row 7
parks).

## Steps

1. `src/world/raid.py` — add `city_places(state)`: CITY places sorted by `place_id`. Sorted so the
   global pick never depends on dict ordering. **Note the field is `place_id`, not `id`** — my first
   attempt used `.id` and the test caught it.
2. `src/world/raid.py` — add `global_raid_anchor(state) -> Optional[tuple]`: city → region centre →
   `None`. Both picks deterministic via the seeded RNG with `sub_id=1`/`sub_id=2`, deliberately distinct
   from `spawn_raid`'s own angle draw at `(Domain.CALAMITY, state.tick, 0)` default sub_id.
3. `src/world/raid.py` — `check_for_raid` passes `origin=anchor, target=anchor`. Both, so `spawn_raid`
   draws its ring *around* the anchor and sends raiders *at* it. Cadence gate untouched.
4. **Do not touch `src/world/camp.py`.** AC-4 requires its behaviour unchanged, and adopting
   `city_places()` there would change tie-breaking from dict order to id order — an improvement, but a
   behaviour change this ticket did not scope. Left as a seam for a later ticket.
5. Tests — see `test_plan.md`.
6. `docs/guidelines/intentional_divergences.md` §2.64, rationale class **Bug Fix** (AC-5).
7. `docs/parity_ledger/world_dynamics.yaml` `WORLD-032` — new `test_path`, real `v2_evidence`,
   `divergence_note`. This entry was **P0 with `test_path: null`**; it now has a pinned test instead of
   a checklist assertion.

## Scope guards

- **`spawn_raid` itself is not modified.** Its ring geometry, scatter grid and `max_active_projects=0`
  signal (TCK-20260913) are load-bearing elsewhere and out of scope.
- Do not change raid size, cadence, the tick-0 exclusion or mob kind.
- Do not touch the camp path.
- Do not fold in `TCK-20260908-RAID-SIZE-FORMULA-DOC-CODE-MISMATCH` (open, same service).
- No cleanup of raider debris in existing saved states.

## Acceptance-criteria map

| AC | Discharged by |
|---|---|
| 1 — origin/target decision recorded with reasoning | This file, plus the two amendments above |
| 2 — raiders land inside a region, test fails on today's code | `test_global_raid_raiders_land_inside_a_region`, confirmed failing on the `(0,0)` code |
| 3 — `region_id` not `None` for a fresh raider | Same test (in-bounds check is the observable form of it) |
| 4 — camp path unchanged, asserted | `camp.py` untouched; whole `tests/unit/world/` + `tests/integration/world/` green |
| 5 — behaviour change recorded with rationale class + ledger | §2.64 (**Bug Fix**) and `WORLD-032` |
| 6 — measurement re-run after the fix and positions reported | **PARTIAL — see below.** Unit-level geometry pinned deterministically; no post-fix full-sim re-measurement run |

**AC-6 is deliberately only partially discharged, and that is stated rather than glossed.** The unit
tests pin the ring geometry and the anchor exactly, and the pre-fix measurement is in the ticket. What
is *not* done is a post-fix 1100-tick corpus run reporting the new coordinates and the downstream
effect of raiders now being live inside regions. That effect is real (engagements, influence,
population) and unmeasured. It is named in the Completion Summary as a known gap rather than claimed.
