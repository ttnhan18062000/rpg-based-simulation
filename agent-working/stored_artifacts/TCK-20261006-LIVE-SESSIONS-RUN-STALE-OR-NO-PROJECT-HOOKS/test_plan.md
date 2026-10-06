# Test Plan — TCK-20261006-LIVE-SESSIONS-RUN-STALE-OR-NO-PROJECT-HOOKS

`tests/tools/test_session_settings_freshness.py` (real git repos, origin/main simulated with update-ref):
1. AC1: fresh detached worktree matches; missing hook named; differing and missing agent file; outside the repo (names both symptoms); missing ref is UNKNOWN; read-only.
2. AC2: `launch.py --dry-run` on a stale worktree exits 4 with the mismatch and no DRY RUN line; `--allow-stale` prints DRY RUN; fresh prints no noise; allow-stale never launches outside the repo; unverifiable ref warns only.
3. AC3, AC4: doc edits (read in review). AC5: owner step, not yet run.
