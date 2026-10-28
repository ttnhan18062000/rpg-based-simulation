---
status: historical
layer: testing
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261023-MEASURED-STEP-RUN-AND-RERUN-LEDGER
phase: done
date: 2026-10-26
tags: [testing, performance]
---

# TCK-20261023-MEASURED-STEP-RUN-AND-RERUN-LEDGER: plan

Files: tools/test_architecture/run_ledger.py (new), tools/test_architecture/rpg_gate_harness.py, .gitignore, docs/plans/test_architecture/reference/run_ledger.md (new), tests/unit/tools/test_run_ledger.py (new), tests/unit/tools/test_rpg_gate_harness.py.
1. run_ledger: dataclasses `RunEntry`, `Host`, `RunLedgerRow` with strict `from_json` / `to_json`; `append_row` (never raises), `begin` / `finish` (started row, end row), `read_rows`, `summarize`, `render_summary`, CLI `summary`.
2. Harness: `run_matrix` wraps the old body (`_run_matrix`) with `begin` / `finish`; `--step` and `--rerun-of` on its CLI.
3. `data/ledgers/` git-ignored. Reference doc. Tests with fakes only.
Scope guards: no CI gate, no upload, no change to what the harness measures, no paired.py edit (rpg writes it, testing reviews). AC map: AC1 row tests; AC2 harness tests; AC3 summary and pinned JSON; AC4 rpg's PR (open); AC5 no heavy run.
