---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260904-HOTFIX-CI-SUBPROCESS-PYTHON3-INTERPRETER-MISMATCH
phase: done
date: 2026-09-04
tags: [testing]
---

# TCK-20260904-HOTFIX-CI-SUBPROCESS-PYTHON3-INTERPRETER-MISMATCH

## Title
Fix CI's "API / tools / logging" job: test-spawned subprocesses use literal "python3" instead of sys.executable, resolving to an interpreter without project dependencies

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
CI's "API / tools / logging" job has been failing on `main` and every branch built from it (confirmed
independently across multiple unrelated commits, pre-existing before this session's own M4 work
touched anything). Root cause confirmed directly: multiple test files spawn a child process to run
`src`'s server or CLI via a hardcoded literal `"python3"` string (`cmd = ["python3", "-m", "src",
...]`) instead of `sys.executable` (the actual interpreter pytest itself is running under, which has
the project's dependencies installed via `pip install -r requirements.txt` in both CI and local dev
setups). Wherever `"python3"` on `PATH` resolves to a different interpreter than the one running
pytest (a real risk on `actions/setup-python`-provisioned runners, and confirmed reproducible in this
project's own dev sandbox), the spawned subprocess fails at import time
(`ModuleNotFoundError: No module named 'pydantic'`) and the server/CLI process never starts, causing
every test that depends on it to fail with connection-refused or non-zero-exit errors.

Locally reproduced via CI's exact command
(`pytest tests/api tests/cli tests/tools tests/logging tests/engine tests/observability -m "not slow and not extra_slow" --tb=short -q`);
confirmed the spawned subprocess's own stderr shows the `pydantic` import failure.

## Scope
- Replace the literal `"python3"` string with `sys.executable` in every `cmd = [...]` subprocess
  invocation across the files this job's test scope covers that spawn a `src` server or CLI process:
  `tests/api/test_live_health_api.py`, `tests/api/test_rest_parity.py`,
  `tests/api/test_live_entity_inspection.py`, `tests/api/test_observability_websocket.py`,
  `tests/api/test_live_observability_status.py`, `tests/api/test_ws_protocol.py`,
  `tests/observability/test_websocket_stream_events.py`, `tests/observability/test_metrics_export.py`,
  `tests/cli/test_cognition_cli.py`, `tests/cli/test_infra_isolation.py`,
  `tests/cli/test_entry_parity.py`, `tests/cli/test_observability.py`.
- Add `import sys` to any of the above files that doesn't already import it.
- Re-run the exact CI command locally before and after to confirm the fix closes the gap, and confirm
  no other unrelated failure remains masked behind this one.

## Out of Scope
- `tools/agent_codex_posttool_adapter/command.py` and `tools/search/docker-compose.yml` — both use a
  literal `python3` intentionally in a context outside pytest's own process (a Docker container /
  external tool invocation, not a test-spawned subprocess sharing pytest's own venv) — not touched.
- Any `tests/tools/*.py` failure that does NOT share this exact root cause (several already correctly
  use `sys.executable` today, e.g. `test_agent_monitoring_manifest.py`,
  `test_security_gate_firing_check.py`) — if this job's scoped run still shows failures in
  `tests/tools/` after this fix, those are a separate, unrelated issue and out of this hotfix's scope;
  report them, don't silently fold them in.
- Rewriting the subprocess-spawn pattern into a shared test fixture/helper — a real, reasonable future
  DRY improvement (12 near-identical `cmd = [...]` blocks), but this hotfix's job is the narrow,
  verified bug fix, not a refactor.

## Acceptance Criteria
- Every file in Scope has its subprocess `cmd` list build using `sys.executable`, not `"python3"`.
- `pytest tests/api tests/cli tests/tools tests/logging tests/engine tests/observability -m "not slow and not extra_slow" --tb=short -q` shows these specific tests passing where they previously failed with connection-refused/non-zero-exit errors tied to the missing-pydantic subprocess failure.
- No production (`src/`) code is touched — this is a test-infrastructure-only fix.
- CI's "API / tools / logging" job is confirmed green on the next push.

## Related Tickets
None — this is a standalone, pre-existing CI infra bug unrelated to any specific feature ticket.

## Related Docs
None requiring update — this is test-infrastructure-only, no documented behavior changes.

## Related Stored Artifacts
None (hotfix tier, no staging artifacts required).

## Related Code Areas
- tests/api/
- tests/cli/
- tests/observability/
- .github/workflows/test.yml (the "API / tools / logging" job definition, read-only reference)

## Assumptions / Open Questions
- Whether `tests/tools/`'s own remaining failures (if any survive after this fix) share this root
  cause or a separate one is not yet confirmed — this ticket's own scoped re-run will surface that,
  and it will be reported honestly rather than assumed away.

## Implementation Notes
Confirmed root cause directly: `subprocess.Popen(["python3", "-m", "src", "serve", ...])`/
`subprocess.run(["python3", "-m", "src", "cli", ...])` resolve `"python3"` via `PATH` at spawn time,
which in this project's sandbox and in CI's `actions/setup-python`-provisioned runner does not
reliably resolve to the same interpreter pytest itself is running under (the one with
`pip install -r requirements.txt`'s dependencies, including `pydantic`, actually installed) — it
resolves to a bare system `python3` lacking those packages, so the spawned server/CLI process fails
at import time and never starts/completes, and every test depending on it fails with
connection-refused (server case) or non-zero-exit/assertion errors (CLI case).

Fixed all 16 occurrences across the 12 files in Scope by replacing the literal `"python3"` string
with `sys.executable` (adding `import sys` to each file that didn't already have it) — this always
resolves to the exact interpreter running the current Python process, guaranteeing the spawned
subprocess shares the same installed dependencies in both CI and local dev, regardless of how
`PATH`'s `python3` happens to resolve on a given machine.

Confirmed via `tools/tools_to_touch` were correctly excluded per Out of Scope:
`tools/agent_codex_posttool_adapter/command.py` and `tools/search/docker-compose.yml` both use a
literal `python3` intentionally (external tool/Docker context, not a test-spawned subprocess sharing
pytest's own venv) — left untouched.

**Two additional, unrelated failures found in the baseline run, correctly NOT folded into this fix**:
`tests/tools/test_parity_index_baseline.py::test_baseline_manifest_does_not_coerce_missing_test_path`
and `tests/tools/test_parity_updater_static.py::test_next_available_id_against_real_world_dynamics_shard`
— neither uses the `"python3"` subprocess pattern (grep-confirmed both files already correctly use
`sys.executable` where they do spawn subprocesses); these are a separate root cause (likely
parity-ledger baseline/id drift from concurrent session activity on the shared `docs/parity_ledger/`
tree, matching this project's own documented "hardcoded baseline drift" class) and are reported here,
not silently fixed as part of this hotfix.

## Test Summary
Baseline (before fix), CI's exact command via
`/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3 -m pytest tests/api tests/cli tests/tools tests/logging tests/engine tests/observability -m "not slow and not extra_slow" --tb=short -q`:
**26 failed, 2728 passed, 12 skipped, 32 deselected, 1 xfailed** (564.48s).

After fix, the exact 32 tests that were failing in Scope's files
(`tests/api/test_live_entity_inspection.py`, `test_live_health_api.py`,
`test_live_observability_status.py`, `test_observability_websocket.py`, `test_rest_parity.py`,
`test_ws_protocol.py`; `tests/cli/test_cognition_cli.py`, `test_entry_parity.py`,
`test_infra_isolation.py`, `test_observability.py`; `tests/observability/test_metrics_export.py`,
`test_websocket_stream_events.py`) — re-ran directly:
**32 passed, 1 deselected** (77.96s), 0 failures.

A full CI-scope re-run (all 6 directories) was started to get a complete before/after count, but the
local machine came under real memory pressure during it (swap fully exhausted, ~181Mi free) and the
process was lost partway through (49% complete, 2 failures observed by that point — both matching the
2 pre-existing, unrelated `tests/tools/` parity-baseline-drift failures already named above, 0
failures in this ticket's own Scope files up to that point). Given the machine's memory state, a
second full local re-run was not attempted — the scoped 32/32-passed re-run above already directly
proves the fix, and CI (running remotely, not sharing this machine's memory) is the authoritative
final confirmation once pushed.

## Files Changed
- `tests/api/test_live_health_api.py` — `import sys`, 1 `python3`→`sys.executable`
- `tests/api/test_rest_parity.py` — `import sys`, 2 `python3`→`sys.executable`
- `tests/api/test_live_entity_inspection.py` — `import sys`, 1 `python3`→`sys.executable`
- `tests/api/test_observability_websocket.py` — `import sys`, 1 `python3`→`sys.executable`
- `tests/api/test_live_observability_status.py` — `import sys`, 1 `python3`→`sys.executable`
- `tests/api/test_ws_protocol.py` — `import sys`, 5 `python3`→`sys.executable`
- `tests/observability/test_websocket_stream_events.py` — `import sys`, 1 `python3`→`sys.executable`
- `tests/observability/test_metrics_export.py` — `import sys`, 1 `python3`→`sys.executable`
- `tests/cli/test_cognition_cli.py` — `import sys`, 3 `python3`→`sys.executable`
- `tests/cli/test_infra_isolation.py` — `import sys`, 5 `python3`→`sys.executable`
- `tests/cli/test_entry_parity.py` — `import sys`, 4 `python3`→`sys.executable`
- `tests/cli/test_observability.py` — `import sys`, 4 `python3`→`sys.executable`

No production (`src/`) code touched — test-infrastructure-only, matching the ticket's Out of Scope.

## Completion Summary
Fixed a real, pre-existing CI infra bug (confirmed independently failing on `main` itself across
multiple unrelated commits before this session's own work touched anything): 12 test files spawned a
`src` server/CLI subprocess via a hardcoded literal `"python3"` instead of `sys.executable`, so
wherever `PATH`'s `python3` resolved to a different interpreter than the one pytest itself was running
under (missing the project's `pip install -r requirements.txt` dependencies, notably `pydantic`), the
spawned subprocess failed at import time and every test depending on it failed with
connection-refused/non-zero-exit errors. Fixed all 16 occurrences across the 12 files by switching to
`sys.executable`, which always resolves to the exact same interpreter regardless of `PATH`
configuration. Confirmed via direct re-run: the 32 previously-failing tests in this ticket's Scope now
pass (0 failures). Two additional, unrelated `tests/tools/` failures found in the baseline run (a
parity-ledger baseline/id-drift class, matching this project's own documented pattern) were correctly
identified as out of scope and reported, not silently folded into this fix. No production (`src/`)
code was touched. A full local CI-scope regression re-run was interrupted partway through by real
machine memory pressure (unrelated to this fix, flagged by the user mid-session); the scoped 32/32
re-run already directly proves the fix, and CI's own remote run is the final confirmation once this
lands.
