---
status: active
ticket_id: TCK-20260619-E32E-REST-HISTORY
artifact_type: plan
date: 2026-06-21
---

# Plan — TCK-20260619-E32E-REST-HISTORY

## Ordered Steps

### Step 1: Presenter layer (src/api/presenters/campaigns.py)
Create `NarrativeLedgerEntryPresenter` and `CampaignHistoryResponse` as Pydantic
BaseModels. No raw domain imports — only primitives and typing.

**Files:** `src/api/presenters/campaigns.py`
**AC:** API boundary rule (no raw domain models) satisfied.

### Step 2: Route module (src/api/routes/campaigns.py)
- Module-level `_CAMPAIGN_REGISTRY: Dict[str, CampaignState]`
- `register_campaign(campaign_id, state)` helper for injection
- `GET /{id}/history` handler with query params: `event_type`, `min_significance`,
  `episode`
- Uses `NarrativeLedger(entries=state.narrative_ledger).query(...)` for filtering
- Returns `CampaignHistoryResponse` via presenter

**Files:** `src/api/routes/campaigns.py`
**AC:** GET /api/v1/campaigns/{id}/history returns structured NarrativeLedger as JSON.

### Step 3: Register router in server.py
Add import and `app.include_router(campaigns.router, prefix="/api/v1")` after
the existing route registrations.

**Files:** `src/api/server.py`
**AC:** Route is live in the FastAPI app.

### Step 4: Write tests (tests/api/test_campaign_history_api.py)
Implement all 7 test cases from test_plan.md using `anyio` + direct handler
calls + registry injection pattern.

**Files:** `tests/api/test_campaign_history_api.py`
**AC:** `test_campaign_history_endpoint_returns_narrative_ledger` passes.

### Step 5: Create docs/simulation/domains/campaign_orchestrator_contract.md
Document CampaignOrchestrator lifecycle, NarrativeLedger schema, episode handoff
rules, carry-forward rules, and the REST endpoint contract.

**Files:** `docs/simulation/domains/campaign_orchestrator_contract.md`
**AC:** File exists with complete contract documentation.

### Step 6: Update docs/simulation/domains/campaigns_contract.md
Add REST endpoint boundary entry to the boundary table.

**Files:** `docs/simulation/domains/campaigns_contract.md`

### Step 7: Run make knowledge-index-update
Rebuild doc index since docs/ changed.

## Scope Guards

- Do NOT add campaign orchestrator to V2EngineManager — out of scope.
- Do NOT implement campaign persistence/checkpoint — out of scope.
- Do NOT add campaign creation/POST endpoints — out of scope.
- Presenter outputs only the 6 fields from the ticket spec shape (plus entry_id
  for dedup transparency).

## AC → Step Mapping

| AC | Step |
|----|------|
| GET /api/v1/campaigns/{id}/history returns structured NarrativeLedger | Step 1, 2, 3 |
| test_campaign_history_endpoint_returns_narrative_ledger passes | Step 4 |
| docs/simulation/domains/campaign_orchestrator_contract.md exists | Step 5 |

## Deviations

None yet.
