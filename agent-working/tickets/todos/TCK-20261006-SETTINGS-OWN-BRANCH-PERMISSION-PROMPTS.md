---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261006-SETTINGS-OWN-BRANCH-PERMISSION-PROMPTS
phase: open
date: 2026-10-06
tags: [ai, hooks, delivery]
---

# TCK-20261006-SETTINGS-OWN-BRANCH-PERMISSION-PROMPTS

## Title
Own-branch force-push and `gh pr create` still prompt, because the static permission lists contradict the owner's own-branch rule

## Status
OPEN

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

## Test Summary

## Files Changed

## Completion Summary
