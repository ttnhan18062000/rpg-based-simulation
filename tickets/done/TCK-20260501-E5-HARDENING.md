
# TCK-20260501-E5-HARDENING

## Title
RPG Engine E5 Hardening: Race Conditions & Idempotency

## Status
DONE

## Request Summary
Harden the RPG V2 engine by implementing race-condition safeguards (deterministic resolution) and exactly-once transaction idempotency.

## Scope
- Implement negative case hardening (invalid actors, depleted nodes).
- Implement deterministic race-condition resolution for movement and resource harvesting.
- Implement exactly-once idempotency for resource transactions via transaction IDs.
- Execute a 2000-tick certification long-run.
- Finalize the exhaustive logic checklist to 100% verified coverage.

## Out of Scope
- Phase 6 (Strategic Depth) logic.
- UI/Client-side changes.

## Acceptance Criteria
- [x] All negative cases rejected with formal failure reasons.
- [x] Race conditions resolved by lowest Entity ID (deterministic).
- [x] Transaction IDs prevent duplicate processing across ticks.
- [x] 2000-tick simulation passes with 0 protocol violations.
- [x] Checklist coverage reaches 100.00%.

## Related Tickets
- None

## Related Docs
- resource_v2_e5_phases.md

## Related Stored Artifacts
- reports/certification_2000_tick.json

## Related Code Areas
- src/engine/pipeline.py
- src/core/state.py
- src/core/updates.py
- src/core/conservation.py
- src/engine/apply.py

## Implementation Notes
- Enforced deterministic resolution by sorting entity keys in `_resolve_resource_transactions`.
- Added `processed_transaction_ids` to state and updates for cross-tick tracking.
- Added in-tick idempotency check in the pipeline.
- Consolidated tests into `tests/engine/test_hardening_e5.py`.

## Test Summary
- `pytest tests/engine/test_hardening_e5.py` (6/6 passed)
- `python3 scripts/certification_long_run.py` (2000 ticks, 0 violations)

## Files Changed
- src/core/state.py
- src/core/updates.py
- src/core/conservation.py
- src/engine/pipeline.py
- src/engine/apply.py
- logic_checklist_exhaustive_v2.md
- tests/engine/test_hardening_e5.py

## Completion Summary
Phase E5 is operationally closed. The engine now guarantees deterministic execution order and prevents duplicate transaction processing. Checklist coverage is 100% verified.
