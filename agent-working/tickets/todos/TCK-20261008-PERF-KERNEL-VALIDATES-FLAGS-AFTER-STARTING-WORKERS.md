---
status: active
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20261008-PERF-KERNEL-VALIDATES-FLAGS-AFTER-STARTING-WORKERS
phase: open
date: 2026-10-08
tags: [performance, engine]
---

# TCK-20261008-PERF-KERNEL-VALIDATES-FLAGS-AFTER-STARTING-WORKERS

## Title
Kernel.__init__ validates its flags only after starting the event-recorder and trace-writer workers, so a Kernel that rejects a forbidden flag leaks background threads

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P3

## Request Summary
Found by perf-implementer during `TCK-20261006-PERF-OPERATIONAL-FLAGS-MATRIX-DRIFT`, and verified by
perf-planner on `main` `28d0af111`.

`Kernel.__init__` (`src/engine/kernel.py`) builds the `EventRecorder` at about line 264. Its comment at about
line 308 notes two background drain workers: `EventRecorder._worker` and `DecisionTraceWriter._worker`. Only
later, at about line 321, does it call `self.validate(flags)`, which raises `ConfigValidationError` for a
forbidden flag (`FORCE_NORMAL`, `BYPASS_GOVERNOR`, `DISABLE_RESOURCE_CEILINGS`). The constructor raises, nothing
holds the half-built Kernel, and nobody stops its workers. The thread-leak guard counted 6 leaked threads when the
rejection was tested through `Kernel(...)`. The flags-matrix tests therefore call
`ProfileValidator.validate_flags` directly.

Impact: low in production, since a forbidden flag is a configuration error that aborts the run. But every
rejected construction (tests, API engine creation with bad flags, a retry loop) leaves workers running, and the
contract tests can't exercise the real constructor path.

**Gate:** `kernel.py` was released to the RPG-core lanes when Phase A merged (#448). This needs a perf window
that names `kernel.py` again, or routing to the RPG side. It's a small, self-contained ordering fix.

## Scope
1. Validate flags (and anything else that can reject the construction) **before** starting any worker or
   background thread in `Kernel.__init__`. If an ordering dependency prevents that, stop every started worker
   on the error path (`try`/`except`, then a shutdown of whatever was started, then re-raise).
2. A test that constructs `Kernel(...)` with each forbidden flag, asserts `ConfigValidationError`, and asserts
   no leaked thread (the existing thread-leak guard). It must fail on `main` today.
3. Move the flags-matrix tests that use `ProfileValidator.validate_flags` directly to the real constructor
   path, or add the constructor-path test beside them.

## Out of Scope
- Changing which flags are forbidden.
- Other construction errors that already happen before the workers start.

## Acceptance Criteria
1. Each forbidden flag raises through `Kernel(...)` with no leaked thread. The test fails on `main` before the
   fix.
2. Normal construction order and behaviour are unchanged (Live golden test and kernel unit tests pass).
3. `uv run make code-health` and `uv run make typecheck-py` report no new or worse finding.
   `Kernel.__init__` is at its function-length ceiling, so extract a helper rather than fold lines.

## Related Tickets
- `TCK-20261006-PERF-OPERATIONAL-FLAGS-MATRIX-DRIFT` (done; where this was found; INFRA-428)
- `TCK-20261006-PERF-GOVERNOR-WALL-CLOCK-INPUTS-DETERMINISTIC-PROXY` (done; Phase A, which last touched `Kernel.__init__`)

## Related Docs
- `docs/engine/matrices/observability_operational_controls_matrix.md`

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261006-PERF-OPERATIONAL-FLAGS-MATRIX-DRIFT/`

## Related Code Areas
- `src/engine/kernel.py` (`__init__`, `validate`), `src/observability/event_recorder.py`

## Assumptions / Open Questions
- Whether the RPG side or perf fixes it depends on who holds `kernel.py` when it's scheduled. Ask in the
  handoff doc.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
