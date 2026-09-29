---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260822-COGNITION-VIEWER-TEMPORAL-PLAYBACK
phase: open
date: 2026-08-22
tags: [observability, cognition]
---

# TCK-20260822-COGNITION-VIEWER-TEMPORAL-PLAYBACK

## Title
Add temporal playback (tick slider) to the single-entity cognition graph viewer

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
The idea doc proposes adding temporal playback to tools/viz_strategy.html, a pure client-side Cytoscape tool, describing it as reusing existing rendering cues including overload red border and a budget bar. Investigation found two of those three cues bind to bounded_cognition_ui_contract.md fields (capacity/usage/overload_score/planning_budget) that do not exist anywhere in the actual snapshot/diff schema -- only overload_source (string) and overload_changed (bool) are real. This ticket adds a tick slider driven by the distinct tick values in cognition_graph_snapshots.jsonl for the selected entity, replacing the tool's current dependency on a hand-authored cognition_e{id}.json elements fixture that no pipeline actually produces, with diff-driven added/removed/changed node coloring -- and drops or explicitly relabels the two non-existent overload/budget cues rather than describing them as reused.

## Scope
- Add a tick slider populated from the distinct, sorted tick values present in cognition_graph_snapshots.jsonl for the selected entity_id; moving it renders that record's graph.nodes/edges as Cytoscape elements.
- Build a snapshot-to-elements transform in the tool's JS, replacing reliance on the externally-produced cognition_e{id}.json fixture for live data (legacy single-file load path must keep working, unchanged).
- Handle sparse/policy-gated capture: scrubbing to a tick with no snapshot must hold the most recent prior state or show an explicit 'no capture at this tick' indicator -- never error or blank.
- When a diff record exists for a tick transition, drive added/removed/changed node coloring, distinct from base kind-coloring.
- Add explicit stylesheet rules for node kinds present in real data but currently unstyled: blocker, lead, hypothesis.
- Correct the two false rendering-cue claims from the proposal: either drop the overload-red-border/budget-bar cues entirely, or implement them as an explicitly labeled approximation using overload_source/overload_changed only (no fabricated numeric score/budget).

## Out of Scope
- Extending the durable snapshot/diff schema to add real overload_score/planning_budget numeric fields (would require backend schema work, out of scope for this pure client-side ticket).
- Any post-run analytics/Parquet/DuckDB wiring, the run-level HTML report, decision_trace join, or CI gate work (separate tickets in this batch).
- Adding a pytest/automated test harness for viz_strategy.html (none exists today; not required by this ticket's AC).

## Acceptance Criteria
- [ ] Loading cognition_graph_snapshots.jsonl populates a tick slider with exactly the distinct sorted tick values present for the selected entity_id; moving the slider renders that record's graph.nodes/edges transformed into Cytoscape elements, without requiring the old pre-shaped elements JSON.
- [ ] Because capture is sparse/policy-gated, scrubbing to a tick with no snapshot does not error or blank -- it holds the most recent prior state or shows an explicit 'no capture at this tick' indicator.
- [ ] When a diff record exists for a tick transition, added/removed/changed nodes drive a defined node coloring distinct from base kind-coloring.
- [ ] Node kinds present in real data but currently unstyled (blocker, lead, hypothesis) get an explicit stylesheet rule; existing directive/project/objective/concern styling and the legacy single-file load path remain unchanged (no regression).
- [ ] The ticket's own documentation/UI explicitly states which of the proposal's original cues (overload red border, budget bar) were dropped vs. approximated, and on what real field -- no cue is claimed as 'reused' if it isn't grounded in real schema data.

## Related Tickets
None.

## Related Docs
- docs/strategy/bounded_cognition_ui_contract.md

## Related Stored Artifacts
None.

## Related Code Areas
- tools/viz_strategy.html
- src/observability/cognition/recorder.py
- src/observability/cognition/schema.py
- src/observability/cognition/diff_builder.py
- src/systems/strategic_systems/cognition_export.py

## Assumptions / Open Questions
- Capture is sparse/event-driven, policy-gated by ObservabilityMode, not one-record-per-tick -- UX must communicate irregular tick gaps rather than implying smooth per-tick scrub.
- No code in the repo produces the cognition_e{id}.json elements-shape file the tool's existing loader expects; it is treated as a legacy/demo fixture, and the new transform is additive, not a replacement of that load path.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
