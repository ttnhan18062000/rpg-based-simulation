---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260904-SIDECAR-SETTINGS-HOOK-MIGRATE
phase: done
date: 2026-09-04
tags: [ai, hooks, agent-monitoring]
---

# TCK-20260904-SIDECAR-SETTINGS-HOOK-MIGRATE

## Title
Migrate settings.json PreToolUse hook to session-scoped sidecar reads

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE added a session-scoped `.claude/current_run.<SESSION_ID>` variant because the old unscoped file was silently overwritten by concurrent sessions, misattributing `tools.jsonl` rows, and left two consumers explicitly reading the old unscoped file. Investigation found this framing is now stale: `tools/retrieval_cache.py`'s `read_current_run_sidecar()` was already migrated by TCK-20260824-RETRIEVAL-CACHE-SIDECAR-UNIFY (closed 2026-08-24), so only one real straggler remains — `.claude/settings.json`'s inline `Edit|Write` PreToolUse hook (line 88), which still reads `.claude/current_run` directly via `python3 -c` with no session scoping. This ticket is scoped down to that single file to avoid duplicate effort on the already-fixed consumer.

## Scope
- Update `.claude/settings.json`'s `Edit|Write` PreToolUse hook (inline `python3 -c` one-liner, line 88) to read the scoped sidecar file `.claude/current_run.<CLAUDE_CODE_SESSION_ID>` first (via `os.environ.get`), falling back to the unscoped `.claude/current_run` when the scoped file doesn't exist — same preference order as `read_current_run_sidecar()`/`post_tool_hook.py`
- Verify a synthetic two-session scenario (two distinct scoped files with different run_ids, plus a stale/foreign unscoped file) resolves RUN_ID to the calling session's own value, not the foreign one
- Add a new regression-guard test mirroring `test_current_run_sidecar_orchestrator.py`'s static-source-string pattern that asserts the exact updated command string in `.claude/settings.json`

## Out of Scope
- `tools/retrieval_cache.py` — already migrated by TCK-20260824-RETRIEVAL-CACHE-SIDECAR-UNIFY; do not re-touch
- Any changes to monitoring write semantics beyond the settings.json hook's read source (must remain fail-open, preserving the existing `2>/dev/null || true`)
- Resolving the shared-file coordination with TCK-20260904-BASH-SECRET-SCAN-HOOK and TCK-20260904-TEST-SCOPER-HANG-GUARD's own hooks-block additions to `.claude/settings.json` beyond an additive merge/rebase — no sequencing dependency is created

