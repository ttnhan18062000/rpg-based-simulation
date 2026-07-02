# Test Plan — TCK-20260619-E61D-PLAN-REVISION

## tests/unit/campaigns/test_plan_revision.py (10 tests)

1. test_generate_initial_plan_level_1_hero — level 1 → head = craft_upgrade
2. test_generate_initial_plan_level_5_hero — level 5 → head = quest_opportunity
3. test_generate_initial_plan_level_10_hero — level 10 → head = gather_resource
4. test_detect_mentor_dead_fires_trigger — dead mentor in relationship_scores → trigger fires, head blocked, queue rotated
5. test_detect_mentor_alive_no_trigger — alive mentor → no revision
6. test_detect_no_social_memory_no_revision — social_memory=None → no revision
7. test_detect_item_unavailable_fires_trigger — target_item_id not in equipment → trigger fires
8. test_revision_emits_narrative_ledger_entry — entry has event_type="plan_revision", significance=0.6
9. test_revision_entry_id_dedup_format — entry_id = "{episode}:0:plan_revision:{entity_id}"
10. test_no_trigger_fired_returns_original_plan — no fires → same plan object returned

## tests/integration/campaigns/test_progression_planner_three_episode.py (1 test)

test_hero_pursues_craft_upgrade_across_three_episodes — 3 episodes via mock SVC; verifies plan generated, carried, then revised when mentor dies
