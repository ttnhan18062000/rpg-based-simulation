---
status: open
layer: social
authority: P1
audience: agent
ticket_id: TCK-20260619-E41A-GROUP-LIFECYCLE
phase: open
date: 2026-06-20
tags: [party, group-record, lifecycle, phase-4]
---

# TCK-20260619-E41A-GROUP-LIFECYCLE

## Title
Epic 4.1A · GroupRecord Lifecycle Extension

## Status
OPEN

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

## Related Code Areas
- `src/core/state.py:L507` (GroupRecord)

## Test Summary
```bash
pytest tests/unit/social/test_party_lifecycle.py -x -v
```
## Files Changed
_To be filled on completion._
## Completion Summary
_To be filled on completion._
