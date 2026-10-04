---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261004-VISUAL-ASSETS-KILL-TREE-TEST-RACE
phase: open
date: 2026-10-04
tags: [testing, mcp]
---

# TCK-20261004-VISUAL-ASSETS-KILL-TREE-TEST-RACE

## Title
`test_kill_tree_kills_a_sigterm_ignoring_descendant_in_its_own_session` can read an empty pid marker under load

## Status
OPEN

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
- [ ] Markers are written atomically; the test reads them only after the rename.
- [ ] A timed-out setup fails with a named-marker message and leaves no process from the test alive.
- [ ] Repeated runs pass: the test 50 times in a row under load (e.g. `pytest --count` or a loop, alongside a CPU-bound
      background job), under the 2 GB cap. Report the command and result.
- [ ] Mutant: revert to the non-atomic write and add a short sleep between `open` and `write` in the child; the test
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

## Test Summary

## Files Changed

## Completion Summary
