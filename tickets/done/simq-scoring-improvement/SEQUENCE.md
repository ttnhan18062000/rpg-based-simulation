# Implementation Sequence — simq-scoring-improvement

Generated from dependency analysis across this batch's 5 tickets (filed 2026-07-13 from
`docs/plans/simq_scoring_improvement_roadmap.md`). `implement-epic` reads this file to override
alphabetical order.

## Order

1. `TCK-20260713-SIMQ-EVAL-PROFILE-BUG` (no deps in this batch — land first so Phase 1's repeated
   live-mode calibration sweeps aren't run against a tool with a known silent-corruption bug)
2. `TCK-20260713-SIMQ-SCORE-CEILING-FIX` (soft dependency: recommended after #1)
3. `TCK-20260713-SIMQ-RAWSCORE-PERSIST` (depends on: TCK-20260713-SIMQ-SCORE-CEILING-FIX — reuses
   its corpus re-anchor pass rather than running a second full sweep)
4. `TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH` (depends on: TCK-20260713-SIMQ-SCORE-CEILING-FIX —
   hard dependency, content authored against an uncorrected formula would not move the grade)
5. `TCK-20260713-SIMQ-COGNITION-PIPELINE-WIRE` (no deps in this batch — fully independent, can run
   in parallel with any of the above)

## Why This Order Matters

Running alphabetically would attempt `TCK-20260713-SIMQ-COGNITION-PIPELINE-WIRE` before
`TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH`, which is fine (they're independent) — but would also
attempt `TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH` and `TCK-20260713-SIMQ-RAWSCORE-PERSIST` before
`TCK-20260713-SIMQ-SCORE-CEILING-FIX`, which both explicitly depend on it landing first. Ticket #5
(`COGNITION-PIPELINE-WIRE`) may be picked up at any point in this sequence, including in parallel
with #1-4, since it shares no files or dependencies with the other four.

Re-run `/implement-epic folder=tickets/todos/simq-scoring-improvement/` after any gate failure —
already-done tickets are skipped automatically.
