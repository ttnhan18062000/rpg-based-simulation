---
status: open
layer: social
authority: P1
audience: agent
ticket_id: TCK-20260619-E41C-REWARD-DIST
phase: open
date: 2026-06-20
tags: [party, reward-distribution, class-synergy, phase-4]
---

# TCK-20260619-E41C-REWARD-DIST

## Title
Epic 4.1C · FairShareProtocol + Class Synergy Bonuses

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
No reward distribution mechanism exists for multi-entity groups. This ticket implements `FairShareProtocol` and class-compatibility synergy bonuses in route scoring.

**Requires:** TCK-20260619-E41B-LEADERSHIP

## Scope

New file `src/systems/social_systems/reward_distribution.py`:

```python
def compute_fair_share(group: GroupRecord, quest_reward: int, contribution_log: dict[int, float]) -> dict[int, int]:
    """Distribute proportional to contribution; equal split if no contributions recorded."""
    total = sum(contribution_log.values()) or len(group.member_ids)
    shares = {mid: int((contribution_log.get(mid, 1.0) / total) * quest_reward) for mid in group.member_ids}
    shares[group.leader_id] = shares.get(group.leader_id, 0) + (quest_reward - sum(shares.values()))
    return shares
```

Apply via `ResourceTransferIntent` (gold_delta=share) for each member — do NOT directly mutate gold.

**Class synergy** in `src/domains/adventure/scoring.py` (`AdventureRouteScorer`):
- WARRIOR + MAGE pair in same group: `combat_route_score *= 1.15`
- HERO + any: `quest_route_score *= 1.10`
- Detect via `GroupRecord.roles` → look up each member's `EntityRole`

## Acceptance Criteria
- `test_fair_share_protocol_distributes_by_contribution` passes (70/30 split on 0.7/0.3 contributions)
- `test_class_synergy_bonus_applied_to_combat_routes` passes (WARRIOR+MAGE → 15% combat score bonus)
- Reward distribution goes through ResourceTransferIntent, not direct mutation

## Related Tickets
- TCK-20260619-E41-PARTY-LOOP (parent epic)
- TCK-20260619-E41B-LEADERSHIP (required)
- TCK-20260619-E41D-DEFECTION-ESCORT (blocked on this)

## Related Code Areas
- `src/systems/social_systems/reward_distribution.py` (new)
- `src/domains/adventure/scoring.py` (AdventureRouteScorer — add synergy multipliers)

## Test Summary
```bash
pytest tests/unit/social/test_party_lifecycle.py::test_fair_share_protocol_distributes_by_contribution -x -v
pytest tests/unit/social/test_party_lifecycle.py::test_class_synergy_bonus_applied_to_combat_routes -x -v
```
## Files Changed
_To be filled on completion._
## Completion Summary
_To be filled on completion._
