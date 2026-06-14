---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260614-RESOURCE-DASHBOARD
phase: open
date: 2026-06-14
tags: [resource-safety, dashboard, diagnostics, observability, performance]
---

# TCK-20260614-RESOURCE-DASHBOARD

## Title
Add runtime resource dashboard CLI — per-subsystem memory, queue, and pressure visibility

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Without visibility into subsystem resource usage, memory pressure is invisible until the process crashes. Add a developer CLI (`python -m src diagnostics resources --run-id <id>`) that queries each subsystem's `pressure_report()` and prints a summary table. This makes future leak investigation faster and enables early human intervention before `MemoryError`.

## Scope
- Add CLI entry point: `python -m src diagnostics resources [--run-id <id>] [--format table|json]`
- Output table:
  ```
  Subsystem        Memory Estimate   Queue/Backlog   Status
  Certification    0.8 MB            3 artifacts     OK
  Replay           240 KB            2 pending       WARN
  Observability    1,200 events      80% queue       DEGRADED
  Cognition        380 snapshots     120 entities    WARN
  Hasher           42 full hashes    high CPU        WARN
  Workers          12 in-flight      4 active        OK
  ```
- Data sourced from `SubsystemPressureReport.pressure_report()` (implemented in TCK-20260614-RESOURCE-BUDGET-GATE)
- For offline use (no running kernel): read from last written `proof_index.json` and replay metrics if available
- JSON format (`--format json`) outputs raw `SubsystemPressureReport` list
- Add `src/cli/diagnostics.py` (or extend `src/cli/entry.py`) with `diagnostics resources` subcommand

## Out of Scope
- Web UI or long-running server endpoint
- Real-time streaming (one-shot snapshot only)
- Automatic remediation

## Acceptance Criteria
- `python -m src diagnostics resources` prints subsystem table without error when run against a completed run
- `--format json` outputs valid JSON with all subsystem reports
- Each row shows subsystem name, estimated usage, backlog/queue count, and status
- CLI exits with code 0 on OK/WARN, code 1 on any DEGRADED subsystem (enables CI gating)
- Tests: CLI integration test with mock kernel showing expected table rows

## Related Tickets
- TCK-20260614-RESOURCE-SAFETY-EPIC (parent)
- TCK-20260614-RESOURCE-BUDGET-GATE (must be done first — provides `pressure_report()` per subsystem)

## Related Docs
- `docs/engine/performance_contract.md`
- `memory_features.md` (Feature 4)

## Related Code Areas
- `src/cli/entry.py:222` — existing CLI entry point
- `src/engine/kernel.py:34` — `Kernel` owns subsystems with `pressure_report()`
- `src/certification/recorder.py` — proof_index.json for offline mode
- `src/config/optimization_profiles.py` — subsystem budget definitions

## Assumptions / Open Questions
- Whether to surface the dashboard as a `Kernel` method (`kernel.resource_snapshot()`) or have the CLI build it from individual subsystem handles — recommend kernel method for testability
- `--run-id` flag: if a live kernel is not running, parse from a saved snapshot file; define the snapshot format in this ticket

## Implementation Notes
- Table formatting: use Python `textwrap` or fixed-width string formatting; no external dependency
- Exit code 1 on DEGRADED enables `make check-resources` CI step

## Test Summary
- `tests/unit/cli/test_diagnostics_resources.py` (new):
  - `test_dashboard_table_contains_all_subsystems`
  - `test_dashboard_json_format_is_valid`
  - `test_dashboard_exits_1_on_degraded_subsystem`
  - `test_dashboard_offline_mode_reads_proof_index`
- Run: `pytest tests/unit/cli/ -v`

## Files Changed
_(filled after implementation)_

## Completion Summary
_(filled after implementation)_
