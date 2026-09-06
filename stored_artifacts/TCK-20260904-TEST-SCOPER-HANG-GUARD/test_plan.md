---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260904-TEST-SCOPER-HANG-GUARD
artifact_type: test_plan
tags: [testing, ai, hooks, debugging]
---

# Test Plan — TCK-20260904-TEST-SCOPER-HANG-GUARD

## Regression Surface

Existing tests that must keep passing, grouped by directory — all under `tests/tools/` and
`tests/agent_orchestration/` (agent-infrastructure tooling; no `src/`-side regression surface
since this ticket touches no simulation code):

**unit (hook scripts, `tests/tools/`):**
- `tests/tools/test_post_tool_hook.py` — existing `PreToolUse`/`PostToolUse` writer; must still
  pass unmodified since this ticket's Out of Scope forbids changing these writers beyond pattern
  reuse.
- `tests/tools/test_retro_nudge_hook.py` — sibling advisory-hook pattern this ticket's new hook
  script should structurally resemble (stdin-JSON-in, `try/except: pass`, subprocess-driven test).
- Any other `tests/tools/*.py` file — per `test-scoper.md`'s own Scoping Rules, a change to any
  flat `tools/*.py` file (a new `tools/agent-monitoring/<new_hook>.py`) requires running the
  **entire `tests/tools/` directory**, never a subset.

