---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260413-INFRA-LOG-ROTATION
phase: done
date: 2026-04-13
tags: [infra, log, rotation]
---

# TCK-20260413-INFRA-LOG-ROTATION

## Title
Implement Automated Log Rotation for HeadlessRunner

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Implement a mechanism to automatically prune old simulation artifacts (replay logs, cognition graphs) from the `logs/` directory to prevent disk clutter during intensive testing.

## Scope
-   Add rotation configuration to `SimulationConfig`.
-   Implement `_rotate_logs` logic in `HeadlessRunner`.
-   Update `test_harness.py` CLI to support the new mechanism.
-   Verify with integration tests.

## Out of Scope
-   Rotation for standard system logs (handled by OS/external tools).
-   Rotation for production database snapshots.

## Acceptance Criteria
-   `HeadlessRunner` maintains at most N runs (default 10) per output directory.
-   Rotation happens automatically at the start of a simulation run.
-   Oldest runs are pruned based on creation time.
-   Mechanism is configurable via `SimulationConfig` and CLI.

## Related Tickets
-   None

## Related Docs
-   [architecture.md](file:///home/vboxuser/Work/rpg-based-simulation/docs/architecture.md)

## Related Stored Artifacts
-   None

## Related Code Areas
-   `src/config.py`
-   `src/testing/headless_regression_runner.py`
-   `scripts/test_harness.py`

## Assumptions / Open Questions
-   Assumed `ctime` is a reliable proxy for run order.

## Implementation Notes
-   Implemented `_rotate_logs` as a private method in `HeadlessRunner`.
-   Default limit set to 10 to balance history vs. disk space.

## Test Summary
-   `tests/integration/test_log_rotation.py`: PASSED (verified limit enforcement).
-   Manual verification via `scripts/test_harness.py --max-runs 2`: PASSED.

## Files Changed
-   `src/config.py`
-   `src/testing/headless_regression_runner.py`
-   `scripts/test_harness.py`

## Completion Summary
-   The simulation infrastructure now maintains a lean footprint. Automated tests and manual runs now rotate their artifacts, keeping only the 10 most recent results by default. Integrated CLI support allows for ad-hoc overrides.
