---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261018-PHASE19-OFF-MODE-RUNTIME-CHECK
phase: open
date: 2026-10-18
tags: [testing, architecture, observability]
---

# TCK-20261018-PHASE19-OFF-MODE-RUNTIME-CHECK

## Title
A runtime test that an OFF-mode kernel imports none of the four heavy observability modules the phase19 import-linter ignores rely on

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Filed by codebase per owner decision on #547 (2026-10-18, "Accept gap + follow-up"); owned by testing-planner. The test lives under `tests/architecture/`, which `route.py` shows as split rpg/testing, so it is testing's to implement.

The import-linter contract `engine and the three hot observability modules do not import the heavy analyzers (phase19)` ignores four edges from `src/engine/kernel.py`. rpg-planner allowed them on #547 (decision (a)) on a condition: every edge is a function-local import inside an `obs_mode != ObservabilityMode.OFF` branch, so an OFF-mode kernel imports none of the four modules, and an edge that moves out of the guard becomes a violation. Nothing enforces that condition today: `tests/architecture/test_phase19_observability_boundaries.py` is a static scan that never matches `src.observability...` and has no notion of OFF mode. Until this ticket lands the condition is UNENFORCED (the `importlinter.toml` phase19 comment says so).

## Scope
A runtime test, in a FRESH subprocess interpreter, that:
1. builds a `Kernel` with `ObservabilityMode.OFF` from the compiled `sandbox_world`, runs one `tick_once` and `shutdown`;
2. asserts that none of `src.observability.reporting.artifact_repository`, `src.observability.reporting.metric_recorder`, `src.observability.cognition.recorder` or `src.observability.cognition.decision_trace_writer` is in `sys.modules`.

Parity proof (testing condition 2), two parts:
- an injected unguarded top-level import of one of the four in `kernel.py` (in a scratch copy, never in the repo) makes the test fail;
- a control run with observability ON shows the four modules DO load, so the test can see them.

## Out of Scope
- Adding or widening any `ignore_imports` entry in `codebase/structure/importlinter.toml`.
- Editing `src/`.
- Changing `test_phase19_observability_boundaries.py` beyond what testing decides (it stays as it is unless testing chooses otherwise).

## Acceptance Criteria
- The test exists under `tests/architecture/`, runs in a fresh interpreter, and passes on `main`.
- The injected-import parity run fails the test; the ON-mode control run loads all four modules.
- Codebase follow-on, after the test lands: update the `importlinter.toml` phase19 comment to name the test (codebase-implementer, one small commit).

## Related Tickets
- TCK-20261005-IMPORT-LINTER-FLIP-AND-TEST-RETIREMENT
- TCK-20261004-IMPORT-LINTER-ADOPTION

## Related Docs
- docs/plans/codebase_health/handoffs/handoff_to_testing.md
- docs/plans/codebase_health/handoffs/handoff_to_rpg.md
- codebase/structure/importlinter.toml (phase19 contract)
- #547 (rpg's (a) answer; owner decision 2026-10-18)

## Related Stored Artifacts
None.

## Related Code Areas
- tests/architecture/test_phase19_observability_boundaries.py
- src/engine/kernel.py (function-local imports behind the OFF guard)
- codebase/structure/importlinter.toml

## Assumptions / Open Questions
- Owner: testing-planner (implementer: testing-implementer). Filed by codebase, not by testing.
- Whether the new test replaces the static phase19 hot-path test or sits beside it is testing's call.
- The kernel line numbers in the toml comments drift; the test must not depend on them.

## Implementation Notes
Not started.

## Test Summary
Not started.

## Files Changed
None yet.

## Completion Summary
Not started.
