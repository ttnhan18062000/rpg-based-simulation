---
status: historical
layer: testing
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261023-MEASURED-STEP-RUN-AND-RERUN-LEDGER
phase: done
date: 2026-10-26
tags: [testing, performance]
---

# TCK-20261023-MEASURED-STEP-RUN-AND-RERUN-LEDGER: test_plan

tests/unit/tools/test_run_ledger.py (~60 cases): round trip of every outcome plus the started row and every mode; every field missing, an unknown field (top-level, run entry, host), wrong types, started/end consistency, rerun_of rules; append, path and env override, write failure warns and returns false, torn lines counted; begin/finish ids; KILLED from a started row with no end row (either order); summary per step from a fixture ledger, --step and --since filters, pinned JSON output and pinned text output.
tests/unit/tools/test_rpg_gate_harness.py (+6): one started row and one end row per `run_matrix` with a fake run; a no-data run is an ERROR row naming it; an exception writes ERROR and re-raises; an interrupt writes KILLED; the step label and rerun_of come from the caller; a ledger write failure leaves the matrix and the CLI exit code unchanged. An autouse fixture keeps the existing tests' rows out of the real ledger.
