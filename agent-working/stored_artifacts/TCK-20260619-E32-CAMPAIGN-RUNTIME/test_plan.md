---
ticket_id: TCK-20260619-E32-CAMPAIGN-RUNTIME
phase: test_plan
date: 2026-06-20
---

# Test Plan: Persistent Campaign Runtime

## Integration Tests (new file: tests/integration/scenarios/test_campaign_runtime.py)

### test_entity_state_persists_across_episodes
- HERO at level 5 at episode 1 end → level 5 at episode 2 start

### test_dead_faction_absent_in_episode_2
- Faction destroyed in ep1 not spawned in ep2

### test_narrative_ledger_populated_with_cross_episode_events
- Assert ≥10 NarrativeLedger entries spanning both episodes

### test_campaign_checkpoint_restores_from_episode_boundary
- Serialize CampaignState, restore, run ep2; assert same outcome as non-checkpoint run

## API Tests (new file: tests/api/test_campaign_history_api.py)
### test_campaign_history_endpoint_returns_narrative_ledger
- GET `/api/v1/campaigns/{id}/history`; assert structured event stream ≥10 entries

## Regression (E32A rename)
```bash
pytest tests/ -x -v -q -k "not slow"  # all must pass after rename
```
