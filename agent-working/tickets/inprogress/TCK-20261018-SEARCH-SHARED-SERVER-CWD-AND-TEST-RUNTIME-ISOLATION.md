---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261018-SEARCH-SHARED-SERVER-CWD-AND-TEST-RUNTIME-ISOLATION
phase: open
date: 2026-10-18
tags: [ai, mcp, testing]
---

# TCK-20261018-SEARCH-SHARED-SERVER-CWD-AND-TEST-RUNTIME-ISOLATION

## Title
The shared search server runs with cwd = the main checkout, and no test can touch the real `$XDG_RUNTIME_DIR/rpg-search`

## Status
OPEN

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
## Test Summary
## Files Changed
## Completion Summary
