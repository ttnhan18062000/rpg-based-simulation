---
status: historical
layer: ai
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261004-DATA-RUNS-CLEAN-NOT-SESSION-SCOPED
date: 2026-10-05
tags: [ai, process-improvement]
---

# Plan: TCK-20261004-DATA-RUNS-CLEAN-NOT-SESSION-SCOPED

1. `clean_data_runs_early` reports and deletes nothing; `check_data_runs_clean` leftovers become `WARN`.
2. Opt-in `delete_data_run_paths` and `--clean-data-runs --path` with refusal rules.
3. Call site log branch for `REPORTED`; update docs; revise the tests whose meaning changed.
Scope guard: no PID-liveness ownership, no CLAUDE.md edit, no change to where run data is written.
