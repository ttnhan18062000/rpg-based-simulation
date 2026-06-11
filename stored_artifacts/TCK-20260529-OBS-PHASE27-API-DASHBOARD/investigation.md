---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260529-OBS-PHASE27-API-DASHBOARD
artifact_type: investigation
tags: [obs, phase27, api, dashboard]
---

# Investigation — Phase 27 API & Dashboard Integration

We analyzed:
1. `src/observability/reporting/artifact_repository.py` and `src/observability/reporting/retention.py` for how to extend the artifact paths and retention policy to support Phase 26/27 behavior files.
2. `src/observability/warehouse/adapters.py` and `src/observability/warehouse/models.py` for local dataset schema extensions.
3. `src/api/server.py` for API routes structure and how `/api/v1/observability/ui` is integrated.

## Rationale
- We need to expose endpoints that return JSON behavior summaries (scorecards, timeline, episodes, comparisons, insights).
- If the artifact files are missing or behavior observability is disabled, these endpoints should degrade gracefully by returning default or empty structures rather than throwing 500 errors.
