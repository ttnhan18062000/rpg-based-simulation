---
ticket_id: TCK-20260619-E32-CAMPAIGN-RUNTIME
phase: plan
date: 2026-06-20
---

# Plan: Persistent Campaign Runtime — Epic Scope

## Child Ticket Sequence

```
E32A (rename CampaignRunner)
  └──► E32B (CampaignState model)
         └──► E32C (CampaignOrchestrator + episode handoff)
                └──► E32D (NarrativeLedger)
                       └──► E32E (REST endpoint)
```

E32A must be first (frees the naming space). E32C requires E32B (needs CampaignState). E32D can start after E32C (NarrativeLedger is populated by episode handoff events). E32E requires E32D (serves the ledger).

## Child Ticket Summary

| Ticket | Scope | Key Deliverable |
|---|---|---|
| E32A | Rename `CampaignRunner` → `SimulationAnalysisRunner`; update all callers | grep-and-rename across src/ + tests/ |
| E32B | `CampaignState` dataclass: episode_history, persistent_entities, persistent_factions, world_timeline, narrative_ledger | `src/domains/campaigns/state.py` (new) |
| E32C | `CampaignOrchestrator`: episode sequencing via `ScenarioRuntimeService`; carry-forward rules for entity XP/equipment/rep/injury; dead factions excluded | `src/domains/campaigns/orchestrator.py` (new) |
| E32D | `NarrativeLedger`: structured significant-event record (quest completions, deaths, faction shifts, calamities) by tick+episode; queryable by event type | `src/domains/campaigns/narrative_ledger.py` (new) |
| E32E | `GET /api/v1/campaigns/{id}/history` → NarrativeLedger as structured event stream | `src/api/routes/campaigns.py` (new) |

## Acceptance Path

1. E32A: all tests pass after rename (no CampaignRunner references remain)
2. E32B: `CampaignState` serializes/deserializes with all fields
3. E32C: 3-episode campaign: HERO level 5 at ep1 end → level 5 at ep2 start; destroyed faction absent in ep2
4. E32D: NarrativeLedger contains ≥10 cross-episode entries
5. E32E: GET `/api/v1/campaigns/{id}/history` returns structured event stream
