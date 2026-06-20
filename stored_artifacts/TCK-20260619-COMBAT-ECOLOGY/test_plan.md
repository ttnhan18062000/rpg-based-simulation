# Test Plan: TCK-20260619-COMBAT-ECOLOGY

## New Tests

### `tests/unit/combat/test_combat_ecology.py`
- `test_grudge_scope_is_defined` — confirms grudge_history and combat_loss_counts exist on SocialComponent; documents run-only scope in docstring
- `test_combat_loss_increments_counter` — verify SocialUpdate with combat_loss_delta={1: 1} correctly increments combat_loss_counts via RelationshipService
- `test_fear_avoidance_posture_at_loss_threshold` — configure entity with combat_loss_counts[opp_id]=3; call CombatEngagementDecisionService.evaluate(); assert posture == AVOID and reason contains "fear_avoidance"
- `test_no_fear_avoidance_below_threshold` — configure entity with combat_loss_counts[opp_id]=2; assert posture is NOT forced AVOID

## Scoped Pytest Commands
```bash
pytest tests/unit/combat/test_combat_ecology.py -v
pytest tests/unit/social/ -v --tb=short -m "not slow"
```
