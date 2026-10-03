---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261003-VISUAL-ASSETS-SANDBOX-TIMEOUT-LEAK
phase: open
date: 2026-10-03
tags: [security, testing, mcp]
---

# TCK-20261003-VISUAL-ASSETS-SANDBOX-TIMEOUT-LEAK

## Title
A timed-out Aseprite job can leave an orphaned bwrap sandbox process alive; the timeout test then fails machine-wide

## Status
OPEN

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
- [ ] Root cause confirmed (or corrected) in Implementation Notes, with the evidence.
- [ ] The stress test leaks against the old code and passes against the new code, both runs recorded.
- [ ] The timeout test no longer depends on machine-wide process state.
- [ ] `make visual-assets-aseprite-local` passes with 0 skipped, run twice in a row (a leak from the first run would fail the second).
- [ ] `tests/visual_assets` passes without Aseprite.

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

## Test Summary

## Files Changed

## Completion Summary
