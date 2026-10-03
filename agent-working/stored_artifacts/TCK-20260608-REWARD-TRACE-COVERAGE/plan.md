---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260608-REWARD-TRACE-COVERAGE
artifact_type: plan
tags: [reward, trace, coverage]
---

# Plan — TCK-20260608-REWARD-TRACE-COVERAGE

## Steps
1. resolve_attack: add trace["REWARD_CATEGORY"] = classification.category.value
2. resolve_skill_usage: add skill_trace dict, REWARD_SOURCE + REWARD_CATEGORY; pass trace= to CombatUpdate
3. resolve_multi_attack: add full_trace["REWARD_CATEGORY"] = classification.category.value
4. Create tests/unit/combat/test_combat_reward_trace.py (8 tests)
