---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260718-GLOSSARY-API
artifact_type: plan
tags: [dashboard, observability, api-design]
---

# Implementation Plan — TCK-20260718-GLOSSARY-API

## Summary
Add `GlossaryEntry`/`GlossaryResponse` Pydantic models, `DashboardCache.get_glossary()` merging
`glossary_registry.py` + `layer_registry.py`'s `note` field, and a new `GET /api/glossary` route.

## Steps

### Step 1 — `models.py`: `GlossaryEntry` (`term`, `category`, `description`) and
`GlossaryResponse` (`terms: Dict[str, GlossaryEntry]`).

### Step 2 — `ingest.py`: import `glossary_registry.load_registry` (aliased
`load_glossary_registry`) and `layer_registry` module-level; add `DashboardCache.get_glossary()`
mirroring `get_ticket_corpus_stats()`'s independent-fresh-read shape. Merge glossary_registry
entries first, then layer_registry entries under `category="layer"` (skip empty-note layers,
skip on term-key collision, first-registered wins).

### Step 3 — `main.py`: import `GlossaryResponse`, add `GET /api/glossary` route.

### Step 4 — Tests: new `tests/tools/test_agent_ops_dashboard_glossary.py` mirroring
`test_agent_ops_dashboard_stats.py`'s fixture-repo pattern — merge happy path, layer-note-reuse
(never duplicated), empty-note-skipped, empty-registries-no-crash, route-level 200 + typed shape,
real-registry end-to-end check. Update `test_agent_ops_dashboard_api_boundary.py`'s pinned
`test_all_declared_routes_present` route-set assertion to include `/api/glossary` (in place, not
deleted — same coordination discipline established by earlier tickets today).

## Scope Guards
- Do not write to either registry file from this endpoint — read-only.
- Do not touch `dashboard-frontend/` — frontend wiring is
  `TCK-20260718-GLOSSARY-TOOLTIPS-FRONTEND`'s scope.
- Do not add a `category="layer"` entry to `glossary_registry.py`'s own `GLOSSARY_CATEGORIES` —
  layer entries are synthesized at read time from a different file, never written via `add_term()`.

## Dependency Map
Depends on `TCK-20260718-GLOSSARY-REGISTRY` (imports its `load_registry()`). Blocks
`TCK-20260718-GLOSSARY-TOOLTIPS-FRONTEND` (fetches this endpoint).

## Acceptance Criteria Map
- AC "`GET /api/glossary`-shaped endpoint returns the registry as a typed Pydantic model, verified
  live" → Steps 1-3 + live curl verification.

## Anti-Drift Notes
`get_glossary()`'s merge loop's collision guard (`if layer in terms: continue`) is deliberately
defensive against a currently-nonexistent collision — a future addition to either registry's term
space could create one; the guard prevents a silent overwrite rather than requiring a human to
notice the bug after the fact.
