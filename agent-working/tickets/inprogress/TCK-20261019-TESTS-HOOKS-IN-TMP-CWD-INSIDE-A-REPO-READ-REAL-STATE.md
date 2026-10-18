---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261019-TESTS-HOOKS-IN-TMP-CWD-INSIDE-A-REPO-READ-REAL-STATE
phase: open
date: 2026-10-19
tags: [ai, testing, bug]
---

# TCK-20261019-TESTS-HOOKS-IN-TMP-CWD-INSIDE-A-REPO-READ-REAL-STATE

## Title
Tools tests that run a hook with `cwd=tmp_path` read the real main checkout's state whenever pytest's basetemp is inside a git repo

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Found 2026-10-19 during batch 3's full `tests/tools` run (approved by lead-planner).
- With `--basetemp` in a gitignored dir *inside* a worktree, the run had **14 failures**. With a basetemp outside any repo (`/data/vboxuser/aw-pytest-tmp`), only 1 unrelated load flake remained.
- The one failure identified by name is `tests/tools/test_session_start_handover_hook.py::test_hook_prints_nothing_when_no_handover_notes_exist`. The hook runs with `cwd=tmp_path`; inside a repo, git resolves the main checkout through `handover_base()`, the hook lists the real `.claude/handover/*.md`, and the "prints nothing" assertion fails.
- The other 13 names were lost (the log was deleted before it was read).
- The tests silently assume that tmp_path isn't inside a git repo. Nothing was written to real state (lead-planner checked the main checkout and handover notes after the run). But a read-only leak still makes results depend on where pytest puts tmp.

## Scope
- **Reproduce and name all of them:**
  - run `tests/tools` with a basetemp inside a gitignored dir of a scratch git repo. Use a throwaway `git init` under /data, never a seat's worktree, and alone in a lead heavy slot;
  - list every failing test in this ticket.
- **Fix at the root, once:**
  - give these tests a cwd that can never resolve to a real repo. One option is a shared fixture that sets `GIT_CEILING_DIRECTORIES` to tmp_path's parent, or that `git init`s tmp_path, so git stops at the test's own dir;
  - or make `handover_base()` / the hook's repo resolution injectable via env;
  - choose the smallest mechanism that covers all of them, and record the choice.
- **Guard:** add a test that runs the handover hook from a tmp dir nested inside a throwaway git repo that has real-looking handover notes, and asserts it never lists them.

## Out of Scope
- The `test_post_tool_hook.py` 10 s timeout flake (a separate ticket if it recurs on CI).
- Changing any hook's production behaviour beyond an injectable resolution point, if that route is chosen.

## Acceptance Criteria
- The full `tests/tools` run is green with a basetemp inside a repo, and stays green with one outside.
- The guard test fails on the old fixture and passes on the new one.

## Related Tickets
- TCK-20261018-SEARCH-SHARED-SERVER-CWD-AND-TEST-RUNTIME-ISOLATION (same class: tests reaching real host state)
- TCK-20261006-HANDOVER-NOTES-RESOLVE-FROM-MAIN-CHECKOUT (why the hook resolves the main checkout)

## Related Docs
- docs/guides/agent_session_reset_boundaries.md (the handover hook)

## Related Stored Artifacts
- none

## Related Code Areas
- tests/tools/test_session_start_handover_hook.py, tests/tools/conftest.py, tools/handover_home.py, tools/agent-monitoring/session_start_handover_hook.py, tools/sessions/session_start_hook.py

## Assumptions / Open Questions
- The other 13 failures are assumed to be the same class until the repro names them.

## Implementation Notes
## Test Summary
## Files Changed
## Completion Summary
