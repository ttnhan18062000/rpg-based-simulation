---
status: historical
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20261014-UNAUDITED-RUNS-DEPEND-ON-HOST-SPEED-THROUGH-PHASE-BUDGETS-EVEN-WITH-THE-PINNED-NORMAL-GOVERNOR
phase: done
date: 2026-10-14
tags: []
---

# TCK-20261014-UNAUDITED-RUNS-DEPEND-ON-HOST-SPEED-THROUGH-PHASE-BUDGETS-EVEN-WITH-THE-PINNED-NORMAL-GOVERNOR

## Title
Unaudited runs depend on host speed through the phase budgets even with the pinned NORMAL governor (investigation; names the source and proposes a fix).

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
rpg-planner: the same seed gave different hashes (crowded_frontier base against base; frontier a950... against 75d4... under PYTHONHASHSEED=0). Separate hash-seed order from wall-clock, bisect to the first diverging tick, name the source with file:line, propose a fix, and fix nothing before the planner has seen it.

## Scope
- PYTHONHASHSEED sweep, same seed under load, normal against audit_mode, bisect to the first diverging tick and the entity fields.
- Find the code, confirm by pinning it, check it is old on b396080cc, and list who is affected.

## Out of Scope
- Any code change (this ticket proposes one).

## Acceptance Criteria
- The source is named with file:line, the evidence is reproducible, and a fix is proposed.

## Related Tickets
PERF-D1 (signal contract); TCK-20261009-PINNED-NORMAL-GOVERNOR-SHARED-TEST-HELPER.

## Related Docs
None.

## Related Stored Artifacts
agent-working/stored_artifacts/TCK-20261014-UNAUDITED-RUNS-DEPEND-ON-HOST-SPEED-THROUGH-PHASE-BUDGETS-EVEN-WITH-THE-PINNED-NORMAL-GOVERNOR/ (plan, investigation, test_plan).

## Related Code Areas
src/engine/phase_governor.py; src/engine/governor.py; tests/helpers/kernel_pinning.py; src/engine/signal_source.py.

## Assumptions / Open Questions
Whether the performance owner wants CANONICAL as the default for non-live runs (option 3 in the investigation).

## Implementation Notes
No code changed. The investigation holds a self-contained repro.

## Test Summary
Four experiments recorded in the investigation (hash-seed sweep, normal against audit, phase budgets pinned, load-induced divergence).

## Files Changed
The ticket and its stored artifacts only.

## Completion Summary
Source: `PhaseBudgetGovernor.evaluate` (src/engine/phase_governor.py:107-143) turns measured per-phase milliseconds into scan policy and budgets; `PinnedNormalGovernor` does not pin it. audit_mode removes it. Proposed: measurements use audit_mode; the helper pins phase budgets; CANONICAL as default is a separate decision.
