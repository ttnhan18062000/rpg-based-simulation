---
status: open
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E32E-REST-HISTORY
phase: open
date: 2026-06-20
tags: [campaign-runtime, rest-api, narrative-ledger, phase-3]
---

# TCK-20260619-E32E-REST-HISTORY

## Title
Epic 3.2E · Campaign History REST Endpoint

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Exposes `NarrativeLedger` via REST. Prerequisite for any external tooling to inspect campaign continuity without reading JSONL files directly.

**Requires:** TCK-20260619-E32D-NARRATIVE-LEDGER

## Scope

New endpoint in `src/api/routes/campaigns.py`:

```
GET /api/v1/campaigns/{id}/history
    ?event_type=entity_death
    &min_significance=0.5
    &episode=2
→ {
    campaign_id: "...",
    entry_count: N,
    entries: [{episode, tick, event_type, subject_id, payload, significance}, ...]
  }
```

Also: create `docs/simulation/domains/campaign_orchestrator_contract.md` documenting `CampaignOrchestrator` lifecycle, `NarrativeLedger` schema, episode handoff rules, carry-forward rules. Run `make knowledge-index-update` after.

## Acceptance Criteria
- GET `/api/v1/campaigns/{id}/history` returns structured NarrativeLedger as JSON
- `test_campaign_history_endpoint_returns_narrative_ledger` passes
- `docs/simulation/domains/campaign_orchestrator_contract.md` exists

## Related Tickets
- TCK-20260619-E32-CAMPAIGN-RUNTIME (parent epic)
- TCK-20260619-E32D-NARRATIVE-LEDGER (required)

## Related Docs
- `docs/simulation/domains/campaign_orchestrator_contract.md` (new)
- `docs/simulation/domains/campaigns_contract.md` (update boundary table)

## Related Code Areas
- `src/api/routes/campaigns.py` (new)
- `src/api/server.py` (register router)
- `tests/api/test_campaign_history_api.py` (new)

## Test Summary
```bash
pytest tests/api/test_campaign_history_api.py -x -v
```
## Files Changed
_To be filled on completion._
## Completion Summary
_To be filled on completion._
