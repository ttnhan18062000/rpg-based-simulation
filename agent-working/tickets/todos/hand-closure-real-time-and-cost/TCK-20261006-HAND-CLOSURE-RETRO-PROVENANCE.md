---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261006-HAND-CLOSURE-RETRO-PROVENANCE
phase: open
date: 2026-10-06
tags: [observability, agent-monitoring, process-improvement]
---

# TCK-20261006-HAND-CLOSURE-RETRO-PROVENANCE

## Title
The retro reports duration and cost by provenance and states which tables changed meaning in the week the change landed

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Child 4 of `TCK-20261006-EPIC-HAND-CLOSURE-REAL-TIME-AND-COST`. It depends on `TCK-20261006-HAND-CLOSURE-COST-ATTRIBUTION`
and on the owner's derived-in-averages decision, recorded in the design child. Today `generate_retro.py`
averages only truthy `duration_s` (:798-800, per mode :818-833), so zero-duration hand runs drop out silently.
Once children 2-3 land, hand runs carry real and derived values, and every duration and cost table changes
meaning.

## Scope
1. Duration and cost aggregates treat provenance as the owner decided: either derived values are included and
   labelled, or they are reported beside measured ones. A null duration is counted as "unknown" and shown as a
   count, not dropped silently.
2. Add a per-provenance coverage line for hand-closed runs: the share with non-null duration and the share with a
   cost value. This is the epic's AC2 instrument.
3. The retro states once, at the top, the first week in which these tables use the new data: Avg duration,
   per-mode avg (:1440, :1451-1461), Slow Runs (:997-1007), duration outliers (:1022-1036), the active/idle split
   (:986-994), Spend Proxy by Phase/Agent and the coverage note (:934-966, :1571-1596), and cost outliers
   (:1045-1055).
4. Update `docs/agent-monitoring/schema.md` or the retro docs where they describe these tables. Move the
   `agent_working_direction.md` row for this direction to `shipped` with the measured coverage. That
   measurement is the epic's AC4, taken on the first full week after landing.

## Out of Scope
- Re-rendering past retros.
- Any gate over these numbers. Report only.

## Acceptance Criteria
1. A fixture week with measured, derived and unknown hand runs renders each table as the owner decided. A
   golden or assertion test covers it.
2. The unknown count is shown wherever a duration average is shown. Tested.
3. The coverage line renders, with a test.
4. The "tables changed meaning from week X" note renders once. Tested.
5. The design child's two acceptance criteria for this child are added here and pass.

## Related Tickets
- `TCK-20261006-EPIC-HAND-CLOSURE-REAL-TIME-AND-COST` (parent), `TCK-20261006-HAND-CLOSURE-COST-ATTRIBUTION` (dependency)
- `TCK-20260929-RUN-EXECUTION-MODE-FIELD` (the per-mode split this extends)

## Related Docs
- `docs/plans/agent_infrastructure/agent_working_direction.md`
- `docs/agent-monitoring/schema.md`

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261006-HAND-CLOSURE-TIME-SOURCE-DESIGN/design.md` (after child 1 closes)

## Related Code Areas
`tools/agent-monitoring/generate_retro.py`, `duration_utils.py`, and its tests under `tests/tools/`.

## Assumptions / Open Questions
- Session-layer M7 (not before about 2026-11-02) reads the same retro data. If this lands first, M7's baseline
  notes which week the meaning changed.

## Implementation Notes
Hand-filed by agent-working-design (interim planner), 2026-10-06.

## Test Summary
(Open.)

## Files Changed
(Open.)

## Completion Summary
(Open.)
