---
status: historical
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20261014-UNAUDITED-RUNS-DEPEND-ON-HOST-SPEED-THROUGH-PHASE-BUDGETS-EVEN-WITH-THE-PINNED-NORMAL-GOVERNOR
artifact_type: plan
tags: []
---

# plan — TCK-20261014-UNAUDITED-RUNS-DEPEND-ON-HOST-SPEED-THROUGH-PHASE-BUDGETS-EVEN-WITH-THE-PINNED-NORMAL-GOVERNOR

1. Separate the two candidate sources: hash-seed order versus wall-clock (PYTHONHASHSEED sweep, then same seed under load).
2. Bisect to the first diverging tick and entity fields; compare audit_mode against normal mode.
3. Find the code that turns measured time into different work; confirm by pinning it.
4. Report the source, evidence and a proposed fix. Fix nothing before rpg-planner has seen it.
