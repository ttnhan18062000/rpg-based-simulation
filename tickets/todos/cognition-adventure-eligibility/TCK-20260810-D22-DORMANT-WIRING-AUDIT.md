---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260810-D22-DORMANT-WIRING-AUDIT
phase: open
date: 2026-08-10
tags: []
---

# TCK-20260810-D22-DORMANT-WIRING-AUDIT

## Title
Record D22 dormant-wiring audit findings

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P1

## Request Summary
This session's investigation surfaced three confirmed dormant-wiring findings — a dead HUNT_WEAK_ENEMY route, a GoalKind/ProjectKind vocabulary split, and a cognition_profile field that was inert until C1 wires it up — that should be durably recorded following the existing D-numbered audit convention (D06, D19, D20, D21), so the findings aren't lost once the parent investigation ticket closes.

## Scope
- Create docs/audits/D22_dormant_content_wiring.md following D21's narrative format (Ticket/Date header + Purpose/Summary table/per-finding sections with a Related Docs footer) — the closer structural fit for this 3-finding scope than D19's Dimension-Profile-table format
- Document 3 distinct findings with file:line citations: (1) HUNT_WEAK_ENEMY dead route generation (src/domains/adventure/mapper.py:37, src/domains/adventure/generator.py confirmed zero references) — status 'open, documented not fixed' per design's explicit non-goal; (2) GoalKind/ProjectKind vocabulary split (src/core/strategic.py:121-148, evaluate_project_switch bypass gap) — status 'fixed differently' once C2 lands (C2 fixes it by making evaluate_project_switch generic, not by unifying the enums); (3) cognition_profile inert-until-fixed gap (src/strategy/cognition_capacity.py CapacityService.derive_profile() never reads cognition_profile_id; src/content/schema.py:91,138,174,212) — status 'fixed' once C1 lands
- Include valid frontmatter (status/layer/authority/audience/tags) passing validate_frontmatter.py, matching the D19/D20/D21 convention
- Cross-reference the source material (the parent investigation, citing its final stored_artifacts/ path once that ticket closes)
- Run make knowledge-index-update after creating the file
- Verify post-regeneration docs/REGISTRY.yaml contains an entry for the new file

## Out of Scope
- Any code fix for the HUNT_WEAK_ENEMY dead route — explicitly documented as open/not-fixed per the design's own non-goal, not this ticket's job to fix
- Implementing C1/C2's actual code changes — this ticket only records their landed (or not-yet-landed) status
- Working this ticket before TCK-20260810-COGNITION-PROFILE-ADVENTURE-ELIGIBILITY (C1), TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION (C2), and TCK-20260810-COGNITION-ELIGIBILITY-BYPASS-DOCS (C3) are DONE — this ticket must be worked LAST so finding statuses are accurate as-landed, not speculative

## Acceptance Criteria
- [ ] D22_dormant_content_wiring.md exists with valid frontmatter (status/layer/authority/audience/tags) passing validate_frontmatter.py, matching the D19/D20/D21 convention
- [ ] The doc contains 3 distinct named findings with file:line citations — HUNT_WEAK_ENEMY dead route (mapper.py:37, generator.py), GoalKind/ProjectKind vocabulary split (strategic.py:121-148), cognition_profile inert-until-now gap (cognition_capacity.py derive_profile()) — each with an explicit open/fixed status as of authoring date, reflecting whatever C1/C2/C3 have actually landed
- [ ] The doc cross-references its source material and make knowledge-index-update is run afterward
- [ ] Post-regeneration docs/REGISTRY.yaml contains an entry for the new file

## Related Tickets
- TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION
- TCK-20260808-TRAIT-EXPRESSED-PRODUCER-INVESTIGATION
- TCK-20260808-ITEM-EQUIPPED-DORMANT-PATH-INVESTIGATION
- TCK-20260808-LOWER-LAYER-FOUNDATION-AUDIT
- TCK-20260810-COGNITION-PROFILE-ADVENTURE-ELIGIBILITY
- TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION
- TCK-20260810-COGNITION-ELIGIBILITY-BYPASS-DOCS

## Related Docs
- docs/audits/D19_domain_phase_inventory.md
- docs/audits/D20_simq_integration.md
- docs/audits/D21_entity_lifecycle_foundation_layers.md

## Related Stored Artifacts
None.

## Related Code Areas
- docs/audits/D19_domain_phase_inventory.md
- docs/audits/D20_simq_integration.md
- docs/audits/D21_entity_lifecycle_foundation_layers.md
- src/domains/adventure/mapper.py
- src/domains/adventure/generator.py
- src/core/strategic.py
- src/strategy/cognition_capacity.py
- src/content/schema.py

## Assumptions / Open Questions
- D22 is genuinely the next free number (confirmed via direct ls), but a simple count+1 rule is not assumed reliable given the D20 filename collision precedent
- finding statuses must reflect actual landed state at authoring time, not a speculative forecast
- source path will move from staging_artifacts/ to stored_artifacts/ once the parent ticket closes — D22 should cite the final path if authored after that move

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
