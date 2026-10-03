---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261003-VISUAL-ASSETS-SANDBOX-TIMEOUT-LEAK
phase: done
date: 2026-10-03
tags: [security, testing, mcp]
---

# TCK-20261003-VISUAL-ASSETS-SANDBOX-TIMEOUT-LEAK

## Title
A timed-out Aseprite job can leave an orphaned bwrap sandbox process alive; the timeout test then fails machine-wide

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
Found by the planner while reviewing `TCK-20261003-VISUAL-ASSETS-BUDGETS` (2026-10-03), in a clean worktree. The cause is older than
this batch: the code came in with PR #286.

Observed:
- `tests/visual_assets/drawing/integration/test_negative.py::test_timeout_publishes_nothing_and_leaves_no_process` (with `JOB_TIMEOUT_S = 0.01`)
  left a `bwrap --unshare-all --die-with-parent --new-session ... /usr/bin/aseprite -b --script /lua/ops.lua` process alive with PPID 1,
  sleeping, still holding a bind mount of the test's job directory.
- It ignored SIGTERM; only SIGKILL removed it.
- A second, fresh leak appeared within eight further runs.
- While any such process exists, the test fails on every run on the machine, from any worktree or session: its `aseprite_pids()`
  helper does a machine-wide `pgrep -f "aseprite -b --script /lua/ops.lua"`.
- It reproduces on `origin/main` (2cfa8ab1) as well. With the strays killed, the test passes again.

Likely cause: `visual_assets/drawing/backend/sandbox.py` runs bwrap with `subprocess.run(..., timeout=...)`. On timeout that kills only
the direct child, the outer bwrap. With `--unshare-all` bwrap forks an inner process. If the kill lands before the inner process has
armed `--die-with-parent` (PR_SET_PDEATHSIG), which is likely with a 0.01 s timeout and possible under load at any timeout, the inner
process is orphaned. `--new-session` puts it in its own session, so killing a process group does not reach it either. Confirm this
before fixing: the hypothesis is the planner's, from observation, not proven.

## Scope
1. Make the timeout path kill the whole sandbox tree. One possible shape: `Popen`, and on timeout SIGKILL the outer bwrap together with
   every descendant (read `/proc/<pid>/task/*/children` recursively before killing, so an inner process that has not armed its death
   signal is still reached), then `wait()`. A different mechanism is fine if it is equally deterministic and needs no new dependency.
   The `AdapterError` message and the publish-nothing behaviour stay exactly as they are.
2. Scope the test to its own job: match only processes whose command line names this test's job directory, so a sandbox started by
   another session or worktree can neither fail nor hide a leak from this test.
