---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260718-GLOSSARY-API
phase: done
date: 2026-07-18
tags: [dashboard, observability, api-design]
---

# TCK-20260718-GLOSSARY-API

## Title
New GET /api/glossary endpoint exposing backend-owned tooltip descriptions

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Child of `TCK-20260718-GLOSSARY-TOOLTIPS-EPIC`, depends on `TCK-20260718-GLOSSARY-REGISTRY`.
Expose the new glossary registry as a typed dashboard API endpoint, and decide/implement how
Layer's existing per-layer descriptions (`layer_registry.jsonl`'s `note` field) surface alongside
it without duplication.

## Scope
- `models.py`: new `GlossaryEntry`/`GlossaryResponse` Pydantic models.
- `ingest.py`: new `DashboardCache.get_glossary()` merging `glossary_registry.py`'s entries with
  `layer_registry.py`'s entries (reusing each layer's existing `note` field as its description,
  under `category="layer"` — never duplicated into a second file).
- `main.py`: new `GET /api/glossary` route.
- `tests/tools/test_agent_ops_dashboard_glossary.py`: 7 new tests. Updated
  `test_agent_ops_dashboard_api_boundary.py`'s pinned route-set assertion in place.
- New parity ledger entry `INFRA-279`.

## Out of Scope
- Any frontend change — `TCK-20260718-GLOSSARY-TOOLTIPS-FRONTEND`'s scope.
- Copying layer descriptions into `glossary_registry.jsonl` — deliberately merged at read time
  instead (see investigation.md's design decision).

## Acceptance Criteria
- [x] `GET /api/glossary` returns a typed `GlossaryResponse`, never a raw dict.
- [x] Layer descriptions reused live from `layer_registry.jsonl`'s `note` field, never duplicated.
- [x] 25 new/updated tests passing (18 glossary_registry + 7 glossary API), full dashboard suite
      (66 tests) still green.
- [x] Verified live: `curl http://localhost:8420/api/glossary` returns 54 real terms after a
      fresh `make dashboard-serve` build (stale server process killed first).

## Related Tickets
- TCK-20260718-GLOSSARY-TOOLTIPS-EPIC (parent epic)
- TCK-20260718-GLOSSARY-REGISTRY (depended on)
- TCK-20260718-GLOSSARY-TOOLTIPS-FRONTEND (depends on this ticket)

## Related Docs
- docs/plans/agent_ops_dashboard/proposal_glossary_tooltips.md
- docs/parity_ledger/infrastructure.yaml (INFRA-279)

## Related Stored Artifacts
- stored_artifacts/TCK-20260718-GLOSSARY-API/

## Related Code Areas
- src/api/agent_ops_dashboard/models.py
- src/api/agent_ops_dashboard/ingest.py
- src/api/agent_ops_dashboard/main.py
- tests/tools/test_agent_ops_dashboard_glossary.py
- tests/tools/test_agent_ops_dashboard_api_boundary.py

## Assumptions / Open Questions
None — both design questions the proposal raised (endpoint shape; layer-merge approach) resolved
in investigation.md.

## Implementation Notes
Executed directly (Read/Edit/Bash/Write) — no Agent-tool subagent access in this execution
context.

Verified no term-key collision exists between the 35 glossary terms and the 19 layer names before
writing the merge loop; added a defensive `if layer in terms: continue` guard regardless, so a
future addition to either registry's term space can never silently overwrite the other's entry.

Live-verified the endpoint end to end after killing a stale server process (same recurring
gotcha from earlier tickets today) and rebuilding fresh — 54 total terms returned, `DONE` and
`economy` spot-checked with correct category/description.

## Test Summary
`python3 -m pytest tests/tools/test_glossary_registry.py tests/tools/
test_agent_ops_dashboard_glossary.py tests/tools/test_agent_ops_dashboard_api_boundary.py
tests/tools/test_agent_ops_dashboard_stats.py tests/tools/test_agent_ops_dashboard_ingest.py
tests/tools/test_agent_ops_dashboard_api.py tests/tools/test_agent_ops_dashboard_serve.py
tests/tools/test_agent_ops_dashboard_concurrency.py
tests/tools/test_agent_ops_dashboard_frontend_api_surface.py -q` — 84/84 passing. Live curl
verification against a freshly-built `make dashboard-serve` confirms real data (54 terms).

## Files Changed
- src/api/agent_ops_dashboard/models.py (new `GlossaryEntry`/`GlossaryResponse`)
- src/api/agent_ops_dashboard/ingest.py (new `get_glossary()` + imports)
- src/api/agent_ops_dashboard/main.py (new `GET /api/glossary` route)
- tests/tools/test_agent_ops_dashboard_glossary.py (new)
- tests/tools/test_agent_ops_dashboard_api_boundary.py (pinned route-set updated in place)
- docs/parity_ledger/infrastructure.yaml (new `INFRA-279`)

## Completion Summary
`GET /api/glossary` is live and verified, merging the new glossary registry with Layer's existing
descriptions at read time (no duplication). 84/84 tests passing. Unblocks
`TCK-20260718-GLOSSARY-TOOLTIPS-FRONTEND`.
