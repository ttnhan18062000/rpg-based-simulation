---
status: historical
layer: ai
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261004-CAPABILITY-ENVELOPE-COVER-HOOKS
date: 2026-10-05
tags: [ai, process-improvement, governance]
---

# Investigation: TCK-20261004-CAPABILITY-ENVELOPE-COVER-HOOKS

`tools/capability_envelope_baseline.py` audited only the four `settings.local.json` fields; hooks live in `.claude/settings.json` (14 hook commands across PreToolUse, PostToolUse, SubagentStop, SessionStart) and no registry row covered them (verified by reading the tool and the registry). Roadmap 5.8 says new hooks are registered there. Design choice: keep the `field`/`value` row schema, add a `hooks` field whose value is `<event>|<matcher>|<command>`, and read hooks from a separate `--hooks-path` so `settings.local.json` behaviour cannot change. Removed hooks are not visible in the existing report shape (it lists only live-but-unregistered values), so a hooks-only `not_in_live` list was added.
