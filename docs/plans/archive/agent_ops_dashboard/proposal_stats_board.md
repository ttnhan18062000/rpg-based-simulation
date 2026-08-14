---
status: historical
layer: observability
authority: P2
audience: developer
maturity: shipped
date: 2026-07-18
archived: 2026-07-19
tags: [dashboard, observability, reporting, agent-monitoring]
---

# Proposal: Statistics board — a 4th "Stats" tab on the Agent Ops Dashboard, covering both agent-monitoring and ticket-corpus aggregate metrics

**Archived:** 2026-07-19 — shipped by `TCK-20260718-AGENTOPS-STATS-BOARD-EPIC` and its five child
tickets (all `tickets/done/`): `TCK-20260718-RETRO-STATS-REFACTOR` (concern 1, `generate_retro.py`'s
`compute_retro_metrics()` extracted as a typed, reusable function, proven byte-identical to the prior
Markdown output via `git stash` comparison), `TCK-20260718-AGENTOPS-STATS-API` (concern 2, agent-
monitoring stats endpoint), `TCK-20260718-TICKET-CORPUS-REPORT` (concern 3, new
`tools/ticket_stats_report.py` covering all four previously-unbuilt pillars: velocity, tier/type/
priority distribution, layer distribution, artifact completeness), `TCK-20260718-STATS-TAB-FRONTEND`
(concern 4, new Stats tab), `TCK-20260718-STATS-DOCS-UPDATE` (concern 5). This document is the
historical design reference.

