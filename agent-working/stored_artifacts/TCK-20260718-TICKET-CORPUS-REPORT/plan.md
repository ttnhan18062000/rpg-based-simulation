---
status: active
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20260718-TICKET-CORPUS-REPORT
artifact_type: plan
tags: []
---

# Implementation Plan — TCK-20260718-TICKET-CORPUS-REPORT

## Summary

New `tools/ticket_stats_report.py`, mirroring `tag_report.py`'s exact shape (computation/
rendering split, `--json` flag, dedicated test file, `make` target), covering the four
previously-unbuilt `ticket_reporting.md` pillars: velocity/throughput, tier/type/priority
distribution, layer distribution, artifact completeness — scoped to `tickets/done/`. Then a new
`GET /api/stats/tickets` backend route exposing it as typed JSON.

## Steps

### Step 1 — `tools/ticket_stats_report.py`: collection + computation

`collect_done_tickets(root)` — walks `tickets/done/` recursively (mirrors `tag_report.py`'s own
walk, skip-rules: `SEQUENCE.md`, unparseable/missing frontmatter — no taxonomy-date skip rule,
this isn't tag-taxonomy-gated), extracting per ticket: `ticket_id`, `layer` (frontmatter),
`tier`/`ticket_type`/`priority` (body sections via `generate_registry.py::parse_body_section`),
`date` (frontmatter).

`compute_velocity(root)` — parses `tickets/working_log.csv`, groups `timestamp` by day
(`YYYY-MM-DD`) and by ISO week (reuse `generate_retro.py::iso_week` — already proven, don't
reimplement).

`compute_distribution(tickets)` — `Counter` over tier/type/priority/layer values from the
collected tickets; a nested `layer x tier` cross-tab dict.

`compute_artifact_completeness(tickets, root)` — for `standard`/`epic` tickets only, checks
`stored_artifacts/{ticket_id}/{investigation,plan,test_plan}.md` all exist and are non-empty.

### Step 2 — Rendering (stdout + JSON)

`print_report(...)`/`build_json_report(...)` — same split as `tag_report.py`. `main()` —
argparse, `--root`, `--json`, mirroring `tag_report.py`'s exact CLI shape.

### Step 3 — Makefile target

New `ticket-stats-report` target mirroring the existing `tag-report` target's shape.

### Step 4 — New backend endpoint

`GET /api/stats/tickets`, new `TicketCorpusStats` Pydantic model in `models.py`, new
`DashboardCache.get_ticket_corpus_stats()` method calling the new tool's computation functions
directly (import, not subprocess/CLI-shell-out).

### Step 5 — Update pinned route-enumeration test

`tests/tools/test_agent_ops_dashboard_api_boundary.py::test_all_declared_routes_present` (already
renamed by the sibling AGENTOPS-STATS-API ticket) — extend its set literal to include
`/api/stats/tickets`, the 7th route.

### Step 6 — Tests

Per test_plan.md.

## Scope Guards

- Do not touch `tag_report.py` — separate tool, separate domain.
- Do not include `tickets/inprogress/`/`tickets/todos/` in the corpus scope — `tickets/done/`
  only, matching `tag_report.py`'s own precedent.
- Do not retroactively fix any corpus data-quality issue this report surfaces — report and count
  it only.

## Dependency Map

Independent of TCK-20260718-RETRO-STATS-REFACTOR/AGENTOPS-STATS-API (different data domain).
Blocks TCK-20260718-STATS-TAB-FRONTEND.

## Acceptance Criteria Map

- AC "tool computes all four pillars, plausible numbers" → Steps 1-2, verified live against real
  corpus during Implement.
- AC "follows tag_report.py's pattern" → Steps 1-3.
- AC "new route, typed model" → Step 4.
- AC "new tests" → Step 6.

## Anti-Drift Notes

`test_all_declared_routes_present`'s exact-set assertion needs a second update in this same
epic (already updated once by the sibling ticket) — Step 5 handles this explicitly.
