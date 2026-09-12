# Test Plan — TCK-20260908-DEGRADED-POLICY-NONURGENT-MOVEMENT-STARVATION

## Unit coverage (`tests/unit/domains/optimization/test_movement_candidate_selector.py`)

- `test_exact_dirty_excludes_starved_entity_off_its_reduced_cadence_tick` -- off-cadence tick,
  entity with a real unreached target stays excluded under `EXACT_DIRTY`.
- `test_exact_dirty_admits_starved_entity_on_its_reduced_cadence_tick` -- the fix itself: same
  entity, on-cadence tick, now admitted.
- `test_exact_dirty_reduced_cadence_still_respects_real_readiness_gate` -- low-readiness entity
  stays excluded even on its cadence tick (the gate is a real gameplay constraint, not bypassed).
- `test_exact_dirty_still_admits_genuinely_urgent_entities_every_tick` -- the 5 existing urgency
  bypasses are untouched; a `target_changed` entity is selected every tick, not only on cadence.
- `test_exact_dirty_admits_only_a_bounded_fraction_per_tick` -- 200 starved entities, exactly the
  cadence-eligible subset selected (not all 200) -- proves work-shedding is preserved, not
  defeated.

## Real-Kernel regression (`tests/integration/world/test_camp_raid_targeting.py`)

Extended the existing real-Kernel raid-spawn test (unmodified spawn/targeting assertions) with a
further real-tick run spanning a full reduced-cadence window (20+5 ticks) after the raiders spawn,
asserting at least one raider shows real net movement by the end of that window -- proves the fix
holds in the exact real-world scenario that originally surfaced the starvation, not only in
isolated unit construction.

## Real-Kernel acceptance-bar verification (scratch, per `rpg-feature-planning`'s explicit ask --
not committed as a test, reproducible via the same construction as the prior measurement scripts)

Re-ran the real 300-entity sustained-load scenario with a fresh mid-run spawn injected after
DEGRADED was independently confirmed active: 5/5 injected raiders now show real movement within
the 15-tick post-injection window (each moved at least once, at different ticks matching their own
`entity_id`-based cadence offset). DEGRADED stayed engaged throughout the same window (real
`tick_compute_ms` continued exceeding budget, real watchdog alerts) -- the governor was not
neutralized by the fix.

## Regression sweep

`pytest tests/unit/kernel/ tests/unit/resource/ tests/unit/domains/optimization/
tests/integration/world/test_camp_raid_targeting.py tests/integration/kernel/ -q -m "not slow and
not extra_slow"`: 384 passed, 1 skipped, 3 deselected -- no regression.
