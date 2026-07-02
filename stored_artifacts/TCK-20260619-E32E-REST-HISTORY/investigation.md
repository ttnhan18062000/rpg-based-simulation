---
status: active
ticket_id: TCK-20260619-E32E-REST-HISTORY
artifact_type: investigation
date: 2026-06-21
---

# Investigation — TCK-20260619-E32E-REST-HISTORY

## Context

E32E adds the REST surface for `NarrativeLedger`. It gates external tooling
that needs to inspect campaign continuity without parsing JSONL directly.
Prerequisite: TCK-20260619-E32D-NARRATIVE-LEDGER (DONE).

## Key Findings

### 1. NarrativeLedgerEntry is fully implemented (7 fields)

`src/domains/campaigns/state.py::NarrativeLedgerEntry` (line 142) is a frozen
dataclass with:
- `episode: int`
- `tick: int`
- `event_type: str`
- `subject_id: str`
- `payload: dict`
- `significance: float`
- `entry_id: str` (dedup key)

`to_dict()` serializes all 7 fields. The ticket scope response shape includes
6 of them (omits `entry_id` — not required in the REST response per spec, but
we include it for deduplication transparency).

### 2. NarrativeLedger query service is fully implemented

`src/domains/campaigns/narrative_ledger.py::NarrativeLedger` wraps a list of
`NarrativeLedgerEntry` objects and exposes `query(event_type, min_significance,
episode)`. This is exactly what the REST endpoint filters need.

### 3. CampaignOrchestrator owns the state

`CampaignOrchestrator.state.narrative_ledger` is the authoritative list.
The REST endpoint needs access to a `CampaignState`. The current API server
has no campaign orchestrator registry — the orchestrator is not exposed via
`V2EngineManager`.

**Resolution:** The endpoint does NOT need a live running orchestrator for unit
testing. The test harness will inject a pre-built `CampaignState` directly
via a registry dict (campaign_id → CampaignState). This follows the existing
pattern where the engine_manager is stored in app state at lifespan.

For the implementation, we use a module-level `_CAMPAIGN_REGISTRY: dict[str,
CampaignState]` on the route module, with a `register_campaign` helper. Tests
inject state directly; production wiring happens when orchestrators run.

### 4. API boundary rule: no raw domain models

The route MUST NOT return `NarrativeLedgerEntry` objects directly. A presenter
layer is required. We add `src/api/presenters/campaigns.py` with:
- `NarrativeLedgerEntryPresenter` (Pydantic BaseModel with 7 fields)
- `CampaignHistoryResponse` (Pydantic BaseModel: campaign_id, entry_count, entries)

### 5. Router prefix and registration

Existing routers use `prefix="/api/v1"` at `include_router` in `server.py`.
The new router uses `prefix="/campaigns"` (tags=["Campaigns"]) inside the module,
so the effective URL is `/api/v1/campaigns/{id}/history`.

`server.py` already imports routes by module; we add:
```python
from src.api.routes import campaigns
app.include_router(campaigns.router, prefix="/api/v1")
```

### 6. Query parameters match ticket scope exactly

- `?event_type=<str>` (optional)
- `?min_significance=<float>` (optional, default 0.0)
- `?episode=<int>` (optional)

These map directly to `NarrativeLedger.query(event_type, min_significance, episode)`.

### 7. 404 when campaign not found

If `campaign_id` is not registered, return HTTP 404. This is the correct
REST behavior for an unknown resource.

### 8. Existing test patterns

`tests/api/test_cognition_history_api.py` patches route-module service objects
and calls route functions directly with `@pytest.mark.anyio`. The same pattern
applies here — patch the registry, call the route handler directly.

### 9. No engine_manager dependency

The campaign history endpoint does NOT depend on `V2EngineManager`. Campaigns
run independently of the scenario runtime; the endpoint reads from the campaign
registry directly. No `Depends(get_engine_manager)` needed.

### 10. campaigns_contract.md update

The existing `docs/simulation/domains/campaigns_contract.md` has a boundary
table. We add a row for this endpoint. We also create the new
`campaign_orchestrator_contract.md` per ticket scope.

## Open Questions

None — design fully resolved from existing code patterns.
