---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260719-STATS-PHASE-OUTLIERS-EXPOSE
phase: done
date: 2026-07-19
tags: [dashboard, observability, agent-monitoring]
---

# TCK-20260719-STATS-PHASE-OUTLIERS-EXPOSE

## Title
Expose Phase Status Distribution and Outliers in the Agent Ops Dashboard's Stats tab

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
`tools/agent-monitoring/generate_retro.py::compute_retro_metrics()` gained two new top-level
return-dict keys today: `phase_status_distribution` (`TCK-20260719-PHASE-AGENT-CASE-FOLD`, a
per-phase `ok`/`failed`/`blocked`/`skipped` breakdown computed after casing-variant normalization)
and `outliers` (`TCK-20260719-RETRO-OUTLIER-FLAGS`, `duration_s`-by-tier and
`cost_proxy_score`-by-phase values flagged at >3x their group median). Both already render in the
CLI retro report (`## Phase Status Distribution`, `## Outliers` sections). Neither is exposed by
the dashboard's `GET /api/stats/agent-monitoring` endpoint or rendered in the Stats tab's frontend —
confirmed by direct read: `AgentMonitoringStats` (`src/api/agent_ops_dashboard/models.py`) has no
`phase_status_distribution` or `outliers` field, and `DashboardCache.get_agent_monitoring_stats()`
(`src/api/agent_ops_dashboard/ingest.py`) builds the response via explicit per-field typed submodel
construction (`RunSummaryStats(**metrics["run_summary"])`, etc.), never a `**metrics` passthrough —
exactly the same "not automatic" gap `TCK-20260719-RETRO-OUTLIER-FLAGS`'s own investigation flagged
and scoped out at the time, deferred to this real, now-scoped follow-up.

## Scope
- Add `PhaseStatusEntry` (or reuse the existing `Dict[str, Dict[str, int]]` shape
  `agent_status_distribution` already uses — mirror it exactly, since `phase_status_distribution`
  has the identical `{phase: {ok, failed, blocked, skipped}}` shape) and a new
  `OutlierStats`/`DurationOutlierEntry`/`CostProxyOutlierEntry` set of Pydantic models in
  `src/api/agent_ops_dashboard/models.py`, matching `compute_retro_metrics()`'s exact return shape
  (`tools/agent-monitoring/generate_retro.py`'s `outliers_duration_s`/`outliers_cost_proxy_score`
  list-of-dicts construction, ~line 443 and ~line 464).
- Add `phase_status_distribution: Dict[str, Dict[str, int]]` and `outliers: OutlierStats` fields to
  `AgentMonitoringStats`.
- Wire both into `DashboardCache.get_agent_monitoring_stats()`'s `AgentMonitoringStats(...)`
  construction (`src/api/agent_ops_dashboard/ingest.py`, ~line 752), following the exact same
  per-field typed-submodel pattern every other field already uses — never a raw dict passthrough.
- Frontend: `dashboard-frontend/src/views/StatsView.tsx` — add a Phase Status Distribution
  rendering (mirror the existing "Top agents by call volume" table pattern, since
  `agent_status_distribution` already renders as a table, not a chart — same shape, same
  treatment) and an Outliers rendering (mirror the existing Slow Runs `<table>` pattern — two
  sub-tables, one for duration outliers, one for cost-proxy-score outliers, matching the CLI
  report's own two-section split). **Load the `dataviz` skill before writing any new chart
  code/colors** if a chart (not a table) ends up being the better fit for either — a reasoned UX
  call, not dictated here, but the CLAUDE.md-mandated skill load applies regardless of which is
  chosen.
- Wire `GlossaryTooltip`/hint-icon coverage onto any new column headers this ticket adds, matching
  every other Stats-tab column header's existing hover-description treatment (established by
  `TCK-20260718-GLOSSARY-TOOLTIPS-EPIC` and `TCK-20260719-AGENT-ROLE-GLOSSARY`) — investigate
  whether `docs/guidelines/glossary_registry.jsonl` needs new terms for "duration outlier"/"cost
  outlier"/"phase status" concepts, or whether existing status-term entries already cover the
  relevant labels.
