---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260718-AGENTOPS-STATS-BOARD-EPIC
artifact_type: investigation
tags: [dashboard, observability, reporting, agent-monitoring]
---

# Investigation — TCK-20260718-AGENTOPS-STATS-BOARD-EPIC

## Context scan

Per this project's Context Scan rule, `mcp__knowledge-search__search_docs` and direct reads
preceded scoping. Found that this gap was already anticipated and deliberately deferred rather
than overlooked:

- `docs/plans/agent_ops_dashboard/idea_agent_ops_dashboard.md` (the dashboard's own origin idea
  doc) explicitly notes `docs/guides/ticket_reporting.md`'s "pillars" framing lists ticket
  velocity/throughput and tier/type/priority distribution as not built.
- The dashboard's existing 3 views (Gantt/Tickets/Replay) are row-level browsing, not aggregate
  statistics — no existing view answers "how many runs failed this week" or "how is the ticket
  corpus distributed by tier" without manual counting.
- `tools/agent-monitoring/generate_retro.py` already computes a rich set of agent-monitoring
  aggregate stats (run/gate-failure rates, tier distribution, tag breakdown, duration/agent-count
  averages, slow-run detection) but only renders them to Markdown — nothing exposed this as
  structured data any interactive tool could consume.

Full investigation, architectural constraints, and candidate child-ticket concerns are written up
in `docs/plans/agent_ops_dashboard/proposal_stats_board.md` (produced via the create-tickets.js
pipeline's Structure phase, `concern-investigator` role) — that document is this epic's real
investigation artifact; this file summarizes rather than duplicates it.

## Overlap check

Re-scanned `tickets/` for prior "dashboard"-named work the proposal doc's own investigation had
already found, and independently re-confirmed each by direct re-read:

- `TCK-20260529-OBS-PHASE27-API-DASHBOARD` — simulation-runtime observability storage/API, not the
  Agent Ops Dashboard.
- `TCK-20260614-RESOURCE-DASHBOARD` — a runtime resource CLI (memory/queue/pressure), unrelated.
- `TCK-20260607-MON-DASHBOARD` — static Docusaurus integration of retro Markdown reports, not an
  interactive chart tool.

None overlap this epic's actual scope: an interactive, chart-based stats tab over ticket-corpus and
agent-monitoring aggregate data, inside the existing Agent Ops Dashboard SPA.

## User scope decisions

Two decisions confirmed directly with the user via `AskUserQuestion` before scoping child tickets:

1. This is a new 4th tab in the existing Agent Ops Dashboard, not a separate tool.
2. v1 covers both agent-monitoring statistics AND ticket-corpus statistics together in one pass,
   not staged sequentially across separate epics.

## Child breakdown rationale

Four build tickets plus this epic, in dependency order (`SEQUENCE.md`):

1. `TCK-20260718-RETRO-STATS-REFACTOR` — extract `generate_retro.py`'s inline computation into a
   reusable `compute_retro_metrics()` function, proven byte-identical to the existing CLI output.
   Must land first: both the API ticket and eventually the frontend depend on this existing and
   being stable.
2. `TCK-20260718-AGENTOPS-STATS-API` — new backend endpoint consuming (1)'s function.
3. `TCK-20260718-TICKET-CORPUS-REPORT` — new, independent report tool + endpoint for the
   ticket-corpus pillars; no dependency on (1)/(2) beyond sharing the same backend app.
4. `TCK-20260718-STATS-TAB-FRONTEND` — the actual user-facing deliverable; depends on both (2) and
   (3) existing first so it has real endpoints to consume.
5. `TCK-20260718-STATS-DOCS-UPDATE` — documentation only, depends on all four prior tickets landing
   so it describes the actually-shipped state, not the plan.
