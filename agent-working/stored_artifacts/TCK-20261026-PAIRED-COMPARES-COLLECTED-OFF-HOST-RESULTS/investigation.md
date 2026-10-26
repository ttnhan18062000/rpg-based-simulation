---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261026-PAIRED-COMPARES-COLLECTED-OFF-HOST-RESULTS
artifact_type: investigation
tags: [testing, performance, determinism]
---

# Investigation

- `paired.py` main: `prepare_tree` (git rev-parse, archive) then `run_arm` (executes missing arms, unlinks a repeat before re-running), then `refuse_non_audit`, the self-check, the report. `result_path` = `<cache>/results/<sha12>-<child hash8>-<ticks>[-repeat]/<world>_<seed>.json`; `child_hash` = sha256 of the tool checkout's `arm_child.py`, so the aggregate job and the matrix jobs must share the tool commit.
- `--jobs` has a default of 2, so an explicit `--jobs` cannot be seen today; it needs a None default.
- The exit-code table: 0 report produced (STOP is in the table, not the code), 2 REFUSED (legacy flag without full self-check; non-byte-identical base repeat), neutral FAIL 1, `NonAuditRunError` raised. The verdict JSON adds a machine-readable outcome without changing those.
- Existing tests stage run dicts (`_run`) and never run the simulation; the new tests do the same.
- Open: the runner line is the only addition to the report, so "byte-identical table" is judged with that one line excluded; flagged to the planner.
