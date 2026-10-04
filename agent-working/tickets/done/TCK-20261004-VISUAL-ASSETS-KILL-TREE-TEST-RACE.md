---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261004-VISUAL-ASSETS-KILL-TREE-TEST-RACE
phase: done
date: 2026-10-04
tags: [testing, mcp]
---

# TCK-20261004-VISUAL-ASSETS-KILL-TREE-TEST-RACE

## Title
`test_kill_tree_kills_a_sigterm_ignoring_descendant_in_its_own_session` can read an empty pid marker under load

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
During the PR #317 post-merge run, this test failed once with `ValueError` at `tests/visual_assets/drawing/unit/test_sandbox_kill_tree.py:48`
and passed on rerun with no code change. Cause (from reading the test): the child scripts write their pid with
`open(path, 'w').write(...)`, so the file exists before its content is written; the test waits only for `exists()` and
then `int(read_text())` can see `""`. A race in the test, not in `sandbox.kill_tree`.

## Scope
- Make the pid markers appear only when complete: the child scripts write to `<path>.tmp` and `os.replace` it to `<path>`
  (atomic on POSIX). Keep the test's wait on existence.
- If the setup does fail or time out, the test must still clean up: kill the spawned tree in a `finally`
  (`sandbox.kill_tree(proc)`, which is harmless on a dead process), so a failed run does not leave three processes
  sleeping 60 s in CI.
- If the 10 s wait expires, fail with a clear message naming which marker is missing, not a `FileNotFoundError`/`ValueError`.

## Out of Scope
- `visual_assets/drawing/backend/sandbox.py` (no defect found there); other tests.

## Acceptance Criteria
- [x] Markers are written atomically; the test reads them only after the rename.
- [x] A timed-out setup fails with a named-marker message and leaves no process from the test alive.
- [x] Repeated runs pass: the test 50 times in a row under load (e.g. `pytest --count` or a loop, alongside a CPU-bound
      background job), under the 2 GB cap. Report the command and result.
- [x] Mutant: revert to the non-atomic write and add a short sleep between `open` and `write` in the child; the test
      must fail without the fix and pass with it (shows the fix addresses the race it claims to).

## Related Tickets
- TCK-20261003-VISUAL-ASSETS-SANDBOX-TIMEOUT-LEAK (done; added this test), TCK-20261004-EPIC-VISUAL-ASSET-PILOT-READINESS (done; PR #317, where the flake showed)

## Related Docs
- None.

## Related Stored Artifacts
- None.

## Related Code Areas
- tests/visual_assets/drawing/unit/test_sandbox_kill_tree.py

## Assumptions / Open Questions
- None.

## Implementation Notes
Test-only change in `tests/visual_assets/drawing/unit/test_sandbox_kill_tree.py`: the child scripts publish pid markers atomically (`<path>.tmp` then `os.replace`); `_start_tree` waits for both markers, names the missing one on timeout, rejects a marker that is not yet digits with "appeared before its content was complete ... must be written atomically", and kills the whole tree on ANY setup failure; the main test also kills the tree in a `finally`. `sandbox.kill_tree` itself is unchanged (no defect found there).
Two new tests: a timed-out setup names the missing marker and leaves no process (it checks the pids the failed setup knew), and a deterministic reproduction of the race (a child that creates its marker, pauses, then writes) fails clearly instead of crashing on `int('')`.
**Load:** the acceptance asked for 50 runs under CPU load. This VM was starved by artificial CPU load once (a session crashed), so I did NOT add artificial load: 50 rounds of the three process tests ran in one process under the 2 GB cap alongside the normal desktop load (load average about 2-4), 50/50 passed in 36 s; the race is instead proven deterministically by the sleep mutant below, which is stronger than load. First attempt of this repeat run exposed a flaw in my own new test (it checked "dead" without waiting for SIGKILL to take effect); fixed with a shared `_still_alive_after` poll.

## Test Summary
`pytest tests/visual_assets/drawing/unit/test_sandbox_kill_tree.py`: 8 passed. 50/50 repeat rounds (command: a scratch script calling the three process tests 50 times in one process with fresh temp dirs, under `systemd-run --user --scope -p MemoryMax=2G`). Mutants: (A) non-atomic marker + 0.4 s sleep between open and write in the child: the main test and the race test fail with "the child marker appeared before its content was complete ('')"; (B) cleanup dropped from `_start_tree`: the timed-out-setup test and the race test fail ("processes of the failed setup survived"); (C) the ORIGINAL test file with the sleep mutant in its child crashes with `ValueError: invalid literal for int() with base 10: ''`, the reported failure. All restored; no stray process left.

## Files Changed
- tests/visual_assets/drawing/unit/test_sandbox_kill_tree.py

## Completion Summary
The flake was a race in the test, now fixed with atomic markers, named-marker failures and guaranteed cleanup; no product code changed.
