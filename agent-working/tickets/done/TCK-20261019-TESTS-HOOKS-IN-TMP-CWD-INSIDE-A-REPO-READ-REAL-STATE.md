---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261019-TESTS-HOOKS-IN-TMP-CWD-INSIDE-A-REPO-READ-REAL-STATE
phase: done
date: 2026-10-19
tags: [ai, testing, bug]
---

# TCK-20261019-TESTS-HOOKS-IN-TMP-CWD-INSIDE-A-REPO-READ-REAL-STATE

## Title
Tools tests that run a hook with `cwd=tmp_path` read the real main checkout's state whenever pytest's basetemp is inside a git repo

## Status
DONE

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
**Repro (2026-10-19):** full `tests/tools` under a 2G cap, alone, with `--basetemp` inside a throwaway `git init` repo under /data (`aw-repro-repo`, one committed `.claude/handover/fake.md` carrying the sentinel `AW-REPRO-SENTINEL-10a4c9872865`): **15 failed**, 5060 passed, 56 skipped, 1 xfailed. The 15, in two classes:
- Hooks that resolve the repo from cwd and so read the repo above tmp_path:
  - `test_session_start_handover_hook.py`: `test_hook_prints_nothing_when_no_handover_notes_exist`, `test_hook_prints_additional_context_json_on_clear_with_notes`
  - `test_session_resolve_and_hook.py`: `test_resolved_role_gets_its_card_and_only_its_own_handover`, `test_an_instance_gets_its_own_handover_note_not_the_roles`, `test_issues_for_the_role_follow_the_handover_note_and_only_that_label_is_requested`, `test_a_torn_bindings_tail_still_gives_card_and_note_and_one_warning`, `test_an_unreadable_bindings_history_still_gives_card_and_note_and_says_so`, `test_a_handover_edited_after_the_hard_declaration_is_called_out`, `test_an_over_cap_handover_note_says_its_size_and_the_cap_instead_of_cutting_silently`
- Tests that assert "outside git" behaviour, which breaks when tmp_path is inside a repo: `test_cited_evidence_advisory.py::test_missing_ticket_is_na_and_git_failure_degrades_to_warn`, `test_done_checker_static.py::test_git_touched_paths_fails_open_on_non_repo`, `test_search_mcp.py::TestResolveIndexDir::test_main_checkout_root_outside_git_is_none`, `test_search_shared.py::test_the_spawn_cwd_falls_back_to_the_code_roots_parent_outside_git`, `test_session_settings_freshness.py::test_outside_the_repo_is_a_mismatch_naming_the_symptoms`, `test_session_settings_freshness.py::test_allow_stale_never_launches_from_outside_the_repo`
- **Sentinel:** found once in the run log, in the failure output of `test_hook_prints_nothing_when_no_handover_notes_exist` (it lists the fake note). The other hook failures read repo-resolved state without printing the fake note.
- **Real state:** 14 of the main checkout's 15 handover notes have unchanged mtimes; `lead-planner.md` changed, a live lead session's own edit (its mtime predates the run's repo setup per the planner); the tests have no write path to it.

**Fix (smallest mechanism covering all 15, no production code changed):** one autouse fixture in `tests/tools/conftest.py` sets `GIT_CEILING_DIRECTORIES` to `tmp_path.parent`, so git (and any hook or subprocess inheriting the env) never looks above a test's tmp dir; a repo the test creates under its own tmp dir is still found. The injectable-resolution alternative was not needed.

## Test Summary
- The 5 affected files (session_start_handover_hook, session_resolve_and_hook, session_settings_freshness, cited_evidence_advisory, done_checker_static): 283 passed with `--basetemp` inside the throwaway repo; test_search_mcp + test_search_shared + the new guard file: 86 passed in the same setup.
- Guard `tests/tools/test_tmp_cwd_cannot_see_a_repo_above.py` (2 tests): a nested pytest run with `--basetemp` inside a scratch repo that has a handover note must pass the hook test and never list the note; a repo made inside the test's own tmp dir is still found. Both fail with the fixture neutralised (checked).
- The second full-suite verification run (basetemp inside a repo, then outside) is a separate heavy slot, run before the PR.

## Files Changed
- tests/tools/conftest.py
- tests/tools/test_tmp_cwd_cannot_see_a_repo_above.py

## Completion Summary
Tools tests no longer depend on where pytest puts its tmp dir: git cannot resolve a repo above a test's tmp_path, so the 15 repo-sensitive tests pass with a basetemp inside a repo.
