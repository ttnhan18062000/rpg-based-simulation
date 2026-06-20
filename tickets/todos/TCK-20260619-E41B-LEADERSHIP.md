---
status: open
layer: social
authority: P1
audience: agent
ticket_id: TCK-20260619-E41B-LEADERSHIP
phase: open
date: 2026-06-20
tags: [party, leadership-election, lifecycle, sociability, phase-4]
---

# TCK-20260619-E41B-LEADERSHIP

## Title
Epic 4.1B · Sustained Party Lifecycle + Leadership Election

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
No mechanism exists to sustain party leadership or detect leadership transitions. This ticket implements `PartyLifecycleService` with periodic leadership election using `sociability` (OCEAN personality trait) and basic cohesion checks.

**Requires:** TCK-20260619-E41A-GROUP-LIFECYCLE

## Scope

New file `src/systems/social_systems/party_lifecycle.py`:

```python
class PartyLifecycleService:
    LEADERSHIP_CHECK_INTERVAL = 100  # ticks

    @staticmethod
    def check_leadership(group: GroupRecord, members: list[EntityState], tick: int) -> Optional[GroupUpdate]:
        """Elect new leader if current leader's sociability < max member sociability by ≥0.2."""
        if tick - group.last_leadership_check_tick < PartyLifecycleService.LEADERSHIP_CHECK_INTERVAL:
            return None
        sociabilities = {e.id: e.personality.sociability for e in members if e.id in group.member_ids}
        current = sociabilities.get(group.leader_id, 0.0)
        best_id = max(sociabilities, key=sociabilities.get)
        if sociabilities[best_id] - current >= 0.2:
            return GroupUpdate(group_id=group.id, new_leader_id=best_id, leadership_changed=True)
        return GroupUpdate(group_id=group.id, last_leadership_check_tick=tick)
```

Wire into the social phase of `src/engine/kernel.py` (find social tick position). Emit `leadership_changed` SimulationEvent on leader transition with morale payload.

## Acceptance Criteria
- `test_leadership_election_picks_highest_sociability` passes (leader change when diff ≥ 0.2)
- Leadership change emits `leadership_changed` SimulationEvent

## Related Tickets
- TCK-20260619-E41-PARTY-LOOP (parent epic)
- TCK-20260619-E41A-GROUP-LIFECYCLE (required)
- TCK-20260619-E41C-REWARD-DIST (blocked on this)

## Related Code Areas
- `src/systems/social_systems/party_lifecycle.py` (new)
- `src/engine/kernel.py` (wire in social phase)
- `src/observability/events.py` (add `leadership_changed` event kind)

## Test Summary
```bash
pytest tests/unit/social/test_party_lifecycle.py::test_leadership_election_picks_highest_sociability -x -v
```
## Files Changed
_To be filled on completion._
## Completion Summary
_To be filled on completion._
