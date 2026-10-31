---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261031-SDLC-GUARD-PAYLOADS-AND-SECRET-REDACTION
phase: done
date: 2026-10-31
tags: [ai, governance, security]
---

# TCK-20261031-SDLC-GUARD-PAYLOADS-AND-SECRET-REDACTION

## Title
The guard inspects interpreter payloads and asks on `gh api` writes and merges, and secret-shaped strings are redacted from tool rows and the transit export.

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
The Phase 1 code items (plan section 39) that change no credential or ruleset. They are second-line controls, and redaction protects the later credential work.

## Scope
1. `tools/sessions/guard.py` and `classify.py`: inspect `python -c`, `node -e` and `env` payloads; add `ask` for `gh api` PUT and merge, and for `--delete-branch`. Cover the four bypass forms in the plan's P-1.
2. A `ConfigChange` warning hook.
3. Redact secret-shaped substrings in `post_tool_hook.py` tool rows and in `handover_transit.py` export, with a positive control.

## Out of Scope
- Any credential or ruleset change.
- Treating the guard as a boundary: the plan calls it mistake reduction.
- Rewriting existing monitoring rows.

## Acceptance Criteria
1. Each of the four bypass forms now classifies as `ask` or `deny`, with a test; ordinary commands stay allowed, with a test.
2. A token-shaped string in a tool input never reaches a shard or a transit bundle, with a test.
3. A `.claude/settings.json` edit is shown to the owner directly first, and shape tests are updated. Shown by the live test: a hand edit to the settings file or a skill file fires the ConfigChange hook, and so did one agent edit that landed; `CLAUDE.md` does not fire it.
4. `tests/tools/` passes in a lead slot.

## Related Tickets
- TCK-20261031-EPIC-AI-FIRST-SDLC-EVOLUTION

## Related Docs
- docs/plans/agent_infrastructure/AI_FIRST_SDLC_ARCHITECTURE_EVOLUTION_PLAN.md
- docs/plans/agent_infrastructure/AI_FIRST_SDLC_DECISION_SUMMARY.md

## Related Stored Artifacts
- none

## Related Code Areas
- tools/sessions/guard.py, tools/sessions/classify.py
- tools/agent-monitoring/post_tool_hook.py, tools/handover_transit.py
- .claude/settings.json

## Assumptions / Open Questions
- Owner condition #715 6528807751: credential details from either host stay out of committed files, tickets and public comments unless a decision needs them; they go to the owner directly.
- No credential or ruleset change is authorised by the epic; each gets its own owner ask, by ticket.
- Undecided, and not to be written as decided: OD-4 to OD-9, OD-11 to OD-13, OD-16 to OD-21.
- `.claude/settings.json` is a governing file: it needs the owner's own OK, asked directly.

## Implementation Notes
Branch `agent-working-sdlc-guard-payloads` off `origin/main` 6fdfdf555. Route checks: `post_tool_hook.py`, `handover_transit.py`, `classify.py` and `guard.py` all route to the agent-working domain; `.claude/settings.json` is unowned (a governing file, owner-approved edits only).

**The four forms, checked against `classify.py` before this change** (probe of `classify_command`, 2026-10-31):

| Form | Example | Before | After |
|---|---|---|---|
| wrapper before the command | `env git push origin main` (also `command`, `nohup`, `time`, `exec`, `nice -n 5`, `timeout 60`) | no action | push + push_default_branch (ask) |
| interpreter payload | `python3 -c "...['git','push','origin','main']..."`, `node -e "...git push..."` | no action | push, uncertain (ask) |
| `gh api -X PUT` | `gh api -X PUT repos/o/r/pulls/1/merge`, `--method PUT`, `-XPUT` | no action | merge (ask); any other PUT also asks |
| `--delete-branch` | `gh pr close 5 --delete-branch` (also `-d`) | no action | delete_remote_branch (ask) |

Already classified before: `git push origin main`, `gh pr merge` (merge), `gh api -X DELETE` (delete_remote_branch), `bash -c`/`eval`/`xargs` (uncertain).

