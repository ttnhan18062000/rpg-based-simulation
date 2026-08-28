# Implementation Sequence — m1-quick-wins

Tickets must be implemented in this order. Generated automatically from intra-batch
dependency analysis. `implement-epic` reads this file to override alphabetical order.

tracking_doc: docs/plans/rpg_design_roadmap/rpg_design_roadmap.md

## Order

1. TCK-20260824-ROLLOUT-FLAG-DECISIONS  (no deps in this batch — moved to position 1, per
   `docs/plans/rpg_design_roadmap/rpg_m1_quick_wins_epic.md`'s own explicit acceptance signal:
   "Idea 9's flag-governance ticket lands before any other M1 ticket that adds new flag-gated
   behavior." Original dependency-analysis position was 11; verified none of positions 1-10 below
   add new flag-gated behavior, so this reorder is a pure sequencing tightening, not a dependency
   fix.)
2. TCK-20260824-ALLOCATE-AP-BRANCH-DECISION  (no deps in this batch)
3. TCK-20260824-BREAKTHROUGH-BONUS-APPLICATION  (no deps in this batch)
4. TCK-20260824-CAUSAL-MEMORY-ROUTE-SCORING  (depends on: TCK-20260824-WIRE-ORPHANED-MECHANISMS)
5. TCK-20260824-DEFAULT-HEIR-ASSIGNMENT  (no deps in this batch)
6. TCK-20260824-GRIEF-NEMESIS-REACHABILITY  (no deps in this batch)
7. TCK-20260824-LEAD-CONTRADICTION-WIRING  (no deps in this batch)
8. TCK-20260824-LIFE-STAGE-TRANSITIONS  (no deps in this batch)
9. TCK-20260824-NEMESIS-MEMORY-UNIT-TESTS  (no deps in this batch)
10. TCK-20260824-OCCUPATION-CHANGE-TRIGGER  (no deps in this batch)
11. TCK-20260824-RELATIONSHIP-ROLE-FIELD  (no deps in this batch)
12. TCK-20260824-ROUTE-KIND-COUNT-FIX  (no deps in this batch)
13. TCK-20260824-SECRETS-DISCLOSURE-SCOPE-SEQ  (depends on: TCK-20260824-ROLLOUT-FLAG-DECISIONS)
14. TCK-20260824-TOWN-CENTER-POINTER-FIX  (no deps in this batch)
15. TCK-20260824-WIRE-ORPHANED-MECHANISMS  (no deps in this batch)
16. TCK-20260824-WOUND-PENALTY-FORMULA-WIRING  (no deps in this batch)
17. TCK-20260824-AFFECTION-CONTRACT-GATE  (no deps in this batch)
18. TCK-20260824-PERSONAL-ECONOMY-SCOPE-BLOCK  (no deps in this batch)
19. TCK-20260824-WOUND-HEALING-DECISION  (depends on: TCK-20260824-WOUND-PENALTY-FORMULA-WIRING)
20. TCK-20260824-WOUND-THRESHOLD-DECISION  (depends on: TCK-20260824-WOUND-PENALTY-FORMULA-WIRING)
21. TCK-20260824-TACTICAL-WOUND-SCAR-WIRING  (depends on: TCK-20260824-WOUND-THRESHOLD-DECISION, TCK-20260824-WOUND-PENALTY-FORMULA-WIRING, TCK-20260824-WOUND-HEALING-DECISION)
22. TCK-20260828-REPUTATION-WITNESSED-EVENT-WIRING  (depends on: TCK-20260824-WIRE-ORPHANED-MECHANISMS — split out of that ticket's Investigate phase; added post-hoc, not part of the original dependency analysis)

## Why This Order Matters

Running alphabetically would attempt tickets before their dependencies are in place.
Re-run `/implement-epic` with the same folder after any gate failure — already-done
tickets are skipped automatically.

## Notes on independence (not dependencies, called out explicitly)

- TCK-20260824-GRIEF-NEMESIS-REACHABILITY and TCK-20260824-NEMESIS-MEMORY-UNIT-TESTS
  reference each other in Related Tickets but are explicitly confirmed independent —
  no shared code, data model, or callers (both tickets' own Assumptions sections state this).
  Listed here without a dependency edge between them.
- TCK-20260824-WOUND-THRESHOLD-DECISION also references TCK-20260824-WOUND-HEALING-DECISION
  in Related Tickets, but per both tickets' own Assumptions, whether the healing decision
  narrows the threshold ticket's scope is an open question, not a hard prerequisite — no
  dependency edge added for that pair specifically, only WOUND-PENALTY-FORMULA-WIRING is a
  hard sequencing dependency for both.
