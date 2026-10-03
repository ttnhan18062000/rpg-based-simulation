---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260718-STATS-DOCS-UPDATE
phase: done
date: 2026-07-18
tags: [dashboard, reporting]
---

# TCK-20260718-STATS-DOCS-UPDATE

## Title
Document the new Stats tab and its two backend endpoints

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
Once the Stats tab and its two backend endpoints exist (all three prior tickets in this epic), the dashboard's own documentation needs updating to describe them — mirroring how the existing three views are documented — and `docs/guides/ticket_reporting.md`'s "Other candidate pillars (not built)" section needs to move the four now-built pillars out of "not built."

## Scope
- `docs/guides/agent_ops_dashboard.md`: new section describing the Stats tab, mirroring the existing "Recent Activity Gantt" / "Tickets view" / "Replay Timeline" sections' style and depth.
- `docs/observability/agent_ops_dashboard_contract.md`: new entries in the routes table and response-models section for the two new endpoints, following the doc's existing per-route/per-model documentation pattern.
- `docs/guides/ticket_reporting.md`: move ticket velocity/throughput, tier/type/priority distribution, and layer distribution out of "Other candidate pillars (not built)" and into a new "Pillar 2: Ticket Corpus Statistics" section (mirroring "Pillar 1: Tag Usage Reporting"'s structure — What it does / Quick start / Technical detail), pointing at the new `tools/*_report.py` tool from TCK-20260718-TICKET-CORPUS-REPORT. Leave "Artifact completeness" in the not-built list only if that specific sub-pillar wasn't actually covered by the report tool — verify against that ticket's actual final scope rather than assuming.
- Update the parity ledger (`docs/parity_ledger/infrastructure.yaml`) if any of the three prior tickets left an entry needing a final consolidation pass — check for staleness the way today's earlier tickets learned to (an independent review, not just trusting each prior ticket's own self-report).

## Out of Scope
- Any further doc restructuring beyond documenting what was actually built.
- Re-verifying the prior three tickets' functional correctness — that's their own Verify phase's job; this ticket only documents the landed state.

## Acceptance Criteria
- [x] Both dashboard docs describe the new Stats tab and its two endpoints accurately, matching what was actually implemented (verify against the real code, don't just describe what the proposal originally planned).
- [x] `ticket_reporting.md` has a new "Pillar 2" section and its "not built" list no longer includes the pillars that were actually built.
- [x] Parity ledger checked for staleness across all three prior tickets' entries, corrected if any drift is found.

## Related Tickets
- TCK-20260718-AGENTOPS-STATS-API (dependency)
- TCK-20260718-TICKET-CORPUS-REPORT (dependency)
- TCK-20260718-STATS-TAB-FRONTEND (dependency)
- TCK-20260718-AGENTOPS-STATS-BOARD-EPIC (parent epic)

## Related Docs
- docs/guides/agent_ops_dashboard.md
- docs/observability/agent_ops_dashboard_contract.md
- docs/guides/ticket_reporting.md
- docs/parity_ledger/infrastructure.yaml

## Related Stored Artifacts
None yet.

## Related Code Areas
None — documentation only.

## Assumptions / Open Questions
None.

## Implementation Notes
- `docs/guides/agent_ops_dashboard.md`: reworded the intro ("three views" → "four views",
  "Five prior tickets" → non-numbered "a series of tickets" since an exact count of every
  incremental follow-up ticket wasn't worth pinning to a number that will drift again), and added
  a new `### Stats` section describing both sub-sections, the fetch-once (no polling) behavior, the
  no-new-dependency/plain-HTML chart convention, the `dataviz`-validated palette decision, and the
  documented no-live-light-theme finding from TCK-20260718-STATS-TAB-FRONTEND's investigation.
- `docs/observability/agent_ops_dashboard_contract.md`: added the two new routes to the routes
  table (including the actual `all`/`days`/`week` priority order read directly from
  `ingest.py::get_agent_monitoring_stats`, not assumed), two new response-model paragraphs
  (`AgentMonitoringStats`/`TicketCorpusStats`, both explicitly noted as wrapping — not
  recomputing — `compute_retro_metrics()`/`build_json_report()`), an ingest/cache-section update
  documenting `_runs_all`/`_events_all` retention and `get_ticket_corpus_stats`'s deliberate
  fresh-file-walk exception to the mtime-cache pattern, and 6 new frontend-structure bullets
  (`StatsView.tsx`, `BarChart.tsx`, `GroupedBarChart.tsx`, `StatTile.tsx`, `chartPalette.ts`,
  `App.tsx`'s extended `PageView` union).
- `docs/guides/ticket_reporting.md`: verified against `tools/ticket_stats_report.py`'s actual
  source (not just the proposal) that all four candidate pillars listed in the old "not built"
  section were genuinely covered — confirmed via the module's own docstring and a live run
  (`python3 tools/ticket_stats_report.py`, snapshot: 1179 scanned, 1155 included, 624/971 artifact
  completeness) — so the entire "Other candidate pillars (not built)" section was replaced with a
  new "Pillar 2: Ticket Corpus Statistics" section, not partially trimmed.
- Parity ledger staleness check: re-read all of INFRA-275's `v2_evidence`/`test_path` content
  covering the three prior tickets (RETRO-STATS-REFACTOR, AGENTOPS-STATS-API,
  TICKET-CORPUS-REPORT, STATS-TAB-FRONTEND) end to end — no drift found; each paragraph's claims
  (route signatures, test counts, live-verification numbers) were independently re-checked against
  the current source and passing test output during this same session's ticket 4 close, so no
  correction was needed here beyond what was already current.
- Ran `make knowledge-index-update` (docs changed) and `graphify update .` (missed after ticket 4's
  `dashboard-frontend/src/` changes — dashboard-frontend is tracked in the graph, confirmed via
  `graphify query "App.tsx"` returning real nodes; caught and run here before Finalize rather than
  left stale).

## Test Summary
- `python3 tools/validate_frontmatter.py <each changed doc> --content-type doc`: all 3 OK.
- Live re-run of `python3 tools/ticket_stats_report.py` to source the doc's numbers directly from
  the tool's real current output, not the proposal's stale estimates.
- `graphify query "StatsView"` confirmed the new frontend nodes (StatsView.tsx, BarChart usage,
  fetchAgentMonitoringStats/fetchTicketCorpusStats) are present in the rebuilt graph.
- No code changed by this ticket (documentation only, per its own scope) — no pytest/npm test
  re-run required beyond the frontmatter validator.

## Files Changed
- `docs/guides/agent_ops_dashboard.md`
- `docs/observability/agent_ops_dashboard_contract.md`
- `docs/guides/ticket_reporting.md`
- `graphify-out/graph.json`, `graphify-out/GRAPH_REPORT.md` (regenerated by `graphify update .`)

## Completion Summary
Documented the Stats tab and its two backend endpoints in both dashboard docs, replaced
`ticket_reporting.md`'s "not built" pillar list with a real "Pillar 2" section (all four candidate
pillars were confirmed built, verified against the tool's actual source and a live run rather than
assumed from the proposal), and confirmed no staleness in the parity ledger's INFRA-275 entry
across all three prior tickets. Closes out the agentops-stats-board epic.
