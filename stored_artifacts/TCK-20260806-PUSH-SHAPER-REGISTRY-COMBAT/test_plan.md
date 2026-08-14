---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260806-PUSH-SHAPER-REGISTRY-COMBAT
artifact_type: test_plan
tags: [observability, engine, combat, simulation-quality]
---

# test_plan.md — TCK-20260806-PUSH-SHAPER-REGISTRY-COMBAT

## Scope of testing

New module `src/observability/event_shapers.py` and its wiring into `kernel.py`'s
`_phase_observability()`. `event_extractor.py`, `apply.py`, `apply_plan.py` untouched — no
regression risk there, confirmed via diff rather than assumed.

## Tests

- `tests/unit/observability/test_event_shapers.py` (new file):
  - Registry mechanism: a dummy shaper registered and invoked correctly.
  - `CombatShaper`: `combat_initiated`/`combat_damage`/`near_death_survival`/`entity_killed` fire
    correctly from `prior_state`+`update` alone (no `current_state` needed) for real combat.
  - Hazard-tagged and biological-pattern (attacker_id=None, outcome_kind="SURVIVE") updates produce
    no combat events — same collision risk the hotfix ticket found, re-verified for the new path
    independently (do not assume the hotfix's fix generalizes without a direct test).
  - `hazard_drain_applied`/`hero_death_unrecorded` fire correctly (Decision 1).
  - `entity_killed` is emitted directly (not `combat_kill`), per plan.md's naming decision.
  - `run_shadow_shapers()` under `ENABLE_PUSH_EVENT_SHAPERS=OFF`/`"SHADOW"`: confirms events are
    constructed in SHADOW mode but never delivered to a mock `BoundedObservabilityQueue`/
    `EventRecorder`.
- `tests/unit/kernel/` (existing kernel tests): scoped run to confirm no existing kernel test
  breaks from the new `_phase_observability()` call, since that method is exercised by kernel-level
  tests even though this ticket's own logic is unit-tested separately.

## Out of scope for this ticket's testing

- Corpus-wide comparison against the old diffing path — `TCK-20260806-PUSH-SHADOW-VALIDATION-PERF`'s
  scope.
- Performance measurement — same.
