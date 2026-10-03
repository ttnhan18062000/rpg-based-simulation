---
status: historical
layer: social
authority: P1
audience: agent
ticket_id: TCK-20260619-E41A-GROUP-LIFECYCLE
phase: done
date: 2026-06-20
tags: [party, group-record, lifecycle, phase-4]
---

# TCK-20260619-E41A-GROUP-LIFECYCLE

## Title
Epic 4.1A · GroupRecord Lifecycle Extension

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
`GroupRecord` at `src/core/state.py:L507` lacks fields needed for sustained party lifecycle: `formation_tick`, `escort_target_id`, `grievance_log`, `reward_pool`, `dissolution_tick`. This ticket adds those fields as the foundation for E41B–E41D.

**Blocks:** All other E41 child tickets

## Scope

Add to `GroupRecord` (`src/core/state.py:L507`):
```python
formation_tick: int = 0
escort_target_id: Optional[int] = None
grievance_log: Tuple[str, ...] = ()      # immutable list of event summary strings
reward_pool: int = 0
last_leadership_check_tick: int = 0
dissolution_tick: Optional[int] = None
```

Update `to_canonical_dict()` to include all new fields (sorted for determinism).

## Acceptance Criteria
- `GroupRecord(formation_tick=10, escort_target_id=5, ...)` constructs without error
- `to_canonical_dict()` includes all new fields
- All existing GroupRecord tests pass

## Related Tickets
- TCK-20260619-E41-PARTY-LOOP (parent epic)
- TCK-20260619-E41B-LEADERSHIP (blocked on this)

## Related Docs
- `docs/parity_ledger/social_narrative.yaml` (SOC-227 added)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260619-E41A-GROUP-LIFECYCLE/`

## Related Code Areas
- `src/core/state.py:L507` (GroupRecord)
- `tests/unit/social/test_group_lifecycle_fields.py`

## Assumptions / Open Questions
None — all fields were pre-agreed in the epic scope.

## Implementation Notes
Added six lifecycle fields to `GroupRecord` in `src/core/state.py` (after `end_apt`, before `_canonical_cache`): `formation_tick` (int=0), `escort_target_id` (Optional[int]=None), `grievance_log` (Tuple[str,...]=()),  `reward_pool` (int=0), `last_leadership_check_tick` (int=0), `dissolution_tick` (Optional[int]=None). Updated `to_canonical_dict()` to emit all six fields flat at the top level; `grievance_log` emitted as `list()` for JSON-serializability. Created `tests/unit/social/test_group_lifecycle_fields.py` with 10 tests (9 behavioral + 1 anti-drift key-completeness guard). Added SOC-227 parity ledger entry to `docs/parity_ledger/social_narrative.yaml`.

## Test Summary
```bash
pytest tests/unit/social/test_group_lifecycle_fields.py tests/unit/social/test_groups.py tests/unit/social/test_party_agency.py tests/unit/social/test_party_coordination.py tests/unit/social/test_social_party_regression.py tests/unit/domains/cooperation/ -x -v
```
46 tests passing, 0 failures.

## Files Changed
- `src/core/state.py` — added 6 lifecycle fields to `GroupRecord`; updated `to_canonical_dict()` to emit all new fields
- `tests/unit/social/test_group_lifecycle_fields.py` — new file; 10 tests (9 behavioral + 1 anti-drift key-completeness guard)
- `docs/parity_ledger/social_narrative.yaml` — added SOC-227 entry for GroupRecord lifecycle fields

## Completion Summary
Added six lifecycle fields (`formation_tick`, `escort_target_id`, `grievance_log`, `reward_pool`, `last_leadership_check_tick`, `dissolution_tick`) to `GroupRecord` in `src/core/state.py`. All fields have safe defaults and are emitted correctly from `to_canonical_dict()`. 10 new tests added; full social suite of 46 tests passes. Parity ledger updated with SOC-227. This unblocks E41B–E41D.
