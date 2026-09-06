---
status: active
layer: testing
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20260906-CORPUS-TEST-NEW-WORLD-NEEDED
date: 2026-09-06
---

# Test Plan: TCK-20260906-CORPUS-TEST-NEW-WORLD-NEEDED

## Scope
No code or test authoring in this ticket — confirmed by Investigate/Plan, both Acceptance Criteria
are documentation-verification only. "Testing" here means verifying the two underlying factual
claims directly against real code, not running a pytest suite.

## Verification Steps
1. `grep -rn "EconomicVacancyEvent\|alt_outcome_kind" src/` — expect 0 hits (confirms idea 50/64's
   mechanisms are genuinely unshipped).
2. `git show 3aa642b7:docs/plans/rpg_design_roadmap/rpg_m9_corpus_test_coverage_epic.md | grep -n
   "idea 50\|idea 64"` — expect the corrected "blocked... mechanism never shipped" text already
   present at the original scoping commit.
3. `git show 3aa642b7:docs/plans/rpg_design_roadmap/rpg_design_roadmap.md | grep -n "12 ideas
   shipped\|EconomicVacancyEvent"` — expect the M4 discrepancy note already present at the original
   scoping commit.
4. `python3 tools/validate_frontmatter.py` on the closed ticket file, and
   `python3 tools/generate_registry.py` to pick up the ticket's new `tickets/done/` location.

## No Regression Suite Needed
`behavior_changed=false`, no `src/`/`tests/` files touched — no pytest run is required for this
ticket's own closure.
