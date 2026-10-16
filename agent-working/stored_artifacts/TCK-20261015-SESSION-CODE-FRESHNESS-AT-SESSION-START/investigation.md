---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261015-SESSION-CODE-FRESHNESS-AT-SESSION-START
artifact_type: investigation
tags: [hooks, process-improvement]
---

# investigation — TCK-20261015-SESSION-CODE-FRESHNESS-AT-SESSION-START

Source: RETRO-2026-W41 final note finding 4. The hook runs the worktree's own copy of `tools/sessions/session_start_hook.py`. On 2026-10-15 a cleared rpg-implementer-2 was given `.claude/handover/rpg-implementer.md` by the `rpg` worktree (rpg-seat, 108 commits behind) that lacks #491's per-instance code; the same cause bound an rpg-implementer-3 launch as rpg-implementer on 2026-10-09. `settings_freshness.py` compared only `.claude/settings.json` and `.claude/agents/`, and only `launch.py` called it, so a plain `claude --resume` or `/clear` skipped it.