- Backend + frontend test coverage: extend `tests/tools/test_agent_ops_dashboard_stats.py` (mirror
  `test_stats_endpoint_returns_typed_shape_for_all_time`'s pattern) and
  `dashboard-frontend/src/test/StatsView.test.tsx`.
- Update `docs/observability/agent_ops_dashboard_contract.md`'s Stats-tab section and
  `docs/guides/agent_ops_dashboard.md`'s Stats section to document the two new fields/renderings,
  mirroring how the existing fields are documented there.

## Out of Scope
- Any change to `compute_retro_metrics()`'s computation itself — this ticket only exposes
  already-computed, already-CLI-rendered data through the dashboard's typed API boundary and
  frontend, never recomputes anything (matching this dashboard's established
  "`tools/*.py` is the single source of truth" architecture).
- Any change to the CLI retro report's own Markdown rendering (`generate()` in
  `generate_retro.py`) — byte-identical output must be preserved, unaffected by this ticket.
- Real-time/live-updating stats — the Stats tab's existing fetch-once-per-view-load behavior is
  unchanged.
- Direct `cost_proxy.py` weight recalibration — unrelated, already explicitly deferred elsewhere
  (`docs/plans/archive/agent_infrastructure/proposal_agent_monitoring_data_quality.md`).

## Acceptance Criteria
- [x] `GET /api/stats/agent-monitoring`'s JSON response includes `phase_status_distribution` and
      `outliers` keys with the exact same values `compute_retro_metrics()` computes (live-verified,
      not just unit-tested) — confirmed byte-for-byte-equivalent to what the CLI retro report
      already renders for the same period. `ingest.py` passes both through unchanged (no
      re-sort/re-round of `generate_retro.py`'s already-sorted/rounded values); backend tests
      `test_stats_endpoint_includes_phase_status_distribution` /
      `test_stats_endpoint_includes_outliers_duration_and_cost_proxy` assert this directly.
- [x] Stats tab visually renders both new sections — a Phase Status Distribution table (mirroring
      the existing Top Agents table pattern) and two Outliers sub-tables (duration-by-tier,
      cost-proxy-score-by-phase), in `StatsView.tsx`.
- [x] A period with zero flagged outliers renders a graceful "no outliers" state — confirmed by
      `test_stats_endpoint_zero_outliers_returns_empty_lists_not_missing_keys` (backend) and the
      frontend's dedicated `no-outliers-state` test (each sub-table independently skips rendering
      when its own list is empty, with a combined "No outliers" message when both are empty).
- [x] All new/updated backend and frontend tests pass; full scoped `tests/tools/` and
      `dashboard-frontend` test suites still pass — 106/106 backend (`tests/tools/`
      dashboard-related modules), 94/94 frontend (`dashboard-frontend` vitest, 11 files), `tsc -b
      --noEmit` clean, all independently re-run and confirmed, not just taken from agent self-report.
- [x] `docs/observability/agent_ops_dashboard_contract.md` and `docs/guides/agent_ops_dashboard.md`
      updated to describe both new fields/renderings.

## Related Tickets
- TCK-20260719-PHASE-AGENT-CASE-FOLD
- TCK-20260719-RETRO-OUTLIER-FLAGS
- TCK-20260718-AGENTOPS-STATS-API
- TCK-20260718-STATS-TAB-FRONTEND
- TCK-20260718-RETRO-STATS-REFACTOR
- TCK-20260718-GLOSSARY-TOOLTIPS-EPIC
- TCK-20260719-AGENT-ROLE-GLOSSARY

## Related Docs
- docs/observability/agent_ops_dashboard_contract.md
- docs/guides/agent_ops_dashboard.md
- docs/guides/agent_monitoring.md (CLI-side counterpart, already documents both new report sections)
- docs/plans/archive/agent_infrastructure/proposal_agent_monitoring_data_quality.md (origin of
  concerns 1 and 3 this ticket exposes on the dashboard side)

## Related Stored Artifacts
None yet — to be created at Investigate/Plan.

