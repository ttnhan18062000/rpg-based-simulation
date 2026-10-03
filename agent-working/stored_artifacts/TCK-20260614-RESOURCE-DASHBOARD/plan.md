---
ticket_id: TCK-20260614-RESOURCE-DASHBOARD
date: 2026-06-14
---

# Plan: TCK-20260614-RESOURCE-DASHBOARD

## Step 1 — Add Kernel.resource_snapshot()
- Collects pressure_report() from _event_recorder and _replay
- Per-subsystem errors swallowed (advisory); returns list of SubsystemPressureReport

## Step 2 — Create src/cli/diagnostics.py
- `format_table(reports)` — fixed-width, no dependencies
- `format_json(reports)` — json.dumps
- `has_degraded(reports)` — any DEGRADED → True
- `run_diagnostics_resources(fmt, run_id, kernel, out)` — main entry, returns exit code
- `_collect_from_kernel(kernel)` — calls kernel.resource_snapshot()
- `_collect_offline(run_id)` — best-effort from RunArtifactRepository

## Step 3 — Wire into src/cli/entry.py
- `diagnostics` subcommand with `resources` sub-subcommand
- `--format table|json`, `--run-id`
- Dispatch calls `run_diagnostics_resources()`, `sys.exit(code)`

## Step 4 — Tests (18 tests in test_diagnostics_resources.py)
- Table format (5), JSON format (3), has_degraded (3), run_diagnostics_resources (5),
  Kernel.resource_snapshot() integration (2)

## Files Changed
- `src/engine/kernel.py` — resource_snapshot()
- `src/cli/diagnostics.py` (new)
- `src/cli/entry.py` — diagnostics subcommand
- `tests/unit/cli/test_diagnostics_resources.py` (new)
- `docs/parity_ledger/infrastructure.yaml` — INFRA-201 added
