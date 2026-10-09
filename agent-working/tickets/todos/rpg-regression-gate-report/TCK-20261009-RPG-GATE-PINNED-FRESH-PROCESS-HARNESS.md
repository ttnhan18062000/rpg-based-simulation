---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261009-RPG-GATE-PINNED-FRESH-PROCESS-HARNESS
phase: open
date: 2026-10-09
tags: [testing, regression, determinism]
---

# TCK-20261009-RPG-GATE-PINNED-FRESH-PROCESS-HARNESS

## Title
A pinned harness runs each (world, seed) of the rpg gate in a fresh process and collects the metric documents

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Child 3 of TCK-20261009-RPG-GATE-REPORT-TESTING-INFRA-EPIC. The report is only meaningful if every run is reproducible and isolated. Two findings from 2026-10-09: process-global state leaks between tests in one process (the strict xfail, the CONFLICT-04 xdist red), and tests are governor-mode-sensitive. So: a fresh process per (world, seed), with everything pinned.

## Scope
1. A runner that reads rpg's gate config (worlds, seeds, ticks; rpg-owned content) and, for each (world, seed), starts a fresh Python process. Inside it: compile the world, build a Kernel with `PinnedNormalGovernor`, `LocalSequentialExecutor`, `audit_mode=True` and no tick budget; run the ticks; call rpg's metric module on the typed records; write the metric document (the epic's contract).
2. The harness hash: a stable hash of the harness code, the pin settings and the config, recorded in every document (it is what the baseline staleness uses).
3. Parallelism across processes, with a bounded worker count. Failures in one run do not stop the others; a crashed run yields a `no-data` document with the error.
4. Run directories go under `data/runs/` with a gate prefix and are cleaned by run id (CLAUDE.md cleanup rule).
5. Measure and record the wall time and peak memory for the full v1 matrix on CI-class hardware. Child 5 sizes the matrix from it.

## Out of Scope
- The metric computation (rpg), evaluation and states (child 4).

## Acceptance Criteria
1. The same (SHA, world, seed) run twice gives byte-identical metric documents (a determinism test on a small world and few ticks).
2. A deliberately leaking stand-in (a module global mutated in run 1) does not affect run 2. This proves the process isolation.
3. A crashing run gives `no-data` with the error, and the others complete.
4. Cost measured and recorded in the ticket.
5. Standard close.

## Related Tickets
- TCK-20261009-RPG-GATE-REPORT-TESTING-INFRA-EPIC; depends on rpg's metric computation module (rpg-planner's ticket) for the real run. Until then a stub metric module that satisfies the contract.

## Related Docs
None.

## Related Stored Artifacts
None.

## Related Code Areas
- `tests/helpers/kernel_pinning.py`, `src/engine/kernel.py` (read only), `src/engine/executor.py` (read only), the new module under `tools/test_architecture/`

## Assumptions / Open Questions
- If rpg's metric module isn't ready, build and test against a stub that implements the contract; the real wiring is the last step.

## Implementation Notes
(implementer)

## Test Summary
(implementer)

## Files Changed
(implementer)

## Completion Summary
(implementer)
