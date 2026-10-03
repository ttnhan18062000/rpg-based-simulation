# Test Plan — TCK-20260619-E41C-REWARD-DIST

## Test file
`tests/unit/social/test_party_lifecycle.py` — append new tests at the bottom.

## Required acceptance tests

### TC-1: test_fair_share_protocol_distributes_by_contribution
- Group: leader_id=10, members={10, 11}
- contribution_log: {10: 0.7, 11: 0.3}
- quest_reward: 100
- Expected: member 10 gets 70 gold, member 11 gets 30 gold (70+30=100, conservation check).
- No remainder because 70+30=100.

### TC-2: test_class_synergy_bonus_applied_to_combat_routes
- Group with roles: {10: "LEADER", 11: "WARRIOR", 12: "MAGE"}
- Entity is a basic HERO scoring a HUNT_WEAK_ENEMY route.
- Base route score computed without group → score_no_group.
- Score computed with group → score_with_group.
- Assert score_with_group == pytest.approx(score_no_group * 1.15, rel=1e-4).

## Additional coverage tests

### TC-3: test_fair_share_equal_split_no_contributions
- contribution_log: {} (empty)
- quest_reward: 100, 3 members
- Each gets 33, leader gets 34 (remainder +1 check).

### TC-4: test_fair_share_conservation_law
- Any distribution: sum(shares.values()) == quest_reward always.

### TC-5: test_build_reward_intents_uses_resource_transfer
- Ensure each returned EntityUpdate has resource_transfers with gold_delta == share.
- source_kind == "QUEST", transfer_kind == "PARTY_REWARD_SHARE".

### TC-6: test_hero_synergy_bonus_applied_to_quest_routes
- Entity EntityRole.HERO scores QUEST_OPPORTUNITY route with a group.
- Score ×1.10 applied on top of existing benefit.

## Regression
- `pytest tests/unit/social/test_party_lifecycle.py -x -v` — all existing tests must still pass.
