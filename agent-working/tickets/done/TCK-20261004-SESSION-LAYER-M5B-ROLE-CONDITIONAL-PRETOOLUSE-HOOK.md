---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261004-SESSION-LAYER-M5B-ROLE-CONDITIONAL-PRETOOLUSE-HOOK
phase: done
date: 2026-10-04
tags: [ai, process-improvement, governance]
---

# TCK-20261004-SESSION-LAYER-M5B-ROLE-CONDITIONAL-PRETOOLUSE-HOOK

## Title
Session-layer M5b: role-conditional PreToolUse hook (deny, ask) with script-level fail-closed discipline

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
A `PreToolUse` hook for `Bash`, `Edit`, `Write` that resolves the caller's role from the binding record by `session_id` (falling back to the payload's `agent_type`), classifies authority-class operations, and returns deny, ask or allow per `registries/session_authority.yaml`. Per M0n the harness is fail-open on a hook crash, so the script must catch every exception itself and convert it to exit 2 or a JSON deny for authority classes.

Child of `TCK-20261002-EPIC-SESSION-LAYER-COMMUNICATION-AND-AUTHORITY`. **Hold rule: do not activate before M2a-M2b are merged** (this ticket consumes the binding record and role-state directory) and M0 results (done). Every `settings.json` or hook edit needs the owner's confirmation of the literal diff, and a settings-shape test search first (grep `tests/` for the pinned hook shape).

## Scope
- `tools/sessions/guard.py` (script) plus `tools/sessions/classify.py` (pure classifier: command or path to class). Classes: commit or push by a role that is not the worktree's writer (writer lease from M2a), merge without grant, remote-branch deletion, governing-file edits (`CLAUDE.md`, `.claude/settings.json`, hooks), edits to `registries/session_authority.yaml`.
- Decision per plan 10: forbidden -> deny; requires user -> ask; allowed -> continue; classification or parsing uncertainty (partial match, `eval`, `bash -c`, variable-expanded `git` or `gh`) -> ask, never silent allow. If ask cannot be returned, deny with a message to ask the user. Output is well-formed JSON; any exception inside the script for an authority-class input exits 2.
- Role resolution: binding record by `session_id` (M2b); unresolved role -> ask for authority classes, allow everything else (a plain `claude` session is not role-governed in v1).
- Narrow matcher (`Bash`, `Edit`, `Write`) so a bug cannot block every tool; non-authority tool calls take a fast path that cannot raise.
- Wire into `.claude/settings.json` after the permission rules of M5a; the hook adds only the role-conditional logic.

## Out of Scope
- Claiming a sandbox (plan 10 threat model), semantic or organisational boundaries (M5c advisory), changing grants.

## Acceptance Criteria
1. A classifier table test: every authority class has a matching command or path fixture and near-miss fixtures; indirection fixtures (`bash -c 'git push'`, `eval`, `$GIT push`) classify as uncertain -> ask.
2. Fail-closed discipline proven: a forced exception inside the script on an authority-class input exits 2 (positive control: an unguarded traceback exits 1 and lets the call run, as M0n measured); a forced exception on a non-authority input never blocks.
3. A non-writer role pushing in a worktree is denied or asked per the authority file; the writer is allowed per its grant; an unresolved role asks.
4. Editing `session_authority.yaml` or `settings.json` by any role asks.
5. Owner confirmed the literal `settings.json` diff; settings-shape test search recorded; scoped tests green; docs and `docs/REGISTRY.yaml` regenerated.

## Related Tickets
- `TCK-20261002-EPIC-SESSION-LAYER-COMMUNICATION-AND-AUTHORITY` (parent), M2a, M2b (hard dependencies), M5a (backstop), M5c