## Related Code Areas
- src/api/agent_ops_dashboard/models.py
- src/api/agent_ops_dashboard/ingest.py
- dashboard-frontend/src/views/StatsView.tsx
- tests/tools/test_agent_ops_dashboard_stats.py
- dashboard-frontend/src/test/StatsView.test.tsx

## Assumptions / Open Questions
- Whether Phase Status Distribution renders as a table (mirroring Agent Status Distribution) or a
  chart — recommended table for consistency, but a real UX call for Plan to confirm.
- Whether Outliers renders as one combined table or two (mirroring the CLI's own two-section
  split) — recommended two, matching the CLI exactly, but a real call for Plan to confirm.

## Implementation Notes
Added `DurationOutlierEntry`, `CostProxyOutlierEntry`, `OutlierStats` Pydantic models to
`src/api/agent_ops_dashboard/models.py` (lines 164-200), plus `phase_status_distribution:
Dict[str, Dict[str, int]]` (reusing `agent_status_distribution`'s existing open-dict shape, per
plan decision — no fixed-field submodel, since the inner key set isn't guaranteed to be exactly
`ok`/`failed`/`blocked`/`skipped`) and `outliers: OutlierStats` fields on `AgentMonitoringStats`.
`CostProxyOutlierEntry.seq` is `Optional[int] = None` (matches `generate_retro.py`'s own
`item.get("seq")` with no fallback — a required `int` would raise on real legacy events).

`DashboardCache.get_agent_monitoring_stats()` (`ingest.py`, lines 773, 784-789) wires both in via
the same explicit per-field typed construction every existing field already uses —
`phase_status_distribution` is a direct dict passthrough (correct, since its declared type is a
plain nested dict, identical treatment to `agent_status_distribution` one line above);
`outliers` is built via per-item `DurationOutlierEntry(**d)`/`CostProxyOutlierEntry(**d)`
unpacking against known Pydantic field sets — not a `**metrics` whole-dict passthrough. No
re-sorting or re-rounding added; `generate_retro.py` already sorts by ratio descending and rounds
median/ratio to 1 decimal.

Frontend (`StatsView.tsx`): Phase Status Distribution renders as a table cloned from the existing
Top Agents pattern (column headers wrapped in `GlossaryTooltip` using the existing `event-status`
registry category; `phase` cell left unwrapped — no `phase` glossary category exists and
investigation found no precedent for wrapping generic non-enum labels). Outliers renders as two
independent sub-tables mirroring the CLI report's own two `###` sub-sections, each conditionally
rendered only when its own list is non-empty, with a combined "No outliers" message when both are
empty.

All three open questions from the ticket's own "Assumptions / Open Questions" section were
resolved during Plan (not deferred): table format for Phase Status Distribution (row-shaped data
convention, matching Top Agents/Slow Runs — `BarChart`/`GroupedBarChart` are reserved for
single-numeric-value-per-label distributions, not row-shaped data); two separate Outliers
sub-tables (mirrors the CLI exactly, and the ticket's own Scope section already specified this,
not genuinely ambiguous); required (non-optional) TS fields on the frontend `AgentMonitoringStats`
interface (matches every other field; the backend always returns these keys, never omits them, so
`?` would misrepresent the contract).

Investigated whether new `docs/guidelines/glossary_registry.jsonl` entries were needed for the new
labels: none required — Phase Status Distribution's status headers already exist under the
`event-status` category; Outliers' `tier` values are covered by the existing `tier` category and
`agent` values by the existing dynamically-merged `agent` category; there is no `phase` category
and no precedent for wrapping generic non-enum columns (`median`, `ratio`, `duration_s`, `seq`,
`cost_proxy_score`), so those stay unwrapped, consistent with current practice.

One deliberate, documented deviation from the full test plan: the optional architecture-guard test
(`test_stats_endpoint_never_passthrough_metrics_dict`, `test_plan.md` item 12) was not added — the
test plan itself marked it optional ("only if not already implicitly covered"), and the four
required new backend tests already assert the correct per-field construction indirectly by
asserting the exact typed shape of the response. No plan.md "Deviations" section entry was needed
since the test plan itself already framed this item as optional, not a commitment.

