---
status: done
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260614-RESOURCE-DASHBOARD
phase: done
date: 2026-06-14
tags: [resource-safety, dashboard, diagnostics, observability, performance]
---

# TCK-20260614-RESOURCE-DASHBOARD

## Title
Add runtime resource dashboard CLI — per-subsystem memory, queue, and pressure visibility

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Added `python -m src diagnostics resources [--format table|json] [--run-id <id>]`
CLI command. Collects `SubsystemPressureReport` from all live subsystems via
`Kernel.resource_snapshot()`, formats as table or JSON, and exits with code 1
if any subsystem is DEGRADED (enables CI gating).

## Scope
- `Kernel.resource_snapshot()` — collects pressure_report() from event_recorder and replay
- `src/cli/diagnostics.py` — format_table, format_json, run_diagnostics_resources
- `src/cli/entry.py` — diagnostics resources subcommand wired
- INFRA-201 parity entry

## Out of Scope
- Web UI or long-running server endpoint
- Real-time streaming
- Automatic remediation
- BudgetedCanonicalHasher in resource_snapshot (not kernel-owned)

## Acceptance Criteria
- [x] `python -m src diagnostics resources` prints subsystem table
- [x] `--format json` outputs valid JSON
- [x] Exit code 0 on OK/WARN, 1 on DEGRADED
- [x] `Kernel.resource_snapshot()` returns advisory list of SubsystemPressureReport
- [x] 18 tests pass

## Related Tickets
- TCK-20260614-RESOURCE-SAFETY-EPIC (parent)
- TCK-20260614-RESOURCE-BUDGET-GATE (provides pressure_report() per subsystem)
- TCK-20260614-REPLAY-BACKPRESSURE (replay.pressure_report() in snapshot)
- TCK-20260614-OBS-BACKPRESSURE (observability.pressure_report() in snapshot)

## Related Docs
- `docs/parity_ledger/infrastructure.yaml` — INFRA-201

## Related Stored Artifacts
- `stored_artifacts/TCK-20260614-RESOURCE-DASHBOARD/`

## Related Code Areas
- `src/cli/diagnostics.py`
- `src/cli/entry.py`
- `src/engine/kernel.py` — resource_snapshot()
- `tests/unit/cli/test_diagnostics_resources.py`

## Assumptions / Open Questions
- `BudgetedCanonicalHasher` is not kernel-owned (no slot); excluded from snapshot for now.
- Offline mode is best-effort; no persisted pressure snapshot format defined in this ticket.

## Implementation Notes
- Fixed-width table uses no external dependencies (pure string formatting).
- `resource_snapshot()` swallows per-subsystem errors — advisory, not authoritative.

## Test Summary
18 tests in `tests/unit/cli/test_diagnostics_resources.py`. All pass.

## Files Changed
- `src/engine/kernel.py` — resource_snapshot() method
- `src/cli/diagnostics.py` — new CLI module
- `src/cli/entry.py` — diagnostics resources subcommand
- `tests/unit/cli/test_diagnostics_resources.py` — new, 18 tests
- `docs/parity_ledger/infrastructure.yaml` — INFRA-201 added

## Completion Summary
`diagnostics resources` CLI command wired end-to-end. `Kernel.resource_snapshot()` aggregates
observability and replay pressure reports. Table and JSON output formats supported. Exit code 1
on any DEGRADED subsystem. 18 tests pass. INFRA-201 added to parity ledger.