**Also classified (planner review):** `gh api` writes by other routes. `POST .../merges` and a GraphQL `mergePullRequest` or `enablePullRequestAutoMerge` are merges; `DELETE` on any endpoint and GraphQL `deleteRef` are remote deletions; a `PATCH` on `git/refs/heads/<default branch>` is a push to the default branch; a `POST` or `PATCH` on `git/refs` and GraphQL `updateRef`/`createRef` are pushes whose target cannot be told, so they are uncertain and ask. The spellings `-X PUT`, `-XPUT`, `--method PUT`, `--method=PUT` and fields implying POST (`-f`, `-F`, `--field`, `--raw-field`, `--input`) are all tested. A `gh api` call is read from the raw command text (so a GraphQL body is seen), through wrappers and inside compound commands.

**Kept allowed (tests):** read-only `python3 -c` (print, json, yaml loads, the word 'commit' in a string), `node -e` console.log, `gh api` GET and the default method, `gh api -X PATCH` on a pull request (the PR-body edit path), `gh api` POST of a comment, a GraphQL query and a non-merge mutation (`addComment`), `gh pr view/checks/list/close` without `--delete-branch`, `gh run list`, `command -v git`, `env VAR=1 python3 x.py`, an own-branch push after a harmless `python3 -c`, and text that merely mentions an API call (`echo 'gh api -X PUT'`, a commit message).

**What "not covered" means.** This guard is mistake reduction, not a boundary (plan section 10): it reads command text and nothing more, and anyone or anything determined to push, merge or delete can write the command so the guard does not see it. These forms are not recognised, on purpose or for cost: a payload that builds its words (`'pu' + 'sh'`); a Python or Node script file, or a heredoc fed to an interpreter (`python3 - <<EOF`); `env -S "git push ..."` (the quoted string is read as data); `sudo` and `su -c`; a `git` alias or a hook that pushes; a command assembled in a variable. The server-side rules (the ruleset and, later, the machine user) are the control; the guard only catches an honest slip.

**Redaction (planner review: one shape list, not two).** `tools/agent-monitoring/secret_redact.py` reuses the compiled patterns of `tools/write_path_guard.py::_SECRET_SCAN_PATTERNS`, the list `scan_for_secrets` already uses for the Bash hook, and only chooses which to redact; it adds no pattern. Redacted: AWS access key, PEM private-key header (and the rest of its block), Bearer token, GitHub token, Slack token, `sk-ant-` and `sk-` keys, credentials in a URL, and `api_key="..."` assignments. Left out: `password=`/`secret=` assignments (false positives). Not covered because the shared list lacks them (widening it is a separate decision, and `write_path_guard.py` is unowned): JWTs, and an `sk-` key with a hyphen in its first 20 characters (`sk-proj-...`); a test states both limits. A hyphenated `sk-ant-` key is redacted whole (tested). I did not edit `write_path_guard.py` or remove any shape from the scan.
- Import direction and speed: the hook imports `write_path_guard` (stdlib only: hashlib, re, sqlite3, dataclasses, pathlib; about 10 ms, measured once) which the Bash hook already loads on every command.
- **If redaction fails**, nothing raw is written and nothing raises. Hook: if the redactor cannot be imported or fails, `input_summary` is `[REDACTION_FAILED]` (identifier fields are left alone, since a marker in `ts` would corrupt the row); a failure on one value marks that value. Transit export: a file whose redaction fails is left out of the bundle and named in the manifest as `{"skipped": "redaction_failed", "error": <class>}`; the export prints a warning and import ignores skipped rows. Tests cover both.
- **Fields covered, `post_tool_hook.py` (every field it writes):** `input_summary` (the only free text: a file path, a Bash command, an Agent description or prompt, an MCP query, or any other tool's input) is redacted before it is cut to 80/120 characters, so a token the cut would split is still replaced; then every string field of the row (`session_id`, `run_id`, `phase`, `agent`, `ts`, `tool`, `status`, `execution_id`, `provider`, `ticket_id`, `error_class`) goes through the redactor too. The hook stores no error text, only `error_class`. Not covered: other writers of free text into shards (`record_events` and the closure tool's event summaries, `working_log.csv`), which take text typed by a session, not tool input.
- **Files covered, `handover_transit.py` export:** every file the bundle carries, by raw bytes, whatever its type: role notes (`.md`), drafts (`.md`, `.yaml`, `.json`, anything else) and memory files, including non-UTF-8 content. The manifest row records `redacted: N` and the hash of the stored file, so import still verifies; the local files are never changed. Not covered: file names and the manifest's own `worktree`/`branch` fields.
- Redaction is on write only; existing rows and bundles are not rewritten. Tests build every fake token by concatenation, and the last test scans the new files with the repository's own `scan_for_secrets` after a positive control.

