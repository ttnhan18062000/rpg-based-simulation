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
DONE

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
- [x] D22_dormant_content_wiring.md exists with valid frontmatter (status/layer/authority/audience/tags) passing validate_frontmatter.py, matching the D19/D20/D21 convention
- [x] The doc contains 3 distinct named findings with file:line citations — HUNT_WEAK_ENEMY dead route (mapper.py:37, generator.py), GoalKind/ProjectKind vocabulary split (strategic.py:121-148), cognition_profile inert-until-now gap (cognition_capacity.py derive_profile()) — each with an explicit open/fixed status as of authoring date, reflecting whatever C1/C2/C3 have actually landed
- [x] The doc cross-references its source material and make knowledge-index-update is run afterward
- [x] Post-regeneration docs/REGISTRY.yaml contains an entry for the new file

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

Worked last in the C1→C2→C3→C4 batch as required by Out of Scope. Before writing, directly
re-verified each of the 3 findings against real, current code rather than trusting the ticket's
own paraphrase or the design doc's forward-looking language:

- **HUNT_WEAK_ENEMY**: re-ran `grep -rn "HUNT_WEAK_ENEMY" src/` — still confirmed zero references
  in `src/domains/adventure/generator.py`; the only real references are `mapper.py:37` (mapping
  entry), `scoring.py` (scoring logic that would apply if the route were ever generated), and
  `schema.py:23` (enum member). Neither C1 nor C2 touched `generator.py`. Cited
  `docs/architecture/2026-08-10-cognition-driven-adventure-eligibility-design.md`'s Non-goals
  section verbatim as the reason this stays open by design, not oversight.
- **GoalKind/ProjectKind**: read `src/core/strategic.py:121-148` directly (both enums unchanged,
  byte-identical pre/post C2) and `src/systems/strategic_systems/intelligence.py`'s real landed
  `_score_scale_max()` helper (lines 89-107) and `evaluate_project_switch()` (now at line 929, was
  881-935 pre-edit). Confirmed via the helper's own docstring and C2's `plan.md` `## Scope Guards`
  section (`stored_artifacts/TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION/plan.md:519-521`)
  that unification was explicitly out of scope for C2 — the split is worked around
  (`isinstance(kind, ProjectKind)` classification), not closed.
- **cognition_profile**: read `src/strategy/cognition_capacity.py` in full — `CapacityService.
  derive_profile()` is confirmed unchanged by C1, still purely attribute-driven, never reads
  `cognition_profile_id`. C1's real fix lives entirely in `src/domains/adventure/phase.py` (new
  module-level `_resolve_cognition_profile_id()`/`_supports_adventure_routing()` helpers) and
  `src/engine/behavior_consumers.py` (new `get_cognition_profile_definition()` accessor), reading
  `supports_adventure_routing` (`src/content/schema.py:101`) to gate `AdventureDecisionPhase`'s
  own hero-eligibility filter — a different consumer than the ticket's own Scope description
  named. Documented explicitly that this is "fixed" for adventure-routing eligibility specifically,
  not "CapacityService.derive_profile() was changed."

**Discrepancy found and corrected from the task brief**: the brief stated the parent investigation
had "already moved to stored_artifacts/ since that ticket closed." Direct check found
`TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION` is still in `tickets/inprogress/` with
its artifacts still in `staging_artifacts/` (not `stored_artifacts/`) — the parent ticket has not
actually closed. Cited the real current path (`staging_artifacts/...`) in the doc instead of the
claimed one, and noted the ticket hasn't closed yet, per this ticket's own "Assumptions/Open
Questions" contingency ("D22 should cite the final path if authored after that move" — it wasn't,
so the staging path is correct as of authoring).

Also found and disclosed a separate hygiene gap in a dependency, not fixed here (out of this
ticket's scope, touching another ticket's file): `tickets/done/
TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION.md`'s body `## Status` field still reads
`INPROGRESS` despite living in `tickets/done/` with all ACs checked and a filled Completion
Summary. Verified C2's actual code is landed and correct directly against source (not inferred
from the stale Status field), and flagged the discrepancy in D22's own text rather than silently
treating C2 as unfinished or silently fixing another ticket's file.

## Test Summary

No code changes — documentation-only hotfix. Verification performed:
- `python3 tools/validate_frontmatter.py docs/audits/D22_dormant_content_wiring.md` → `OK: 1 file(s) checked — no violations`
- `make knowledge-index-update` → `Incremental update complete: 7091 chunks total (1 files re-embedded, 2643 from cache, 0 deleted).`
- `python3 tools/generate_registry.py` → `Wrote 1742 entries`; `grep -n "D22_dormant_content_wiring" docs/REGISTRY.yaml` confirms an entry at `path: docs/audits/D22_dormant_content_wiring.md`
- All 3 findings' file:line citations re-verified directly against current source (`grep`/`Read`)
  rather than trusted from the ticket's original paraphrase — see Implementation Notes.

## Files Changed

- `docs/audits/D22_dormant_content_wiring.md` (new)
- `docs/REGISTRY.yaml` (regenerated, includes new entry)
- `tickets/inprogress/TCK-20260810-D22-DORMANT-WIRING-AUDIT.md` (this file — Status, Acceptance
  Criteria, Implementation Notes, Test Summary, Files Changed, Completion Summary)

## Completion Summary

Created `docs/audits/D22_dormant_content_wiring.md` following D21's narrative structure
(Purpose/Summary table/per-finding sections/Related Docs footer), recording the 3 dormant-wiring
findings from `TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION`'s investigation with
file:line citations and statuses re-verified directly against current landed code: `HUNT_WEAK_ENEMY`
dead route generation (open, documented not fixed — explicit design non-goal), the
`GoalKind`/`ProjectKind` vocabulary split (fixed differently — C2 classifies by enum identity
rather than unifying the enums, which remains open), and the `cognition_profile` inert-until-fixed
gap (fixed — but via `AdventureDecisionPhase`'s own eligibility helpers in `phase.py`, not via
`CapacityService.derive_profile()` as the ticket's own Scope description implied). Frontmatter
validated, knowledge index rebuilt, and `docs/REGISTRY.yaml` regenerated and confirmed to include
the new file.
