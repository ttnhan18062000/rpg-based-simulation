---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261008-SESSION-DISK-HEADROOM-GUARD
artifact_type: test_plan
tags: [workflows, setup]
---

# Test plan

`tests/tools/test_disk_headroom.py` (11 tests): free space vs statvfs and `df`; per-worktree run data vs `du` on a two-worktree fixture, largest first; `--json` key set and types; CLI exit 0; warning only below the threshold and naming holders (silent at the threshold); threshold default, env override, bad env; launcher warns below and does not call `measure` above; launcher warning never raises; launcher exit code identical with and without the warning; SessionStart line only below the threshold; hook failure yields no line. Regression: `test_session_launch.py`, `test_session_resolve_and_hook.py`, `test_session_start_handover_hook.py`.
