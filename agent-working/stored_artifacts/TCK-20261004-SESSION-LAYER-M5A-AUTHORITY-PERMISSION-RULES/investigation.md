---
status: historical
layer: ai
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261004-SESSION-LAYER-M5A-AUTHORITY-PERMISSION-RULES
date: 2026-10-05
tags: [ai, process-improvement, governance]
---

# Investigation: TCK-20261004-SESSION-LAYER-M5A-AUTHORITY-PERMISSION-RULES

Plan section 10 makes harness permission rules the primary backstop for command patterns, because the PreToolUse hook is fail-open on a crash (M0n). The inventory (merge, remote deletion, force push, worktree removal, shard removal) came from the plan; evidence of what `settings.local.json` already allows shows `git *` and `rm *` are allowed, and ask/deny override allow. The harness pattern syntax differs from a plain glob in one case (`*` before a trailing `:*`), which only a live session shows.
