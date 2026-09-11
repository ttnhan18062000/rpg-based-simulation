---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260904-BASH-SECRET-SCAN-HOOK
phase: done
date: 2026-09-04
tags: [governance, ai, hooks, security]
---

# TCK-20260904-BASH-SECRET-SCAN-HOOK

## Title
Bash secret-exposure advisory hook

## Status
DONE

## Unblocked 2026-09-08
Both stated blockers are now resolved: (a) `TCK-20260824-KGMCP-KEEP-OR-DEPRECATE` was re-ratified
to Option C (deprecate) via `TCK-20260907-KGMCP-DEPRECATION-EPIC` M1
(`docs/engine/contracts/knowledge_gateway_mcp/keep_or_deprecate_decision.md` §4); (b)
`scan_for_secrets()` was extracted to `tools/write_path_guard.py` (a gateway-independent module)
via `TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE` M2 steps 1-2, PR #147, merged. `Related Code
Areas` below updated accordingly (was `tools/knowledge_gateway_redaction.py`/
`tests/tools/test_knowledge_gateway_redaction.py`, now archived at `tools/archive/`/
`tests/archive/` — this ticket must cite the live location, not the archived one).

## Tier
standard

## Type
feature

## Priority
P0

## Request Summary
This ticket is BLOCKED. It was originally gated on a cross-epic hard prerequisite: scan_for_secrets() must first be extracted out of tools/knowledge_gateway_redaction.py into a location independent of the knowledge-gateway module, as milestone 1 of a separate "Remove/archive knowledge-gateway" standalone item. That knowledge-gateway-removal work was explicitly skipped this pass, because it conflicts with the already-ratified TCK-20260824-KGMCP-KEEP-OR-DEPRECATE decision ("keep as-is, no further investment... No changes to tools/knowledge_gateway_mcp.py or any related module are authorized by this decision"). That means this ticket's hard prerequisite (the scan_for_secrets() extraction) is now also blocked, pending a fresh re-ratification decision that has not happened. (Live confirmation during ticket creation: the knowledge-gateway MCP tools are still fully functional and callable today — this is not dead/disabled infrastructure, just underused — so there is no urgency pressure to route around the ratification.) Once unblocked and extracted, the plan is to reuse scan_for_secrets(text: str) -> str | None as-is, wired as a NEW advisory-only PreToolUse hook matching Bash in .claude/settings.json, following the exact shell-wrapper pattern already used by every other hook there — scanning the outgoing command string itself, never denying, and scoped strictly to secret-shaped values (not a dangerous-command policy, not command-injection detection).

## Scope
- Once unblocked: wire scan_for_secrets() (reused unmodified, post-extraction) as a new hooks.PreToolUse entry matching Bash in .claude/settings.json, following the exact existing shell-wrapper pattern (python3 -c one-liner parsing tool_input.command from stdin JSON, emitting hookSpecificOutput.additionalContext)
- Scan the outgoing Bash command string itself, advisory-only — warning via additionalContext, never permissionDecision/deny
- New test file (e.g. tests/tools/test_bash_secret_scan_hook.py) asserting both positive-fire (synthetic secret-shaped command) and negative-no-fire (ordinary command) cases, closing the currently-zero settings.json-embedded-hook test coverage gap

## Out of Scope
- The scan_for_secrets() extraction step itself — that belongs to the separate knowledge-gateway removal/archive item, which is out of scope this pass and currently skipped pending re-ratification
- Any dangerous-command or command-injection detection policy
- Any modification to scan_for_secrets()'s own logic or its 10-pattern _SECRET_SCAN_PATTERNS list
- Catching commands that merely read a secret (e.g. cat ~/.aws/credentials) — accepted named limitation, not a gap to close

## Acceptance Criteria
- [x] New hooks.PreToolUse entry with matcher: Bash whose embedded python3 -c one-liner parses tool_input.command and, on match, emits valid {"hookSpecificOutput":{"hookEventName":"PreToolUse","additionalContext":"..."}} JSON — never permissionDecision/deny
- [x] A synthetic secret-shaped command (matching any of the 10 existing patterns) produces non-empty additionalContext naming the pattern; an ordinary command (git status, pytest tests/) produces no output
- [x] Hook calls scan_for_secrets() unmodified — verified by a diff showing the (post-extraction) module is unchanged by this ticket except for the extraction landing separately
- [x] New test file (e.g. tests/tools/test_bash_secret_scan_hook.py) asserts both positive-fire and negative-no-fire cases via subprocess/thin wrapper, closing the settings.json-hook coverage gap

## Related Tickets
- TCK-20260907-KGMCP-DEPRECATION-EPIC (done, M1) — re-ratified TCK-20260824-KGMCP-KEEP-OR-DEPRECATE
  to Option C, unblocking this ticket's first prerequisite.
- TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE (done) — extracted scan_for_secrets() to
  tools/write_path_guard.py, unblocking this ticket's second prerequisite.
- TCK-20260824-KGMCP-KEEP-OR-DEPRECATE (done, superseded 2026-09-07 — "keep as-is" ratification
  that originally blocked this ticket, now re-ratified to Option C)
- TCK-20260815-KGMCP-P2-REDACTION-WRITE-PATH (done — added scan_for_secrets() originally, no hook wiring)
- TCK-20260814-KGMCP-REDACTION-RETENTION-POLICY (done — ratified the reject-outright policy scan_for_secrets() implements)
- TCK-20260807-CURRENT-RUN-SIDECAR-HAND-ORCHESTRATION-GAP (done — closest prior-art for adding a new advisory PreToolUse hook)

## Related Docs
- docs/plans/agent_infrastructure/ai_first_hardening_epics/governance_capability_policy_epic.md

## Related Stored Artifacts
None.

## Related Code Areas
- tools/write_path_guard.py (was tools/knowledge_gateway_redaction.py — extracted to this
  gateway-independent module by TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE; scan_for_secrets()
  moved unmodified)
- .claude/settings.json
- tests/tools/test_write_path_guard.py (was tests/tools/test_knowledge_gateway_redaction.py,
  now archived at tests/archive/)

## Assumptions / Open Questions
- RESOLVED 2026-09-08 (was BLOCKED): (a) TCK-20260824-KGMCP-KEEP-OR-DEPRECATE was re-ratified to
  Option C (deprecate) via TCK-20260907-KGMCP-DEPRECATION-EPIC M1; (b) scan_for_secrets() was
  extracted to tools/write_path_guard.py via TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE M2. Both
  independently re-verified before starting this ticket's own Investigate phase.
- This ticket must not be scoped to include the extraction step itself — that belongs to the
  knowledge-gateway item, already done separately
- Shared-file coordination note (not a real sequencing dependency): .claude/settings.json's hooks block is also touched by this batch's TCK-20260904-TEST-SCOPER-HANG-GUARD and by a separate, not-in-this-batch Workflow Reliability ticket — coordinate at merge time via rebase, don't let this block scheduling
- Every hook in settings.json is wrapped 2>/dev/null || true so a malformed entry fails silently — no CI currently validates settings.json's embedded shell snippets; this ticket may end up owning a small smoke-test addition for its own entry
- Named/accepted limitation must be documented, not silently dropped: this hook catches embedded secret literals only, not commands that merely read a secret
- Confirmed live during ticket creation (2026-09-04): the knowledge-gateway MCP tools (mcp__knowledge-gateway__knowledge_status, knowledge_context) are still fully registered and functional, not disabled — the underlying infra is underused, not broken, which removes any technical urgency to bypass the pending re-ratification

## Implementation Notes

**Known limitation, knowingly inherited (flagged by `agent-working-design` peer review, 2026-09-08):**
`scan_for_secrets()`'s own docstring self-describes as "a documented starting point, not a
production-complete secret scanner" that "must be reviewed and expanded by a security-focused pass."
That disclosure was written for its original caller (gating durable cache writes, where a miss has
a real cost). This ticket reuses the function unmodified for a strictly lower-stakes application —
an advisory-only Bash-command nudge, where a miss costs nothing versus having no hook at all. This
hook must not be read as a completeness guarantee: it catches only the 10 patterns
`_SECRET_SCAN_PATTERNS` already covers, nothing more, and a future security-focused pass on
`scan_for_secrets()` itself (if one happens) is separate, out-of-scope work for this ticket.

All 7 plan steps implemented exactly as specified, no deviations from `plan.md`:

1. **`.claude/settings.json`**: appended a 5th `hooks.PreToolUse` array entry (index 4, matcher
   `"Bash"`) programmatically via `json.load`/`json.dump` (never hand-typed escaped JSON). Command
   string is the exact live-verified snippet from `investigation.md`/`plan.md` Step 1: imports
   `scan_for_secrets` from `tools.write_path_guard`, reads `tool_input.command` from stdin JSON,
   and on a match prints `{"hookSpecificOutput":{"hookEventName":"PreToolUse","additionalContext":"..."}}`
   — never `permissionDecision`/`deny`. Wrapped in `2>/dev/null || true` matching every other hook's
   fail-open convention. Verified `python3 -m json.tool` succeeds and indices 0-3 are unchanged
   (compared against `git show HEAD:.claude/settings.json`, byte-identical for `PreToolUse[0:4]`,
   `PostToolUse`, `SubagentStop`, and `permissions`).
2. **`tests/tools/test_settings_json_hooks_wiring.py`**: `test_existing_hook_writers_untouched`'s
   `len(settings["hooks"]["PreToolUse"]) == 4` assertion updated to `== 5`, with a one-line comment
   noting the count now includes the new entry.
3. **`tests/tools/test_bash_secret_scan_hook.py`** (new): 7 tests as specified in `plan.md`/
   `test_plan.md` — entry-registration, positive-fire (parametrized over 4 of the 10
   `_SECRET_SCAN_PATTERNS` keys: AWS key, generic API key, bearer token, generic password),
   negative-no-fire (3 ordinary commands), a dedicated `permissionDecision`/`deny` anti-drift
   guard, fail-open-on-malformed-stdin, module-unchanged (runs the full
   `tests/tools/test_write_path_guard.py` suite as a subprocess and asserts returncode 0 — the
   "simpler and more robust" form `test_plan.md` specified, not a git-diff check), and
   existing-hooks-untouched (`PreToolUse[1]`/`[3]` command strings). All run via real subprocess
   execution of the live `.claude/settings.json` command string (`bash -c`), modeled on
   `test_settings_json_edit_write_hook_sidecar_scope.py`.
4. **`governance_capability_policy_epic.md`**: M4 heading changed to "(gated on nothing —
   SHIPPED)"; prepended a SHIPPED paragraph naming the ticket, the new `PreToolUse[4]` entry, and
   the new test file, mirroring the guardrail epic's M3 SHIPPED-paragraph shape. Updated the M4
   Acceptance-signal bullet to past-tense-confirmed phrasing.
5. **`roadmap.md`**: three edits — (a) item 2's table row struck through with **SHIPPED** and the
   ticket ID, matching items 5/7/10's markup; (b) the "unaffected and still open" prose split so
   item 2 reads shipped while item 3 stays open; (c) a new dated **Item 2 — shipped (2026-09-08)**
   paragraph appended after the existing running-count paragraph (not rewriting the original
   snapshot sentence in place, per the doc's own established convention), recomputing the count to
   "6 remaining to implement overall (1, 3, 7, 9, plus item 1's remaining waves)". Line 281's
   Bucket-B item 2 reference was read and confirmed to already correctly frame the *escalation
   decision* as distinct from item 2 itself — left untouched, no contradiction found.
6. **`docs/guidelines/subsystem_ownership_lifecycle.md`**: removed the "Bash secret-exposure
   advisory hook" bullet from Excluded Subsystems; added a new Ownership & Lifecycle Table row
   (Workflow Runtime Maintainer, matching the Test-scoper hang guard row's role) with the exact
   update-trigger/staleness-signal/removal-condition text specified in the plan.
7. **`docs/parity_ledger/infrastructure.yaml`**: re-verified live immediately before writing (grep
   confirmed highest existing ID still `INFRA-412`, so `INFRA-413` was still available at
   Implement time — not trusted blindly from the plan's placeholder). Added via
   `tools/parity_ledger_writer.py::write_entry()` (never a raw YAML edit) — `status: verified`,
   `priority: P0`, `test_path: tests/tools/test_bash_secret_scan_hook.py`.

   **Deviation, found while moving this ticket to its own branch (2026-09-08, post-Finalize):** a
   different, unrelated ticket (`TCK-20260907-CAMPAIGN-BRIDGE-FIELDS-STATE-HASH-COVERAGE`, landed
   in PR #148, merged to `origin/main` after this ticket's own Implement phase but before this
   ticket's branch/PR) independently claimed `INFRA-413` for its own, unrelated entry — a genuine
   ID race the plan's own "re-verify live, don't trust a stale placeholder" instruction anticipated
   in principle but could not fully prevent, since both tickets' Implement phases ran concurrently
   in different worktrees against the same shared file. Resolved by renumbering this ticket's own
   entry to **`INFRA-414`** (the real next-available ID once the collision was found) via a fresh
   `write_entry()` call — the other ticket's `INFRA-413` entry is untouched. This is a real,
   disclosed deviation from the plan's own literal ID, not a silent renumber — the ticket's own
   `plan.md`/`investigation.md` still say `INFRA-413` as an accurate record of what was true at
   Plan/Investigate time, superseded by this note as the actual shipped outcome.

   Writer's in-process `parity_index.py` rebuild completed without error. `git diff` on the shard
   confirms a purely additive insertion at `INFRA-414` — every other entry (spot-checked `INFRA-405`,
   `INFRA-412`) is untouched.

**Do-NOT-touch discipline confirmed**: `git diff tools/write_path_guard.py` is empty (0 lines) —
the module is byte-identical, satisfying AC #3 literally, including its stale "*planned*" M4
docstring wording (left as-is per the plan's explicit instruction not to fix it in this ticket).
`redaction_retention_policy.md` and `standalone_items.md` were not touched.
`PreToolUse[1]`/`[2]`/`[3]`, `PostToolUse`, and `SubagentStop` were not touched (verified live
above and by `test_existing_bash_and_sidecar_hooks_untouched`).

**Never-deny verification**: `test_hook_never_emits_permission_decision_or_deny` plus a live
manual smoke test (both run during Implement) confirm the hook emits no `permissionDecision` key
under any tested case — positive-fire (4 pattern types), negative-fire, malformed stdin, and
missing `tool_input.command` all exit 0 with either empty or advisory-only JSON stdout.

## Test Summary

Scoped pytest commands from `test_plan.md`, run via `.venv/bin/python3` (bare `python3` lacks
`pydantic`, needed by `tests/conftest.py`'s collection-time import chain — not a CI-relevant gap,
same local-sandbox quirk noted elsewhere in this repo's history):

```
pytest tests/tools/test_write_path_guard.py tests/tools/test_bash_secret_scan_hook.py \
  tests/tools/test_settings_json_hooks_wiring.py \
  tests/tools/test_settings_json_edit_write_hook_sidecar_scope.py -v
