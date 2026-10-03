# Implementation Sequence — world-rendering-core

Tickets must be implemented in this order. Generated from intra-batch dependency analysis
(cross-referencing each ticket's own `## Related Tickets` section against the other 8 tickets in
this batch). `implement-epic` reads this file to override alphabetical order.

## Order

1. TCK-20260821-WORLD-RENDER-CORE  (no deps in this batch)
2. TCK-20260821-VISUAL-CONNECTIVITY-METRIC  (depends on: TCK-20260821-WORLD-RENDER-CORE)
3. TCK-20260821-VISUAL-DENSITY-METRIC  (depends on: TCK-20260821-WORLD-RENDER-CORE)
4. TCK-20260821-VISUAL-SHAPE-METRIC  (depends on: TCK-20260821-WORLD-RENDER-CORE)
5. TCK-20260821-VISUAL-VARIANTS-METRIC  (depends on: TCK-20260821-WORLD-RENDER-CORE)
6. TCK-20260821-VISUAL-GRADE-SCORER  (depends on: TCK-20260821-VISUAL-SHAPE-METRIC, TCK-20260821-VISUAL-DENSITY-METRIC, TCK-20260821-VISUAL-VARIANTS-METRIC, TCK-20260821-VISUAL-CONNECTIVITY-METRIC)
7. TCK-20260821-VISUAL-AGENT-REVIEW  (depends on: TCK-20260821-WORLD-RENDER-CORE, TCK-20260821-VISUAL-GRADE-SCORER)
8. TCK-20260821-VISUAL-QUALITY-CALIBRATION  (depends on: TCK-20260821-VISUAL-GRADE-SCORER)
9. TCK-20260821-VISUAL-QUALITY-DOCS  (depends on: TCK-20260821-VISUAL-GRADE-SCORER, TCK-20260821-VISUAL-QUALITY-CALIBRATION, TCK-20260821-VISUAL-AGENT-REVIEW)

## Why This Order Matters

TCK-20260821-WORLD-RENDER-CORE is the load-bearing prerequisite: it's the only ticket with no
in-batch dependency, and every other ticket in this batch either directly or transitively needs
its renderer/data-access layer to exist first. The four metric-family tickets (Shape, Density,
Variants, Connectivity) are independent of each other — any order among positions 2-5 is fine —
but all four must land before TCK-20260821-VISUAL-GRADE-SCORER, since the grade-band scorer
consumes their real outputs rather than being designed against a stub interface.
TCK-20260821-VISUAL-AGENT-REVIEW and TCK-20260821-VISUAL-QUALITY-CALIBRATION both consume the
scorer's real Tier-0 output and threshold-config shape, so both wait on it.
TCK-20260821-VISUAL-QUALITY-DOCS is last by design — it documents the finished system's real
implemented contract (scoring rules, calibration output, agent-review pipeline), not a speculative
design, so writing it before its three dependencies land would produce docs describing behavior
that doesn't exist yet.

Running alphabetically would attempt several tickets before their real prerequisites are in place.
Re-run `/implement-epic` with the same folder after any gate failure — already-done tickets are
skipped automatically.
