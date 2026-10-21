---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20261016-TOOLS-HOOK-LOADED-AND-LATE-ROWS-FLUSH
artifact_type: test_plan
tags: [agent-monitoring, observability, hooks]
---

# Test plan — TCK-20261016-TOOLS-HOOK-LOADED-AND-LATE-ROWS-FLUSH

- AC "a session without the hook gets one line": `tests/tools/test_session_settings_freshness.py` — wired worktree gets no line; settings without the hook, a PreToolUse-only mention, no settings file, and a missing script each get one `monitoring:` line; a non-repo directory gets none.
- AC "late-row decision": the reminder is tested with an uncommitted older-week shard (counts rows and files, names the weeks) and with a committed shard (no line).
- Wiring: `tests/tools/test_session_resolve_and_hook.py` — both lines appear once on startup and are absent on `compact`.
- Guard: `tests/tools/test_agent_working_paths_guard.py` (path constants).
