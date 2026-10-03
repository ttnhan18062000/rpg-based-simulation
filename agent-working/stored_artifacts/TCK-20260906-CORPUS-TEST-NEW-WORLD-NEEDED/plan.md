---
status: active
layer: testing
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20260906-CORPUS-TEST-NEW-WORLD-NEEDED
date: 2026-09-06
---

# Plan: TCK-20260906-CORPUS-TEST-NEW-WORLD-NEEDED

## Summary
Investigate found both Acceptance Criteria already satisfied by the M9 scoping pass's own doc edits
(pre-existing at the original scoping commit, before this ticket was picked up for implementation).
No doc edit, no code, no test is needed. This ticket's real, remaining scope is formal closure only:
record the confirmation, cite the exact pre-existing evidence, and close.

## Steps
1. Independently re-verify (not re-trust) both underlying claims: zero real code hits for
   `alt_outcome_kind` (idea 50) and `EconomicVacancyEvent` (idea 64) anywhere in `src/`.
2. Confirm both target docs' relevant sections already exist and already cross-reference this exact
   ticket ID, at the original M9-scoping commit (before any implementation work began).
3. Fill in this ticket's own Implementation Notes / Test Summary / Completion Summary citing the
   above, move to `tickets/done/`, append `working_log.csv`.
4. No `docs/REGISTRY.yaml` regeneration needed for the doc files themselves (unchanged), but the
   ticket's own move to `tickets/done/` still requires the standard registry regen for the ticket
   entry itself.

## Acceptance Criteria Map
- AC1 ("epic doc's item 4 entries for ideas 50/64 corrected") → satisfied by
  `rpg_m9_corpus_test_coverage_epic.md` lines 294-298, 325-330 (pre-existing).
- AC2 ("M4 discrepancy flagged somewhere real and citable") → satisfied by
  `rpg_design_roadmap.md` lines 141-147 (pre-existing), cross-referencing this ticket by name.

## Scope Guards
- Do not edit either doc — both already state the correct finding.
- Do not build either idea's mechanism, and do not open a new future-work ticket for idea 64's
  re-scoping — that is a product decision for the user/roadmap owner, out of this ticket's scope per
  its own Assumptions section.
- Do not author a corpus test for either idea — genuinely blocked, confirmed unbuildable until a
  future milestone ships the missing mechanism.

## Risks
None — this is a confirm-and-close ticket, not new work.
