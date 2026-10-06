# Investigation — TCK-20261006-LIVE-SESSIONS-RUN-STALE-OR-NO-PROJECT-HOOKS

Run on origin/main 9299891a9 with `settings_freshness.py`:
- `/mnt/data/Working` (not a git repo): MISMATCH, outside the repo.
- `/mnt/data/Working/rpg-based-simulation` (main checkout): MISMATCH: settings.json differs, 4 hook commands missing (edit_ratchet PostToolUse, session guard PreToolUse, SessionStart hook, manual_actions UserPromptSubmit), 4 agent files differ, 12 `session-*` agent files missing.
- A fresh `git worktree add --detach origin/main`: match (unit-tested in a simulated repo).

Design choices:
- Content comparison, not commit distance (a branch 57 commits behind that changed nothing under `.claude/` is fine).
- A branch that itself edits settings.json reports a difference (e.g. the branch carrying TCK-20261006-SETTINGS-OWN-BRANCH-PERMISSION-PROMPTS until it merges); `--allow-stale` covers it.
- The ref is never fetched: an offline or never-fetched checkout gets exit 2 / a warning, not a refusal.
- The preflight skips a worktree directory that does not exist (self-heal creates it from the role's branch).

## (b) manual_actions and session_role dark where SessionStart binds a role (Scope 6, added 2026-10-06)

Evidence list is in the ticket's Implementation Notes. Commands: `git log -S'manual_actions.py' -- .claude/settings.json` (landed 58aa22f67, 2026-10-05T17:43+07); the settings.json UserPromptSubmit command run with a sample payload from a current worktree (wrote a row); `resolve_session_role(<bound session id>, <worktree>)` (returns the role) versus cwd `/mnt/data/Working` (unresolved); stamped versus absent `session_role` in W41 runs on origin/main (30 stamped, all unresolved; 33 absent); a settings and `manual_actions.py` presence check over the 20 local worktrees (9 lack the sampler).
