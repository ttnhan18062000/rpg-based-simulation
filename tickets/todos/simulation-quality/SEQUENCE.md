# Implementation Sequence — simulation-quality

All 9 tickets here came out of a 2026-08-05 SimQ status review, a follow-up per-entity event-chain
investigation, and a corpus scale-diversity gap sweep. Two soft dependencies exist (#3 → #4, #9 →
#2, both noted below); everything else is independent and can be picked up in any order or in
parallel. This sequence reflects priority, not strict blocking, except where noted.

## Order

1. **TCK-20260805-SIMQ-WORLD-ANCHOR-RECALIBRATION** (hotfix) — no dependencies. Highest urgency:
   the WORLD regression gate is currently untrustworthy until this lands. Do first.
2. **TCK-20260805-SIMQ-ECONOMY-ADVENTURE-ROUTE-SCORER-BIAS** (standard, investigation-first) — no
   dependencies. The one remaining genuinely open pillar-quality question in the system; highest
   value of the standard-tier tickets here.
3. **TCK-20260805-COGNITION-GRAPH-CAPTURE-CORPUS-GAP** (standard, investigation-first) — no
   dependencies on the others, but should land before #4 for that ticket's full evaluation (see
   below).
4. **TCK-20260805-BEHAVIOR-SCORECARD-REDUNDANCY-INVESTIGATION** (standard) — **soft-depends on
   #3.** Its option (b) evaluation (whether `EntityBehaviorScorecard` fields are derivable from
   `decision_trace.jsonl` + `cognition_graph_diffs.jsonl` together) needs #3's capture-mode fix
   landed to be tested against real data. It can still *start* immediately against
   `decision_trace.jsonl` alone (already live), so it doesn't need to wait to begin — just should
   not be marked DONE with a final verdict before #3 lands.
5. **TCK-20260805-SIMQ-GRADE-ORDER-F-BAND-GAP** (hotfix) — fully independent of all the others.
   Lowest urgency (dormant, 0 real occurrences observed). Can run in parallel with any of #1-#4, or
   last — pure scheduling convenience, not a dependency constraint.
6. **TCK-20260805-SIMQ-CORPUS-FACTION-DENSITY-SMALL-MAP** (standard) — no dependencies. Backlog:
   corpus scale-diversity coverage, not a fix for a known-wrong signal.
7. **TCK-20260805-SIMQ-CORPUS-RESOURCE-DENSITY-DECOUPLE** (standard) — no dependencies. Backlog,
   same rationale as #6.
8. **TCK-20260805-SIMQ-CORPUS-QUEST-DENSITY-DECOUPLE** (standard) — no dependencies. Backlog, same
   rationale as #6.
9. **TCK-20260805-SIMQ-CORPUS-AGENCY-REAL-ARCHETYPE** (standard) — no dependencies, but **soft-feeds
   #2**: a real, coherent routing-active archetype world would give #2's investigation better
   substrate than the corpus's current purpose-built fixtures. Doesn't block #2 either direction —
   #2 can complete first using existing worlds, or #9 can land first to improve #2's evidence base.
   Ranked above #6-8 in practical priority (though listed last) precisely because of this
   connection to already-open work.

## Notes

- #1 and #5 are both hotfix-tier and mutually independent — safe to batch together if picking up
  small items first.
- #2, #3, #4 are all standard-tier investigations; #2 has no relationship to #3/#4 at all (ECONOMY
  routing vs. observability capture are unrelated subsystems) and can be done in any order relative
  to them.
- #6-9 are all corpus-authoring tickets (world-scale-diversity backlog, `layer: world`), explicitly
  lower priority than #1-#5 — see each ticket's Request Summary for the corpus-breadth
  deprioritization rationale. They're listed last for that reason, not because #9's connection to
  #2 is unimportant (see #9's note above).
