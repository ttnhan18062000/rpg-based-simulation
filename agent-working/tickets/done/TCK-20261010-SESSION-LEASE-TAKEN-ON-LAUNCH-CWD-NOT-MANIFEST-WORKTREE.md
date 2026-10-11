---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261010-SESSION-LEASE-TAKEN-ON-LAUNCH-CWD-NOT-MANIFEST-WORKTREE
phase: done
date: 2026-10-10
tags: [ai, process-improvement, governance]
---

# TCK-20261010-SESSION-LEASE-TAKEN-ON-LAUNCH-CWD-NOT-MANIFEST-WORKTREE

## Title
SessionStart takes the writer lease on whatever directory the session was launched in, not on the role's manifest worktree

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Observed live on host ubuntu, 2026-10-10. Seven seats were relaunched with
`launch.py <role> --worktree <main checkout>`:
- lead-planner
- codebase-planner, codebase-implementer
- asset-planner, asset-implementer
- perf-planner, perf-implementer

The main checkout's single writer lease went to `lead-planner`, the first writer-role to start.
`tools/sessions/status.py` now prints six flags of the form
`recorded writer lead-planner is not the manifest writer <role>`. Because `tools/sessions/guard.py:210`
denies commit, push and PR creation to any non-holder, only lead-planner can commit in the main
checkout. The lead is advisory and mostly reads, so it is the wrong holder.

Root cause, `tools/sessions/session_start_hook.py` around line 146:
- The hook checks that the role is the `writer` of its **manifest** worktree (`role.worktree`).
- It then calls `st.take_lease(state_root, worktree, ...)` with `worktree` = the session's
  **physical launch directory**, never checking that this directory *is* the manifest worktree.
- So a writer-role launched anywhere else leases that other place.

## Scope
- Take the lease only when the physical worktree resolves to the role's manifest worktree path,
  meaning the path `launch.py` would default to or the one recorded for that role.
- Never take a lease on the main checkout unless a manifest worktree names it explicitly.
- When the hook skips the lease, emit one SessionStart note saying why
  (`session-roles: writer lease not taken: launched outside <manifest worktree>`).
- Tests:
  - a writer-role launched in a foreign path takes no lease;
  - one launched in its own worktree still does;
  - the main checkout is never leased by default;
  - the existing `<role>-2` second-instance behaviour is unchanged.

## Out of Scope
- Recording per-batch worktrees and the launch policy for read-mostly seats
  (`TCK-20261010-SESSION-MAIN-CHECKOUT-LAUNCH-AND-BATCH-WORKTREE-RECORD`).
- Releasing the currently held lease. That is the owner's `release_lease` call, and it is
  unnecessary once this fix lands and the lead relaunches.
- Any change to `guard.py`'s deny rule.

## Acceptance Criteria
1. Seven seats launched from the main checkout leave the main checkout with **no** lease, and
   `status.py` prints no `recorded writer ... is not the manifest writer` flag for it.
2. A writer-role launched in its own manifest worktree still takes and holds the lease (regression).
3. The skipped-lease note appears at SessionStart and fails open.
4. `pytest tests/tools/test_session_*.py` passes.

## Related Tickets
- `TCK-20261004-SESSION-LAYER-M2A-ROLE-STATE-DIRECTORY-AND-LIVENESS` (lease library)
- `TCK-20261004-SESSION-LAYER-M2B-ROLE-AWARE-SESSIONSTART-AND-BINDING` (the hook)
- `TCK-20261010-SESSION-MAIN-CHECKOUT-LAUNCH-AND-BATCH-WORKTREE-RECORD` (sibling)
- Reported by lead-planner on PR #476 (comment 6095526830)

## Related Docs
- `docs/plans/agent_infrastructure/session_layer_working_process.md` §5, §6.1
- `docs/guides/agent_session_reset_boundaries.md` ("Launching a role")

## Related Stored Artifacts
None.

## Related Code Areas
`tools/sessions/session_start_hook.py`, `tools/sessions/state.py`, `tools/sessions/status.py`,
`tests/tools/test_session_*.py`

## Assumptions / Open Questions
- "Resolves to the manifest worktree" compares physical paths (`realpath`), as the lease key
  already does.

## Implementation Notes
`session_start_hook._manifest_worktree(role, cwd)` = realpath of `<main checkout>/.claude/worktrees/<role.worktree>` (main checkout = parent of `git rev-parse --path-format=absolute --git-common-dir`, the path `launch.py` defaults to). The writer's lease is taken only when the session's physical worktree realpath equals it; otherwise one SessionStart note `session-roles: writer lease not taken: launched outside <manifest worktree>` is added and the session is still bound and carded. If the main checkout cannot be determined (git failure) the old behaviour is kept (fail open). Only the default path is compared: a `launch.py --worktree` override to another path is treated as foreign (no recorded per-role override exists in state to compare against), which is the safe direction: no lease rather than the wrong lease. Existing hook tests that launched writers in the repo root now launch in the role's manifest worktree.

## Test Summary
New: writer launched in the main checkout takes no lease and says why (still bound/carded); in a foreign git worktree takes none; seven seats launched in the main checkout leave it unleased. Regression: designer/planner/writer launched in its own manifest worktree still take the lease; `<role>-2` unchanged; another role's lease still reported not stolen. tests/tools/test_session_*.py: 612 passed.

## Files Changed
`tools/sessions/session_start_hook.py`, `tests/tools/test_session_resolve_and_hook.py`.

## Completion Summary
A writer role launched outside its manifest worktree no longer takes a lease there; the main checkout stays unleased.
