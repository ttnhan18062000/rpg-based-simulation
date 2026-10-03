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

**Rewritten for retirement.** The earlier version's table proved the withdrawn re-anchoring fix; three
of its rows are now moot and say so rather than disappearing.

| AC | level | proof kind | oracle source | expected effect | selected commands |
|---|---|---|---|---|---|
| 1 — decision recorded with reasoning | n/a | record | `plan.md`; `owner_decision_memo.md` row 9; PLACE-01 / CAUSE-01 / ID-04 / ORG-03 | A written retirement decision with the rule-layer basis | none — not test-provable |
| 2 — raiders land inside a region | unit | **moot, superseded** | — | No raiders are created at all; the re-anchored version failed this in real worlds (11/12 off-region) while passing on an unrepresentative fixture | `pytest tests/unit/world/test_global_raid_retired.py::test_no_entity_is_created_at_the_world_origin_ring_on_the_cadence_tick -q` |
| 3 — `region_id` not None for a fresh raider | unit | **moot** | — | No fresh raider exists | same as AC-2 |
| 4 — camp path unchanged | unit | regression + positive control | `src/world/camp.py` untouched | `spawn_raid` still composes raiders correctly | `pytest tests/unit/world/test_global_raid_retired.py::test_camp_triggered_spawn_raid_still_works -q` |
| 5 — behaviour change recorded | n/a | record | `intentional_divergences.md` §2.58/§2.59 shape | §2.64 exists, class **Bug Fix**; `WORLD-032` restated with a real `test_path` | `python3 -c "import yaml; yaml.safe_load(open('docs/parity_ledger/world_dynamics.yaml'))"` |
| 6 — post-fix corpus measurement | integration | corpus run | the pre-fix arm as same-harness control | **Discharged, and it reversed the decision** — see `investigation.md` §6 | 8 runs, `audit_mode=True`, `max_tick_budget_ms=1e9`, `dropped_work_total == 0`, repeat byte-identical |

## T1 — retirement tests

`tests/unit/world/test_global_raid_retired.py`:

| test | guards |
|---|---|
| `test_global_world_clock_raid_surface_is_absent` | `check_for_raid` is **gone**, not guarded — a guarded entry point invites re-enabling a never-functional mechanic. Also asserts the withdrawn `global_raid_anchor`/`city_places` helpers do not linger |
| `test_no_raiders_spawn_on_the_former_cadence_tick` | nothing spawns at tick 500 |
| `test_no_entity_is_created_at_the_world_origin_ring_on_the_cadence_tick` | the actual defect: no durable entity outside every region |
| `test_camp_triggered_spawn_raid_still_works` | **positive control** — the absence assertions pass because the cadence path is gone, not because raid composition broke |

`tests/unit/world/test_world_dynamics.py::test_world_dynamics_no_longer_spawns_a_global_raid_on_the_cadence_tick`
inverts the former spawn assertion.

## T2 — tests changed, each with its reason

Not relaxed to pass; each called or encoded the retired path. All recorded in §2.64.

1. `tests/unit/world/test_raid_spawn_origin.py` — **deleted**; it tested the withdrawn fix.
2. `test_calamity_raid_spawning` and
   `test_calamity_raid_spawn_positions_are_the_ring_around_the_given_origin` — rebased onto
   `spawn_raid` with an explicit origin. What they really exercise is composition, which survives.
   The second one had **passed vacuously** in an interim revision (empty `entities_add`, so its loop
   never ran) and now carries an explicit non-empty assertion.
3. `tests/unit/ai/test_guild_need_scorer.py::test_real_spawned_raid_mob_scores_zero_guild_utility` —
   switched to `spawn_raid`; it needs a real raid mob, which that still produces. Its own sanity
   assertion is kept.
4. `test_phase9_stability::test_1000_tick_stability` — monster floor **2 → 1**, reason in its
   docstring: the fixture declares no places, so no camp raid and no boss spawn; the retired global
   raid was its **only** monster source and the old floor was met by inert off-map raiders. Pinning the
   count of a non-event is not a world semantic.

## T3 — scope run

```
PYTHONPATH=. /home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3 \
  -m pytest tests/unit/world/ tests/integration/world/ tests/unit/engine tests/unit/ai \
  -q -m "not slow and not extra_slow" \
  --deselect tests/integration/world/test_long_run_stability.py::test_long_run_stability
```
Result: **638 passed, 1 skipped.**

## Pre-existing failures — reported, not fixed, not masked

- `test_long_run_stability` — `TimeoutError`, deselected above, fails on clean `src/` too (verified
  earlier this session). Not caused here and not silenced beyond that one explicit deselect.

## Not tested, deliberately

No test asserts anything about *where* a world-clock raid would spawn, because there is no longer such
a raid. If one returns as a declared feature it needs its own tests, a settlement-Place predicate
(SETT-01, not `== CITY`), no coordinate fallback, and `TCK-20261003-TACTICAL-RETREAT-TARGETS-HARDCODED-WORLD-ORIGIN`
fixed first — otherwise `PANIC_RETREAT` will swallow it exactly as measured here.
