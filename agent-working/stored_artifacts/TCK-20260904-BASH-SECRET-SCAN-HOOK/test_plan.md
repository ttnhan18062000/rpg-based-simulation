---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260904-BASH-SECRET-SCAN-HOOK
artifact_type: test_plan
tags: [governance, ai, hooks, security]
---

# Test Plan — TCK-20260904-BASH-SECRET-SCAN-HOOK

## Regression Surface

Unit:
- `tests/tools/test_write_path_guard.py` — full `scan_for_secrets()` coverage (all 10 patterns,
  clean-content negative case, docstring-disclosure assertion). Must stay 100% green and
  byte-identical in behavior; this ticket must not edit `tools/write_path_guard.py` at all (AC #3).

Integration / settings.json-hook:
- `tests/tools/test_settings_json_hooks_wiring.py` — existing static structural assertions on
  `hooks.PreToolUse`/`PostToolUse`/`SubagentStop` array lengths and the `Edit|Write` entry's
  command string (`settings["hooks"]["PreToolUse"][3]`). Adding a new `PreToolUse[4]` entry must
  not change any index this file currently asserts on (`[3]` stays the `Edit|Write` entry;
  `PreToolUse` length assertions elsewhere in that file, if any at fixed indices for `[0]`/`[1]`/
  `[2]`, must still hold).
- `tests/tools/test_settings_json_edit_write_hook_sidecar_scope.py` — exercises `PreToolUse[3]`
  (the `Edit|Write`/sidecar hook) via subprocess execution of the extracted command string. Not
  touched by this ticket's changes, but must stay green as proof the new array entry didn't shift
  or corrupt sibling entries.
- `python3 -m json.tool .claude/settings.json` — file must remain valid JSON after the edit.

Architecture-guard (agent-orchestration contract, not touched by this ticket but must stay green
as a coordination-safety check against the same-batch `SubagentStop` addition):
- `PYTHONPATH=tools:. pytest tests/agent_orchestration/test_contract_structure.py`

## New Tests Required

New file: `tests/tools/test_bash_secret_scan_hook.py` (per ticket Scope). Model directly on
`tests/tools/test_settings_json_edit_write_hook_sidecar_scope.py`'s subprocess-execution pattern
(load `.claude/settings.json`, extract or run the real command string, feed it synthetic stdin JSON,
assert stdout) — a purely static string-shape assertion (like
`test_settings_json_hooks_wiring.py`'s style) is not sufficient on its own for the ticket's own AC
#2 ("produces non-empty additionalContext... produces no output"), since that AC is a behavioral
claim about running the command, not just its presence in the file.

1. **`test_new_bash_secret_scan_hook_entry_registered`**
   - Category: integration (structural)
   - Verifies: a new `PreToolUse` array entry exists with matcher `"Bash"` whose command references
     `scan_for_secrets` (or `write_path_guard`) — proves the entry is wired, distinct from the
     existing `PreToolUse[1]` grep-nudge `Bash`-matcher entry (both must coexist).
   - Location: `tests/tools/test_bash_secret_scan_hook.py`

2. **`test_positive_fire_on_synthetic_secret_shaped_command`**
   - Category: integration (behavioral, subprocess)
   - Verifies: feeding stdin JSON `{"tool_input": {"command": "<a command embedding one of the 10
     documented secret-shaped literals, e.g. an AWS-style key or a generic `api_key=\"...\"`
     assignment>"}}` through the real extracted/executed command string produces valid JSON on
     stdout matching `{"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext":
     "<non-empty, names the matched pattern>"}}`. Parametrize over at least 2-3 of the 10 patterns
     (not just one), consistent with `test_write_path_guard.py`'s own per-pattern test granularity.
   - Location: `tests/tools/test_bash_secret_scan_hook.py`

3. **`test_negative_no_fire_on_ordinary_commands`**
   - Category: integration (behavioral, subprocess)
   - Verifies: feeding stdin JSON for several ordinary commands (a scoped `pytest` invocation, a
     status-check-style read-only command, a `python3` script invocation with no embedded secret)
     produces **empty stdout** — no `hookSpecificOutput` emitted at all. Parametrize over 2-3 clean
     commands, mirroring `test_write_path_guard.py::_CLEAN_CONTENT`'s negative-case discipline.
   - Location: `tests/tools/test_bash_secret_scan_hook.py`

4. **`test_hook_never_emits_permission_decision_or_deny`**
   - Category: integration (behavioral, anti-drift)
   - Verifies: on a positive-fire case, the emitted JSON has no `permissionDecision` key anywhere,
     and no exit code other than 0/success from the wrapping command — directly enforces the
     ticket's "advisory-only, never `permissionDecision`/deny" acceptance criterion, not just an
     assumption from reading the command string.
   - Location: `tests/tools/test_bash_secret_scan_hook.py`

5. **`test_hook_fails_open_on_malformed_or_missing_stdin`**
   - Category: integration (behavioral, failure mode)
   - Verifies: malformed/non-JSON stdin, or stdin with no `tool_input.command` key, produces no
     traceback on stderr and exit code 0 (matching every existing hook's `2>/dev/null || true`
     fail-open convention) — mirrors
     `test_settings_json_edit_write_hook_sidecar_scope.py::test_malformed_or_missing_sidecar_json_degrades_to_empty_not_traceback`.
   - Location: `tests/tools/test_bash_secret_scan_hook.py`

6. **`test_scan_for_secrets_module_unchanged_by_this_ticket`**
   - Category: architecture guard (anti-drift)
   - Verifies: AC #3's "unmodified" claim mechanically, not just by ticket-author assertion — e.g.
     hash/diff `tools/write_path_guard.py` against its state at the `TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE`
     commit (or, simpler and more robust to unrelated future edits, assert the specific
     `_SECRET_SCAN_PATTERNS` dict and `scan_for_secrets` function source text are byte-identical to
     the values already covered by `test_write_path_guard.py`'s own existing per-pattern tests — if
     those all still pass unmodified, the function's *behavior* is unchanged, which is the load-bearing
     claim). If a git-diff-based check is preferred instead, scope it to run only in CI/Verify context,
     not as a standing pytest (a plain diff-against-HEAD test is fragile across rebases/branches).
   - Location: `tests/tools/test_bash_secret_scan_hook.py` or left to the Architecture-Verify
     phase's own diff review — either is acceptable; state the choice explicitly in Implementation
     Notes rather than silently picking one.

7. **`test_existing_bash_and_sidecar_hooks_untouched`**
   - Category: architecture guard (anti-drift, regression)
   - Verifies: `PreToolUse[1]` (existing grep-nudge `Bash` entry) and `PreToolUse[3]` (`Edit|Write`
     sidecar entry) command strings are byte-identical to their pre-ticket values — proves the new
     entry was purely additive, mirroring
     `test_settings_json_hooks_wiring.py::test_existing_hook_writers_untouched`'s pattern.
   - Location: `tests/tools/test_bash_secret_scan_hook.py`

## Scoped Pytest Commands

```
pytest tests/tools/test_write_path_guard.py tests/tools/test_bash_secret_scan_hook.py \
  tests/tools/test_settings_json_hooks_wiring.py \
  tests/tools/test_settings_json_edit_write_hook_sidecar_scope.py -v
```

Plus the cross-check against the same-batch `SubagentStop` addition (confirms no collision damage
to the shared contract bundle):
```
PYTHONPATH=tools:. pytest tests/agent_orchestration/test_contract_structure.py -v
```

Never `pytest tests/` — scope stays to `tests/tools/` (the hook-script/settings.json domain) plus
the one `tests/agent_orchestration/` file that structurally cross-references the same
`.claude/settings.json` file this ticket edits.

## Anti-Drift Test Guards

- Test #7 above (existing-hooks-untouched) directly catches accidental edits to sibling
  `PreToolUse` entries — the most likely scope-creep failure mode given three tickets in this same
  batch (`TCK-20260904-TEST-SCOPER-HANG-GUARD`, `TCK-20260904-SIDECAR-SETTINGS-HOOK-MIGRATE`, this
  one) all touch `.claude/settings.json`.
- Test #6 catches silent modification of `scan_for_secrets()`/`_SECRET_SCAN_PATTERNS` — the
  regression this ticket is most likely to accidentally introduce if an implementer "improves" the
  patterns while wiring the hook, which is explicitly Out of Scope.
- Test #4 catches the single most consequential possible regression: a future edit accidentally
  escalating this hook from advisory to blocking (`permissionDecision`/`deny`) without a documented
  Bucket-B experiment first — this is the exact escalation path the epic doc explicitly reserves
  for a separate, evidence-gated decision.
- Regression Surface's `tests/tools/test_write_path_guard.py` full run is the guard against this
  ticket accidentally breaking `scan_for_secrets()`'s existing gateway/cache-write callers (even
  though those callers are now archived/dormant, the function itself is still exercised by
  `tools/retrieval_cache.py`'s live callers per the module's own docstring).
