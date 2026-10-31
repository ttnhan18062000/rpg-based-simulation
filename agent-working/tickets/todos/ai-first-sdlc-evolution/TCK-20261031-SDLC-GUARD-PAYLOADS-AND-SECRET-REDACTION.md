---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261031-SDLC-GUARD-PAYLOADS-AND-SECRET-REDACTION
phase: open
date: 2026-10-31
tags: [ai, governance, security]
---

# TCK-20261031-SDLC-GUARD-PAYLOADS-AND-SECRET-REDACTION

## Title
The guard inspects interpreter payloads and asks on `gh api` writes and merges, and secret-shaped strings are redacted from tool rows and the transit export.

## Status
INPROGRESS

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
3. A `.claude/settings.json` edit is shown to the owner directly first, and shape tests are updated.
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

**ConfigChange hook:** `tools/sessions/config_change_warning.py` (warn only, exit 0, fails open) with tests. The `.claude/settings.json` wiring waits for the owner's direct OK on the exact diff (sent to agent-working-planner). Search of `tests/` for shapes pinned to settings.json: `test_settings_json_hooks_wiring.py` pins PreToolUse = 8 and PostToolUse = 5 groups and a subset of event names; `test_bash_secret_scan_hook.py` pins 4 Bash PreToolUse groups; `test_monitoring_hook_subdirectory_cwd.py` and `test_settings_json_edit_write_hook_sidecar_scope.py` pin PreToolUse indexes. A new top-level `ConfigChange` key changes none of those. `tools/capability_envelope_baseline.py` lists hook entries in `registries/capability_envelope_registry.jsonl` (15 hooks): a new hook should be registered there after the edit.

## Test Summary
(to be filled by the implementer)

## Files Changed
(to be filled by the implementer)

## Completion Summary
(to be filled by the implementer)
