---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260821-VISUAL-QUALITY-DOCS
phase: open
date: 2026-08-21
tags: [documentation, visualization, simulation-quality]
---

# TCK-20260821-VISUAL-QUALITY-DOCS

## Title
Documentation deliverables for the visual-quality system

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Two docs deliverables mirroring SimQ's precedent exactly: a new docs/visual_quality/ subfolder (naming TBD) mirroring docs/simulation_quality/'s shape (scoring contract, current-state doc, calibration/audit-workflow doc), and a new docs/audits/ periodic dimension entry — confirmed next number D26 at investigation time (D25 claimed same-day by an unrelated ticket) — mirroring D20_simq_integration.md's relationship to docs/simulation_quality/.

## Scope
- Create docs/visual_quality/ subfolder with files mirroring quality_scoring_contract.md, current_state.md, and audit_workflow.md's shapes/headers/frontmatter
- Create docs/audits/D26_<slug>.md following D20_simq_integration.md's Dimension Profile table + Related dimensions + Findings Summary format
- Re-verify D26 is still the correct next available number at actual implementation time (already re-confirmed twice during proposal/investigation, but this is a shared, actively-changing repo)
- Decide whether to also fix docs/audits/audit_dimensions.md's already-stale master index (missing D19/D21-D25) or follow the stale precedent
- Use only registry-allowlisted layer/tags (rendering/visualization already registered 2026-08-20)

## Out of Scope
- Documenting speculative/undesigned behavior — this ticket documents the grade-scorer ticket's REAL implemented contract, so it must be sequenced after that ticket (and, per epic ordering, after the calibration and agent-review tickets too)
- Adding docs/visual_quality/ to tests/docs/test_doc_path_existence.py's currently-scoped coverage (worth deciding, not required by this ticket)

## Acceptance Criteria
- [ ] docs/visual_quality/ subfolder exists with >=3 files mirroring quality_scoring_contract.md/current_state.md/audit_workflow.md's shapes, each passing tools/validate_frontmatter.py
- [ ] docs/audits/D26_<slug>.md is created following D20's Dimension Profile table format, with D26 re-confirmed as the correct next number at implementation time (not just trusted from prior investigation)
- [ ] All new docs use only registry-allowlisted layer/tags
- [ ] docs/REGISTRY.yaml regeneration at ticket close correctly picks up the new docs

## Related Tickets
- TCK-20260821-VISUAL-GRADE-SCORER
- TCK-20260821-VISUAL-QUALITY-CALIBRATION
- TCK-20260821-VISUAL-AGENT-REVIEW
- TCK-20260820-EPIC-WORLD-RENDERING-CORE

## Related Docs
- docs/simulation_quality/quality_scoring_contract.md
- docs/simulation_quality/current_state.md
- docs/simulation_quality/audit_workflow.md
- docs/audits/D20_simq_integration.md
- docs/audits/audit_dimensions.md
- docs/plans/world_rendering/idea_world_render_validation.md
- docs/plans/world_rendering/idea_world_rendering_core.md
- docs/plans/world_rendering_core_epic.md

## Related Stored Artifacts
None.

## Related Code Areas
None.

## Assumptions / Open Questions
- D26 was independently re-verified twice already (proposal + investigation) but must be checked again at actual implementation time since this is a shared, actively-changing repo
- Whether D26 should also repair audit_dimensions.md's stale master index or follow the existing stale precedent is an open question, not resolved here
- docs/visual_quality/ naming is explicitly TBD
- simulation-quality: this ticket documents a SimQ-sibling system (not a SimQ-subsystem change itself), tagged for topical adjacency since it mirrors SimQ's own doc precedent

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
