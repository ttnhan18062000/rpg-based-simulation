---
status: active
ticket_id: TCK-20260619-E51E-REST-API
artifact_type: plan
date: 2026-06-22
---

# Plan — TCK-20260619-E51E-REST-API

## Files to Create

1. `src/api/presenters/chronicle.py` — Pydantic read models
   - `ChronicleEraPresenter`
   - `ChronicleEpisodePresenter`
   - `ChronicleMilestonePresenter`
   - `ChronicleResponse` (full response)
   - `ErasSummaryResponse`

2. `src/api/routes/chronicle.py` — FastAPI router
   - Module-level registry: `Dict[str, dict]` (chronicle JSON dict keyed by campaign_id)
   - `register_chronicle(campaign_id, data)` / `unregister_chronicle()` / `_clear_registry()`
   - `GET /chronicle/{campaign_id}` → `ChronicleResponse`
   - `GET /chronicle/{campaign_id}/eras/{era_id}/summary` → `ErasSummaryResponse`

3. `tests/api/test_chronicle_api.py` — tests
   - `test_chronicle_rest_endpoint_returns_structured_json` (AC-1)
   - `test_era_summary_endpoint_returns_milestone_names` (AC-2)
   - `test_chronicle_404_unknown_campaign`
   - `test_era_summary_404_unknown_era`
   - `test_chronicle_empty_eras`

## Files to Modify

4. `src/api/server.py` — add `from src.api.routes import chronicle` + include_router

5. `docs/simulation/domains/chronicle_contract.md` — new doc (required by ticket scope)

## Ordering

1. Presenters (no deps)
2. Route (depends on presenters)
3. Register in server.py
4. Tests
5. Doc
6. Run tests
