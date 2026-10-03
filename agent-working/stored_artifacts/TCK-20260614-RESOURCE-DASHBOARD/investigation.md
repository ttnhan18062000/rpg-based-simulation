---
ticket_id: TCK-20260614-RESOURCE-DASHBOARD
date: 2026-06-14
---

# Investigation: TCK-20260614-RESOURCE-DASHBOARD

## Subsystems with pressure_report()

Only 3 subsystems implement `pressure_report()`:
1. `EventRecorder.pressure_report()` — INFRA-194 (queue occupancy)
2. `ReplayManager.pressure_report()` — INFRA-198 (inflight flushes)
3. `BudgetedCanonicalHasher.pressure_report()` — INFRA-196 (hash call rate)

`BudgetedCanonicalHasher` is not kernel-owned (it's a wrapper class); no slot for it
on Kernel. `resource_snapshot()` collects from event_recorder and replay only.
The hasher can be added in a future ticket if needed.

## CLI Pattern

`entry.py` uses `argparse` with `add_subparsers(dest="command")`. The `cognition`
subcommand demonstrates nested sub-subcommands — the same pattern is used for
`diagnostics resources`. The dispatch block at the bottom handles each `args.command`.

## Output Format

Fixed-width string formatting (no external dependencies). Columns:
  `Subsystem` (18), `Usage` (18), `State` (10).

JSON: `json.dumps(list_of_dicts, indent=2)`.

## Offline Mode

`RunArtifactRepository` lists completed runs. Best-effort — if no runs found, a
notice is printed and exit code 0 is returned (no DEGRADED data = not degraded).
