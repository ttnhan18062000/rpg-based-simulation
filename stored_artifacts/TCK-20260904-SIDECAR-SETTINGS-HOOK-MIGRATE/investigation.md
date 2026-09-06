---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260904-SIDECAR-SETTINGS-HOOK-MIGRATE
artifact_type: investigation
tags: [ai, hooks, agent-monitoring]
---

# Investigation — TCK-20260904-SIDECAR-SETTINGS-HOOK-MIGRATE

## Current Behavior

### `.claude/settings.json` — `Edit|Write` PreToolUse hook (line 84-91, `hooks.PreToolUse[3]`)

Verbatim command (raw, as stored in the JSON file, i.e. with `\"` literal escapes intact):

```
FILE=$(python3 -c \"import json,sys; d=json.load(sys.stdin); print(d.get('tool_input',d).get('file_path',''))\" 2>/dev/null || true); case \"$FILE\" in */tickets/*|*/staging_artifacts/*|*/src/*|*/tests/*|*/docs/*) if ls tickets/inprogress/*.md >/dev/null 2>&1; then RUN_ID=$(python3 -c \"import json; print(json.load(open('.claude/current_run')).get('run_id') or '')\" 2>/dev/null || true); if [ -z \"$RUN_ID\" ]; then echo '{\"hookSpecificOutput\":{\"hookEventName\":\"PreToolUse\",\"additionalContext\":\"sidecar-check: tickets/inprogress/ has an active ticket but .claude/current_run has no run_id. If you are hand-orchestrating implement-ticket.js, write the sidecar (writeSidecar shape: run_id/seq/phase/agent/execution_id/provider) before continuing, or tool_call_count/cost_proxy_score will read 0 for this phase.\"}}'; fi; fi ;; esac
```

Confirmed byte-for-byte identical to the ticket's "Already-found facts" #1 (Read at `.claude/settings.json:88`, `hooks.PreToolUse` array, `"matcher": "Edit|Write"` entry). The exact substring the ticket flags:

```
RUN_ID=$(python3 -c \"import json; print(json.load(open('.claude/current_run')).get('run_id') or '')\" 2>/dev/null || true)
```

This is the sole remaining unscoped read. It always opens `.claude/current_run` directly — whichever concurrent session's `writeSidecar()`/Scope-resume call wrote it last — with no session-scoping at all.

### Precedent 1 — `tools/retrieval_cache.py::read_current_run_sidecar()` (lines 555-622)

```python
session_id = os.environ.get("CLAUDE_CODE_SESSION_ID", "")
scoped_path = (
    _CURRENT_RUN_SIDECAR_PATH.parent / f"{_CURRENT_RUN_SIDECAR_PATH.name}.{session_id}"
    if session_id
    else None
)
sidecar_path = (
    scoped_path if scoped_path is not None and scoped_path.exists() else _CURRENT_RUN_SIDECAR_PATH
)
```
Reads `CLAUDE_CODE_SESSION_ID` from the process environment (this call path has no hook payload to source a `session_id` field from). Preference order: scoped file if `session_id` is set AND the scoped file exists; **else falls back to the unscoped file** (`.claude/current_run`). This was migrated by `TCK-20260824-RETRIEVAL-CACHE-SIDECAR-UNIFY` (confirmed in `tickets/done/`, `## Status: DONE`, all 4 ACs checked, `Test Summary`: 113/113 + 339 broader regression tests pass). `tools/retrieval_cache.py` needs **no further changes** for this ticket — confirmed correct, matches this ticket's own Out-of-Scope constraint.

### Precedent 2 — `tools/agent-monitoring/post_tool_hook.py` (lines 96-131)

Reads `session_id` from the **hook's JSON payload** (`payload.get("session_id", "")`), not the environment — it has that field available, unlike the settings.json bash hook and unlike `retrieval_cache.py`. Preference order differs subtly from precedent 1:
- scoped file exists → use it.
- `session_id` present but scoped file absent → **write a null-valued sentinel to the scoped path and use that** (no unscoped fallback at all) — `TCK-20260824-SIDECAR-ADHOC-NULL-ATTRIBUTION`'s behavior.
- no `session_id` in payload at all (defensive, never actually hit) → falls back to unscoped file.

**These two precedents are NOT identical.** `read_current_run_sidecar()` falls back to the unscoped file when no scoped file exists; `post_tool_hook.py` does not (it self-writes a null sentinel instead). The ticket's own Scope text ("falling back to the unscoped `.claude/current_run` when the scoped file doesn't exist") matches **precedent 1's behavior exactly**, not precedent 2's null-sentinel write. This is the correct choice for this hook: it is a read-only, advisory bash one-liner with no mechanism (and no justification) to create a new durable sentinel file as a side effect of an `Edit|Write` PreToolUse check — mirroring `read_current_run_sidecar()`'s reasoning (a read path should not gain a write side effect) applies here even more strongly, since this is not even a Python module but an inline shell snippet embedded in JSON.

