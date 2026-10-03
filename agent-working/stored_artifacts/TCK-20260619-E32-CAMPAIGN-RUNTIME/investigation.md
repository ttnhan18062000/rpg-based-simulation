---
ticket_id: TCK-20260619-E32-CAMPAIGN-RUNTIME
phase: investigation
date: 2026-06-20
---

# Investigation: Persistent Campaign Runtime

## Current State (verified 2026-06-20)

### CampaignRunner — `src/domains/campaigns/runner.py:L29`
Exists. Is analysis-only (isolated shadowed state, no `Failed` state). Must be renamed `SimulationAnalysisRunner` as E32's first child ticket — before any other E32 work begins.

### CampaignEvent — `src/domains/campaigns/schema.py:L43`
Exists. Fields: `event_type: str`, plus others. Extend for NarrativeLedger entries.

### CampaignSpec — `src/domains/campaigns/spec.py`
Exists. Does not support multi-episode sequence. Needs `episodes: List[ScenarioSpec]`, `carry_forward_rules`, `campaign_victory_conditions`.

### No `CampaignOrchestrator`, `NarrativeLedger`, `CampaignState` exist.

## Gap Summary

| Gap | Size |
|---|---|
| Rename CampaignRunner | grep + replace across callers |
| `CampaignState` model (episode_history, persistent_entities, etc.) | ~50 lines |
| `CampaignOrchestrator` (episode sequencing, state carry-forward) | ~100 lines |
| `NarrativeLedger` (structured event record, queryable) | ~60 lines |
| REST endpoint `/api/v1/campaigns/{id}/history` | ~30 lines |
