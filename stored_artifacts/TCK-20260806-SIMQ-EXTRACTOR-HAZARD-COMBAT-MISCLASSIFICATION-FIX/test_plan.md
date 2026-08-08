---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260806-SIMQ-EXTRACTOR-HAZARD-COMBAT-MISCLASSIFICATION-FIX
artifact_type: test_plan
tags: [observability, combat, simulation-quality]
---

# test_plan.md — TCK-20260806-SIMQ-EXTRACTOR-HAZARD-COMBAT-MISCLASSIFICATION-FIX

## Scope of testing

`src/observability/event_extractor.py` only. Confirmed via grep that no other module in `src/`
imports `combat_upd` or otherwise depends on the buggy attribute name. Confirmed via grep across
`tests/simulation_quality/` and `tests/integration/observability/` that none of those test files
import or call `EventExtractor` directly — they hand-construct events/envelopes, unaffected by
this change.

## Tests run

- `tests/unit/observability/test_event_extractor_simq.py` — 25 tests (21 pre-existing + 4 new),
  all pass. 3 pre-existing tests' mocks corrected (wrong attribute name), 2 pre-existing tests
  updated to supply a valid combat mock (previously relied on the bug to fire an event with no
  causal data at all).
- `tests/unit/observability/test_event_extractor_world.py` — 18 tests (17 pre-existing + 1 new),
  all pass.
- Full `tests/unit/observability/` directory — 759 passed, 6 skipped (unchanged skip count from
  before this change).

## New regression coverage added

- `test_combat_initiated_not_emitted_for_hazard_damage` / `test_near_death_survival_not_emitted_for_hazard_damage`
  — hazard-tagged HP loss does not fire combat events.
- `test_combat_initiated_not_emitted_for_biological_damage` — directly targets the Bug 3 finding
  (biological/starvation damage relies on `CombatUpdate`'s default `outcome_kind="SURVIVE"`, which
  a naive outcome_kind-only allow-list would have let through).
- `test_combat_damage_attacker_id_populated_for_real_combat` — proves `attacker_id` is now
  correctly populated for genuine combat, not always `None` as before.
- `test_hazard_damage_not_misclassified_as_combat` (`test_event_extractor_world.py`) — the one
  test in the suite that actually varies prior/curr HP for a hazard scenario, proving
  `hazard_drain_applied` fires while `combat_damage`/`combat_initiated` correctly do not.

## Out of scope for this ticket's testing

- Full calibration-corpus re-run — deferred to the migration epic's dedicated validation ticket
  (`TCK-20260806-PUSH-SHADOW-VALIDATION-PERF`), per plan.md's acceptance-criteria-map reasoning.
- Performance/perf-harness re-run — this fix adds O(1) attribute checks to an already-executed
  branch, not a new loop or query; no measurable overhead expected, and the migration epic's own
  perf validation ticket will cover the broader observability-path performance question properly.
