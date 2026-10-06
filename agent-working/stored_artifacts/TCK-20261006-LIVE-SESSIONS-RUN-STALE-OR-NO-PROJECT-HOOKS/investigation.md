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