## Related Docs
- `docs/plans/agent_infrastructure/session_layer_working_process.md` (binding; sections 9.0, 10, 11, 12.2)
- `agent-working/stored_artifacts/TCK-20261003-SESSION-LAYER-M0-HARNESS-SPIKE/investigation.md` (M0n: exit 2 or JSON deny blocks; exit 1 and unparseable output fail open)

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261002-EPIC-SESSION-LAYER-FOUNDATION/external_reviews/`

## Related Code Areas
- `tools/sessions/guard.py`, `tools/sessions/classify.py` (new; reuse `roster.py`, `state.py`), `.claude/settings.json`, tests.

## Assumptions / Open Questions
- Whether `ask` renders in the owner's real terminal is a class-2 M0 item still unrun; until verified the fallback (deny with an ask-the-user message) is the stated behaviour. The hook must not block read-only investigation commands.

## Implementation Notes
- `tools/sessions/classify.py` (pure): `classify(tool_name, tool_input)` returns the authority-class actions (`commit`, `push`, `open_pr`, `merge`, `delete_remote_branch`, `governing_file_edit`, `authority_file_edit`) plus an `uncertain` flag. Compound commands are split and every segment checked; `git` global options (`-C`, `-c`, `--no-pager`) are skipped; shell indirection (`eval`, `bash -c`, `xargs git`, a variable-expanded verb, command substitution) and unparseable text containing an authority word are `uncertain`. Edit, Write, MultiEdit and NotebookEdit (`file_path` or `notebook_path`) are checked against the governed files and hook directories.
- `tools/sessions/guard.py`: resolves the caller by session id from the binding records (a small scan helper over the role directories, off the fast path and inside the fail-closed try, because `state.py` has no lookup by session id), falling back to `agent_type` `session-<role>`; unresolved role asks for authority classes and allows the rest. Decision order: forbidden for the function -> deny; commit/push/open_pr by a role that is not the worktree's lease holder -> deny, no lease -> ask; merge, governing-file edit, authority-file edit, remote deletion -> ask for every role (grants never override); push/open_pr -> ask unless a grant names the action (scope text is print-only); uncertain -> ask. Output is well-formed `hookSpecificOutput` JSON, exit 0.
- Fail-closed discipline (M0n): any exception on a payload that mentions an authority word exits 2; a non-authority payload exits 0 whatever happens; repo imports sit in a module-level try so a broken import is also caught. A positive-control test shows a bare traceback exits 1.
- **Missing-script hazard (found 2026-10-05):** `python3 <missing script>` exits 2, which blocks the tool call. The wiring is therefore a wrapper that resolves the repo root and treats a missing script or a non-repo cwd as a pass while forwarding the script's own exit code: `R=$(git rev-parse --show-toplevel 2>/dev/null) || exit 0; test -f "$R/tools/sessions/guard.py" || exit 0; python3 "$R/tools/sessions/guard.py"`. A subdirectory cwd cannot disable it (tested).
- Wiring (owner approved the literal text directly, 2026-10-05, after design's review answers): appended LAST in `PreToolUse` with matcher `Bash|Edit|Write|MultiEdit|NotebookEdit` (design asked for MultiEdit and NotebookEdit so they cannot bypass the governed-file check). `capability_envelope_baseline.py seed` added the hook row.
- Settings-shape test search (recorded): `test_settings_json_hooks_wiring.py` (count 7 -> 8), `test_delivery_pre_push_advisory.py` (two history pins: count and "appended last", now PreToolUse[6] with the guard at [7]; the pre-push hook itself is unmoved) and `test_bash_secret_scan_hook.py` (4 entries with matcher exactly `Bash`, unaffected because the new matcher differs). Each changed pin carries its reason.
- Review points from design: `workflow_run` is NOT enforced by this hook (the Workflow tool is not Bash/Edit/Write); it stays an explicit gap, covered today only by the CLAUDE.md opt-in rule, and could get an `ask` permission rule on the `Workflow` tool, which needs the owner's literal-text yes. `delete_worktree_or_data` stays with the M5A rules to avoid double prompts. Which wins between M5A's `--admin` deny and this guard's `merge` ask is for the M5A live probe to record.
- Operational finding: the writer lease is keyed by the physical worktree path, so after the checkout moved from `/home/...` to `/mnt/data/...` this session's lease was no longer found and the guard would have asked on every commit and push. SessionStart re-takes the lease on resume or clear; the session's own lease was re-taken with the same call SessionStart uses (`take_lease`), and a commit and push by the writer with a grant then pass without a prompt.
- Plan section 10 gets an "Implemented" note.

## Test Summary
`tests/tools/test_session_classify.py` (61) and `tests/tools/test_session_guard.py` (38 across the decision table, role resolution with two concurrent sessions, fail-closed behaviour and the wired command) pass; the hook, settings, session, capability and pre-push suites pass (549). Covered: every authority class with matching and near-miss fixtures; indirection fixtures classify as uncertain; non-writer implementer denied and writer allowed per its grant; unresolved role asks; editing the authority file or `settings.json` asks for every role; a forced exception on an authority input exits 2 and on a non-authority input never blocks; the wired command passes with no script or no repo and forwards exit 2 from a subdirectory. Not run: a live end-to-end probe in a fresh session.

## Files Changed
- tools/sessions/classify.py
- tools/sessions/guard.py
- tests/tools/test_session_classify.py
- tests/tools/test_session_guard.py
- .claude/settings.json
- registries/capability_envelope_registry.jsonl
- tests/tools/test_settings_json_hooks_wiring.py
- tests/tools/test_delivery_pre_push_advisory.py
- docs/plans/agent_infrastructure/session_layer_working_process.md

## Completion Summary
The role-conditional guard is implemented, tested and wired behind a wrapper that cannot block sessions when its script is absent.
