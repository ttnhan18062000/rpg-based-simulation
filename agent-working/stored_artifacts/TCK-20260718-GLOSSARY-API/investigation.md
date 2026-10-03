---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260718-GLOSSARY-API
artifact_type: investigation
tags: [dashboard, observability, api-design]
---

# Investigation: TCK-20260718-GLOSSARY-API

## Current Behavior
`TCK-20260718-GLOSSARY-REGISTRY` built `tools/glossary_registry.py`/`docs/guidelines/
glossary_registry.jsonl`, but nothing yet exposes it to the dashboard frontend. `src/api/
agent_ops_dashboard/models.py` has no glossary shape; `ingest.py`'s `DashboardCache` has no
`get_glossary()` method; `main.py` has no `/api/glossary` route.

`docs/guidelines/layer_registry.jsonl` (built earlier today) already carries a per-layer `note`
field with real descriptions for all 19 layers — confirmed via direct read.
`facets.layers` (the dashboard's existing Layer filter data) carries only the bare layer name, no
description.

## Mechanics/Engine Constraints
Dashboard tooling only, read-only over `tickets/**`/`agent-monitoring/*.jsonl` — no Mechanics
Bible/engine contract applies. This dashboard's own established API-boundary rule does apply:
every route must declare a real Pydantic `response_model`, never a raw dict
(`tests/tools/test_agent_ops_dashboard_api_boundary.py::test_typed_response_models_not_dict`).

## Design Decision: Layer descriptions — merge at read time, not duplicate
Proposal explicitly flagged this as a real design call. Decision: `get_glossary()` merges two
sources at read time — `glossary_registry.py`'s own entries, plus every `layer_registry.py` entry
re-exposed under `category="layer"` using its existing `note` field as the description. Never
copies layer descriptions into `glossary_registry.jsonl` as a second, parallel source (would
immediately go stale the moment either file is edited independently — the exact class of drift
this whole effort exists to prevent, per `status_drift_check.py`'s own precedent). Verified no
term-name collision exists between the two registries' key spaces (35 glossary terms, 19 layer
names, zero overlap) and added a defensive first-registered-wins guard in code regardless, in
case a future addition to either ever collides.

## Prior Work / Precedent
`get_ticket_corpus_stats()` is the direct template for a `DashboardCache` method that does its own
independent file read rather than participating in the mtime-cached `_rebuild()` cycle — followed
exactly for `get_glossary()`, for the same reason (two small, append-only, rarely-changing source
files; not worth restructuring `_rebuild()` for).

## Risks and Open Questions
None outstanding — both open questions the proposal raised (endpoint shape, layer-merge design)
are resolved above.

## Anti-Drift Hazards
- `get_glossary()` must never write to either registry file — read-only, matching this whole
  dashboard's contract.
- The layer-merge loop's `if layer in terms: continue` guard must never be removed even though no
  current collision exists — it is the only thing preventing a silent future data-loss bug if
  either registry's term space ever grows to overlap.
