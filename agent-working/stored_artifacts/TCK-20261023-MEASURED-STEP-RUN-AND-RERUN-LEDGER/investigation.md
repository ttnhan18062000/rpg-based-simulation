---
status: historical
layer: testing
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261023-MEASURED-STEP-RUN-AND-RERUN-LEDGER
phase: done
date: 2026-10-26
tags: [testing, performance]
---

# TCK-20261023-MEASURED-STEP-RUN-AND-RERUN-LEDGER: investigation

## Findings
- `rpg_gate_harness.run_matrix` already writes per-run `wall_seconds` and `peak_rss_mb` to `<doc>.cost.json` and into `matrix.json["runs"]`; the ledger row reuses those values, so no measurement changes.
- The harness never raises for a bad run (a crash becomes a `no-data` document), so "a failed invocation" has two shapes: a matrix with `no-data` runs (outcome ERROR naming them) and an exception out of `_run_matrix` (ERROR, re-raised) or an interrupt (KILLED, re-raised). `main()` returns 0 whatever the ledger does.
- The harness has no cache, so every gate run entry is `cached: false`.
- `data/ledgers/` was not git-ignored; it is added next to `data/runs/` in `.gitignore` (the ticket's assumption).
- Test trap: every `run_matrix` call now writes a row, so the harness test file sets `RUN_LEDGER_PATH` to a tmp path in an autouse fixture; other callers of `run_matrix` are only the CLI.

## Schema additions agreed with rpg-planner (2026-10-26)
rpg-planner asked, on reading the schema, for `mode` (what a PASS means: paired `step` / `neutral` / `report_only`, gate `gate`) and `workers` (the `--jobs` parallelism the per-arm wall time depends on). Both are required row-level fields in v1, validated per tool. Neutral IDENTICAL maps to PASS and DIFFERENT to STOP (the differing keys in `outcome_detail`); `NonAuditRunError` maps to REFUSED; arm `self` is paired's base-vs-base repeat, never cached. testing-planner is told, since this widens Scope 2.

## Decisions
1. `from_json` is strict (unknown/missing field, wrong type, naming the field); a started row must have both `outcome` and `ended_at` null, an end row neither.
2. `append_row` uses one `O_APPEND` write per line so two processes do not interleave; every failure is caught and warned.
3. The summary counts the executed runs for wall time and RSS (cached runs are counted separately and carry no cost), treats a started row without an end row as KILLED, and reports lines it could not read instead of failing.
