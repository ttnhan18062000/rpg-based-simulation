---
status: historical
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20261014-UNAUDITED-RUNS-DEPEND-ON-HOST-SPEED-THROUGH-PHASE-BUDGETS-EVEN-WITH-THE-PINNED-NORMAL-GOVERNOR
artifact_type: test_plan
tags: []
---

# test_plan — TCK-20261014-UNAUDITED-RUNS-DEPEND-ON-HOST-SPEED-THROUGH-PHASE-BUDGETS-EVEN-WITH-THE-PINNED-NORMAL-GOVERNOR

Proposed, not built: a test that runs the same seed twice in one process under an artificial sleep in a phase (or with the phase-cost signal forced above 15 ms) and asserts equal per-tick hashes for a kernel built with the shared PinnedNormalGovernor. It fails today.
