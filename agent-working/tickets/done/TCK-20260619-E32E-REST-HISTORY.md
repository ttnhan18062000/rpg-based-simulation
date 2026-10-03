---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E32E-REST-HISTORY
phase: done
date: 2026-06-21
tags: [campaign-runtime, rest-api, narrative-ledger, phase-3]
---

# TCK-20260619-E32E-REST-HISTORY

## Title
Epic 3.2E · Campaign History REST Endpoint

## Status
DONE

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
## Implementation Notes
- Module-level `_CAMPAIGN_REGISTRY` dict in `src/api/routes/campaigns.py` is the
  injection point for `CampaignState`. Tests call `register_campaign()` directly;
  production orchestrators do the same after creation.
- Tests call route handlers directly with explicit param values (no FastAPI DI
  resolution) — same pattern as `test_cognition_history_api.py`.
- Pre-existing `QueueDrainWorker` thread leak in `test_scenario_runtime_api.py::
  test_route_registered_in_server` is unrelated to this ticket and pre-dates it
  (confirmed via git stash).

## Files Changed
- `src/api/routes/campaigns.py` (new) — GET /api/v1/campaigns/{id}/history route
- `src/api/presenters/campaigns.py` (new) — CampaignHistoryResponse, NarrativeLedgerEntryPresenter
- `src/api/server.py` — registered campaigns router
- `tests/api/test_campaign_history_api.py` (new) — 7 tests, all passing
- `docs/simulation/domains/campaign_orchestrator_contract.md` (new) — full orchestrator contract
- `docs/simulation/domains/campaigns_contract.md` — added REST API section + boundary table
- `docs/parity_ledger/infrastructure.yaml` — added INFRA-219

## Completion Summary
Epic 3.2E complete. `GET /api/v1/campaigns/{id}/history` endpoint implemented with
optional `event_type`, `min_significance`, and `episode` query filters. All responses
shaped through Pydantic presenter layer (no raw domain models). 7 tests pass covering
normal flow, 404, all three filters individually, combined filters, and empty ledger.
`docs/simulation/domains/campaign_orchestrator_contract.md` created documenting
orchestrator lifecycle, NarrativeLedger schema, episode handoff, carry-forward rules,
and REST contract. Parity ledger updated (INFRA-219). Knowledge index rebuilt.
