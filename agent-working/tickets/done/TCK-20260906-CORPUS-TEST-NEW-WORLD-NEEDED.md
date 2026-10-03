---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260906-CORPUS-TEST-NEW-WORLD-NEEDED
phase: done
date: 2026-09-06
tags: [testing, simulation-quality, corpus]
---

# TCK-20260906-CORPUS-TEST-NEW-WORLD-NEEDED

## Title
Ideas 50 (Material-Gated Evolution) and 64 (The Empty Chair) — corpus-test authoring is blocked, mechanisms never shipped

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P3

## Request Summary
M9 epic (`TCK-20260824-EPIC-RPG-M9-CORPUS-TEST-COVERAGE`) child 5 of 8. **Correction, 2026-09-06,
found while scoping this ticket, not inherited from the original M9 doc uncritically**: this item's
original framing ("new Unit-tier world needed" for corpus testing) wrongly assumed both ideas'
underlying mechanisms already exist. Direct verification found otherwise:
- **Idea 64 (The Empty Chair)**: M4's own epic doc (`rpg_m4_beyond_city_epic.md`) explicitly states
  "No code precedent anywhere for the economic-vacancy signal it needs" — confirmed still true via
  direct grep, zero real code hits for `EconomicVacancyEvent` anywhere in `src/`. M4's roadmap summary
  claims "all 12 ideas shipped," but idea 64 was evidently not actually among the ideas that landed
  in that batch — a real discrepancy between the roadmap's summary count and this specific idea's
  real state, matching the "roadmap overclaims completion" pattern found repeatedly elsewhere in this
  roadmap.
- **Idea 50 (Material-Gated Evolution)**: does not appear in any shipped milestone's epic doc at all
  (only in the atlas and M9's own speculative doc) — zero real code hits for `alt_outcome_kind`.
  Never actually ticketed into any milestone's real scope.

Both ideas are real design concepts (confirmed present in `docs/brainstorm/rpg_feature_atlas.html`),
just never built. M9 itself builds nothing (see epic's Out of Scope) — corpus-test authoring for these
two is genuinely blocked until each idea's own mechanism ships via a future milestone ticket, not
ready work today.

## Scope
- Correct the M9 epic doc's item 4 entries for ideas 50/64 to reflect this finding (mechanism not
  shipped, not merely "needs a new world").
- Flag idea 64 specifically to whoever eventually re-audits M4's completion claims — its "all 12
  ideas shipped" framing appears to not actually include this idea.
- No corpus-test authoring in this ticket — genuinely blocked, not this ticket's work to do.

## Out of Scope
- Building either idea's underlying mechanism — that belongs in a future milestone's own ticket, not
  this M9 corpus-testing epic.
- Re-auditing the rest of M4's "12 ideas shipped" claim beyond this one specific discrepancy.

## Acceptance Criteria
- [x] M9 epic doc's item 4 entries for ideas 50/64 corrected to state the real blocker (mechanism not
      shipped) rather than "new world needed."
- [x] The M4 "12 ideas shipped" discrepancy for idea 64 is flagged somewhere real and citable (this
      ticket, or a cross-reference from M4's own roadmap section) — not silently left uncorrected.

## Related Tickets
- `TCK-20260824-EPIC-RPG-M9-CORPUS-TEST-COVERAGE` (parent epic)

## Related Docs
- `docs/plans/rpg_design_roadmap/rpg_m9_corpus_test_coverage_epic.md`

## Related Stored Artifacts
None yet — created by this ticket's own Investigate/Plan phases once picked up for implementation.

## Related Code Areas
- `docs/plans/rpg_design_roadmap/rpg_m4_beyond_city_epic.md`
- `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md` (M4 section's "12 ideas shipped" claim)

## Assumptions / Open Questions
- Whether idea 64 should be re-scoped into a real future ticket (since M4 apparently never actually
  built it despite being reviewed in that epic's own doc) is a real product decision, not resolved
  here — flag to the user/roadmap owner, don't unilaterally ticket new feature work from within this
  M9 corpus-testing epic.

## Implementation Notes
Investigate found both Acceptance Criteria were already satisfied by the M9 scoping pass's own doc
edits — confirmed via `git show 3aa642b7:...` (the original M9-scoping commit, PR #138, predating
any M9 child-ticket implementation) that `rpg_m9_corpus_test_coverage_epic.md` lines 294-298/325-330
and `rpg_design_roadmap.md` lines 141-147 already carried the corrected "mechanism never shipped"
framing and the M4-discrepancy flag, both already cross-referencing this exact ticket ID by name. No
doc edit was made — re-writing already-correct text would add no value. Both underlying factual
claims were independently re-verified rather than re-trusted: `grep -rn "EconomicVacancyEvent\|
alt_outcome_kind" src/` returns 0 hits for both. This ticket's real, remaining work was formal
closure only.

## Test Summary
No pytest run required — `behavior_changed=false`, no `src/`/`tests/` files touched. Verification
was direct grep + `git show` against the original scoping commit (see stored_artifacts test_plan.md
for the exact steps), both confirmed passing.

## Files Changed
None in `docs/` or `src/` — both target docs already carried the correct text. Only this ticket's
own file (moved to `tickets/done/`) and `tickets/working_log.csv`/`docs/REGISTRY.yaml` changed.

## Completion Summary
Confirmed both Acceptance Criteria were already satisfied by the M9 epic's own scoping pass, before
this ticket was ever picked up for implementation — not new work, a formal-closure ticket. Both
underlying claims (idea 50/64 mechanisms never shipped) were independently re-verified via direct
grep rather than re-trusted from the pre-existing doc text. No code, doc, or test changes were
needed or made.
