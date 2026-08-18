---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260818-STANDARD-LONGRUN-DETERMINISM-WATCHDOG-AUDITMODE
artifact_type: test_plan
tags: [engine, determinism, bug, debugging, root-cause, testing]
---

# Test Plan — TCK-20260818-STANDARD-LONGRUN-DETERMINISM-WATCHDOG-AUDITMODE

## Normal flow
- `tests/integration/world/test_long_run_stability.py::test_long_run_stability` run under
  `--resource-budget large` (matching the real CI invocation shape) — must pass, both internal
  hash-parity runs producing bit-identical `CanonicalStateHasher` output.

## Regression-prone path (the actual bug)
- Repeated-run determinism verified independently of pytest via a standalone script invoking the
  exact same `Kernel(profile, state, rng, flags={"audit_mode": True})` construction 3 times (2 in
  one process, 1 in a fresh separate process) — all 3 hashes must be bit-identical. (Already done
  in investigation.md Step 5; re-confirmed via the real pytest invocation below.)
- Confirm 0 watchdog trips (`"exceeded budget"` / `"WatchdogTrip"`) appear in the log for the fixed
  test, proving Mechanism A is genuinely suppressed, not merely coincidentally not triggered.

## Failure modes checked (not just happy path)
- Bisection on the pre-spawn-collision-fix commit (`db6335ad`) via isolated worktree — confirms
  the bug is NOT a regression introduced by this session's other work.
- `test_long_run_determinism_parity` (Mechanism B) explicitly left failing/unfixed — verify it is
  NOT accidentally fixed as a side effect (would indicate my understanding of Mechanism B is wrong)
  and NOT accidentally made worse.
- `test_long_run_pure_stability`'s TimeoutError explicitly left untouched — verify the file is not
  modified at all (this ticket's Related Code Areas exclude it).

## Out of scope for this ticket's test verification
- Full 5000-tick `test_long_run_pure_stability` / `test_long_run_runtime_stability` re-runs — not
  modified, no new evidence needed beyond the sibling ticket's already-closed read-only
  investigation (cited in investigation.md Step 4).
- Fixing/re-testing Mechanism B — explicitly deferred to a follow-up ticket.

## Commands to run before closing
```
.venv/bin/python3 -m pytest tests/integration/world/test_long_run_stability.py::test_long_run_stability \
  --resource-budget large --tb=long -v -s
```
Must show `1 passed`, both hash values printed identical, 0 `WatchdogTrip`/`exceeded budget` lines.
