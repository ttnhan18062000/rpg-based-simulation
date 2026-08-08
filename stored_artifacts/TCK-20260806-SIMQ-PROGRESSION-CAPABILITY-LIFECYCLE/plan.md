---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260806-SIMQ-PROGRESSION-CAPABILITY-LIFECYCLE
artifact_type: plan
tags: [simulation-quality, progression]
---

# plan.md — TCK-20260806-SIMQ-PROGRESSION-CAPABILITY-LIFECYCLE

## Ordered Steps

1. `src/observability/event_extractor.py`: add module constants `_CAPABILITY_STALL_TICKS = 300`,
   `_LATE_GENERATION_THRESHOLD = 2`; add class-level state `_last_capability_growth_tick: dict`,
   `_emitted_capability_stalled: set`, `_emitted_life_arc_incoherent: set` (cleared in
   `reset_run_state()`); add new, unconditional (not flag-gated) code in the entity loop,
   immediately after the existing `progression_plateau_detected` block, constructing
   `capability_growth_stalled` and `life_arc_incoherent` per investigation.md's rule design.
2. `config/simulation_quality/scoring_weights.yaml`: add `capability_growth_stalled: -10.0` and
   `life_arc_incoherent: -15.0` under `PROGRESSION:`.
3. `src/simulation_quality/scorers/progression.py`: add `capability_growth_stalled` and
   `life_arc_incoherent` to `EVENT_TYPES`, add two new `if et == ...` branches in `score()`.
4. `docs/simulation_quality/quality_scoring_contract.md`: add both event types to PROGRESSION's
   "Event types scored" list and 2 new rows to the Signal/Delta/Tag table (§5).
5. `docs/simulation_quality/event_type_coverage.md`: add both to §1.1's Direct Emission table.
6. `docs/parity_ledger/progression.yaml`: new entry (next available `PROG-` ID).
7. Unit tests: extend `tests/unit/observability/test_event_extractor_*.py` (new test class/cases)
   and `tests/simulation_quality/test_progression_scorer.py` (new `TestCapabilityGrowthStalled`,
   `TestLifeArcIncoherent` classes), per test_plan.md.
8. Recalibrate `grade_anchors.json` only if a real scoped pytest + real-kernel check shows a
   scenario's PROGRESSION grade actually shifted — do not recalibrate reflexively.

## Files to Change

- `src/observability/event_extractor.py`
- `config/simulation_quality/scoring_weights.yaml`
- `src/simulation_quality/scorers/progression.py`
- `docs/simulation_quality/quality_scoring_contract.md`
- `docs/simulation_quality/event_type_coverage.md`
- `docs/parity_ledger/progression.yaml`
- `tests/unit/observability/test_event_extractor_simq.py` (or `_world.py`, whichever holds
  PROGRESSION-block tests — confirm exact file during Implement)
- `tests/simulation_quality/test_progression_scorer.py`

## Scope Guards

- Do NOT touch `ProgressionShaper` (`event_shapers.py`) — this is deliberately extractor-only new
  code, per investigation.md's architecture decision; do not mirror it into the shaper.
- Do NOT touch `_push_shapers_phase2_active` or any existing flag-gated block — the new code is
  additive and unconditional, inserted after the existing gated block, not inside it.
- Do NOT touch COMBAT's scorer or any COMBAT-owned event — per the ticket's own Out of Scope and
  §7.6's own boundary ruling ("COMBAT stays resolution-only").
- Do NOT touch FACTION — `TCK-20260806-SIMQ-FACTION-LIFECYCLE-TRAJECTORY`'s own scope.
- Do NOT add gameplay mechanics (new equipment types, new skills) — observability signal addition
  only.

## Dependency Map

Steps 1-3 must land together (new event types are meaningless without both extractor construction
and scorer handling). Steps 4-6 (docs/parity) depend on 1-3's final field names/weights. Step 7
depends on 1-3. Step 8 depends on 7's real test results.

## Acceptance Criteria Map

- AC "investigation.md documents queryable state + new-event decision" → investigation.md (done)
- AC "plan.md specifies exact rule(s), tag(s), delta placeholders" → this file + investigation.md
- AC "new rule(s) implemented, weights in scoring_weights.yaml, no numeric literals in scorer" →
  steps 2-3
- AC "quality_scoring_contract.md §5 + event-type list updated" → step 4
- AC "event_type_coverage.md updated" → step 5
- AC "unit tests added" → step 7
- AC "docs/parity_ledger/progression.yaml updated" → step 6
- AC "grade_anchors.json recalibrated for any shifted scenario" → step 8
- AC "scoped pytest run passes" → step 7's real run
