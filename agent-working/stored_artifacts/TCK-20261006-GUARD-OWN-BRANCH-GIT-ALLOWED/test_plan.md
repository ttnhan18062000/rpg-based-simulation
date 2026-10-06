---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261006-GUARD-OWN-BRANCH-GIT-ALLOWED
artifact_type: test_plan
tags: [ai, process-improvement, governance]
---

# test_plan

| AC | Test | Result |
|---|---|---|
| 1 allow (no lease, feature branch: commit, push, push -u, force-with-lease, merge, gh pr create) | `test_session_guard.py::test_own_branch_actions_are_allowed_with_or_without_a_lease` (3 implementer roles x lease/no lease x 7 commands) and `test_end_to_end_in_a_real_repo_with_no_lease` | pass |
| 2 ask (gh pr merge, push HEAD:main, push origin main, bare push on main, commit on main) | `test_landing_on_the_default_branch_asks_for_every_role`, the e2e test in a real repo on `main`, and the classify tests for `push_default_branch` | pass |
| 3 deny (another role's lease) | `test_another_roles_lease_still_denies_on_a_feature_branch` | pass |
| 4 unchanged (designer commit deny, settings edit ask, push --delete ask, bash -c ask) | `test_unchanged_rules_still_hold_on_a_feature_branch` | pass |
| 5 yaml diff matches owner's confirmation | owner confirmed "Apply as shown"; file copied from the shown draft | pass |
| 6 session tests, cards <= 400 | `tests/tools/test_session_*.py` 456 passed; cards below | pass |
| 7 live probe | not done | open |

Added after review: two-real-worktree tests for `cd`/`pushd` (ask on main's worktree, allow on a feature worktree, ask when unresolvable or after the action), classify tests for `cd_chain`, `effective_cwd` unit test.

Cards before (PR #359 head) -> after: rpg 398/386/382 -> 398/386/383; agent-working 391/395/394 -> 391/395/396; testing 377/356/351 -> 377/356/352; codebase 377/366/363 -> 377/366/364. All at most 400.