3. Add a stress test: run the timeout path N times (for example 50, at a timeout short enough to hit bwrap's setup window) and assert
   no process naming the test's job directories survives. Mark it `needs_aseprite`, so it runs in the strict local target.
4. Prove it: the stress test fails, or reports a leak, against the old `sandbox.py` and passes with the fix. Record both runs.

## Out of Scope
- Any change to the sandbox's isolation flags (what is bound, unshared or set in the environment).
- Process cleanup outside the test's own job directories (an operator kills strays by hand; say how in `docs/assets/drawing_tools.md`).

## Acceptance Criteria
- [x] Root cause confirmed (or corrected) in Implementation Notes, with the evidence.
- [x] The stress test leaks against the old code and passes against the new code, both runs recorded.
- [x] The timeout test no longer depends on machine-wide process state.
- [x] `make visual-assets-aseprite-local` passes with 0 skipped, run twice in a row (a leak from the first run would fail the second).
- [x] `tests/visual_assets` passes without Aseprite.

## Related Tickets
- TCK-20261003-EPIC-VISUAL-ASSET-HARDENING-AND-REHEARSAL (parent)
- TCK-20261003-VISUAL-ASSETS-BUDGETS (review that found it)
- TCK-20261002-ASEPRITE-MCP-SPIKE-HARDENING (where the timeout test came from)

## Related Docs
- docs/assets/drawing_tools.md, docs/architecture/visual_asset_foundation_adr.md (D10)

## Related Stored Artifacts
- None.

## Related Code Areas
- visual_assets/drawing/backend/sandbox.py, tests/visual_assets/drawing/integration/test_negative.py

## Assumptions / Open Questions
- Production `JOB_TIMEOUT_S` is 30 s, so in real use the kill normally lands long after setup, but load can stretch setup. The fix is
  required either way, because a leaked process keeps a bind mount on a workspace job directory.

## Implementation Notes
- **Root cause confirmed, with one correction to the hypothesis.** Reproduced on the old code by sweeping the timeout (0.002 s to 0.12 s) over the real `apply_ops` path with a per-run workspace: 1 to 2 leaked processes per 100 runs in 3 of 4 trials, none that were aseprite itself. Inspected before killing: `Name: bwrap`, `PPid: 1`, `NSpid: <host pid> 1` (so it is the **init of the sandbox's PID namespace**, the inner bwrap), state sleeping in `do_wait`, no children left, cmdline naming the job's `--bind <workspace>/.jobs/<tmp> /job`. That matches the hypothesis (outer bwrap killed by `subprocess.run(timeout=)`, inner one orphaned; as a namespace init it ignores SIGTERM) except that the survivor is the inner bwrap, not Aseprite; Aseprite itself was already gone.
- Fix in `visual_assets/drawing/backend/sandbox.py`: `Popen` + `communicate(timeout=)`; on timeout (or any exception) `kill_tree` SIGSTOPs the outer process and every descendant found in `/proc/<pid>/task/*/children`, repeating until no new child appears (nothing can fork or exec in between), then SIGKILLs all and reaps the outer one. No new dependency. The `AdapterError` text and the publish-nothing behaviour are unchanged. Isolation flags untouched.
- Tests scope to their own workspace: `tests/visual_assets/drawing/proc_support.py` matches a process only when its command line or mount table names the test's workspace (the inner bwrap and Aseprite share the job directory's bind mount). The machine-wide `pgrep` is gone.
- Not done (out of scope): `intake/quarantine.py` still names `config.MAX_RECORD_BYTES` for four files; the planner marked that optional.
- **Review rework (planner, 2026-10-03):**
  1. *Race fixed.* `os.kill(SIGSTOP)` returns before the target has stopped, so a process could finish a fork after its children were read. `kill_tree` now waits (bounded, `STOP_WAIT_S` = 1 s) until every pid reads `T`/`t`/`Z` or is gone in `/proc/<pid>/stat` before reading its children; if the wait times out, everything known is still SIGKILLed and the children are read once more. Unit tests with a fake `/proc` prove children are read only after the state check and that a process that will not stop is still killed (mutant without the wait fails).
  2. *The unexplained stress failure was a hang, not a leak, and a second bug in `kill_tree`.* With the stress test looped under CPU load (8 busy loops on 6 cores: 3 of 12 runs failed with `TimeoutError: Test execution exceeded the resource time limit`; the repo's `tests/conftest.py` arms a 60 s SIGALRM per test), one later run hung for 13 minutes with load back to normal. Inspected live: pytest in `do_wait`, the outer bwrap in state `T` and the inner bwrap `Ts` (stopped, never killed). Cause: the SIGALRM handler raised `TimeoutError` inside `kill_tree` after SIGSTOP and before SIGKILL, so the tree stayed stopped for good and `Popen.__exit__` waited on it forever. Fix: the SIGKILL of everything known is now in a `finally`, so an interrupt (alarm, KeyboardInterrupt) cannot leave a stopped tree. Unit test `test_an_interrupt_between_stop_and_kill_still_kills_the_tree` (mutant without the `finally` fails). The post-kill pipe drain is also bounded (`DRAIN_WAIT_S` = 2 s) so a survivor holding the pipes cannot block it. The stress test is marked `resource_budget_large` (7 s idle, 17-43 s under that load, over the 60 s default) and now prints `timed_out` and, for each survivor, pid, NSpid, State, PPid and the command line; the `timed_out >= RUNS // 3` assertion became `timed_out >= 1`.
  3. *Doc safety.* `drawing_tools.md` now lists candidates with `pgrep -af 'bwrap .*--bind .*\.jobs/'` and says to kill only processes that bind a `.jobs/` directory of a workspace you own (the broader pattern also matches GNOME's own image-loader sandboxes).
- Known limit (bounded best effort, no change): if a process will not stop within `STOP_WAIT_S` (for example stuck in D state), the late children scan after the SIGKILL can miss a child that was already reparented.
- Note on the loop that found it: running 8 CPU burners starved the host (load average 43; a session crashed once and a later 4-burner run pushed the load average to 44 until stopped). Do not repeat that on this machine; the interrupt behaviour is now covered by a deterministic unit test instead.

## Test Summary
- Rework: stress test looped 20 times without load: 20 of 20 passed (the earlier loaded runs passed 8 of 8 completed runs plus the one hang that exposed the bug). Unit file `test_sandbox_kill_tree.py`: 6 tests. Strict target twice in a row: 202 passed, 0 skipped both times. `tests/visual_assets` without Aseprite: 924 passed, 202 skipped. static/architecture/docs: 240 passed.
- Old code vs new code with `test_sandbox_timeout_leak.py` (150 runs, timeouts 0.002 s to 0.12 s, one test each): **old `sandbox.py`: 2 of 5 runs failed** ("1 sandbox process(es) outlived 60 timeouts", "... 61 timeouts"; 3 passed); **new: 6 of 6 passed**, plus four 100-run reproduction sweeps with 0 strays after 3 of 4 leaked on the old code. The stress test is probabilistic against the old code (about 40% per run); the deterministic guard is `unit/test_sandbox_kill_tree.py` (real processes: a child in its own session that ignores SIGTERM, plus a grandchild; no Aseprite, runs in CI).
- Mutants of `kill_tree`: outer process only (the old behaviour) and "never looks at descendants" both fail `test_kill_tree_kills_a_sigterm_ignoring_descendant_in_its_own_session` ("a descendant survived kill_tree").
- `make visual-assets-aseprite-local` twice in a row: 202 passed, 0 skipped, both times.
- `tests/visual_assets` without Aseprite: 920 passed, 202 skipped after the isolation-test adaptation (one test faked `subprocess.run`; it now fakes `Popen`); `tests/static tests/architecture tests/docs`: 240 passed.
- A killed `pkill -f` pattern on my own shell cost one command during the old-code runs; the leftover test strays were killed and no stray naming a pytest directory remained.

## Files Changed
- `visual_assets/drawing/backend/sandbox.py`
- `tests/visual_assets/drawing/proc_support.py` (new), `integration/test_sandbox_timeout_leak.py` (new), `unit/test_sandbox_kill_tree.py` (new), `integration/test_negative.py`, `unit/test_workspace_isolation.py`
- `docs/assets/drawing_tools.md`

## Completion Summary
A timed-out Aseprite job now kills its whole sandbox tree, so no orphaned bwrap holds a job directory; the timeout test no longer depends on machine-wide process state.
