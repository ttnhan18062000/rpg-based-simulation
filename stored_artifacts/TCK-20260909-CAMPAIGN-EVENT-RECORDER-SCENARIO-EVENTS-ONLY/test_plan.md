# Test Plan — TCK-20260909-CAMPAIGN-EVENT-RECORDER-SCENARIO-EVENTS-ONLY

## Determination evidence (already captured, real not synthetic)
- Real 70-tick `CampaignOrchestrator.run_episode()` run (default config), reading
  `data/runs/{run_id}/simulation_events.jsonl` directly: 303 events across 19 real types,
  confirming the file SimQ replays is not bookkeeping-only. See investigation.md for the full
  event-type breakdown.

## Rename regression (naming/docs only, no behavior change — verify nothing broke)
- `tests/unit/engine/test_scenario_runtime_service.py` — all `scenario_event_recorder=`
  construction/assertion sites.
- `tests/unit/domains/campaigns/` (full dir) — `CampaignOrchestrator` construction and direct
  `_scenario_event_recorder` attribute sets (grief/urgency tests).
- `tests/integration/campaigns/` (full dir, including the 3 `@pytest.mark.slow` real-episode
  tests) — confirms the renamed param still threads through the real production path end to end.
- `tests/integration/scenarios/test_social_memory.py`,
  `tests/integration/tools/test_calibrate_simq_campaign_mode.py` — other real construction sites.
- Sanity check (unrelated to the rename, confirms `Kernel._event_recorder` untouched):
  `tests/simulation_quality/test_calibrate_simq.py`,
  `tests/simulation_quality/test_kernel_simq_integration.py`,
  `tests/unit/observability/test_event_recorder.py`.

Scoped pytest command:
```
pytest tests/unit/engine/test_scenario_runtime_service.py tests/unit/domains/campaigns/ \
       tests/integration/campaigns/ tests/integration/scenarios/test_social_memory.py \
       tests/integration/tools/test_calibrate_simq_campaign_mode.py \
       -m "not slow and not extra_slow"
```
Plus the 3 `@pytest.mark.slow` tests in `test_catalog_entity_spawn_wiring.py` run separately
(unmarked filter).