## Acceptance Criteria
- [x] The Edit|Write PreToolUse hook's inline `python3 -c` one-liner in `.claude/settings.json` reads `.claude/current_run.<CLAUDE_CODE_SESSION_ID>` (via `os.environ.get`) when that scoped file exists, falling back to the unscoped `.claude/current_run` when it doesn't
- [x] A synthetic two-session scenario (two scoped files with different run_ids plus a stale/foreign unscoped file) demonstrates the hook resolves RUN_ID to the calling session's own value
- [x] `tools/retrieval_cache.py` is left untouched (already correct) — the ticket's Scope explicitly states this
- [x] A new regression-guard test (mirroring `test_current_run_sidecar_orchestrator.py`'s static-source-string pattern) asserts the exact updated command string in `.claude/settings.json`

## Related Tickets
- TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE
- TCK-20260824-RETRIEVAL-CACHE-SIDECAR-UNIFY
- TCK-20260824-SIDECAR-ADHOC-NULL-ATTRIBUTION
- TCK-20260807-CURRENT-RUN-SIDECAR-HAND-ORCHESTRATION-GAP

## Related Docs
None.

## Related Stored Artifacts
None.

## Related Code Areas
- .claude/settings.json
- tools/retrieval_cache.py
- tools/agent-monitoring/post_tool_hook.py
- .claude/workflows/implement-ticket.js
- tests/tools/test_current_run_sidecar_orchestrator.py
- tests/tools/test_retrieval_cache.py
- tests/tools/test_post_tool_hook.py

## Assumptions / Open Questions
- The original concern's "2 remaining stragglers" framing is factually stale — only 1 (settings.json) remains unmigrated; this must be stated explicitly in the ticket rather than silently corrected
- This hook fires in a bare shell/`python3 -c` context with no hook-payload `session_id` field (unlike `post_tool_hook.py`), so it must read `CLAUDE_CODE_SESSION_ID` directly from the environment, the same forced approach `retrieval_cache.py` already took
- This hook is purely advisory — a stale/wrong RUN_ID degrades to a missing or wrong reminder, not data corruption, which bounds the blast radius of any residual edge case

## Implementation Notes

Implemented plan.md's 4 steps in order, no deviations from the approved (twice-fixed) plan.

**Step 1** — `git status`/`git diff -- .claude/settings.json` confirmed the file itself had zero
diff (clean) before editing, and `TCK-20260904-BASH-SECRET-SCAN-HOOK` (the sibling ticket
investigation.md/plan.md flagged as a shared-file risk) was re-confirmed still `phase: blocked` /
`## Status: BLOCKED` with no `Bash`-matcher entry present in the live file — it has not unblocked
or touched this file since Plan time, so no merge/re-verification was needed beyond the plan's own
assumption. Replaced only the `RUN_ID=$(...)` substring in
`hooks.PreToolUse[3].hooks[0].command` (the `Edit|Write` entry) with the scoped-then-unscoped-
fallback form from plan.md verbatim. `FILE=$(...)`, the `case`/`esac` matcher list, the
`ls tickets/inprogress/*.md` guard, the `echo` JSON reminder text, and both subshells' trailing
`2>/dev/null || true` were left byte-identical. `hooks.PreToolUse` array length confirmed still 4
after the edit.

**Step 2** — Appended 3 new test functions to `tests/tools/test_settings_json_hooks_wiring.py`
(`test_edit_write_hook_reads_scoped_sidecar_via_env_var`,
`test_edit_write_hook_still_fail_open_and_advisory`,
`test_edit_write_hook_json_still_valid_after_edit`), reusing the file's existing
`_load_settings()` helper. The 4 pre-existing test functions were not touched (append-only,
verified by diff review).

**Step 3** — Created `tests/tools/test_settings_json_edit_write_hook_sidecar_scope.py` with the 6
test functions plan.md specified, using the exact two-technique split the plan's twice-fixed
version calls for: tests #1/#2/#4/#5
(`test_run_id_resolution_prefers_scoped_over_unscoped_when_scoped_exists`,
`test_run_id_resolution_falls_back_to_unscoped_when_scoped_absent`,
`test_run_id_resolution_empty_when_session_id_env_var_unset`,
`test_two_concurrent_sessions_resolve_to_their_own_run_id`) extract-and-execute the bare inner
`python3 -c` snippet directly via `subprocess.run(["python3", "-c", snippet], ...)`; tests #3/#6
(`test_run_id_resolution_empty_when_both_absent`,
`test_malformed_or_missing_sidecar_json_degrades_to_empty_not_traceback`) run the FULL command via
`subprocess.run(["bash", "-c", full_command], input=json.dumps({"tool_input": {"file_path":
"a/src/foo.py"}}), ...)` — using `"a/src/foo.py"` (not the bare `"src/foo.py"` plan.md's own
review history flagged as the earlier bug) so the `case "$FILE" in */src/*|...)` matcher's
leading-`*` glob actually matches. All 6 pass.

**Step 4** — Re-checked the live max parity ledger id
(`grep -oE 'INFRA-[0-9]+' docs/parity_ledger/infrastructure.yaml | sort -t- -k2 -n | uniq | tail`)
immediately before writing: still `INFRA-409` (unchanged from plan-writing time — no other
concurrent ticket landed an entry in between), confirming `INFRA-410` as the correct next id.
Appended the new entry via `tools/parity_ledger_writer.py::write_entry()` (schema-validated,
auto-rebuilds the derived SQLite index) rather than a raw YAML edit, per the sanctioned-tool
requirement. `INFRA-382`'s existing entry text was not touched (confirmed via `git diff` — its
line range shows no modification). Note: `docs/parity_ledger/infrastructure.yaml` was already
`git status`-dirty before this ticket touched it, from sibling ticket
`TCK-20260904-COST-PROXY-EPIC-TICKETS` (already in `tickets/done/` but its own working-tree changes
— `INFRA-281`/`INFRA-282` text edits and the `INFRA-407` addition — remain uncommitted in this
shared worktree); `write_entry()`'s full-file `yaml.safe_dump()` round-trip picked up that
pre-existing state as-is (confirmed via `git diff` review: the only new content is the appended
`INFRA-410` block, everything else in the diff traces to that sibling ticket's own prior edit, not
this implementation).

No deviations from plan.md.

## Test Summary

`pytest tests/tools/test_settings_json_hooks_wiring.py tests/tools/test_settings_json_edit_write_hook_sidecar_scope.py -v`
(via the repo's real `.venv`, `/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3` —
the worktree's own bare `python3`/`pip3` lacks `pydantic` and is not usable for this repo's test
suite): **13 passed, 0 failed** (7 in `test_settings_json_hooks_wiring.py` — 4 pre-existing + 3
new; 6 in the new `test_settings_json_edit_write_hook_sidecar_scope.py`).

Regression confirmation: `pytest tests/tools/test_retrieval_cache.py -q`: **115 passed, 0 failed**
— confirms `tools/retrieval_cache.py`'s own already-migrated sidecar tests are unaffected (AC #3).

