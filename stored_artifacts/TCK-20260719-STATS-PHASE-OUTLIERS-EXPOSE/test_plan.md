---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260719-STATS-PHASE-OUTLIERS-EXPOSE
artifact_type: test_plan
tags: [dashboard, observability, agent-monitoring]
---

# Test Plan — TCK-20260719-STATS-PHASE-OUTLIERS-EXPOSE

## Regression Surface

**Unit / backend:**
- `tests/tools/test_agent_ops_dashboard_stats.py` — all 8 existing tests must keep passing,
  especially `test_stats_endpoint_returns_typed_shape_for_all_time`,
  `test_stats_endpoint_empty_data_does_not_crash`, and
  `test_stats_endpoint_uses_real_compute_retro_metrics_not_reimplemented` (source-text anti-drift
  guard — must keep passing unchanged since `ingest.py` must keep importing, never redefining,
  `compute_retro_metrics`).
- `tests/tools/test_generate_retro.py` — all existing tests, in particular
  `test_compute_retro_metrics_returns_all_documented_keys`,
  `test_phase_status_distribution_merges_casing_variants_review_failure_rate`,
  `test_phase_status_distribution_rendered_in_report`,
  `test_duration_outlier_flagged_relative_to_tier_median_not_global`,
  `test_duration_outlier_excludes_null_from_flagging_and_median`,
  `test_duration_outlier_skips_group_below_minimum_size`,
  `test_cost_proxy_outlier_flagged_relative_to_normalized_phase_median`,
  `test_cost_proxy_outlier_excludes_events_with_no_score`,
  `test_outliers_section_omitted_when_none_flagged`,
  `test_outliers_section_rendered_when_flagged` — this ticket must not touch `generate_retro.py`
  at all (out of scope), so these prove that invariant holds by staying green with zero source
  diff.
- `tests/tools/test_agent_ops_dashboard_ingest.py` (or equivalent, if it exists as a separate file
  from the stats test — confirm at Implement time) covering other `DashboardCache` methods
  (`get_tickets`, `get_runs`, `get_timeline`, `get_glossary`) — unaffected but part of the same
  module, run as a broader regression check.

**Integration / frontend:**
- `dashboard-frontend/src/test/StatsView.test.tsx` — all 10 existing tests, especially:
  - `'renders real data from both endpoints once loaded'`
  - `'renders empty-state charts and tables for a zero-corpus/zero-runs response, without
    crashing'`
  - `'never hardcodes a glossary description string in its own source — always sourced from the
    fetched glossary'` (source-text anti-drift guard on `STATS_VIEW_SOURCE`)
- `dashboard-frontend/src/test/GlossaryTooltip.test.tsx` (if present) / `BarChart.test.tsx` —
  unaffected but confirms shared components used by the new sections still behave.

## New Tests Required

