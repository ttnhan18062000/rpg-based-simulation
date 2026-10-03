# Implementation Sequence — m5-history-belief

Tickets must be implemented in this order. Generated from intra-batch dependency analysis.
`implement-epic` reads this file to override alphabetical order.

tracking_doc: docs/plans/rpg_design_roadmap/rpg_m5_memory_reputation_epic.md

## Order

1. TCK-20260905-CHRONICLE-FIDELITY-DRIFT  (no deps in this batch — independent sibling of idea 57, per this epic's own re-confirmed "alongside" resolution)
2. TCK-20260905-FAME-DERIVER-LEGEND-FACT  (no deps in this batch — independent of idea 62; idea 63 hard-blocks on this one)
3. TCK-20260905-BELIEF-INSTITUTION-DESIGN  (depends on: TCK-20260905-FAME-DERIVER-LEGEND-FACT — HARD dependency, not a hedge: idea 63 must consume idea 57's actual shipped FameState/LegendFact shape, not an assumed one)

## Why This Order Matters

Idea 62 (CHRONICLE-FIDELITY-DRIFT) and idea 57 (FAME-DERIVER-LEGEND-FACT) are independent siblings
that both read Chronicle's raw output directly — neither needs the other's output as an input, per
this epic's own investigation correcting the epic doc's original "idea 62 as mandatory upstream
transform" claim (infeasible against the already-shipped `CultureDeriver`). They are listed in this
order for no technical reason beyond simplicity of implementation, and could be swapped.

Idea 63 (BELIEF-INSTITUTION-DESIGN) is different: its own atlas card names idea 57's fame substrate
as a real prerequisite, and no ticket for idea 57 existed anywhere before this epic. Idea 63's
Implement phase must not start until idea 57 is confirmed DONE and its real shipped shape is
re-verified — this is a hard block, not a sequencing preference.

Re-run `/implement-epic` with the same folder after any gate failure — already-done tickets are
skipped automatically.
