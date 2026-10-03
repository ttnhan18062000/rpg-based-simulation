---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260908-CAMP-RAID-ORIGIN-SPAWN-FIX
artifact_type: test_plan
tags: [world, content]
---

# Test Plan — TCK-20260908-CAMP-RAID-ORIGIN-SPAWN-FIX

## Coverage Map

1. **Discard bug fixed** — `test_camp_raid_trigger` (`tests/unit/world/test_camp_lifecycle.py`),
   updated to seed a real CITY place and assert `entities_add` actually contains a
   `goblin_raider`, not just correct maturity bookkeeping.
2. **No-CITY skip, cost not charged** — new
   `test_camp_raid_trigger_skips_entirely_with_no_city_place_no_cost_charged`: the one place peer
   review flagged this fix could regress into its own bug (charging cost for a raid that didn't
   happen). Asserts both no raiders AND unchanged (growth-only) `maturity_delta`.
3. **Global path unchanged** — new `test_calamity_raid_spawn_positions_unchanged_by_spawn_raid_extraction`
   (`tests/unit/world/test_calamity_raid.py`): independently recomputes the expected spawn
   position from the same RNG call and asserts exact equality, proving the `spawn_raid()`
   extraction didn't alter `check_for_raid()`'s own observable behavior (the Out of Scope
   guarantee).
4. **Real spawn + real anchoring + real targeting** — new
   `tests/integration/world/test_camp_raid_targeting.py`: a real `Kernel` run against
   `camp_maturity_calibration_pilot` proving raiders spawn near the camp (not `(0,0)`) and target
   the real nearest CITY place.
5. **Existing flag/classification tests** — `test_camp_flag_off_nest_kind_camp_still_raids`,
   `test_camp_flag_on_camp_kind_still_raids`, `test_campservice_raid_and_spawn_branches_not_newly_flag_gated`
   updated to seed a CITY place (previously never actually verified a raid spawned anything, since
   the discard bug always produced zero raiders regardless).

## Regression discipline
Every new/modified assertion in items 1-3 confirmed to fail against the pre-fix code before
finalizing (reverted `camp.py`/`raid.py` to `HEAD`, reran, restored). See each ticket's own
Implementation Notes for the exact revert/rerun evidence.

## Deliberately not covered here
Live movement over further real ticks — investigated, found to be blocked by an unrelated,
pre-existing governor policy issue, deferred to
`TCK-20260908-DEGRADED-POLICY-NONURGENT-MOVEMENT-STARVATION` per explicit peer-review agreement.
See `CAMP-RAID-ORIGIN-SPAWN-FIX`'s own Acceptance Criteria for the full rationale.
