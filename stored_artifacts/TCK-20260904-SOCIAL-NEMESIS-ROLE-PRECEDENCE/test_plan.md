---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260904-SOCIAL-NEMESIS-ROLE-PRECEDENCE
artifact_type: test_plan
tags: [social, combat]
---

# Test Plan — TCK-20260904-SOCIAL-NEMESIS-ROLE-PRECEDENCE

## New tests (tests/unit/social/test_party_composition.py)
- `test_candidate_role_value_nemesis_overrides_stale_friend_bond`
- `test_candidate_role_value_nemesis_without_bond`
- `test_candidate_role_value_non_conflicting_cases_unchanged`
- `test_party_composition_score_lower_for_nemesis_with_friend_bond_than_true_friend`
- `test_form_party_route_blocked_by_canonical_nemesis_ids_without_strategic_blocker`

## Result
All pass. `pytest tests/unit/domains/adventure/ tests/unit/social/ tests/integration/domains/adventure/
tests/architecture/test_adventure_routing_flag_inert.py
tests/architecture/test_adventure_route_score_max_unchanged.py -m "not slow"` → 355 passed, 1 deselected,
0 failed.