**ConfigChange hook:** `tools/sessions/config_change_warning.py`, wired in `.claude/settings.json` as one new top-level `ConfigChange` key at the start of `hooks` (the exact text of #715 6543054968, approved by the owner). Order of events: my own Edit of that file was refused by the auto-mode classifier (`[Self-Modification]`, no prompt reached the owner); the owner then allowed lead-planner to make the same edit in this worktree, uncommitted (#715 6543728270), and I compared it byte for byte with 6543054968 before committing it. The hook was first written to warn through `systemMessage`; the hooks documentation (hooks.md, "ConfigChange decision control") says ConfigChange discards `systemMessage` and `continue`, so the owner chose option (a) (#715 6543766327): change only the script. It now returns `{"terminalSequence": ...}` (OSC 9 and OSC 777 notifications plus a bell, all values stripped of control characters and `;`) and appends one JSON line per event to `tmp/config_change.log` (gitignored): time, `hook_event_name`, `source`, `file_path`, `session_id` and the sorted top-level key names, nothing else from the event. (`session_id` goes slightly past the owner's "source, path and time": it is an identifier, not a credential, and without it a line cannot be tied to the session that saw the change; lead-planner was told.) The log and the notification fail independently; the script always exits 0. The agent is not told: that would need new settings text and a fresh ask. Registered in `registries/capability_envelope_registry.jsonl` (`hooks` = `ConfigChange||<command>`, `reviewed: true`); nine older hooks were already outside that registry and are untouched.

Search of `tests/` for shapes pinned to settings.json: `test_settings_json_hooks_wiring.py` pins PreToolUse = 8 and PostToolUse = 5 groups and a subset of event names; `test_bash_secret_scan_hook.py` pins 4 Bash PreToolUse groups; `test_monitoring_hook_subdirectory_cwd.py` and `test_settings_json_edit_write_hook_sidecar_scope.py` pin PreToolUse indexes. A new top-level `ConfigChange` key changes none of those. Four new wiring tests (one group, fail-open command, runs from the repo and prints the sequence, silent outside a git repo, registry row) are in `tests/tools/test_config_change_warning.py`; the wiring test sets `CONFIG_CHANGE_WARNING_LOG` so it writes no line into the real `tmp/`.

**Live test (owner, 2026-10-31, commit `75961d563`; throwaway session `e7f09076` started in auto mode with `--session-id`, the implementer's session `0a8bb26e` also in the worktree; planner and lead-planner read `tmp/config_change.log` and the debug log).**
- `.claude/settings.json` edited by hand: the event fired for the edit and for the restore (13:56:53, 13:57:07), `source` `project_settings`.
- A skill file (`.claude/skills/api-design-principles/SKILL.md`) edited by hand: the event fired for the edit and the restore (13:57:15, 13:57:21), `source` `skills`.
- `CLAUDE.md` edited by hand: no log line and no debug line, from any session. `CLAUDE.md` is **not covered**; it stays with TCK-20261031-GOVERNING-FILE-EDITS-VISIBLE-TO-OWNER.
- An agent edit (the Edit tool, in the throwaway session): the edit landed at 13:58:09 with no refusal and no prompt visible in the transcript's tool results; the same session logged at 13:58:12 (debug: "Detected change") and again on the restore at 13:58:24. So on this one sample an agent edit that lands is covered.
- Notification: the owner reports that the bell icon and sound appeared. The report is not per step, so it is not claimed per step here.
- Field names from real events: `hook_event_name`, `source`, `file_path` and `session_id` are present as the script reads them. Real events also carry `cwd`, `prompt_id`, `scratchpad_dir`, `transcript_path` and (in the implementer's session) `agent_type`; the docs' example does not list all of them. The script reads only the four.
- The implementer's session logged the same changes with its own `session_id` (and lagged on one: the skill change at 13:57:43), so every session in the worktree warns separately and duplicates are expected.

## Test Summary
Full `tests/tools` at `f5b9469fe` (lead-planner slot, `-n 2`, cores 4-5, 3G cap, 21:07-21:14, 6 min 42 s): 5430 passed, 56 skipped, 1 xfailed, 1 failed. The failure was `test_generate_registry.py::TestRealDocsTree::test_check_flag_detects_no_drift_against_real_registry`: the registry was stale until the two tickets of this batch were closed and `docs/REGISTRY.yaml` regenerated; after the close and regeneration, `test_generate_registry.py` and `tests/docs` were rerun: 160 passed, 2 skipped, 1 xfailed. `tests/docs` at the same commit: 91 passed, 2 skipped, 1 xfailed.
Scoped runs during the work: the guard payload, classify and redaction tests, and the ConfigChange, settings-wiring and capability-envelope tests (33 passed, 1 skipped before the session-id change; 14 passed in `test_config_change_warning.py` after it).
Live test of the ConfigChange hook by the owner: see Implementation Notes.

## Files Changed
- `tools/sessions/classify.py`, `tools/sessions/config_change_warning.py` (new); `tools/sessions/guard.py` is unchanged (it calls `classify.py`)
- `tools/agent-monitoring/secret_redact.py` (new), `tools/agent-monitoring/post_tool_hook.py`, `tools/handover_transit.py`
- `.claude/settings.json` (one `ConfigChange` hook key, owner-approved text), `registries/capability_envelope_registry.jsonl` (one row)
- `tests/tools/test_session_guard_payloads.py`, `tests/tools/test_config_change_warning.py`, `tests/tools/test_secret_redact.py` (new); the transit export is covered in `test_secret_redact.py`
- this ticket and its three standard-tier artifacts; `docs/REGISTRY.yaml`; agent-monitoring shards

## Completion Summary
Delivered: the guard classifies wrapper-prefixed commands, interpreter payloads, `gh api` writes and merges, and `--delete-branch` (tests in `tests/tools/test_session_guard_payloads.py`, ordinary commands stay allowed); secret-shaped strings are redacted from tool rows and the transit export (`tools/agent-monitoring/secret_redact.py`); and the ConfigChange hook is wired and notifies, verified by the owner's live test above. AC3 as shown: a hand edit to `.claude/settings.json` or a skill file fires the hook, one agent edit that landed also fired it (one sample, auto mode), and `CLAUDE.md` does not.

Known gap: `CLAUDE.md` edits are not covered by the ConfigChange hook (no event); that stays with TCK-20261031-GOVERNING-FILE-EDITS-VISIBLE-TO-OWNER.
Known gap: the ConfigChange warning reaches only sessions on a tree that has the hook, and only the user, as a terminal notification; the agent is not told. Every session in a worktree warns separately, so duplicates are expected and one session may lag. After this merges, a checkout or merge that changes a watched file also fires it, so expect some noise.
Known gap: agent-edit coverage rests on one sample in auto mode; whether the Edit tool always fires the event, and what happens in other permission modes, is not shown.
Known gap: JWTs and `sk-proj-` keys (an `sk-` key with a hyphen in its first 20 characters) are not redacted, because the shape list is `write_path_guard.py`'s and is shared with the Bash secret-scan hook; widening it changes what a blocking hook rejects (and a hyphen-tolerant `sk-` pattern with no word boundary would also match names like `task-some-long-hyphenated-name`), so it is its own decision.
Known gap: typed text written by other tools into committed files (`record_events` and closure event summaries, `working_log.csv`) is not redacted; only tool rows and the handover transit export are covered.
