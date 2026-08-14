---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260718-AGENTOPS-STATS-BOARD-EPIC
artifact_type: plan
tags: [dashboard, observability, reporting, agent-monitoring]
---

# Plan — TCK-20260718-AGENTOPS-STATS-BOARD-EPIC

Per this project's Tier Routing table, epic tier is "Scope only — tracks child tickets; no direct
implementation." This epic's plan **is** its child-ticket breakdown and dependency order — there is
no separate implementation plan for the epic itself, since epics never touch code directly.

## Child tickets, in `SEQUENCE.md` order

1. `TCK-20260718-RETRO-STATS-REFACTOR` (standard) — computation/rendering split in
   `generate_retro.py`, byte-identical CLI output required.
2. `TCK-20260718-AGENTOPS-STATS-API` (standard) — new `GET /api/stats/agent-monitoring` typed
   endpoint, consuming (1).
3. `TCK-20260718-TICKET-CORPUS-REPORT` (standard) — new `tools/ticket_stats_report.py` +
   `GET /api/stats/tickets` typed endpoint.
4. `TCK-20260718-STATS-TAB-FRONTEND` (standard) — new "Stats" tab consuming (2) and (3), gated on
   invoking the `dataviz` skill before any chart code.
5. `TCK-20260718-STATS-DOCS-UPDATE` (hotfix) — doc updates once (1)-(4) have landed.

## Acceptance-criteria map

| Epic AC | Closed by |
|---|---|
| Agent-monitoring stats via new endpoint, backed by `generate_retro.py`'s own computation | 1, 2 |
| `generate_retro.py` CLI output proven byte-identical | 1 |
| New ticket-corpus report tool covers all 4 named pillars | 3 |
| 4th "Stats" tab, built using the `dataviz` skill | 4 |
| All new endpoints return typed Pydantic models only | 2, 3 |
| Relevant docs updated | 5 |

Each child ticket's own `plan.md` (in its `stored_artifacts/{id}/`) carries the actual
implementation-level plan; this file only records the epic-level breakdown and sequencing decision.
