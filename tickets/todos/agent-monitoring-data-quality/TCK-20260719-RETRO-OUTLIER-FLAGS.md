---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260719-RETRO-OUTLIER-FLAGS
phase: open
date: 2026-07-19
tags: []
---

# TCK-20260719-RETRO-OUTLIER-FLAGS

## Title
Add outlier flagging to agent-monitoring retro report

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
The author wants a per-run/per-event outlier flag (e.g. duration_s greater than 3x a median, or cost_proxy_score greater than Nx the phase/agent median) surfaced as a visible line in make agent-monitoring-retro's output, closing the gap where real, unexplained outliers currently sit unflagged in the data with zero recorded investigation. The flag does not need to explain why an outlier occurred, just make it visible. Investigation found the proposal's claim that the dashboard "would benefit from this epic's fixes automatically" is FALSE for this concern: src/api/agent_ops_dashboard/ingest.py::get_agent_monitoring_stats() builds AgentMonitoringStats via explicit per-field typed submodel construction, never **metrics passthrough, so a new top-level 'outliers' key would be silently dropped at the API boundary unless models.py/ingest.py are also updated — this ticket is scoped to CLI/Markdown output only, and the ticket body corrects that claim explicitly.

## Scope
- Add a new top-level 'outliers' key to compute_retro_metrics()'s return dict in generate_retro.py flagging duration_s outliers (run-level, median basis per Plan decision) and cost_proxy_score outliers (phase/agent-scoped), Nx median, excluding nulls from both flag computation and median basis
- Add a new conditionally-rendered '## Outliers' Markdown section to the CLI report
- Update test_compute_retro_metrics_returns_all_documented_keys for the new key
- Ticket body explicitly corrects the proposal's false claim that the dashboard benefits from this automatically, and records dashboard exposure as a separate deliberate future follow-up

## Out of Scope
- Dashboard/API exposure — no changes to src/api/agent_ops_dashboard/models.py or ingest.py; the new key would be silently dropped at the API boundary today and wiring it through is a separate, deliberate future follow-up, not assumed free
- Removing or replacing the existing slow_runs fixed 1800s-threshold mechanism — relationship between it and the new relative/median outlier section is a Plan-phase decision, not a removal

## Acceptance Criteria
- [ ] compute_retro_metrics() returns a new top-level 'outliers' key covering duration_s (run-level) and cost_proxy_score (phase/agent-scoped) outliers at Nx median, with null values excluded from both flagging and median basis
- [ ] A new '## Outliers' section renders conditionally in the CLI Markdown report produced by make agent-monitoring-retro
- [ ] test_compute_retro_metrics_returns_all_documented_keys updated to include the new 'outliers' key
- [ ] Ticket body explicitly states the dashboard does NOT get this automatically (get_agent_monitoring_stats() uses explicit typed submodel construction, not **metrics passthrough) and records dashboard exposure as an out-of-scope future follow-up

## Related Tickets
- TCK-20260718-RETRO-STATS-REFACTOR
- TCK-20260718-AGENTOPS-STATS-API
- TCK-20260708-AGENT-COST-OBSERVABILITY

## Related Docs
- docs/agent-monitoring/schema.md

## Related Stored Artifacts
None.

## Related Code Areas
- tools/agent-monitoring/generate_retro.py
- tests/tools/test_generate_retro.py
- src/api/agent_ops_dashboard/models.py
- src/api/agent_ops_dashboard/ingest.py

## Assumptions / Open Questions
- Median basis for duration_s outliers needs an explicit Plan-phase decision: runs.jsonl has no 'phase' field, only 'tier', so the proposal's literal 'duration_s > 3x the phase median' wording doesn't map onto the real schema — Plan must decide overall-median vs. tier-scoped-median
- Relationship between the new relative/median outlier section and the existing fixed-threshold slow_runs (1800s) mechanism needs an explicit Plan-phase decision so the two signals don't read as redundant or conflicting

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
