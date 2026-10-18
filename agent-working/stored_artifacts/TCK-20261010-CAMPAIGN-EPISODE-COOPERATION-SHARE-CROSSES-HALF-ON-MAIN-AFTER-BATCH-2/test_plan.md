---
status: historical
layer: testing
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261010-CAMPAIGN-EPISODE-COOPERATION-SHARE-CROSSES-HALF-ON-MAIN-AFTER-BATCH-2
date: 2026-10-16
tags: []
---

# Test plan: TCK-20261010-CAMPAIGN-EPISODE-COOPERATION-SHARE-CROSSES-HALF-ON-MAIN-AFTER-BATCH-2

Both new tests pass on the tip (test_every_cooperation_event_comes_from_a_decision_with_a_typed_basis, test_real_campaign_episode_cooperation_volume_per_entity_tick_stays_bounded); the module runs 12 passed, 1 strict xfail (deliberate attacks, unchanged). Falsifiability: a scratch copy with every entity spawned on one tile fails (b) with 0.4513 per entity-tick against the 0.30 ceiling and passes (a), as expected.

## Proof Plan

- level: integration (real campaign episode)
- proof kind: regression, falsifiable
- oracle source: the original co-location bug re-introduced in a scratch copy
- expected effect: (b) fails on co-location, both pass on the tip
- selected commands: `pytest tests/integration/campaigns/test_catalog_entity_spawn_wiring.py`; `pytest tests/unit/tools/test_known_reds.py`