### `tests/tools/test_current_run_sidecar_orchestrator.py` — the "static-source-string pattern"

This file (regression coverage for `TCK-20260710-CURRENT-RUN-SIDECAR-BASH` and its follow-ups) asserts exact literal substrings/regexes against `.claude/workflows/implement-ticket.js`'s raw source text via `Path.read_text()` — never executing the file (no JS runner exists in-repo for `.claude/workflows/*.js`). Example pattern (`test_write_sidecar_also_writes_session_scoped_copy`):
```python
assert "os.environ.get('CLAUDE_CODE_SESSION_ID', '')" in helper_body
assert "open('.claude/current_run.' + sid, 'w')" in helper_body
assert "open('.claude/current_run', 'w')" in helper_body
```
The pattern to mirror for `.claude/settings.json` is: load the file with `json.loads()` (not raw regex against the whole file — `.claude/settings.json` is real JSON, unlike the `.js` workflow file), navigate to the exact hook entry (`settings["hooks"]["PreToolUse"][3]["hooks"][0]["command"]`), then assert the **exact updated command string** (or an exact substring of it) via plain `==`/`in`. `tests/tools/test_settings_json_hooks_wiring.py` (already exists, added by `TCK-20260904-TEST-SCOPER-HANG-GUARD`) is the closer, more directly reusable precedent for `.claude/settings.json` specifically — it already does `json.loads()`-based structural assertions against this exact file (e.g. `test_subagent_stop_command_not_suffixed_with_swallowing_fallback`, `test_existing_hook_writers_untouched` which asserts `len(settings["hooks"]["PreToolUse"]) == 4`). The new regression test should either extend this file or add a sibling file, using the same `_load_settings()` helper.

## Mechanics / Engine Constraints

None from `docs/mechanics/` or `docs/engine/` — this is a Claude Code harness/tooling concern (agent-monitoring attribution), not a simulation-domain change. No Mechanics Bible chapter or engine contract governs `.claude/settings.json` hooks.

## Proposed Exact Replacement Command Text

New RUN_ID segment (drop-in replacement for the exact substring identified above), mirroring `read_current_run_sidecar()`'s scoped-then-unscoped-fallback order, reading `CLAUDE_CODE_SESSION_ID` via `os.environ.get` per the ticket's own constraint:

Raw (unescaped) form:
```
RUN_ID=$(python3 -c "import json,os; sid=os.environ.get('CLAUDE_CODE_SESSION_ID',''); path='.claude/current_run.'+sid if sid and os.path.exists('.claude/current_run.'+sid) else '.claude/current_run'; print(json.load(open(path)).get('run_id') or '')" 2>/dev/null || true)
```

As it must appear inside the JSON string value (same escaping convention as the surrounding command — outer `python3 -c "..."` double quotes escaped as `\"`, all string literals inside the `-c` body use single quotes so no additional escaping is introduced):
```
RUN_ID=$(python3 -c \"import json,os; sid=os.environ.get('CLAUDE_CODE_SESSION_ID',''); path='.claude/current_run.'+sid if sid and os.path.exists('.claude/current_run.'+sid) else '.claude/current_run'; print(json.load(open(path)).get('run_id') or '')\" 2>/dev/null || true)
```

Full proposed replacement for the whole hook `command` value (only the `RUN_ID=$(...)` segment changes; everything else — the `FILE=$(...)` extraction, the `case` matcher, the `ls tickets/inprogress/*.md` guard, the `if [ -z "$RUN_ID" ]` check, the `echo` JSON payload, and the trailing `2>/dev/null || true` fail-open wrappers — is unchanged):

```
FILE=$(python3 -c \"import json,sys; d=json.load(sys.stdin); print(d.get('tool_input',d).get('file_path',''))\" 2>/dev/null || true); case \"$FILE\" in */tickets/*|*/staging_artifacts/*|*/src/*|*/tests/*|*/docs/*) if ls tickets/inprogress/*.md >/dev/null 2>&1; then RUN_ID=$(python3 -c \"import json,os; sid=os.environ.get('CLAUDE_CODE_SESSION_ID',''); path='.claude/current_run.'+sid if sid and os.path.exists('.claude/current_run.'+sid) else '.claude/current_run'; print(json.load(open(path)).get('run_id') or '')\" 2>/dev/null || true); if [ -z \"$RUN_ID\" ]; then echo '{\"hookSpecificOutput\":{\"hookEventName\":\"PreToolUse\",\"additionalContext\":\"sidecar-check: tickets/inprogress/ has an active ticket but .claude/current_run has no run_id. If you are hand-orchestrating implement-ticket.js, write the sidecar (writeSidecar shape: run_id/seq/phase/agent/execution_id/provider) before continuing, or tool_call_count/cost_proxy_score will read 0 for this phase.\"}}'; fi; fi ;; esac
```

