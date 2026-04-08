# Test Plan - Phase 3 Pass 3: Behavioral Integration

## Automated Tests
### Integration Tests: `tests/integration/social/test_lived_ai_behavior.py`
- `test_routine_goal_priority`: Verify that an entity with a "Sleep" routine at hour 22 selects `GoalType.SLEEP` more often.
- `test_place_attachment_bias`: Verify that choosing `GoalType.REST` results in a movement proposal toward the `HOME` attachment location.
- `test_routine_disruption`: Verify that an entity undergoing combat (high `anger`/`panic`) ignores its "Sleep" routine.
- `test_cluster_unanimity`: Verify that cluster members spawned together tend to adopt the same `ai_state` (e.g., all WANDER or all HUNT) when nearby.

## Core Scenarios
1. **The Merchant**: Spawns in town, has a `TRADE` routine during the day. Verify they stay in the market area during market hours.
2. **The Guard**: Has a `PATROL` routine. Verify they stay active at night if their schedule reflects it.
3. **The Cluster**: A group of Goblins spawns. Verify that when one goblins starts "HUNTING", it increases the likelihood of others in the same cluster nearby also starting "HUNTING".

## Manual Verification
- Launch the web UI or CLI inspector.
- Select an entity with an active routine (e.g., a Hero at home).
- Verify "Routine: SLEEP" appears in the `Decision Drivers` list with a significant weight.
