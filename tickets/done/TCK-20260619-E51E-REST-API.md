---
status: done
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E51E-REST-API
phase: open
date: 2026-06-20
tags: [chronicle, rest-api, phase-5]
---

# TCK-20260619-E51E-REST-API

## Title
Epic 5.1E · Chronicle REST Endpoints

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Exposes `chronicle.json` via REST. Prerequisite for any tooling to inspect campaign history without reading files directly.

**Requires:** TCK-20260619-E51D-RENDERER

## Scope

New file `src/api/routes/chronicle.py`:

```
GET /api/v1/chronicle/{campaign_id}
    → full chronicle.json (eras, episodes, incidents, named_milestones)

GET /api/v1/chronicle/{campaign_id}/eras/{era_id}/summary
    → {era_id, name, milestone_count, named_milestones: [str, ...]}
```

Register router in `src/api/server.py`. Load `chronicle.json` from campaign output directory.

After E51E: create `docs/simulation/domains/chronicle_contract.md` documenting ChronicleCompiler pipeline, significance scoring formula, hierarchy definitions, Chronicle.md schema, REST endpoints. Run `make knowledge-index-update`.

## Acceptance Criteria
- `test_chronicle_rest_endpoint_returns_structured_json` passes
- `test_era_summary_endpoint_returns_milestone_names` passes

## Related Tickets
- TCK-20260619-E51-CHRONICLE (parent epic)
- TCK-20260619-E51D-RENDERER (required)

## Related Docs
- `docs/simulation/domains/chronicle_contract.md` (new — create after implementation)

## Related Code Areas
- `src/api/routes/chronicle.py` (new)
- `src/api/server.py` (register router)
- `tests/api/test_chronicle_api.py` (new)

## Test Summary
```bash
pytest tests/api/test_chronicle_api.py -x -v
```
## Files Changed
- `src/api/presenters/chronicle.py` (new) — Pydantic presenter models: ChronicleEraPresenter, ChronicleEpisodePresenter, ChronicleMilestonePresenter, ChronicleResponse, ErasSummaryResponse
- `src/api/routes/chronicle.py` (new) — FastAPI router with registry pattern; GET /chronicle/{campaign_id} + GET /chronicle/{campaign_id}/eras/{era_id}/summary
- `src/api/server.py` (modified) — registered chronicle router
- `tests/api/test_chronicle_api.py` (new) — 7 tests, all pass
- `docs/simulation/domains/chronicle_contract.md` (new) — full pipeline + schema + REST docs
- `docs/parity_ledger/social_narrative.yaml` (modified) — added SOC-CHRON-004, SOC-CHRON-005

## Completion Summary
Implemented Chronicle REST API (E51E). Two GET endpoints: full chronicle (eras/episodes/named_milestones) and era summary with milestone names. Registry pattern (same as campaigns.py). All responses shaped through Pydantic presenter layer — no raw domain models. 7 tests pass (including both AC-required tests). Chronicle contract doc created. Parity ledger updated with SOC-CHRON-004 and SOC-CHRON-005.