`tools/agent-monitoring/generate_retro.py` was not touched at any point — confirmed via `git
status` before Architecture-Verify and again before Parity — this ticket only exposes
already-computed, already-CLI-rendered data through the typed API boundary.

## Test Summary
- `python3 -m pytest tests/tools/test_agent_ops_dashboard_stats.py tests/tools/test_agent_ops_dashboard_ingest.py tests/tools/test_agent_ops_dashboard_api.py tests/tools/test_agent_ops_dashboard_api_boundary.py tests/tools/test_agent_ops_dashboard_concurrency.py tests/tools/test_agent_ops_dashboard_glossary.py tests/tools/test_agent_ops_dashboard_serve.py tests/tools/test_agent_ops_dashboard_frontend_api_surface.py tests/tools/test_generate_retro.py -q` — 106/106 passing, independently re-run and confirmed (not just taken from agent self-report, which initially misreported a "200" count inconsistent with its own "106/106" summary line).
- `cd dashboard-frontend && npm run test -- --run` — 94/94 passing across 11 test files, independently re-run.
- `cd dashboard-frontend && npx tsc -b --noEmit` — clean, zero errors.
- 4 new backend tests: `test_stats_endpoint_includes_phase_status_distribution`,
  `test_stats_endpoint_includes_outliers_duration_and_cost_proxy`,
  `test_stats_endpoint_outliers_seq_field_tolerates_none`,
  `test_stats_endpoint_zero_outliers_returns_empty_lists_not_missing_keys`.
- New frontend tests covering: phase-status table rendering, both outlier sub-tables, the combined
  no-outliers empty state, glossary-tooltip wrapping on the new column headers, and an anti-drift
  string guard.

## Files Changed
- src/api/agent_ops_dashboard/models.py (`DurationOutlierEntry`/`CostProxyOutlierEntry`/`OutlierStats`, 2 new `AgentMonitoringStats` fields)
- src/api/agent_ops_dashboard/ingest.py (`get_agent_monitoring_stats()` wiring)
- dashboard-frontend/src/api.ts (matching TS interfaces, 2 new required fields)
- dashboard-frontend/src/views/StatsView.tsx (Phase Status Distribution table, 2 Outliers sub-tables)
- dashboard-frontend/src/test/StatsView.test.tsx (fixture update, 4 new tests)
- dashboard-frontend/src/test/App.test.tsx
- tests/tools/test_agent_ops_dashboard_stats.py (4 new tests)
- docs/observability/agent_ops_dashboard_contract.md
- docs/guides/agent_ops_dashboard.md
- docs/parity_ledger/infrastructure.yaml (new entry INFRA-286, cross-references INFRA-283/INFRA-284)

## Completion Summary
`GET /api/stats/agent-monitoring` now includes `phase_status_distribution` and `outliers` —
both already computed by `tools/agent-monitoring/generate_retro.py::compute_retro_metrics()` and
already rendered in the CLI retro report, but previously silently dropped at the dashboard's typed
API boundary since `AgentMonitoringStats` had no corresponding fields. The Stats tab now renders a
Phase Status Distribution table and two Outliers sub-tables (duration-by-tier,
cost-proxy-score-by-phase), each gracefully degrading to a "no outliers" state when empty. Zero
change to `compute_retro_metrics()`/`generate()` — this ticket only exposes already-computed data
through the existing explicit-per-field-typed-construction pattern, never a `**metrics`
passthrough, and never recomputes anything. One deliberate scope deferral: the test plan's
optional architecture-guard test (`test_stats_endpoint_never_passthrough_metrics_dict`) was not
added, since the test plan itself marked it optional and the required new tests already cover the
correct construction pattern indirectly. All claims independently re-verified: 106 backend + 94
frontend tests passing, clean TypeScript, and parity ledger entry `INFRA-286` cross-referencing
(not rewriting) `INFRA-283`/`INFRA-284`.
