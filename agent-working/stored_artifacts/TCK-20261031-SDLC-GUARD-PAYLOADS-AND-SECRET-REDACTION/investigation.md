---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261031-SDLC-GUARD-PAYLOADS-AND-SECRET-REDACTION
artifact_type: investigation
tags: [ai, governance, security]
---

# Investigation

- Route checks: `post_tool_hook.py`, `handover_transit.py`, `classify.py` and `guard.py` route to the agent-working domain; `.claude/settings.json` and `tools/write_path_guard.py` are unowned (the latter was not edited).
- The four bypass forms in the plan's P-1 were probed against `classify_command` before the change: a wrapper before the command, an interpreter payload, `gh api -X PUT`, and `--delete-branch` all produced no action. Already classified: `git push origin main`, `gh pr merge`, `gh api -X DELETE`, `bash -c`/`eval`/`xargs` (uncertain).
- Redaction: `write_path_guard.py` already holds the shape list that the Bash secret-scan hook uses, so the redactor reuses it instead of adding a second list. JWTs and hyphenated `sk-proj-` keys are not in that list, and widening it changes what a blocking hook rejects; this is a Known gap, not a change here.
- ConfigChange hook input (hooks.md, read from the raw markdown): `source` always, `file_path` optional, common fields include `session_id`. ConfigChange discards `systemMessage` and `continue`; `terminalSequence` is honoured in interactive sessions only and the whole field is ignored if it holds anything outside OSC 0/1/2/9/99/777 and BEL. The docs do not say whether an agent's own edit fires the event, and `CLAUDE.md` is not in the matcher table.
- The owner's live test (2026-10-31, commit `75961d563`) showed: hand edits to the settings file and to a skill file fire the event; `CLAUDE.md` does not; one agent Edit that landed fired it in its own session; real events carry the four fields the script reads plus `cwd`, `prompt_id`, `scratchpad_dir`, `transcript_path` and sometimes `agent_type`.
- Settings shape tests: a new top-level `ConfigChange` key changes none of the pinned shapes (PreToolUse = 8 groups, PostToolUse = 5, 4 Bash PreToolUse groups, the index pins).
