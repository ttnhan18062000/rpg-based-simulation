---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261006-SETTINGS-OWN-BRANCH-PERMISSION-PROMPTS
phase: done
date: 2026-10-06
tags: [ai, hooks, delivery]
---

# TCK-20261006-SETTINGS-OWN-BRANCH-PERMISSION-PROMPTS

## Title
Own-branch force-push and `gh pr create` still prompt, because the static permission lists contradict the owner's own-branch rule

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Owner rule (2026-10-06): "only block the merge branch to main, every action on their own branch is allowed".
TCK-20261006-GUARD-OWN-BRANCH-GIT-ALLOWED made `tools/sessions/guard.py` stop asking for own-branch commit, push,
force-push, local merge and PR create. The guard can only return `deny` or `ask` (`guard.py` :61, :206); it never
returns `allow`. Prompts are therefore still decided by the static lists in `.claude/settings.json` on origin/main:
- `permissions.ask` has `Bash(git push --force*)`, `Bash(git push * --force*)`, `Bash(git push -f *)` and
  `Bash(git push * -f*)`, so own-branch force-push still prompts;
- `permissions.allow` has `Bash(git *)` but nothing for `gh pr create`, so PR creation still prompts.

## Scope
1. In `.claude/settings.json`:
   - add `Bash(gh pr create *)` to `permissions.allow`;
   - remove the four force-push patterns from `permissions.ask`.
   Keep `gh pr merge *`, remote-branch delete and `git worktree remove` on ask, and keep the `--admin` deny.
2. Before the edit, show the owner the literal diff via AskUserQuestion. Session-layer hold rule: no settings or
   hook change lands without that confirmation.
3. Confirm by test that the guard still asks for a force-push to the default branch, so the protection moves from
   the static list to the guard rather than disappearing. Add the test if `tests/tools/test_session_guard.py` lacks
   it.

## Out of Scope
- Making the guard load in live sessions: TCK-20261006-LIVE-SESSIONS-RUN-STALE-OR-NO-PROJECT-HOOKS. The settings
  file is loaded as a whole, so any session that sees the relaxed permissions also loads the guard hook in the same
  file.
- Server-side branch protection on GitHub.

## Acceptance Criteria
1. The owner confirmed the literal diff. Record the date in Implementation Notes.
2. `settings.json` parses, the allow list contains `Bash(gh pr create *)`, and the ask list contains none of the
   four force-push patterns.
3. A guard test shows `git push --force origin main` (and the `-f` form) classify as ask. A test shows an
   own-branch force-push gets no deny or ask from the guard.

## Related Tickets
- TCK-20261006-GUARD-OWN-BRANCH-GIT-ALLOWED
- TCK-20261006-LIVE-SESSIONS-RUN-STALE-OR-NO-PROJECT-HOOKS

## Related Docs
- `agent-working/agent-monitoring/retro/RETRO-2026-W41.md` (Notes, proposal 1)

## Related Stored Artifacts
- none

## Related Code Areas
- `.claude/settings.json`, `tools/sessions/guard.py`, `tests/tools/test_session_guard.py`

## Assumptions / Open Questions
- None.

## Implementation Notes
Owner confirmed the literal diff through AskUserQuestion on 2026-10-06 ("Apply as shown"): `Bash(gh pr create *)` added to allow; the four force-push patterns removed from ask. Kept on ask: gh pr merge, push --delete, gh api DELETE, git worktree remove, rm in agent-monitoring, Workflow; kept deny: gh pr merge --admin. Verified against origin/main 9299891a9 (`guard.py` DENY/ASK at :61).

## Test Summary
`tests/tools/test_session_guard.py`: 133 passed (5 new: four force-push-to-main forms ask, settings.json parse/allow/ask contents). Own-branch force-push no-ask was already covered by test_own_branch_actions_are_allowed_with_or_without_a_lease. Correction: the first closure missed `tests/tools/test_settings_permission_rules.py`, which pinned the removed force-push ask rules and failed; it now asserts no static ask rule for force-push (the guard test covers the default branch). Found when running every test that reads settings.json (381 passed, 1 skipped).

## Files Changed
`.claude/settings.json`, `tests/tools/test_session_guard.py`, `tests/tools/test_settings_permission_rules.py`.

## Completion Summary
Own-branch `gh pr create` and force-push no longer prompt from the static lists; force-push to the default branch is still asked by the guard (tested). The relaxed lists load together with the guard hook, but only in sessions that load the project settings (see TCK-20261006-LIVE-SESSIONS-RUN-STALE-OR-NO-PROJECT-HOOKS).