Backend (`tests/tools/test_agent_ops_dashboard_stats.py`, mirroring
`test_stats_endpoint_returns_typed_shape_for_all_time`'s pattern):

1. **`test_stats_endpoint_includes_phase_status_distribution`**
   Category: unit. Verifies `AgentMonitoringStats.phase_status_distribution` is present and equals
   `compute_retro_metrics(...)["phase_status_distribution"]` for the same input runs/events —
   proves the API boundary passes the value through unchanged (no reshaping, no re-sorting).
   Location: `tests/tools/test_agent_ops_dashboard_stats.py`.

2. **`test_stats_endpoint_includes_outliers_duration_and_cost_proxy`**
   Category: unit. Fixture with >=3 same-tier runs where one is >3x the tier median duration_s
   (mirrors `test_duration_outlier_flagged_relative_to_tier_median_not_global`'s fixture shape) and
   >=3 same-phase events where one cost_proxy_score is >3x the phase median. Asserts
   `stats.outliers.duration_s` and `stats.outliers.cost_proxy_score` contain the expected flagged
   entries with correct `run_id`/`tier`/`median`/`ratio` (or `phase`/`agent`/`seq`/
   `cost_proxy_score`/`median`/`ratio`) values, matching `compute_retro_metrics()`'s own output
   exactly. Location: `tests/tools/test_agent_ops_dashboard_stats.py`.

3. **`test_stats_endpoint_outliers_seq_field_tolerates_none`**
   Category: unit / regression guard. Fixture with a cost_proxy_score-outlier-triggering event
   that has no `seq` key. Must not raise a Pydantic `ValidationError` — proves the new
   `CostProxyOutlierEntry.seq` field is `Optional[int]`, not `int` (the concrete risk flagged in
   investigation.md). Location: `tests/tools/test_agent_ops_dashboard_stats.py`.

4. **`test_stats_endpoint_zero_outliers_returns_empty_lists_not_missing_keys`**
   Category: unit / edge case. Empty or below-minimum-group-size fixture. Asserts
   `stats.outliers.duration_s == []` and `stats.outliers.cost_proxy_score == []` (present, empty —
   never absent/null), and `stats.phase_status_distribution == {}` for a no-events fixture. Backs
   the "graceful no-outliers state" AC at the API layer. Location:
   `tests/tools/test_agent_ops_dashboard_stats.py`.

5. **`test_stats_endpoint_uses_real_compute_retro_metrics_not_reimplemented`** (existing test,
   assert unmodified) — no new assertions needed, but confirm it still passes; it already proves
   `ingest.py` doesn't hand-roll outlier/phase-status logic.

Frontend (`dashboard-frontend/src/test/StatsView.test.tsx`, extending `makeAgentStats()`):

6. **`makeAgentStats()` fixture update** — add default `phase_status_distribution` and `outliers`
   values (not a standalone test, but a required fixture change every other test in the file
   depends on for typecheck/behavior — flagged explicitly since it's easy to miss).

7. **`'renders a Phase Status Distribution table with ok/failed/blocked/skipped columns'`**
   Category: integration. Mirrors `'renders real data from both endpoints once loaded'`'s
   `top-agent-row-*` assertions — asserts a `phase-status-row-<phase>` (or equivalent
   `data-testid`) row renders per phase with correct counts.

8. **`'renders Duration and Cost-Proxy-Score outlier tables when outliers are present'`**
   Category: integration. Asserts both outlier sub-tables render with `data-testid`s per row
   (e.g. `duration-outlier-row-<run_id>`, `cost-outlier-row-<run_id>-<seq>`), matching the CLI's
   two-section split.

9. **`'renders a graceful "no outliers" state when both outlier lists are empty, not a broken
   table'`**
   Category: integration / edge case. Directly backs the ticket's own zero-outliers AC — mirrors
   the existing `'No slow runs'` single-row empty-state test pattern
   (`StatsView.test.tsx:131-157`).

10. **`'wraps tier and agent values in outlier tables with GlossaryTooltip, matching existing
    Slow Runs / Top Agents cell-wrapping pattern'`**
    Category: integration. Confirms `o.tier` (duration outliers) and `o.agent` (cost-proxy
    outliers) get the same `GlossaryTooltip`-driven hint-icon treatment `run.final_status` and
    `row.agent` already get elsewhere in this file — regression guard against the glossary-wiring
    convention silently not being applied to the new tables.

11. **`'never hardcodes a glossary description string in its own source'`** (existing anti-drift
    test) — no new assertions strictly required, but re-run to confirm the new code additions
    don't introduce a hardcoded description string.

Architecture guard (new or extended):

12. **`test_agent_ops_dashboard_stats.py::test_stats_endpoint_never_passthrough_metrics_dict`**
    (optional, only if not already implicitly covered) — source-text guard confirming
    `AgentMonitoringStats(**metrics)` (a full-dict passthrough) never appears in `ingest.py`,
    extending the existing anti-passthrough convention this ticket must not violate for the two
    new fields either.

## Scoped Pytest Commands

Backend:
```
python3 -m pytest tests/tools/test_agent_ops_dashboard_stats.py tests/tools/test_generate_retro.py -q
```

Broader monitoring-domain regression sweep (mirrors INFRA-283/284's own verification scope):
```
python3 -m pytest tests/tools/ -q -k "monitoring or record_events or record_run or cost_proxy or sidecar or agent_ops_dashboard or generate_retro or validate_agent"
```

Frontend (from `dashboard-frontend/`):
```
npm test -- src/test/StatsView.test.tsx
```

Full frontend suite regression check (dashboard-frontend only, never the whole repo's test
surface):
```
npm test
```

Never run bare `pytest tests/` — always scoped as above, per project testing rules.

## Anti-Drift Test Guards

- **`test_stats_endpoint_uses_real_compute_retro_metrics_not_reimplemented`** (existing, unmodified)
  — guards against Implement accidentally hand-rolling phase-status or outlier computation inside
  `ingest.py` instead of reading `metrics["phase_status_distribution"]`/`metrics["outliers"]`
  straight from the imported function's return dict.
- **New: assert no re-sort/re-round of outlier lists** — a test comparing
  `stats.outliers.duration_s` list order directly against
  `compute_retro_metrics(...)["outliers"]["duration_s"]` list order (not just set-equality) catches
  any accidental `sorted(...)` call added in `ingest.py` that could silently diverge from the CLI's
  own ratio-descending order.
- **`test_compute_retro_metrics_returns_all_documented_keys`** (existing, in
  `test_generate_retro.py`, unmodified) — guards against a future accidental edit to
  `generate_retro.py` in this ticket (explicitly out of scope) by keeping the full expected-keys
  list under an untouched test.
- **Frontend source-text guard extension**: confirm `STATS_VIEW_SOURCE` (already asserted against
  in the existing `'never hardcodes a glossary description string'` test) has no hardcoded
  `phase_status_distribution`/`outliers` label strings duplicating registry-owned tooltip text —
  same anti-drift shape as the existing assertion, just re-verified against the larger file.
- **CLI byte-identical guard**: no new test should call `generate()` or assert on Markdown string
  output as part of this ticket's own test additions — that surface belongs entirely to
  `test_generate_retro.py` and is explicitly out of scope to modify. A new test accidentally
  asserting against Markdown formatting would blur the ticket's own scope boundary between "expose
  already-computed data" and "recompute or reformat it."
- **Empty-state guard**: `test_stats_endpoint_zero_outliers_returns_empty_lists_not_missing_keys`
  and the frontend `'renders a graceful "no outliers" state...'` test together guard against the
  most likely regression shape for this kind of feature — a `KeyError`/`undefined` crash when a
  period genuinely has zero flagged outliers (the common case for most real periods, per INFRA-284's
  own live-corpus numbers: only 26 duration + 82 cost-proxy outliers across 677 runs / 3435 events
  all-time — most week-scoped queries will have zero).
