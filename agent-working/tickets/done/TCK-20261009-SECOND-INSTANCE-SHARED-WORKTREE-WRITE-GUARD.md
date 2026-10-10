---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261009-SECOND-INSTANCE-SHARED-WORKTREE-WRITE-GUARD
phase: done
date: 2026-10-09
tags: []
---

# TCK-20261009-SECOND-INSTANCE-SHARED-WORKTREE-WRITE-GUARD

## Title
A second or third instance of a role can commit in the role's shared launch worktree whenever the first instance is not running

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Found by TCK-20261009-PER-INSTANCE-HANDOVER-NOTE (AC4). `session_start_hook.py` (around line 148) gives the writer lease only to a role's first instance. `guard.decide()` (around line 210) denies commit, push and open_pr only when a lease exists and belongs to another instance; "no lease" is not a denial. So with `rpg-implementer` not running, `rpg-implementer-2` and `rpg-implementer-3` both launch into `.claude/worktrees/rpg`, neither takes a lease, and nothing refuses either of them a commit there. The implementer card says an instance beyond the first writes only in its own per-piece worktree, but only the lease enforces that, and only while instance 1 is live. rpg now runs three lanes. The owner approved the fix on 2026-10-09.

## Scope
- `tools/sessions/guard.py`: when the caller is an instance beyond the first (`caller.instance != caller.role_id`) and the command's worktree toplevel is that role's placement worktree (`<main>/.claude/worktrees/<placement.worktree>`, resolved the same way `launch.py` does), deny commit, push and open_pr whether or not a lease exists. The reason names the rule: work in a per-piece worktree.
- Per-piece worktrees, which have no lease, stay allowed for every instance. The first instance's behaviour is unchanged.
- Tests in `tests/tools/test_session_guard.py`:
  - `-2` committing in the role worktree is denied with no lease;
  - `-2` committing in a per-piece worktree with no lease is allowed;
  - instance 1 is unchanged;
  - the existing case where `-2` is denied by instance 1's lease still passes.
- Write the rule as one clause in `docs/guidelines/session_roles/functions/implementer.md` only if the card already mentions per-piece worktrees, then regenerate the cards and keep them within the 400-token budget.

## Out of Scope
- Giving each instance its own registered worktree in `session_roles.yaml`.
- Leases for per-piece worktrees.

## Acceptance Criteria
- AC1: the four guard cases above pass; `pytest tests/tools/test_session_*.py` is green.
- AC2: generate_agents shows no drift and the validator passes.
- AC3: closure by `record_hand_orchestrated_closure.py` (`small_change`).

## Related Tickets
- TCK-20261009-PER-INSTANCE-HANDOVER-NOTE (found it; same batch)
- TCK-20261009-RPG-IMPLEMENTER-THIRD-SEAT (#467)

## Related Docs
- `docs/guidelines/session_roles/functions/implementer.md`

## Related Stored Artifacts
None (hotfix).

## Related Code Areas
- `tools/sessions/guard.py`, `tools/sessions/session_start_hook.py`, `tools/sessions/launch.py`

## Assumptions / Open Questions
- Assumes the guard can tell which role worktree it is in from the roster and the main checkout, as `launch.py` does. If the physical path differs (`launch.py --worktree`), compare against the lease-keyed physical path recorded at SessionStart if one exists, and say which you used.

## Implementation Notes
- `guard.in_shared_role_worktree(caller, roster, toplevel, cwd)`: true when the caller is an instance beyond the first and the command's git toplevel realpath equals `<main checkout>/.claude/worktrees/<role placement worktree>`. The main checkout is the parent of `git rev-parse --path-format=absolute --git-common-dir`, which is what `launch.py` resolves as its default; a `launch.py --worktree` override is NOT visible to the guard (no physical path is recorded at SessionStart for this), so I used the default placement path and say so here.
- `decide(..., in_role_worktree=False)` denies commit/push/open_pr with the reason "work in a per-piece worktree" before the lease check, lease or no lease. Per-piece worktrees and the first instance are unchanged; the existing "-2 denied by instance 1's lease" case still passes.
- The implementer card does not mention per-piece worktrees (`grep per-piece` over `docs/guidelines/session_roles/functions/implementer.md` is empty), so by the ticket's own condition no card clause was added; generate_agents shows 0 drift.

## Test Summary
New guard tests (denied in shared worktree with no lease x3 commands; allowed in per-piece x3; first instance unchanged x3; helper on real git worktrees; existing lease denial). tests/tools/test_session_*.py green. generate_agents --check 0 drift.

## Files Changed
`tools/sessions/guard.py`, `tests/tools/test_session_guard.py`.

## Completion Summary
A later instance can no longer commit, push or open a PR in its role's shared worktree, with or without a lease.
