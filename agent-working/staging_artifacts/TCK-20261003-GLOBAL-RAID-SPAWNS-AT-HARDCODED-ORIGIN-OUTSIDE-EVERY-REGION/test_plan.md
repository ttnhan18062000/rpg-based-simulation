---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20261003-GLOBAL-RAID-SPAWNS-AT-HARDCODED-ORIGIN-OUTSIDE-EVERY-REGION
artifact_type: test_plan
tags: [world, root-cause, testing]
---

# Test plan — global raid anchored at `(0,0)`

## Proof Plan

| AC | level | proof kind | oracle source | expected effect | selected commands |
|---|---|---|---|---|---|
| 1 — origin/target decision recorded | n/a | record | `plan.md`; `TCK-20260908-CAMP-RAID-ORIGIN-SPAWN-FIX` Open Questions | A written decision naming the city→region fallback and why frequency must not move | none — not test-provable |
| 2 — raiders land inside a region | unit | new regression test | `docs/mechanics/06_worldbuilding_foundation.md` (region bounds); measured defect in the ticket | Every spawned raider inside some region's bounds; fails on the `(0,0)` code | `pytest tests/unit/world/test_raid_spawn_origin.py::test_global_raid_raiders_land_inside_a_region -q` |
| 3 — `region_id` not None for a fresh raider | unit | new regression test | same | In-bounds is the observable form; same test | `pytest tests/unit/world/test_raid_spawn_origin.py::test_global_raid_raiders_land_inside_a_region -q` |
| 4 — camp path unchanged | unit+integration | regression (unchanged behaviour) | `src/world/camp.py` as its own oracle; untouched by this ticket | No camp behaviour moves; whole world suite green | `pytest tests/unit/world/ tests/integration/world/ -q -m "not slow and not extra_slow"` |
| 5 — behaviour change recorded | n/a | record | `docs/guidelines/intentional_divergences.md` §2.58/§2.59 shape | §2.64 exists, class **Bug Fix**; `WORLD-032` updated | `python3 -c "import yaml; yaml.safe_load(open('docs/parity_ledger/world_dynamics.yaml'))"` |
| 6 — post-fix measurement re-run and positions reported | integration | corpus run | the pre-fix measurement in the ticket as the comparison arm | Raiders spawn on the anchor's outskirts, inside a region, and are no longer inert | see T3 |

## T1 — new regression tests

`tests/unit/world/test_raid_spawn_origin.py`, 7 tests:

| test | guards |
|---|---|
| `test_global_raid_spawns_near_a_city_not_at_world_origin` | ring is drawn around the city; target is the city |
| `test_global_raid_raiders_land_inside_a_region` | **AC-2/AC-3**: nothing spawns out of world |
| `test_global_raid_falls_back_to_a_region_when_no_city_exists` | **frequency is unchanged** — the raid still fires without a city |
| `test_global_raid_does_not_fire_with_nowhere_to_raid` | no anchor at all → no spawn into empty space |
| `test_global_raid_city_choice_is_deterministic` | same seed+tick → same choice |
| `test_city_places_is_sorted_and_filters_non_cities` | the shared settlement definition |
| `test_global_raid_still_gated_by_cadence` | cadence and the tick-0 exclusion unchanged |

**Positive control, run and recorded:** restoring the `(0,0)` literals and re-running fails 6 of these
(the 4 behavioural ones plus the two updated pre-existing tests) and leaves the cadence/determinism/
helper tests passing. The failure coordinates `(4.0, -25.0) (5.0, -25.0) (6.0, -25.0)` **match the
full-sim probe's `frontier_marches`/42 tick-500 observation exactly** — independent corroboration
between a 1100-tick instrumented run and a unit fixture.

## T2 — three pre-existing tests updated, with reasons

Not relaxed to pass; each encoded the old assumption and its update is recorded in §2.64.

1. `test_calamity_raid_spawning` — asserted `navigation.target == (0, 0)` outright. Now asserts the
   city's position; a CITY place added to the fixture (every corpus world has exactly one).
2. `test_world_dynamics_raid_spawning` — count-only test whose fixture had no places. City added.
3. `test_calamity_raid_spawn_positions_unchanged_by_spawn_raid_extraction` → renamed
   `..._are_the_ring_around_the_chosen_anchor`. It recomputed positions from a zero origin **and was
   passing vacuously** once the anchor existed: no anchor meant no raiders, so the assertion loop never
   ran. Now recomputes from `global_raid_anchor()` and carries an explicit `assert update.entities_add`
   so it can never silently assert nothing again.

## T3 — scope run, and the AC-6 corpus re-measurement

```
PYTHONPATH=. /home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3 \
  -m pytest tests/unit/world/ tests/integration/world/ tests/unit/engine \
  -q -m "not slow and not extra_slow" \
  --deselect tests/integration/world/test_long_run_stability.py::test_long_run_stability
```
Result: **594 passed, 1 skipped** — including `test_phase9_stability::test_1000_tick_stability`, which
the first (frequency-changing) implementation broke.

AC-6's corpus re-measurement must set `audit_mode=True` and raise `max_tick_budget_ms`, or
`kernel.py:612-620` drops authoritative result items and the numbers measure the throttle
(`INFRA-273`). The pre-fix arm did both (`dropped_work_total == 0`) and the post-fix arm must match it.

## Pre-existing failures — reported, not fixed, not masked

- `tests/integration/world/test_long_run_stability.py::test_long_run_stability` — `TimeoutError`,
  deselected above and failing on clean `src/` too (verified earlier this session). Not caused here,
  not silenced in the committed state beyond the explicit deselect in this one command.

## Not tested, deliberately

No test asserts which *specific* city is chosen when several exist, because every corpus world has
exactly one and pinning a particular index would encode an arbitrary choice. Determinism of the choice
is asserted; its identity is not.
