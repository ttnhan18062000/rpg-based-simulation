# Implementation Sequence — simulation-quality

All 5 tickets here came out of a 2026-08-05 SimQ status review and a follow-up per-entity
event-chain investigation. Only one real dependency exists between them (#3 → #4, soft); the rest
are independent and can be picked up in any order or in parallel. This sequence reflects priority,
not strict blocking, except where noted.

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

## Notes

- #1 and #5 are both hotfix-tier and mutually independent — safe to batch together if picking up
  small items first.
- #2, #3, #4 are all standard-tier investigations; #2 has no relationship to #3/#4 at all (ECONOMY
  routing vs. observability capture are unrelated subsystems) and can be done in any order relative
  to them.
