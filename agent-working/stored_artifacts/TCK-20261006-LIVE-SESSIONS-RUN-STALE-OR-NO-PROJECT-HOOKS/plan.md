# Plan — TCK-20261006-LIVE-SESSIONS-RUN-STALE-OR-NO-PROJECT-HOOKS

1. `tools/sessions/settings_freshness.py`: read-only content check of a directory against `origin/main` (inside repo, settings.json, `.claude/agents/`, missing hook commands). Exit 0/1/2 (match / mismatch / cannot verify).
2. `launch.py` preflight after the role plan and before the exec line: refuse (exit 4) on mismatch or outside the repo unless `--allow-stale` (which never overrides outside-the-repo); an unverifiable ref only warns.
3. Guide: launch rule, symptoms, freshness command, `/clear` resume note in `docs/guides/agent_session_reset_boundaries.md`.
4. Re-baseline the M7 clock in epic D, the session-layer INDEX and the working-process plan (first real `manual_actions.jsonl` record + 4 weeks).
5. Live probe (Scope 5) is an owner step; recorded as not yet run.
