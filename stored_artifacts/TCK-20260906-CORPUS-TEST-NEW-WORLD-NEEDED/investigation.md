---
status: active
layer: testing
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20260906-CORPUS-TEST-NEW-WORLD-NEEDED
date: 2026-09-06
---

# Investigation: TCK-20260906-CORPUS-TEST-NEW-WORLD-NEEDED

## Current Behavior — both Acceptance Criteria already satisfied by the M9 scoping pass itself
This ticket's own text is explicit that its "correction" was found "while scoping this ticket"
(2026-09-06, by the peer planning session that authored the whole M9 epic + 8 child tickets).
Confirmed via `git show 3aa642b7:...` (the original M9-scoping commit, PR #138, before any M9 child
ticket implementation began) that both required doc corrections already existed at that exact
commit — this ticket's own deliverable was pre-completed by its own scoping pass, not left as open
work for implementation:

- `docs/plans/rpg_design_roadmap/rpg_m9_corpus_test_coverage_epic.md` lines 294-298 (idea 50) and
  325-330 (idea 64) already state "blocked, 2026-09-06 (re-verified): mechanism never shipped" for
  both ideas, each with a real, direct grep-confirmed claim (zero hits for `alt_outcome_kind` /
  `EconomicVacancyEvent` anywhere in `src/`, re-confirmed independently here) and a cross-reference
  to this exact ticket ID.
- `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md` lines 141-147 (M4 section) already states
  the real discrepancy: idea 64 does not appear to be among M4's own "all 12 ideas shipped" (PR
  #115) claim, cross-referencing this exact ticket ID.

## Re-verification (not just re-trusting the pre-existing doc text)
- `grep -rn "EconomicVacancyEvent\|alt_outcome_kind" src/` — 0 hits, confirmed independently.
- `rpg_m4_beyond_city_epic.md`'s own idea-64 entry text ("No code precedent anywhere for the
  economic-vacancy signal it needs") is unchanged since M4's own scoping — the mechanism was never
  built at any point, not merely dropped from a later pass.
- Idea 50 does not appear in any shipped milestone's epic doc (only the atlas and this M9 doc's own
  speculative text) — never actually ticketed into any milestone's real scope.

## No further doc edit needed
Both Acceptance Criteria are satisfied by content that already exists, cross-referencing this exact
ticket ID by name. Re-writing already-correct text would add no real value and risks introducing an
inconsistency between two now-independently-maintained copies of the same finding. This ticket's own
real, remaining work is formal closure: recording that these criteria are met, not re-doing them.

## Docs Requiring Update
None — both target docs already carry the correct, cross-referenced text.

## Parity Ledger Overlap
None — no `src/` change, no behavior change, `behavior_changed=false`.

## Prior Work
- `TCK-20260906-AGE-TIER-TIMING-BUG-AND-CORPUS-TEST` (M9 ticket 2) — its own roadmap.md edit
  (adjacent text in the same section) independently arrived at and stated the same idea 50/64
  finding as a passing observation, consistent with (not contradicting) this ticket's own dedicated
  citation.

## Risks and Open Questions
- Whether idea 64 should be re-scoped into a real future milestone ticket is a real product decision,
  correctly left unresolved by this ticket per its own explicit Assumptions section — flagged to the
  user/roadmap owner via the citations above, not unilaterally ticketed here.

## Anti-Drift Hazards
- Do not duplicate or rewrite the existing correct doc text — cite it, don't re-derive it.
- Do not build either idea's underlying mechanism from within this M9 corpus-testing epic.
