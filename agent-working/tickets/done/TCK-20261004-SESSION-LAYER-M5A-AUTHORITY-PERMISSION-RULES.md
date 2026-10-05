---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261004-SESSION-LAYER-M5A-AUTHORITY-PERMISSION-RULES
phase: done
date: 2026-10-04
tags: [ai, process-improvement, governance]
---

# TCK-20261004-SESSION-LAYER-M5A-AUTHORITY-PERMISSION-RULES

## Title
Session-layer M5a: harness-native permission rules for authority-class commands

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Declare the authority-class command patterns as harness `permissions` ask and deny rules: they are the primary backstop because the `PreToolUse` hook fails open on a crash (M0n). Rules apply with or without the hook running.

Child of `TCK-20261002-EPIC-SESSION-LAYER-COMMUNICATION-AND-AUTHORITY`. **Hold rule: do not activate before M2a-M2b are merged** (this ticket consumes the binding record and role-state directory) and M0 results (done). Every `settings.json` or hook edit needs the owner's confirmation of the literal diff, and a settings-shape test search first (grep `tests/` for the pinned hook shape).

## Scope
- Inventory the authority-class commands from plan section 10: merge without authority (`gh pr merge`, including `--admin`), remote-branch deletion (`git push` with a delete refspec or `--delete`, `gh api -X DELETE .../git/refs`), force push, `git worktree remove`, removal of run data and shards.
- Add `ask` rules for user-required actions and `deny` rules for forbidden ones in `.claude/settings.json` `permissions`, following the existing allow/ask structure. Decide per rule with evidence of what is already allowed in `settings.local.json`; do not widen any allow.
- A rule test harness: for each rule, a fixture command that must match, and near-miss commands (read-only `git push --dry-run`, `gh pr view`) that must not.
- Record each rule's pattern, class and rationale in the plan's section 10 or a guide; register the change in the capability envelope baseline if the hooks/permissions extension has landed.

## Out of Scope
- The role-conditional hook (M5b), allowlists and advisory events (M5c). No change to existing allow rules.

## Acceptance Criteria
1. Each authority-class command pattern is covered by a permission rule; the harness blocks or asks without the hook installed (verified by a probe with a positive control that an unlisted command runs).
2. Near-miss read-only commands are not caught.
3. Owner confirmed the literal `settings.json` diff; recorded in the ticket; the settings-shape test search is recorded and any pinned-shape test is updated, not weakened.
4. Scoped tests green; docs and `docs/REGISTRY.yaml` regenerated.

## Related Tickets
- `TCK-20261002-EPIC-SESSION-LAYER-COMMUNICATION-AND-AUTHORITY` (parent), M2 (not required for M5a itself; it can land first), M5b

## Related Docs
- `docs/plans/agent_infrastructure/session_layer_working_process.md` (binding; sections 9.0, 10, 11, 12.2)
- `agent-working/stored_artifacts/TCK-20261003-SESSION-LAYER-M0-HARNESS-SPIKE/investigation.md` (M0n: exit 2 or JSON deny blocks; exit 1 and unparseable output fail open)

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261002-EPIC-SESSION-LAYER-FOUNDATION/external_reviews/`

## Related Code Areas
- `.claude/settings.json`, tests pinning hook/permission shape, `docs/guides/`.

## Assumptions / Open Questions
- Pattern fragility (variable-expanded `git`, `bash -c`) is why the hook asks on uncertainty (M5b); this ticket does not try to solve indirection.

## Implementation Notes
- **Rules (owner approved the literal diffs directly in the implementer terminal, 2026-10-05, three rounds):** `.claude/settings.json` `permissions` gained an `ask` list and a `deny` list; no `allow` rule changed; no ask rule for `data/runs` removal (owner decision; the close-out uses it). Final text: ask `Bash(gh pr merge *)`, `Bash(git push --delete *)`, `Bash(git push * --delete *)`, `Bash(gh api -X DELETE *)`, `Bash(gh api --method DELETE *)`, `Bash(git push --force*)`, `Bash(git push * --force*)`, `Bash(git push -f *)`, `Bash(git push * -f*)`, `Bash(git worktree remove *)`, `Bash(rm *agent-working/agent-monitoring/*)` and the bare `Workflow` tool; deny `Bash(gh pr merge*--admin*)`.
- Class and rationale per rule: merge without authority (`gh pr merge`, user only; `--admin` denied outright, the delivery guide says an agent never retries with it); remote-branch deletion (needs the user); force push (needs the user); `git worktree remove` (delete_worktree_or_data); removal of monitoring shards (audit-trail tampering); `Workflow` (workflow_run is invisible to the Bash/Edit/Write guard, and CLAUDE.md requires the user's opt-in).
- Settings-shape test search: `test_settings_json_hooks_wiring.py` pins hook counts and that `permissions.allow` exists; nothing pins the permissions block beyond that.
- Harness: `tests/tools/test_settings_permission_rules.py` (must-match and near-miss fixtures per class, deny-admin, no widened allow, no data-runs ask, no wildcard mixed with the trailing `:*` syntax, Workflow asked). It first found three gaps in the initial pattern text (bare trailing `-f`, `merge --admin 5` only asked, bare `rm agent-working/...`); the owner approved corrected text.
- **Live probe with positive controls (fresh headless `claude -p` sessions in this worktree, 2026-10-05):** `git status --short` RAN (positive control: an unlisted command runs); `gh pr merge --admin 999999` DENIED by the permission rule and not by the later guard ask, so **a permission deny beats the guard's `merge` ask**; `gh pr merge 999999`, `git push --force ...`, `git push origin main -f --dry-run`, `gh api -X DELETE ...`, `git worktree remove ...` and `rm -f agent-working/agent-monitoring/...` were all refused (headless sessions cannot answer an ask, so asks surface as "not granted"); `git push origin :zzz...` and `touch CLAUDE.md` were refused by the session-roles guard (unresolved role asks for authority classes). The running session's own settings had been loaded before the edit, so its first probe (`gh pr merge 999999 --admin`) was not blocked: rule changes only take effect in a fresh session.
- **Defect found by the probe, fixed:** the harness warns at every session start that `Bash(git push * :*)` mixes `*` with the trailing `:*` prefix syntax and is matched as a literal prefix, so it never matched `git push origin :branch`. My static harness had treated `*` as a plain glob and missed it. The owner approved removing the rule; refspec deletes stay covered by the guard (probe above). The warning is gone in a fresh session (a different, pre-existing warning about a `settings.local.json` allow rule remains and is not part of this ticket).

## Test Summary
`tests/tools/test_settings_permission_rules.py` passes (18 with the hooks-wiring file); the earlier static harness could not see the `:*` prefix quirk, which only the live probe exposed. Live probes listed above, run against fresh sessions with a positive control.

## Files Changed
- .claude/settings.json
- tests/tools/test_settings_permission_rules.py

## Completion Summary
Authority-class commands now ask or are denied by harness-native permission rules, verified in fresh sessions, with the guard hook as the role-aware second layer.