**Maturity: SHIPPED** — user asked for "a board to view statistical agent
monitoring and tickets system." Investigated before proposing anything
(`search_docs` + direct reads, per this repo's Context Scan rule): this gap
was already anticipated and deliberately deferred by the dashboard's own
origin idea doc. User confirmed scope via two direct questions: (1) this is
a new tab in the existing Agent Ops Dashboard, not a separate tool; (2) v1
covers **both** agent-monitoring stats and ticket-corpus stats together, not
staged sequentially.

## Background investigation (already done, feed this to Investigate — do not redo)

[`idea_agent_ops_dashboard.md`](idea_agent_ops_dashboard.md) (the dashboard's
own origin doc, "Relationship to Planned Tickets" section) explicitly flags:
> `docs/guides/ticket_reporting.md`'s "pillars" framing for ticket-corpus
> reporting explicitly lists ticket velocity/throughput and tier/type/priority
> distribution as **not built** — this dashboard's Tickets view covers those
> implicitly via a filterable table over the same underlying data, but does
> not attempt the full reporting-pillar treatment. Not resolved here.

`docs/guides/ticket_reporting.md`'s "Other candidate pillars (not built)"
section names exactly four ticket-corpus statistics as known-wanted,
never-scoped work:
- **Ticket velocity/throughput** — from `tickets/working_log.csv` timestamps
  (tickets closed per day/week, by tier or layer). Confirmed the CSV's real
  columns: `timestamp,ticket_id,title,status,summary,artifacts_path` —
  sufficient for this, no schema change needed.
- **Tier/type/priority distribution** — now trivially computable and
  guaranteed-canonical, since today's `TCK-20260718-CANONICAL-FIELD-ENUMS-EPIC`
  gave all three fields real hard-validated enums
  (`tools/ticket_field_values.py`).
- **Layer distribution** — cross-tab layer against tier/type, reading
  `docs/REGISTRY.yaml`. Also now registry-backed and canonical
  (`docs/guidelines/layer_registry.jsonl` / `tools/layer_registry.py`,
  from the same epic).
- **Artifact completeness** — how many `standard`/`epic` tickets have a
  matching `stored_artifacts/{ticket_id}/` folder with all 3 required files
  (`investigation.md`/`plan.md`/`test_plan.md`), vs. gaps.

`docs/guides/ticket_reporting.md` also states its own convention for any new
pillar: "belongs as a new `tools/*_report.py` script following the same
pattern as `tools/tag_report.py` (reuse `validate_frontmatter.py`/
`generate_registry.py` parsing, dedicated test file, `make` target) — not
folded into `tag_report.py` itself." Whoever implements the ticket-corpus
side of this proposal should follow that established convention for the
underlying computation, then have the dashboard backend import and expose it
as JSON — mirroring exactly how `tag_report.py`'s logic is reused by
`generate_retro.py` today (see below), rather than reimplementing corpus
aggregation from scratch inside `src/api/agent_ops_dashboard/`.

For the agent-monitoring side: `tools/agent-monitoring/generate_retro.py`
(the existing weekly retro report generator, invoked via the
`agent-monitoring-retro` skill) **already computes almost everything
relevant** — read its `generate()` function (`tools/agent-monitoring/
generate_retro.py:168`) in full before designing anything new. It already
calculates, per period: total runs, DONE count/rate, gate-failure count and
breakdown by status, reason-code breakdown, tier distribution (counts/done/
scoped), avg duration, avg agents per run, total agent calls, tag breakdown
(subsystem-topic and process-skill-signal categories, reusing
`tag_registry.py`/`tag_report.py`'s `categorize_tag`), agent status
distribution, slow-run detection (>30min), and summary-quality metrics
(empty/legacy/long summaries). **The problem is entirely presentational**:
this logic renders straight to Markdown `lines.append(...)` calls today —
there is no JSON/structured-data return value, so nothing outside this one
script can consume the computed numbers. Whoever implements the
agent-monitoring side of this proposal should refactor `generate()` (or
extract its computation into a new, separate function `generate()` calls)
to return a typed/structured result the existing CLI can still render to
Markdown from, AND the new dashboard endpoint can also consume as JSON — do
not duplicate the computation in a second module. This exact "same
computation, formatted two ways" pattern already exists once in this repo
(`tools/tag_report.py`'s logic feeding both its own stdout and
`generate_retro.py`'s tag-breakdown section) — follow that precedent.

## Architectural constraints (carry forward from the existing dashboard)

- API responses must be typed Pydantic models (`models.py`), never raw
  dicts — the dashboard's established, tested rule
  (`tests/tools/test_agent_ops_dashboard_api_boundary.py`).
- `src/api/agent_ops_dashboard/main.py` never reads a file directly —
  `ingest.py` (or a new sibling module, if Investigate judges `ingest.py` is
  getting too large — it already handles tickets+runs+events+tools; a new
  `stats.py` in the same package may be the cleaner home, decide and
  document during Investigate rather than reflexively growing `ingest.py`
  further) owns all file reads.
- `DashboardCache`'s existing `RLock`-per-method pattern and mtime-triggered
  rebuild should extend naturally to serve computed stats — investigate
  whether stats need their own cache entry or can be derived from the
  existing cached tickets/runs data without a second full corpus re-read.
- No chart library exists in `dashboard-frontend/package.json` today
  (confirmed via direct read — only `@radix-ui/*`, no charting dependency).
  **Before writing any chart code or choosing chart colors, load the
  `dataviz` skill** — its own trigger description explicitly covers this
  exact situation ("stat tile", "KPI row", "dashboard", "chart colors").
  It teaches a design-system-agnostic method and ships a validated default
  palette; it does not mandate a specific charting library, so the actual
  library choice (Recharts, a lightweight D3-based approach, or inline SVG)
  is still an implementation decision — but the visual design discipline
  (form heuristic, color formula, light/dark theming) is not optional per
  that skill's own stated scope.
- This dashboard is read-only over `tickets/**` and `agent-monitoring/
  *.jsonl` — a stats endpoint must never write anything, including no
  `reports/*.json` side-effect files the CLI tool might otherwise produce.

## Concerns for Comprehend/Investigate to turn into child tickets

1. **Refactor `generate_retro.py`'s computation into a reusable, typed
   form.** Extract the metric calculations already in `generate()` into a
   function returning structured data (not Markdown lines), keep the
   existing CLI/Markdown output byte-identical (regression-test this
   explicitly — the weekly retro report is a real, relied-on artifact,
   nothing about its current output should change). This is the
   prerequisite both the new backend endpoint and nothing else depends on.

2. **New backend endpoint(s) for agent-monitoring statistics**, consuming
   concern 1's refactored function, exposed as new typed Pydantic model(s)
   in `models.py`. Should support the same period-selection `generate_retro
   .py` already has (current week / `--days N` / `--all` / specific week) —
   a dashboard stats view is more useful with a real time-range picker than
   a single fixed snapshot; investigate what query-param shape fits the
   existing `/api/tickets`/`/api/runs` convention.

3. **New ticket-corpus statistics report tool + backend endpoint.** Per
   `ticket_reporting.md`'s own stated convention, a new `tools/*_report.py`
   script (mirroring `tag_report.py`'s shape: reuse
   `validate_frontmatter.py`/`generate_registry.py` parsing, dedicated test
   file, `make` target) covering the four named-but-unbuilt pillars:
   velocity/throughput (from `working_log.csv`), tier/type/priority
   distribution (via `tools/ticket_field_values.py`'s new canonical enums),
   layer distribution (via `tools/layer_registry.py` + `docs/REGISTRY.yaml`),
   artifact completeness (`stored_artifacts/{ticket_id}/` presence check for
   standard/epic tickets). Then a new dashboard backend endpoint exposing
   this as typed JSON, same pattern as concern 2.

4. **New "Stats" frontend view/tab.** A 4th entry in `App.tsx`'s view-switch
   state (alongside `'activity' | 'tickets' | 'replay'`), fetching from the
   concern-2/3 endpoints and rendering charts/stat tiles. **Must load the
   `dataviz` skill before writing any chart code**, per the architectural
   constraint above. Investigate whether one unified view or two sub-sections
   (agent-monitoring stats / ticket-corpus stats) reads better given the two
   data domains' different shapes — a reasoned UX call, not dictated here.

5. **Docs update.** `docs/guides/agent_ops_dashboard.md` and `docs/
   observability/agent_ops_dashboard_contract.md` need a new section
   describing the Stats view/endpoints, mirroring how the existing three
   views are documented. `docs/guides/ticket_reporting.md`'s "Other
   candidate pillars (not built)" section needs updating once pillars 1-4
   actually get built — move them out of "not built" once concern 3 lands.

## Explicitly out of scope

- Any change to `generate_retro.py`'s actual Markdown CLI output format —
  concern 1 is a pure refactor (extract reusable computation), not a
  redesign of the existing retro report.
- Any new agent-monitoring instrumentation or schema change — this proposal
  only aggregates/visualizes data that already exists in
  `agent-monitoring/{runs,events,tools}.jsonl` and `tickets/**` today.
- Real-time/live-updating charts — the existing dashboard's polling-based
  `useRunsPolling` pattern for the Gantt view is the only precedent for
  "live" data in this app; whether stats need similar polling vs.
  fetch-once-per-view-load is an Investigate decision, not assumed here.
- Any change to CI — this repo currently has no frontend CI wired
  (confirmed in the dashboard's own origin idea doc); out of scope to add
  it as a side effect of this proposal.