`python3 -c "import json; json.load(open('.claude/settings.json'))"` — succeeds, file is valid
JSON after the edit.

## Files Changed

- `.claude/settings.json` — Step 1: in-place edit of `hooks.PreToolUse[3].hooks[0].command`'s
  `RUN_ID=$(...)` substring only (session-scoped-then-unscoped-fallback read). Array length
  unchanged (still 4).
- `tests/tools/test_settings_json_hooks_wiring.py` — Step 2: appended 3 new test functions
  (append-only, 4 pre-existing tests untouched).
- `tests/tools/test_settings_json_edit_write_hook_sidecar_scope.py` (new) — Step 3: 6 new
  integration test functions.
- `docs/parity_ledger/infrastructure.yaml` — Step 4: appended new entry `INFRA-410` via
  `tools/parity_ledger_writer.py::write_entry()`. `INFRA-382` left untouched. (Note: this file's
  working tree already carried unrelated, pre-existing uncommitted changes from sibling ticket
  `TCK-20260904-COST-PROXY-EPIC-TICKETS` before this ticket's own edit — those are not this
  ticket's work; see Implementation Notes.)
- `docs/agent-monitoring/schema.md` — Document-Update phase: rewrote the "Cross-session
  contamination fix" paragraph's stale "both deferred rather than migrated" clause to state both
  `tools/retrieval_cache.py` and the settings.json hook are now migrated (naming both tickets).
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/roadmap.md` — Document-Update phase:
  marked inventory row 7 as SHIPPED, matching the doc's existing shipped-item convention. (Note:
  this file's working tree already carried unrelated, pre-existing uncommitted changes from
  sibling tickets in this same shared worktree before this ticket's own edit — those are not this
  ticket's work.)
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/workflow_reliability_epic.md` —
  Document-Update phase: marked M1 SHIPPED, updated the Problem-section item 1, Acceptance-signal
  bullet, and References list. (Note: this file's working tree already carried unrelated,
  pre-existing uncommitted changes from sibling tickets in this same shared worktree before this
  ticket's own edit — those are not this ticket's work.)
- `tickets/inprogress/TCK-20260904-SIDECAR-SETTINGS-HOOK-MIGRATE.md` — this file (Implementation
  Notes / Test Summary / Files Changed / Completion Summary / AC checkboxes / Status).
- `staging_artifacts/TCK-20260904-SIDECAR-SETTINGS-HOOK-MIGRATE/{investigation.md,plan.md,test_plan.md}`
  — pre-existing from this run's own Investigate/Plan phases (not authored during this Implement
  pass, but part of this run's real changeset per ticket-hygiene requirements — confirmed present
  via `git status` as untracked, not modified by this Implement step).

Not created/edited by this ticket, despite appearing modified in `git status` in this shared
worktree: `docs/REGISTRY.yaml`, `docs/architecture/agent_orchestration_contract.md`,
`docs/guidelines/agent_working_environment.md`,
`docs/guidelines/artifact_retention_classification.md`,
`docs/guidelines/subsystem_ownership_lifecycle.md`,
`docs/plans/agent_infrastructure/ai_first_hardening_epics/bucket_c_future_options.md`,
`docs/plans/agent_infrastructure/ai_first_hardening_epics/governance_capability_policy_epic.md`,
`docs/plans/agent_infrastructure/ai_first_hardening_epics/standalone_items.md`,
`docs/plans/agent_infrastructure/ai_first_hardening_epics/telemetry_retention_epic.md` — all belong
to other, already-Finalized-but-uncommitted sibling tickets in this shared worktree.

## Completion Summary

Migrated `.claude/settings.json`'s `Edit|Write` PreToolUse hook's inline `RUN_ID=$(...)` read from
an unscoped-only `.claude/current_run` read to the same scoped-then-unscoped-fallback preference
order already shipped in `tools/retrieval_cache.py::read_current_run_sidecar()`: it now reads
`CLAUDE_CODE_SESSION_ID` via `os.environ.get` and prefers `.claude/current_run.<session_id>` when
that file exists, falling back to the unscoped file otherwise — with no null-sentinel write side
effect (deliberately not mirroring `post_tool_hook.py`'s different, payload-sourced pattern). Added
3 structural regression tests to the existing `test_settings_json_hooks_wiring.py` and a new
6-test integration file (`test_settings_json_edit_write_hook_sidecar_scope.py`) proving the
synthetic two-session scenario resolves each session to its own `run_id`, never a foreign one, and
degrades gracefully (no traceback, exit 0) when sidecar files are absent or malformed. Added parity
ledger entry `INFRA-410` documenting the change without touching `INFRA-382`'s historical text. All
13 new/extended tests pass, plus 115/115 pre-existing `test_retrieval_cache.py` regression tests
and JSON-validity confirmed.
