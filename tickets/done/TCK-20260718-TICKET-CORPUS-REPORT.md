---
status: historical
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20260718-TICKET-CORPUS-REPORT
phase: done
date: 2026-07-18
tags: [dashboard, reporting, api-design]
---

# TCK-20260718-TICKET-CORPUS-REPORT

## Title
New ticket-corpus statistics report tool + backend endpoint (velocity, tier/type/priority/layer distribution, artifact completeness)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`docs/guides/ticket_reporting.md`'s "Other candidate pillars (not built)" section names four ticket-corpus statistics that have never been implemented: ticket velocity/throughput (from `tickets/working_log.csv` timestamps), tier/type/priority distribution, layer distribution (cross-tab against tier/type), and artifact completeness (`stored_artifacts/{ticket_id}/` presence for standard/epic tickets). That doc also states its own convention for a new pillar: "belongs as a new `tools/*_report.py` script following the same pattern as `tools/tag_report.py`" (reuse `validate_frontmatter.py`/`generate_registry.py` parsing, dedicated test file, `make` target) — "not folded into `tag_report.py` itself." This ticket builds that tool, then exposes it via a new Agent Ops Dashboard backend endpoint so the frontend Stats tab can render it.

Tier/type/priority distribution is now trivially accurate since `tools/ticket_field_values.py` (from today's earlier `TCK-20260718-CANONICAL-FIELD-ENUMS-EPIC`) gives all three fields real hard-validated canonical enums — no drift-handling logic needed, unlike when `ticket_reporting.md` originally scoped this pillar as "not built." Layer distribution is similarly now backed by the registry-based `tools/layer_registry.py`/`docs/guidelines/layer_registry.jsonl` from that same epic.

## Scope
- New `tools/ticket_stats_report.py` (or equivalent name — follow `tag_report.py`'s naming convention, e.g. `<domain>_report.py`) computing:
  - Velocity/throughput: tickets closed per day/week from `tickets/working_log.csv`'s `timestamp` column, optionally broken down by tier/layer.
  - Tier/type/priority distribution: counts per value, using `tools/ticket_field_values.py`'s canonical `TIER_VALUES`/`PRIORITY_VALUES` for the type field.
  - Layer distribution: counts per registered layer (`tools/layer_registry.py::layer_values()`), cross-tabbed against tier.
  - Artifact completeness: for `standard`/`epic` tickets in `tickets/done/`, whether `stored_artifacts/{ticket_id}/` exists with all 3 required files (`investigation.md`, `plan.md`, `test_plan.md`).
- Same shape as `tag_report.py`: a computation function returning structured data, a separate stdout-rendering function, a `--json <path>` flag, argparse CLI, dedicated test file (`tests/tools/test_ticket_stats_report.py`), a new `make` target following the `tag-report` pattern.
- New route in `src/api/agent_ops_dashboard/main.py`, e.g. `GET /api/stats/tickets`, backed by a new Pydantic model in `models.py`, calling the new tool's computation function directly (not shelling out to the CLI) — same reuse discipline as the sibling agent-monitoring stats ticket.

## Out of Scope
- Agent-monitoring statistics — that's TCK-20260718-AGENTOPS-STATS-API's scope, a separate endpoint.
- The frontend consuming this endpoint — that's TCK-20260718-STATS-TAB-FRONTEND's scope.
- Retroactively fixing any ticket corpus data-quality issues the new report surfaces (e.g. more drift beyond what today's canonical-field-enums epic already fixed) — report and count it, do not silently "fix" the corpus as a side effect of building a reporting tool.

## Acceptance Criteria
- [x] `tools/ticket_stats_report.py` computes all four pillars (velocity, tier/type/priority distribution, layer distribution, artifact completeness) against the real corpus, producing plausible numbers: 1153 included tickets (1177 scanned, 24 SEQUENCE.md skipped), tier distribution 929 standard/103 hotfix/40 epic/81 unknown, 622/969 artifact-complete standard+epic tickets.
- [x] Follows `tag_report.py`'s exact pattern: computation/rendering split, `--json` flag, dedicated test file, new `make` target (`ticket-stats-report`).
- [x] A new `/api/stats/tickets`-style route exists, `response_model=TicketCorpusStats`, calling `tools/ticket_stats_report.py`'s computation functions directly — confirmed live returning identical numbers to the CLI.
- [x] New tests cover both the standalone tool (8 tests) and the new API route (2 tests).

## Related Tickets
- TCK-20260718-STATS-TAB-FRONTEND (consumes this endpoint)
- TCK-20260718-AGENTOPS-STATS-BOARD-EPIC (parent epic)

## Related Docs
- docs/plans/agent_ops_dashboard/proposal_stats_board.md
- docs/guides/ticket_reporting.md

## Related Stored Artifacts
None yet.

## Related Code Areas
- tools/tag_report.py (precedent to follow)
- tools/ticket_field_values.py
- tools/layer_registry.py
- tickets/working_log.csv
- docs/REGISTRY.yaml
- src/api/agent_ops_dashboard/main.py
- src/api/agent_ops_dashboard/models.py

## Assumptions / Open Questions
- Exact new tool filename left to Investigate/implementation, following the `<domain>_report.py` convention `tag_report.py` established.

## Implementation Notes
New `tools/ticket_stats_report.py` mirrors `tag_report.py`'s exact shape. Confirmed
`docs/REGISTRY.yaml` alone is insufficient (checked directly — its ticket entries have no
`layer`, no `priority`, no body status), so the tool parses ticket files directly via
`validate_frontmatter.py::extract_frontmatter` (layer) and
`generate_registry.py::parse_body_section` (tier/type/priority), reusing
`tools/ticket_field_values.py`'s `TIER_VALUES`/`PRIORITY_VALUES` and
`tools/layer_registry.py::layer_values()` for canonical cross-referencing (both flag
non-canonical values live in stdout output — independently rediscovered the same 3
layer-drift tickets found during today's earlier `LAYER-REGISTRY-CONVERSION` verification, a
useful cross-check of correctness). `compute_velocity()` reuses `generate_retro.py::iso_week()`
rather than reimplementing ISO-week math.

`get_ticket_corpus_stats()` is the one `DashboardCache` method that does its own fresh file walk
per call rather than reading cached state — documented explicitly in its own docstring (this
tool's output shape isn't a subset of what `parse_ticket_file()` already caches; folding it into
the mtime-rebuild cycle would be more invasive than this ticket's scope warranted).

Live-verified: `make ticket-stats-report` and `GET /api/stats/tickets` (via `FastAPI
TestClient`) return identical `included_tickets`/distribution numbers against the real
1153-ticket corpus.

Deviation (self-flagged, per this session's established precedent): all phases performed
directly, no Agent-tool subagent access in this context.

## Test Summary
`python3 -m pytest tests/tools/test_agent_ops_dashboard_ingest.py
tests/tools/test_agent_ops_dashboard_api.py tests/tools/test_agent_ops_dashboard_api_boundary.py
tests/tools/test_agent_ops_dashboard_concurrency.py
tests/tools/test_agent_ops_dashboard_frontend_api_surface.py
tests/tools/test_agent_ops_dashboard_serve.py tests/tools/test_agent_ops_dashboard_stats.py
tests/tools/test_generate_retro.py tests/tools/test_ticket_stats_report.py -q` — 87/87 passing.
`tools/gate_checks/architecture_reviewer_static.py::run_architecture_checks()` — zero findings
across 7 changed/new files.

## Files Changed
- tools/ticket_stats_report.py (new)
- Makefile (new `ticket-stats-report` target)
- src/api/agent_ops_dashboard/ingest.py (new `get_ticket_corpus_stats()` method + imports)
- src/api/agent_ops_dashboard/main.py (new `GET /api/stats/tickets` route)
- src/api/agent_ops_dashboard/models.py (5 new Pydantic models)
- tests/tools/test_ticket_stats_report.py (new, 8 tests)
- tests/tools/test_agent_ops_dashboard_stats.py (2 new tests)
- tests/tools/test_agent_ops_dashboard_api_boundary.py (extended pinned route-set assertion)
- docs/parity_ledger/infrastructure.yaml (extended `INFRA-275`)

## Completion Summary
`tools/ticket_stats_report.py` closes all four `ticket_reporting.md` "not built" pillars
(velocity, tier/type/priority distribution, layer distribution, artifact completeness), and
`GET /api/stats/tickets` exposes it as typed JSON, verified live against the real corpus.
Unblocks `TCK-20260718-STATS-TAB-FRONTEND`.