Notes on this proposal:
- Remains a single inline `python3 -c "..."` invocation (no external script file introduced) — matches the existing style of every other hook in this file.
- Introduces no new double quotes inside the `-c` body (only single-quoted Python string literals), so the JSON-string escaping burden is identical to what already exists — `.claude/settings.json` stays valid JSON with no new escape characters needed beyond the ones already present for the enclosing `python3 -c \"..\"`.
- Preserves the trailing `2>/dev/null || true` on the `RUN_ID=$(...)` subshell — fail-open is unchanged, per Out of Scope.
- Does not touch `FILE=$(...)`, the `case` matcher, the `ls tickets/inprogress/*.md` guard, or the `echo` JSON payload text — smallest possible diff.
- Uses `os.path.exists(...)` (stdlib, no extra import) rather than `pathlib.Path` — keeps the one-liner shorter and avoids importing an unused module; behaviorally equivalent to `retrieval_cache.py`'s `Path.exists()` check.

## Docs Requiring Update

- `docs/parity_ledger/infrastructure.yaml`: `INFRA-382`'s `text` field explicitly says the unscoped-file fallback is "kept for tools/retrieval_cache.py and .claude/settings.json's inline sidecar-check hook, both deferred not migrated." This is now doubly stale — `tools/retrieval_cache.py` was migrated by `INFRA-390`/`TCK-20260824-RETRIEVAL-CACHE-SIDECAR-UNIFY`, and this ticket migrates the settings.json hook, the second (and last) named straggler. Either amend `INFRA-382`'s text to drop the now-false "deferred not migrated" framing, or add a new entry documenting the settings.json hook's own migration with `v2_evidence: .claude/settings.json` and a `test_path` pointing at the new regression-guard test this ticket adds. Given CLAUDE.md's Authoritative Mechanics Rule ("If logic changes, update the corresponding doc AND the parity ledger entry... If no entry exists, add one"), and that this is a genuine behavior fix (bug), a new entry is the cleaner choice — it keeps `INFRA-382`'s own historical record of what it fixed at the time intact rather than retroactively editing it to describe a later ticket's work.

The `docs/mechanics/` and `docs/engine/` doc sets (path: `docs/mechanics/*.md`, `docs/engine/*.md`) are not required to change for this ticket: this is Claude Code harness tooling (agent-monitoring hook attribution), not simulation-domain logic, and none of those chapters/contracts describe `.claude/settings.json` or the sidecar convention.

The `docs/guides/agent_monitoring.md` doc (path: `docs/guides/agent_monitoring.md`, section "Sidecar Reminder Hook") is not required to change for this ticket: it documents the *purpose* of the sidecar-check hook (advisory reminder to hand-orchestrating sessions), which does not change — only its internal *read-path selection* changes, an implementation detail this doc does not describe at that level.

## Parity Ledger Overlap

- `INFRA-382` (`docs/parity_ledger/infrastructure.yaml`, status: `verified`, priority: `P2`) — `TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE`'s entry; its own text names both stragglers this epic of tickets has been closing one-by-one. Needs a text update or a sibling new entry (see Docs Requiring Update).
- `INFRA-389` (status: `verified`, priority: `P2`) — `TCK-20260824-SIDECAR-ADHOC-NULL-ATTRIBUTION`, the null-sentinel behavior `post_tool_hook.py` adopted but this ticket's hook deliberately does NOT mirror (see Anti-Drift Hazards).
- `INFRA-390` (status: `verified`, priority: `P2`) — `TCK-20260824-RETRIEVAL-CACHE-SIDECAR-UNIFY`, confirms `tools/retrieval_cache.py` is already migrated and out of scope here.
- No `P0` entries are touched by this ticket — all three related entries are `P2`, so no pre-existing `test_path` is contractually blocking, though a new entry (recommended above) should still carry a real, passing `test_path` once the new regression test exists.

## Prior Work

