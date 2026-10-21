---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20261016-TOOLS-HOOK-LOADED-AND-LATE-ROWS-FLUSH
artifact_type: plan
tags: [agent-monitoring, observability, hooks]
---

# Plan — TCK-20261016-TOOLS-HOOK-LOADED-AND-LATE-ROWS-FLUSH

1. `tools/sessions/settings_freshness.py`: `monitoring_hook_line(dir)` (settings lacks the PostToolUse `post_tool_hook.py` hook, or the script is missing) and `unstaged_tool_rows_line(dir)` (uncommitted rows in any `*tools.jsonl` shard, any week). Both report-only, fail open, no fetch, no write.
2. `tools/sessions/session_start_hook.py`: emit both lines on the same sources as the session-code freshness line (startup, resume, clear; not compact).
3. Tests: fixture settings files (wired, absent, PreToolUse-only, no file, not a repo, missing script), an older-week dirty shard, a committed shard, and the SessionStart wiring.
4. No `.claude/settings.json` change, no new write path.
Scope guard: no back-fill of historical rows; the pre-push check is left as is.
