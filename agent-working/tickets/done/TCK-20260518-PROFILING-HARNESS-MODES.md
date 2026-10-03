---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260518-PROFILING-HARNESS-MODES
phase: done
date: 2026-05-18
tags: [profiling, harness, modes]
---

# TCK-20260518-PROFILING-HARNESS-MODES

## Title
Profiling Harness Modes (Pure, Runtime, Audit) and Report Flag Inclusion

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Implement profiling harness modes (pure, runtime, audit) in `scripts/profile_engine.py` to isolate compute performance from replay serialization and frame pacing, ensure generated reports include the flags used, and prevent unverified claims of GC/memory stability without explicit RSS/GC metrics.

## Scope
- Updated `scripts/profile_engine.py` to support `--mode` with `pure`, `runtime`, and `audit` options.
- Set appropriate `Kernel` flags based on the selected mode:
  - `pure`: `no_replay=True`, `no_frame_pacing=True`, `audit_mode=False`
  - `runtime`: `no_replay=False`, `no_frame_pacing=False`, `audit_mode=False`
  - `audit`: `no_replay=False`, `no_frame_pacing=True`, `audit_mode=True`
- Updated naming of output files to include the mode (e.g., `f"{scenario_name}_{entity_count}_{mode}.prof"` and `.txt`).
- Generated a summary markdown report (`report.md`) that explicitly lists the mode and flags used, and does not claim GC/memory resilience without explicit RSS/GC measurements.
- Created unit test suite `tests/unit/perf/test_profiling_harness_modes.py` verifying all criteria.

## Out of Scope
- Modifying `Kernel` or `BenchHarness` core logic.

## Acceptance Criteria
- [x] Pure profile excludes replay and frame pacing.
- [x] Runtime profile is labeled separately.
- [x] Audit profile is labeled separately.
- [x] Report includes flags used.
- [x] Report cannot claim GC/memory stability without GC/RSS data.

## Related Tickets
- TCK-20260517-PERF-HARDENING

## Related Docs
- perf_test_plan.md

## Related Stored Artifacts
- `stored_artifacts/TCK-20260518-PROFILING-HARNESS-MODES/`

## Related Code Areas
- `scripts/profile_engine.py`

## Assumptions / Open Questions
- None

## Implementation Notes
- Enhanced `ProfilingHarness.run_scenario` to accept `mode` string, mapping directly to rigorous flag configurations for `Kernel`.
- Ensured generated text reports and `report.md` preserve complete traceability of runtime flags.

## Test Summary
- `pytest tests/unit/perf/test_profiling_harness_modes.py`: 5/5 passed in 1.13s.
- `pytest tests/unit/ -m "not slow"`: 797/797 passed in 13.98s.

## Files Changed
- `scripts/profile_engine.py`
- `tests/unit/perf/test_profiling_harness_modes.py`

## Completion Summary
- Successfully integrated profiling harness isolation modes, achieving clean separation of pure computational cost from observational/pacing overhead.
