# TCK-20260518-STRATEGIC-WORK-QUEUE

## Title

Implement StrategicWorkQueue for Bounded Strategic Cognition

## Status

DONE

## Request Summary

Implement `StrategicWorkQueue` to narrow candidate entities evaluated in strategic intelligence loops across 7 urgency tiers, respecting a configurable budget and preventing starvation via deterministic round-robin background sampling.

## Scope

- Implement `StrategicWorkQueue` class in `src/systems/strategic_systems/work_queue.py`.
- Categorize entities into 7 priority tiers: failed action/path, unresolved blockers, active project transition, biological emergency, contract expiration, dirty strategic entities, background sweep sample.
- Integrate into `fused_strategic_pass`, `evaluate_all_concerns`, and `evaluate_all_strategic_intents`.
- Implement comprehensive unit tests in `tests/unit/optimization/test_strategic_work_queue.py`.

## Out of Scope

- Modifying cognition capacity formulas or individual intent execution logic.

## Acceptance Criteria

- Queue order is deterministic.
- Urgent entities are processed before routine entities.
- Budget is respected.
- Starvation prevention exists.
- `force_full_scan` bypasses queue narrowing.

## Related Tickets

- TCK-20260518-CACHE-INVALIDATION-POLICY

## Related Docs

- `perf_test_plan.md`
- `docs/mechanics/`

## Related Stored Artifacts

- `stored_artifacts/TCK-20260518-STRATEGIC-WORK-QUEUE/`

## Related Code Areas

- `src/systems/strategic_systems/work_queue.py`
- `src/systems/strategic_systems/intelligence.py`

## Assumptions / Open Questions

- None.

## Implementation Notes

- Implemented deterministic round-robin shift in Tier 7 via `state.tick % len(tier7)` rotation.
- Handled biological emergencies via `bio.hunger`, `bio.sleep_debt`, `bio.rest_pressure`, and `stamina.current`.

## Test Summary

- Ran `pytest tests/unit/optimization/test_strategic_work_queue.py -v`: 7/7 passed.
- Ran full regression suite `pytest tests/unit/ -m "not slow"`: 792/792 passed.

## Files Changed

- `src/systems/strategic_systems/work_queue.py` [NEW]
- `src/systems/strategic_systems/__init__.py` [MODIFY]
- `src/systems/strategic_systems/intelligence.py` [MODIFY]
- `tests/unit/optimization/test_strategic_work_queue.py` [NEW]

## Completion Summary

- `StrategicWorkQueue` successfully narrows strategic cognition candidates to bounded budgets while ensuring urgent entities and background starvation prevention are fully handled. All tests and regression checks passed flawlessly.