- `TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE` (`tickets/done/`) — introduced the scoped-sidecar convention and `post_tool_hook.py`'s preference order.
- `TCK-20260824-RETRIEVAL-CACHE-SIDECAR-UNIFY` (`tickets/done/`) — migrated `retrieval_cache.py`; its own "Implementation Notes" section is directly relevant precedent: it explicitly chose scoped-then-unscoped-fallback (not the null-sentinel convention) for the same reasons this ticket's hook should — a read-only path with no natural place to persist a write side effect, and confirmed this choice was compatible with all pre-existing tests.
- `TCK-20260824-SIDECAR-ADHOC-NULL-ATTRIBUTION` (`stored_artifacts/`, referenced) — the null-sentinel mechanism `post_tool_hook.py` uses; explicitly NOT the pattern to mirror here.
- `TCK-20260904-TEST-SCOPER-HANG-GUARD` (`tickets/done/`) — added `tests/tools/test_settings_json_hooks_wiring.py`, the direct precedent for structurally testing `.claude/settings.json`'s hooks via `json.loads()` + dict-path assertions, including an assertion on `len(settings["hooks"]["PreToolUse"]) == 4` that this ticket's edit must keep satisfying (the edit changes only the *content* of the existing Edit|Write entry's `command` string, not the array length).
- `TCK-20260904-BASH-SECRET-SCAN-HOOK` (`tickets/inprogress/`) — a sibling, concurrently in-progress ticket that also touches `.claude/settings.json`'s `hooks` block (per this ticket's own Out of Scope note). Real coordination risk — see Risks below.

## Risks and Open Questions

- **Concurrent edit conflict on `.claude/settings.json`**: `TCK-20260904-BASH-SECRET-SCAN-HOOK` is currently `tickets/inprogress/` and, per this ticket's Out of Scope text, also adds to the `hooks` block of the same file. If both land around the same time in this shared worktree, a naive sequential edit-and-commit could produce a merge conflict on the same JSON file (though likely on different array entries, so an additive/non-overlapping merge is the expected, low-risk outcome per the ticket's own "no sequencing dependency" framing). Flagging so the implementer checks `git status`/`git diff` on `.claude/settings.json` immediately before editing, per this repo's shared-worktree hard rule.
- **No open question blocks implementation.** The proposed replacement command (above) is a direct, mechanical mirror of an already-shipped, already-tested precedent (`retrieval_cache.py::read_current_run_sidecar()`'s preference order) — nothing here requires a new design decision.
- **Testing AC2 ("synthetic two-session scenario")** requires a new test pattern not yet present anywhere in this repo for a bash-embedded (not standalone-script) hook — see Test Plan for the concrete recommended approach (extract-and-execute the inner `python3 -c` snippet directly, rather than trying to drive the full `case`/`ls`/`echo` bash construct through a shell subprocess). This is a test-design decision, not a blocking open question — the approach is unambiguous once the constraint ("the hook only externally signals empty-vs-nonempty RUN_ID, not its actual value") is recognized.

## Anti-Drift Hazards

- **Do not adopt `post_tool_hook.py`'s null-sentinel-on-absence behavior for this hook.** It would require the read-only Edit|Write PreToolUse hook to gain a file-write side effect (creating `.claude/current_run.<session_id>` when absent) — a scope-creep that (a) contradicts this ticket's own explicit Scope wording ("falling back to the unscoped... when the scoped file doesn't exist"), (b) is inconsistent with `read_current_run_sidecar()`'s own precedent and its documented reasoning for NOT doing this, and (c) would need its own pruning/lifecycle story (currently solely owned by `post_tool_hook.py`'s `_prune_stale_scoped_sidecars()`) that this ticket's Out of Scope does not authorize adding.
- **Do not touch the `FILE=$(...)` extraction, the `case` matcher list, the `ls tickets/inprogress/*.md` guard, or the `echo` JSON payload text.** Only the `RUN_ID=$(...)` subshell's inner `python3 -c` body changes. A wider rewrite would risk drifting from `test_settings_json_hooks_wiring.py::test_existing_hook_writers_untouched`'s `len(settings["hooks"]["PreToolUse"]) == 4` guard if a new hooks-array entry were accidentally introduced instead of an in-place edit, and would widen the diff far beyond the ticket's stated scope.
- **Keep the trailing `2>/dev/null || true` on the `RUN_ID=$(...)` subshell.** This hook is advisory-only (a missing/stale reminder is not data corruption) — CLAUDE.md's "Monitoring write failure must never fail the workflow" rule and this ticket's own Out of Scope both require the fail-open wrapper stays exactly as-is.
- **`tools/retrieval_cache.py` is explicitly out of scope — do not re-touch it**, even though it is listed in "Related Code Areas" (it's there only so the implementer can *read* it as the reference pattern, not modify it). Re-editing it would duplicate `TCK-20260824-RETRIEVAL-CACHE-SIDECAR-UNIFY`'s already-shipped, already-tested work.
- **`os.environ.get`, not a hook-payload `session_id` field.** This hook has no JSON stdin payload wired into its bash context the way `post_tool_hook.py` does (which reads `session_id` from `sys.stdin`) — it must read the `CLAUDE_CODE_SESSION_ID` environment variable directly, exactly as `retrieval_cache.py` does. Do not attempt to parse a `session_id` out of stdin JSON for this hook; the stdin JSON here only carries `tool_input`/`file_path`.