```
→ **79 passed**, 0 failed.

```
PYTHONPATH=tools:. pytest tests/agent_orchestration/test_contract_structure.py -v
```
→ **24 passed**, 0 failed.

Total: **103 passed, 0 failed.** Re-ran both suites a second time after the doc/ledger edits
(Steps 4-7) landed — still 103/103 green, confirming the doc-only changes did not disturb the
code/test surface.

## Files Changed

- `.claude/settings.json` — modified (new `PreToolUse[4]` entry, Step 1)
- `tests/tools/test_settings_json_hooks_wiring.py` — modified (Step 2)
- `tests/tools/test_bash_secret_scan_hook.py` — new (Step 3)
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/governance_capability_policy_epic.md` — modified (Step 4)
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/roadmap.md` — modified (Step 5)
- `docs/guidelines/subsystem_ownership_lifecycle.md` — modified (Step 6)
- `docs/parity_ledger/infrastructure.yaml` — modified via `tools/parity_ledger_writer.py::write_entry()` (Step 7, new `INFRA-414` entry — renumbered from the original `INFRA-413` after a real ID collision with a concurrently-landed unrelated ticket, see Implementation Notes)
- `tickets/inprogress/TCK-20260904-BASH-SECRET-SCAN-HOOK.md` — this ticket, updated with Implementation Notes/Test Summary/Files Changed/Completion Summary/Status/Acceptance Criteria
- `staging_artifacts/TCK-20260904-BASH-SECRET-SCAN-HOOK/investigation.md` — created this run's Investigate phase (read and confirmed accurate during Implement, not modified)
- `staging_artifacts/TCK-20260904-BASH-SECRET-SCAN-HOOK/plan.md` — created this run's Plan phase (read and followed exactly during Implement, not modified)
- `staging_artifacts/TCK-20260904-BASH-SECRET-SCAN-HOOK/test_plan.md` — created this run's Plan phase (read and followed exactly during Implement, not modified)

Not touched (explicit Scope Guards, verified): `tools/write_path_guard.py` (0-line diff),
`docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md`,
`docs/plans/agent_infrastructure/ai_first_hardening_epics/standalone_items.md`,
`docs/parity_ledger/schema.json`, `PreToolUse[0..3]`, `PostToolUse`, `SubagentStop`.

## Completion Summary

Implemented the Bash secret-exposure advisory hook: a new, purely additive `PreToolUse[4]` entry
in `.claude/settings.json` (matcher `Bash`) that reuses `tools/write_path_guard.py::scan_for_secrets()`
unmodified to scan outgoing Bash command strings for 10 secret-shaped literal patterns, emitting an
advisory `hookSpecificOutput.additionalContext` warning on match and never a `permissionDecision`/
`deny` — confirmed by a dedicated anti-drift test and a live manual smoke test across positive-fire,
negative-fire, and malformed-input cases. Added 7 new behavioral tests
(`tests/tools/test_bash_secret_scan_hook.py`, all passing) plus updated the one pre-existing
structural test whose fixed-length assertion the new array entry broke. Updated the three docs the
investigation flagged as stale (epic doc M4 → SHIPPED, roadmap.md item 2 → SHIPPED with a
recomputed running count, subsystem ownership table gained a real row) and added a new
`INFRA-414` parity-ledger entry via the sanctioned writer tool (renumbered from `INFRA-413` after
a real ID collision with a concurrently-landed unrelated ticket, PR #148). `tools/write_path_guard.py` is
verified byte-identical (0-line diff) and all explicitly out-of-scope files were left untouched.
