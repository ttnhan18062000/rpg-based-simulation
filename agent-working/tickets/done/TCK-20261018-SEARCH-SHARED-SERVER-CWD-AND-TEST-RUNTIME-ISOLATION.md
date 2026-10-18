---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261018-SEARCH-SHARED-SERVER-CWD-AND-TEST-RUNTIME-ISOLATION
phase: done
date: 2026-10-18
tags: [ai, mcp, testing]
---

# TCK-20261018-SEARCH-SHARED-SERVER-CWD-AND-TEST-RUNTIME-ISOLATION

## Title
The shared search server runs with cwd = the main checkout, and no test can touch the real `$XDG_RUNTIME_DIR/rpg-search`

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Two findings from the live check of #639 on 2026-10-18 (lead-planner asked for both in batch 2):
1. The spawned `search_shared.py serve` (pid 569364) inherited the spawning client's cwd, which was the planner's worktree, and that client's cgroup. A server for the whole fleet shouldn't pin a worktree path: a removed worktree leaves the server with a deleted cwd.
2. `$XDG_RUNTIME_DIR/rpg-search/` gained two extra state dirs holding only an empty `server.lock` (created 19:13–19:15 on 2026-10-18, during the batch-1 test runs). So some test reaches the real runtime dir. **Leave those two dirs alone** (lead-planner).

## Scope
- `search_shared._spawn`: pass `cwd=<main checkout root>`, from `main_checkout_root(_TOOLS_DIR)`, falling back to the code root's parent. Add a test asserting the Popen cwd.
- Find which test(s) created real-dir state: bisect `tests/tools/test_search_shared.py` / `test_search_mcp.py` and any other caller of `state_dir`/`_server_lock_held` with a tmp HOME, and record the culprit in the ticket.
- Fix: every test gets a tmp `XDG_RUNTIME_DIR` via an autouse fixture in `tests/tools/conftest.py`, and in any other conftest whose tests import search_shared/search_mcp.
- **Guard test that fails if any test touches the real runtime dir**, deterministic and not flaky while live sessions run. For example:
  - under pytest, `search_shared.state_dir()` raises unless `XDG_RUNTIME_DIR` (or the tempdir base) differs from the value captured at conftest import, the "real" one;
  - plus a test asserting the guard trips when the env is pointed back at the real value.
  - **Don't** compare listings of the real dir: other sessions write there concurrently.

## Out of Scope
- Moving the server out of the spawning client's cgroup: systemd scopes are the caller's choice.
- Deleting the two stray dirs.

## Acceptance Criteria
- The spawn uses the main-checkout cwd (test).
- The culprit test is named and fixed.
- The guard fails when a test points at the real runtime dir.
- `tests/tools/test_search_shared.py`, `test_search_mcp.py` and `test_knowledge_search.py` are green.

## Related Tickets
- TCK-20261018-SEARCH-SHARED-SINGLE-SERVER-FROM-MAIN-CHECKOUT (#628, #639)

## Related Docs
- docs/guidelines/agent_working_environment.md § One shared search model

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261018-SEARCH-SHARED-SINGLE-SERVER-FROM-MAIN-CHECKOUT/

## Related Code Areas
- tools/search_shared.py, tests/tools/conftest.py, tests/tools/test_search_*.py

## Assumptions / Open Questions
- none

## Implementation Notes
- **Culprit (named):** the two tests that call `search_shared._main`, `test_the_server_refuses_to_serve_a_database_other_than_the_one_it_searches` and `test_the_server_accepts_the_database_it_searches_under_any_spelling` (tests/tools/test_search_shared.py). Before batch 1 `_main` only loaded a model and touched no state, so they needed no runtime dir and set none. Batch 1 made `_main` claim `<state dir>/server.lock` first, so on their first run (19:15:17, my first test run after that change, before I added an `XDG_RUNTIME_DIR` to them in the same hour) they created `$XDG_RUNTIME_DIR/rpg-search/<key>/server.lock` for their two tmp db paths. Evidence: exactly two `server.lock`-only dirs (`adbf7c9c9627`, `b33e180f12e1`), both modified at 19:15:17, and `_main` has exactly two callers in tests/. They were fixed in batch 1; the autouse fixture and guard below make the whole class impossible. The two dirs are left alone, as instructed.
- `_spawn` passes `cwd=_server_cwd(db_path)`: the main checkout (`_own_main_root()`), else the code root's parent.
- `tests/tools/conftest.py`: captures the real runtime base into `RPG_SEARCH_TEST_REAL_RUNTIME_BASE` at import and adds an autouse fixture giving every tools test its own `XDG_RUNTIME_DIR` (made with `tmp_path_factory`, outside the test's own `tmp_path`: `test_subagent_stop_background_guard` asserts its `tmp_path` stays empty). `search_shared.state_dir()` raises `RuntimeError` under pytest when its base equals that captured base (deterministic; never reads the real dir's contents). tests/conftest.py is not touched; the only tests importing the search modules are in tests/tools.

## Test Summary
test_search_shared + test_search_mcp + test_knowledge_search: 159 passed, 35 skipped before the last fix, test_search_shared alone 46 passed after it. 5 new tests: spawn cwd is the main checkout (mutation-checked: dropping `cwd=` fails it), cwd fallback outside git, every tools test runs in a tmp runtime dir, the guard trips on the real base (and on the tempdir fallback base), `_main` lands in tmp. The real `$XDG_RUNTIME_DIR/rpg-search` still has the same 3 dirs after the runs.

## Files Changed
- tools/search_shared.py
- tests/tools/conftest.py
- tests/tools/test_search_shared.py
- docs/guidelines/agent_working_environment.md

## Completion Summary
The shared server runs with the main checkout as its cwd, and no tools test can reach the real runtime dir: every test gets a tmp one and `state_dir()` refuses the real base under pytest.
The guard is armed only where `tests/tools/conftest.py` sets the env var, so a search module imported from another test tree needs the same two lines in that tree's conftest.