**integration / contract (`tests/agent_orchestration/`):**
- `tests/agent_orchestration/test_contract_structure.py` — specifically
  `test_hook_events_yaml_unchanged_normalized_vocabulary` (pins `hook-events.yaml`'s `hook_types`
  to exactly `{PreToolUse, PostToolUse}`) and `test_policy_represents_claude_two_enabled_events`
  (pins `hook-surface-policy.yaml`'s `providers.claude.enabled_events` to exactly the same set).
  **If a real `Stop`/`SubagentStop` hook is wired into `.claude/settings.json`, both of these
  tests go stale by design** — they must be deliberately updated (not left failing, not silently
  weakened) as part of this ticket's implementation, since they currently assert the exact
  vocabulary this ticket's own AC #2 requires expanding. Flag this explicitly at Verify: a
  passing scoped run that still shows these two tests green *unchanged* after a real hook ships
  would mean the hook was never actually registered in `.claude/settings.json`/`hook-events.yaml`
  — a contradiction Verify must catch.

**architecture guard:**
- `tests/agent_orchestration/test_contract_structure.py::test_load_contract_succeeds_against_the
  _real_contract` and `test_load_contract_includes_hook_surface_policy` — must still load/parse
  cleanly if `hook-surface-policy.yaml`'s schema gains a `claude.available_events` key or similar
  (a schema-shape decision Plan must make explicitly, mirroring the same open question the prior
  `TCK-20260730-PROVIDER-HOOK-POLICY` investigation flagged and left to that ticket's own Plan
  phase).

## New Tests Required

Per Acceptance Criteria (four items — the literal (a)/(b) fork, the "new hook event key" proof,
the "exercises the hook script directly" requirement, and the prose-section disposition):

1. **Test name**: `test_hook_fires_for_still_running_background_task` (or equivalent, exact name
   TBD by Implement)
   **Category**: unit (hook-script, stdin-driven subprocess test)
   **Verifies**: given a synthetic transcript fixture (a JSONL file recording a `Bash` tool_use
   with `tool_input.run_in_background: true` and no subsequent completed-status `BashOutput`/
   `Monitor` entry) and a synthetic `SubagentStop` stdin payload whose `transcript_path` points at
   that fixture, the new hook script exits with code 2 (block) and its stderr/output names the
   still-pending background command.
   **Where**: `tests/tools/test_<new_hook_script_name>.py`, following `test_post_tool_hook.py`'s
   `_run_hook(cwd, payload)` subprocess-driven pattern exactly (stdin JSON in, assert on
   `returncode`/`stdout`/`stderr`).

2. **Test name**: `test_hook_allows_stop_when_background_task_already_polled_complete`
   **Category**: unit (hook-script)
   **Verifies**: the negative case — a synthetic transcript where the last `run_in_background`
   Bash call *does* have a later `BashOutput`/`Monitor` entry showing a completed (non-running)
   status; the hook must exit 0 (allow stop), proving the guard does not false-positive on the
   correct, compliant pattern.
   **Where**: same file as #1.

3. **Test name**: `test_hook_allows_stop_when_no_background_task_was_ever_started`
   **Category**: unit (hook-script)
   **Verifies**: a transcript with zero `run_in_background: true` Bash calls at all (the common
   case — most turns never touch this path) exits 0 with no side effects; proves the guard is
   inert for the overwhelming majority of turns, not just correct on the two hang-specific cases.
   **Where**: same file as #1.

4. **Test name**: `test_hook_fails_open_on_malformed_or_missing_transcript`
   **Category**: unit (hook-script) — mirrors `test_retro_nudge_hook_fail_silent_on_malformed_
   data_dir`'s established fail-open pattern for this repo's hook scripts.
   **Verifies**: a missing `transcript_path`, an unreadable file, or malformed JSONL never raises
   an uncaught exception and never blocks a turn it cannot actually evaluate — exits 0 (allow),
   consistent with `hook-surface-policy.yaml`'s own `failure_timeout_fail_open` activation
   prerequisite (fail-open, never fail-closed, on hook error).
   **Where**: same file as #1.

5. **Test name**: `test_new_hook_event_key_not_previously_wired` (or fold into an existing
   contract-structure test)
   **Category**: architecture guard
   **Verifies**: AC #2's literal requirement — `.claude/settings.json`'s `hooks` block contains a
   `Stop` and/or `SubagentStop` key, proving this is a genuinely new deterministic surface and not
   a restatement of the existing `PreToolUse`/`PostToolUse` writers. A simple structural read of
   the committed JSON (`json.load(open(".claude/settings.json"))["hooks"]`), asserting the new
   key(s) exist and reference the new hook script's path.
   **Where**: `tests/agent_orchestration/test_contract_structure.py` (new test alongside the
   existing hook-vocabulary pins) or a new `tests/tools/test_settings_json_hooks_wiring.py` if
   Plan judges the contract-structure file the wrong home (that file currently asserts
   `agent-orchestration/`-governed content, not `.claude/settings.json` directly — Plan should
   decide explicitly rather than default).

6. **Test name**: `test_hook_events_yaml_and_hook_surface_policy_updated_for_new_claude_event`
   (replacing/extending the now-stale pinned tests named in Regression Surface above)
   **Category**: architecture guard
   **Verifies**: `hook-events.yaml`'s normalized vocabulary and `hook-surface-policy.yaml`'s
   `providers.claude.enabled_events` both include the new event(s) actually wired, keeping the
   contract's own "normalized ⊇ enabled" invariant intact rather than silently drifting stale
   relative to the real `.claude/settings.json`.
   **Where**: `tests/agent_orchestration/test_contract_structure.py` (updates the two named
   tests) and `tests/agent_orchestration/test_validator_errors.py` if `loader.py`'s validation
   rules need a corresponding update.

7. **If the fallback path is taken instead** (deterministic detection proven infeasible during
   Implement, contradicting this investigation's YES finding after the scratch-first fixture
   capture): no new hook-script test is required, but **`test_test_scoper_background_commands_
   section_still_present`** (or equivalent) must exist asserting `.claude/agents/test-scoper.md`
   still contains its `## Background Commands` prose section verbatim (grep-style, mirroring
   `TCK-20260902-AGENT-BACKGROUND-TASK-TURN-END-DEFENSE-IN-DEPTH`'s own verification command
   `grep -L "run_in_background" .claude/agents/*.md`), and the literal fallback string must be
   confirmed present in `docs/plans/agent_infrastructure/ai_first_hardening_epics/
   guardrail_enforcement_epic.md` by a text-match check, not just eyeballed.

## Scoped Pytest Commands

```
pytest tests/tools/ tests/agent_orchestration/ -v
```

Never `pytest tests/`. This scope covers: every hook script in `tools/agent-monitoring/`
(flat-directory rule, run the whole `tests/tools/` dir per `test-scoper.md`'s own Scoping Rules),
and the contract-structure/validator tests that pin `hook-events.yaml`/`hook-surface-policy.yaml`.
If Plan's implementation also touches `tools/agent_orchestration/loader.py` or `generator.py`
(needed only if the schema itself changes, e.g. adding a `claude.available_events` key), also
include:

```
pytest tests/agent_orchestration/ tests/agent_orchestration_claude_adapter/ \
       tests/agent_orchestration_codex_adapter/ tests/tools/ -v
```

(mirroring `TCK-20260730-PROVIDER-HOOK-POLICY`'s own final regression command, which is the
closest precedent for a change touching this same contract surface).

## Anti-Drift Test Guards

- **`test_hook_events_yaml_unchanged_normalized_vocabulary` and
  `test_policy_represents_claude_two_enabled_events` must be deliberately updated, never deleted
  or weakened to "pass either way."** These are the exact anti-drift pins that would otherwise
  let a hook get wired into `.claude/settings.json` without the contract files staying honest
  about what's actually enabled — the specific failure mode `TCK-20260730-PROVIDER-HOOK-POLICY`'s
  whole ticket existed to prevent (available/normalized/enabled conflation), now applied to
  Claude instead of Codex.
- **`tests/agent_codex_pilot_guardrails/test_no_live_execution_path.py` is out of this ticket's
  blast radius and must show zero diff.** This ticket does not touch `tools/agent_codex_pilot_
  guardrails/`; if a scoped run ever shows this file's collection changing, that is a sign of
  scope creep into Codex-activation territory, not this ticket's own Claude-side work.
  (Not part of the scoped pytest command above — included here only as a boundary check Verify
  should spot-run if there is any doubt about scope drift.)
- **A guard against the loop-prevention risk flagged in investigation.md**: if Plan/Implement
  ships the real hook, add a test proving the hook script itself does not unconditionally
  re-block on every `Stop` firing for the same still-pending command indefinitely without
  respecting `stop_hook_active` — a synthetic payload with `stop_hook_active: true` should behave
  differently (e.g. allow-through with a warning, not block again) than the first firing, per
  whatever loop-safe design Plan settles on. This test does not yet have a name because the exact
  design is not yet fixed pending the scratch-first fixture capture — Plan must add it, not treat
  its absence as acceptable.
- **A guard against false-positives from this repo's own known multi-concurrent-session
  environment**: the hook must key off the `session_id`/`transcript_path` in its own payload only
  — never off a shared, unscoped state file (the exact cross-session-contamination bug class
  `TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE` already fixed once for `post_tool_hook.py`'s sidecar
  reads). A test seeding two different sessions' transcripts/sentinels and asserting each hook
  invocation only ever inspects its own `transcript_path` is required if the implementation
  introduces any new sidecar/state file at all (it should not need one, since `transcript_path` is
  already self-contained per invocation — but if Implement adds one anyway, this guard is
  mandatory, mirroring `test_post_tool_hook.py`'s own `test_foreign_scoped_sidecar_not_read_by_
  different_session` precedent).
