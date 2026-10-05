---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261004-SESSION-LAYER-M5B-ROLE-CONDITIONAL-PRETOOLUSE-HOOK
phase: open
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
- **Not started; the settings wiring was deliberately NOT applied.** The owner approved the literal hook entry (append LAST in `PreToolUse`, matcher `Bash|Edit|Write`, command `python3 tools/sessions/guard.py`) believing it would stay inert until the script exists. It would not: measured here, `python3 tools/sessions/guard.py` with no such file exits **2**, and a PreToolUse hook exiting 2 blocks the tool call, so wiring it first would block every Bash, Edit and Write call in every session. The wiring therefore lands in the same change as `tools/sessions/guard.py` and `classify.py`.
- Settings-shape test search (recorded): `test_settings_json_hooks_wiring.py` pins `len(PreToolUse) == 7` (becomes 8 with a stated reason) and `test_bash_secret_scan_hook.py` pins exactly 4 entries with matcher `Bash` plus indexes [1], [3], [4]; the new entry must be last with matcher `Bash|Edit|Write` so neither pin breaks beyond the count. A `capability_envelope_baseline.py seed` row is also needed after wiring.
- The guard script must itself exit 0 for non-authority input and fail closed (exit 2) only for authority classes, never on a missing import for other inputs.

## Test Summary
Not started.

## Files Changed
None yet.

## Completion Summary
Not started.
