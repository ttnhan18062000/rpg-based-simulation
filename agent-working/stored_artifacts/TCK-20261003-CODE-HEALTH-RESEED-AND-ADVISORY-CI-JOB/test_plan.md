---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261003-CODE-HEALTH-RESEED-AND-ADVISORY-CI-JOB
artifact_type: test_plan
tags: [delivery]
---

# Test Plan — TCK-20261003-CODE-HEALTH-RESEED-AND-ADVISORY-CI-JOB

All runs one at a time under `systemd-run --user --scope -q -p MemoryMax=2G -p MemorySwapMax=0`, main `.venv` on PATH, exit status checked separately.

- New unit tests: `ratchet.format_summary` (pass, changed-first ordering, cap, empty changed list), CLI `--summary-for/--summary-out` and unchanged exit codes (fixture registry and scan, as `test_code_health_ratchet_registry.py` does), reseed carry-over of `reviewed`/`retiring_ticket`/`added_date`.
- Static: job exists, name ends "(advisory)", `continue-on-error` on job and check step, syncs `lint`, no pip.
- Existing: `tests/static`, `tests/tools/test_ci_workflow_test_coverage.py`, `tests/tools/test_code_health_*.py`, `tests/tools/test_codebase_health_snapshot_craft.py` (reads the registry; row counts change), `test_no_tracked_old_root_files.py`, `test_generate_registry.py`.
- Real data: `scan` then `seed --force --from`, `validate`, `check --from` exit 0; counts before/after recorded.
- Failure modes: missing tool (exit 2) still produces no workflow failure in CI (advisory); empty changed-files list.
- PR run (after owner push): job green, summary visible, wall time recorded; the other jobs unchanged.
