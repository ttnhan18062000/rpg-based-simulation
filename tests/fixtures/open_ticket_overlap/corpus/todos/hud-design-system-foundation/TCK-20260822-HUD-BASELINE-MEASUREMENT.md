---
status: active
layer: frontend
authority: P1
audience: agent
ticket_id: TCK-20260822-HUD-BASELINE-MEASUREMENT
phase: open
date: 2026-08-22
tags: [hud, documentation]
---

# TCK-20260822-HUD-BASELINE-MEASUREMENT

## Title
Record baseline HUD usability measurement before M2

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Pick 3-5 representative observer tasks and measure them against the current, unmodified HUD before any further change lands, sourced from what the project's own simulation actually surfaces as meaningful.

## Scope
- Author a dated markdown doc containing exactly 3-5 named observer tasks, each explicitly sourced from a real simulation-surfaced concept (faction event, quest, calamity, economy event, entity-state anomaly).
- For each task, record: task description, date measured, exact HUD commit/state measured against, and observed result on the current unmodified HUD (steps taken, success/failure, friction points, time-to-complete).
- Structure the doc's task set and format to be stable/versioned, mirroring measurement_baseline_contract.md's fixed-corpus convention, so M4 can re-run identical tasks post-wiring and produce a real diff.

## Out of Scope
- Any frontend source file change — this is a measurement chore only, not a code change.
- Applying docs/simulation_quality/quality_scoring_contract.md's grade-band model — it explicitly excludes human-judgment content quality and does not apply to this human-observer HUD usability axis.
- Building any UX measurement tooling/template — measurement is manual/human-recorded, not scripted.

## Acceptance Criteria
- [ ] A dated markdown doc exists containing exactly 3-5 named observer tasks, each explicitly sourced from a real simulation-surfaced concept, not invented in the abstract.
- [ ] For each task, the doc records: task description, date measured, exact HUD commit/state measured against, and observed result on current unmodified HUD (steps taken, success/failure, friction points, time-to-complete).
- [ ] The doc's task set and format are stable/versioned so M4 can re-run identical tasks post-wiring and produce a real diff.
- [ ] No frontend source file is modified by this ticket's own work.

## Related Tickets
- TCK-20260822-EPIC-HUD-DESIGN-SYSTEM-FOUNDATION
- TCK-20260822-EPIC-HUD-CONTENT-POLISH-MEASUREMENT
- TCK-20260822-EPIC-HUD-CORE-PANEL-WIRING

## Related Docs
- docs/plans/hud_delivery_roadmap.md
- docs/engine/contracts/knowledge_gateway_mcp/measurement_baseline_contract.md
- docs/simulation_quality/quality_scoring_contract.md

## Related Stored Artifacts
None.

## Related Code Areas
None modified by this ticket (see Out of Scope — this is a measurement/documentation chore, no code
change). The observer tasks measured exercise, but do not touch, App.tsx, EntityList.tsx, Sidebar.tsx,
InspectPanel.tsx, and EventLog.tsx.

## Assumptions / Open Questions
- Where the baseline artifact durably lives (a registered docs/ file vs. stored_artifacts/-only) is explicitly unresolved in both epic tickets; the closest project convention (measurement_baseline_contract.md) suggests a registered docs/ file since M4 must reference and re-run against it later. Recommend: docs/hud/baseline_usability_measurement.md, or similar — final path decision belongs to this ticket's own Investigate phase.
- Task "representativeness" is inherently subjective; no automated check can verify it, so the AC compensates by requiring each task cite a real simulation-surfaced concept.
- No UX measurement tooling/template exists in this repo; measurement is necessarily manual/human-recorded, so the AC must accept prose/timing evidence rather than a script exit code.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
