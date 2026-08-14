---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260730-CODEX-POSTTOOL-ADAPTER
artifact_type: test_plan
tags: [ai, hooks, agent-monitoring, observability, testing]
---

# Test Plan — TCK-20260730-CODEX-POSTTOOL-ADAPTER

## Regression Surface

Existing tests that must keep passing (none of this ticket's changes should touch these files —
they are the boundary this ticket must not cross):

**Unit — fixture and evidenced-surface baseline**
- `tests/tools/test_codex_hook_payload_fixture.py` (7 tests: fixture exists/parses, capture
  grade, hook event name, common fields, PostToolUse-specific fields, schema version/metadata) —
  the adapter's input-model tests must not modify this fixture file.
- `tests/agent_codex_pilot_guardrails/test_enabled_surface.py` (5 tests) — the adapter's chosen
  hook event/writer function must remain a subset of `EVIDENCED_HOOK_EVENTS`/
  `EVIDENCED_WRITER_FUNCTIONS`; these tests must not need modification.

**Unit — shared writer and Claude hook (must stay untouched)**
- `tests/tools/test_writer.py` (if present) / any existing `writer.py` coverage — this ticket
  adds a new call site, not a new writer implementation.
- `tests/tools/test_post_tool_hook.py` — Claude's own hook; this ticket must not modify
  `post_tool_hook.py`, so this suite's behavior is unaffected and must be re-run unmodified as a
  negative-control (proves the Claude path is untouched).

**Integration — no-live-execution / config-guard precedent**
- `tests/agent_codex_pilot_guardrails/test_no_live_execution_path.py` (6 tests: no static import
  of `invoker`, no dynamic load of `invoker`/`agent_replay_codex`, no subprocess calls/imports
  anywhere in that package, no execution-shaped function names, committed config stays hook-free).
- `tests/agent_replay_codex/test_codex_config_guard.py` and
  `tests/agent_replay_codex/test_no_production_hook_invocation.py` — the reused
  `assert_committed_config_hook_free`/`snapshot_config_bytes` functions must keep passing their
  own existing suite unmodified.
- `tests/agent_replay_codex/test_containment.py`, `test_no_forbidden_calls.py` — confirm the
  broader "no live Codex side effect" test infrastructure this ticket's own guard tests should
  mirror stays green.

**Arena-combat**: not applicable — this ticket has no simulation/combat surface.

## New Tests Required

Per acceptance criteria, in `tests/agent_codex_posttool_adapter/` (new directory, mirroring
`tests/agent_codex_pilot_guardrails/` and `tests/agent_replay_codex/`'s existing package-per-tool
layout):

**AC #1 — fixture validates against the documented input model; malformed payloads fail safely**
- `test_real_fixture_parses_into_adapter_input_model` (unit) — verifies
  `tests/fixtures/codex_hook_payloads/post_tool_use_stdin_capture.json`'s `raw_stdin_payload`
  parses into the adapter's typed input dataclass/model without error. Lives in
  `tests/agent_codex_posttool_adapter/test_input_model.py`.
- `test_missing_required_field_fails_safely_no_write` (unit) — a payload missing `tool_name` (or
  another required field) is rejected without raising past the adapter's public entrypoint and
  without any call reaching `write_line`. Same file.
- `test_non_post_tool_use_hook_event_name_rejected` (unit) — a payload with
  `hook_event_name != "PostToolUse"` is rejected safely (proves the adapter enforces the
  evidenced-event boundary from `enabled_surface.EVIDENCED_HOOK_EVENTS`, not just trusts the
  caller). Same file.
- `test_malformed_json_or_wrong_shape_fails_safely` (unit) — non-dict top-level payload, or a
  `tool_input` that isn't a dict, is rejected without a repository write. Same file.
- `test_malformed_payload_never_invokes_write_line` (unit, using a monkeypatched/spy writer) —
  direct proof (not just absence-of-exception) that the write path is never reached for any
  malformed-payload case above. `tests/agent_codex_posttool_adapter/test_no_write_on_failure.py`.

**AC #2 — redacted/minimal fields only, via the shared writer, not a new append mechanism**
- `test_output_record_omits_transcript_path_cwd_model_permission_mode_turn_id_tool_use_id` (unit)
  — proves the adapter's output record does not carry any of the 6 Codex-specific fields that
  have no home in the shared `tools.jsonl` shape. `tests/agent_codex_posttool_adapter/test_redaction.py`.
- `test_tool_response_content_never_appears_in_output_record` (unit) — the real fixture's
  `tool_response` string (directory listing output) must not appear verbatim (or as a substring)
  anywhere in the produced record; only a derived `status` flag is present. Same file.
- `test_tool_input_summary_is_truncated_and_field_allowlisted` (unit) — mirrors
  `post_tool_hook.py::_input_summary`'s own precedent: per-tool-type extraction + length cap,
  applied to Codex's `tool_input` shape (`{"command": "..."}` for `Bash`). Same file.
- `test_adapter_calls_write_line_not_a_new_append_mechanism` (architecture guard, source-text or
  AST scan) — asserts the adapter module imports `write_line` from
  `tools.agent-monitoring.writer` (via the existing hyphenated-directory import technique already
  used in this repo, e.g. `entry_criterion.py`'s `importlib.util.spec_from_file_location`
  pattern) and contains no direct `open(..., "a")`/`os.open(..., os.O_APPEND...)` call anywhere in
  its own source. `tests/agent_codex_posttool_adapter/test_uses_shared_writer.py`.
- `test_output_record_carries_provider_codex_literal` (unit) — every successfully-produced record
  has `"provider": "codex"` exactly (never inferred, never a caller-overridable default). Same
  file as the writer-usage guard or `test_redaction.py`.

**AC #3 — non-blocking behavior for writer, parse, timeout, and diagnostic failure cases**
- `test_writer_returning_false_does_not_raise` (unit, `write_line` monkeypatched to return
  `False`) — adapter entrypoint completes without raising and without crashing the caller.
  `tests/agent_codex_posttool_adapter/test_failure_injection.py`.
- `test_writer_raising_unexpected_exception_does_not_propagate` (unit, `write_line` monkeypatched
  to raise, simulating a defect in the writer itself despite its own no-raise contract) — proves
  the adapter's own boundary is fail-open even if a dependency violates its contract. Same file.
- `test_parse_failure_does_not_block_tool_workflow` (unit) — malformed stdin (invalid JSON, or a
  payload failing the AC #1 checks) results in a clean no-op return, never an unhandled exception
  reaching the process exit code. Same file.
- `test_bounded_timeout_behavior` (unit) — if the adapter performs any I/O beyond the pre-parsed
  payload (e.g. a `tickets/` existence check for the "known ticket ID" requirement — see
  investigation.md's open question), that I/O has an explicit bound and a fail-open path proven
  under a simulated slow/hanging dependency. Same file. (If Plan resolves "known ticket ID" as
  format-only with no filesystem I/O, this test narrows to proving no unbounded I/O exists at
  all — an architecture guard rather than a timeout-injection test.)
- `test_diagnostic_failure_does_not_block` (unit) — if the adapter writes its own diagnostic/log
  line (distinct from the monitoring record), a failure in that diagnostic write path must not
  prevent the adapter from returning cleanly, mirroring `writer.py::_write_diagnostic`'s own
  swallow-everything precedent. Same file.

**AC #4 — project-config guard proves committed `.codex/config.toml` stays byte-identical/hook-free**
- `test_committed_config_hook_free_reused_not_reimplemented` (architecture guard) — imports
  `assert_committed_config_hook_free` from `tools.agent_replay_codex.codex_config_guard` (exactly
  as `tests/agent_codex_pilot_guardrails/test_no_live_execution_path.py:23,175-178` already does)
  and calls it against the real repo root at suite start/end.
  `tests/agent_codex_posttool_adapter/test_config_guard.py`.
- `test_config_bytes_unchanged_across_full_adapter_suite` — snapshot `.codex/config.toml` bytes
  before and after this ticket's own test module runs, using `snapshot_config_bytes`/
  `assert_config_bytes_unchanged` (also imported, not reimplemented). Same file.

**AC #5 — proposed activation fragment enables only PostToolUse, gated behind approval; never
invoked by any test or normal run**
- `test_proposed_fragment_registers_only_post_tool_use` (unit) — the adapter's proposed
  hook-registration TOML fragment (whether it's a new constant or an update to
  `config_toggle.py::_HOOK_BLOCK`) contains exactly one `[[hooks.*]]` table and it is
  `PostToolUse`. `tests/agent_codex_posttool_adapter/test_activation_fragment.py`.
- `test_proposed_fragment_never_applied_to_real_config` — reuses/extends
  `config_toggle.py`'s `_assert_scratch_target` discipline; any test constructing the enabled
  fragment must target a scratch path, never `repo_root/.codex/config.toml`. Same file.
- `test_no_test_or_default_code_path_invokes_the_proposed_fragment` (architecture guard, AST/
  source scan over the new package, mirroring
  `test_no_live_execution_path.py::test_no_execution_shaped_function_names`'s technique) —
  denylist-style scan proving no function in the new package's own source calls
  `config_toggle.enable(...)` against a non-scratch path, and no test module invokes the fragment
  as a live hook. Same file.

**Cross-cutting — the "approved later runtime path" gate (Scope bullet 3 / investigation.md
Question 3's resolution)**
- `test_append_refused_without_explicit_live_gate` (unit) — a fully valid, well-formed payload
  with correct `provider="codex"`/execution identity/known ticket_id is still refused (no
  `write_line` call reached) unless the ticket's chosen env-var gate (e.g.
  `CODEX_POSTTOOL_ADAPTER_LIVE_APPEND=1`, exact name per Plan's decision) is set, mirroring
  `consent_gate.py::require_live_consent`/`signoff_gate.py::require_pilot_signoff`'s strict
  equality (no truthy coercion) pattern. `tests/agent_codex_posttool_adapter/test_live_gate.py`.
- `test_execution_id_shape_validated_against_monitoring_schema` (unit) — a synthetic
  `execution_id` not matching `f"codex-{ticket_id}-{unix_ts_ms}-{token_hex_8}"` is rejected.
  `tests/agent_codex_posttool_adapter/test_identity_validation.py`.
- `test_provider_field_must_be_exactly_codex_literal` (unit) — `provider="claude"` or any other
  value on the input side (if the adapter ever accepts a caller-supplied provider rather than
  hardcoding it) is rejected, not silently coerced. Same file.

## Scoped Pytest Commands

```
python3 -m pytest tests/agent_codex_posttool_adapter/ -q
python3 -m pytest tests/agent_codex_pilot_guardrails/ tests/agent_replay_codex/ -q
python3 -m pytest tests/tools/test_codex_hook_payload_fixture.py tests/tools/test_post_tool_hook.py -q
```

Never `pytest tests/`. If a `writer.py`-specific unit test file exists (confirm exact name via
`ls tests/tools/ | grep -i writer` at Implement time — not confirmed present during this
investigation pass), add it to the second command above so the shared writer's own regression
surface is re-run alongside the guardrail/replay packages this ticket's design borrows from.

## Anti-Drift Test Guards

- **Real-corpus write guard**: every test in `tests/agent_codex_posttool_adapter/` that reaches
  the adapter's write path must assert (via `tmp_path` injection, never the literal
  `Path("agent-monitoring/tools.jsonl")`) that no line is ever appended to the real
  `agent-monitoring/tools.jsonl`/`runs.jsonl`/`events.jsonl` — add a suite-level fixture that
  snapshots those three files' byte content before and after the whole
  `tests/agent_codex_posttool_adapter/` run and asserts byte-identity, mirroring
  `config_toggle.py::snapshot_rollback_scope`/`assert_rollback_scope_unchanged`'s existing
  pattern (reuse those functions directly if their signatures fit, rather than re-deriving the
  hashing logic).
- **Config-immutability guard**: `test_config_bytes_unchanged_across_full_adapter_suite` (above)
  doubles as an anti-drift guard — any future change that accidentally wires the proposed
  fragment into a fixture setup step would be caught here.
- **Evidenced-surface guard**: a new test importing
  `tools.agent_codex_pilot_guardrails.enabled_surface.assert_enabled_surface_subset` and calling
  it with the adapter's actual chosen hook-event/writer-function set — catches any future drift
  where the adapter starts using a second writer function or hook event without updating the
  evidenced-surface declaration first.
- **No-subprocess guard for this new package** (mirrors
  `test_no_live_execution_path.py`'s `test_no_subprocess_module_imported_anywhere_in_package` and
  `test_no_subprocess_or_os_system_calls_anywhere_in_package`): this adapter parses an
  already-captured stdin payload and should never itself invoke `codex exec` or any subprocess —
  add an equivalent AST scan for `tools/agent_codex_posttool_adapter/*.py` specifically, since
  `test_no_live_execution_path.py`'s existing scan is scoped only to
  `tools/agent_codex_pilot_guardrails/*.py` and will not catch a violation in the new package.
- **Claude-hook non-regression guard**: re-run `tests/tools/test_post_tool_hook.py` unmodified as
  part of this ticket's own verification, specifically to catch any accidental shared-helper
  extraction that changes Claude's hook behavior as a side effect of building the Codex adapter
  (Out of Scope explicitly forbids touching `post_tool_hook.py`).
- **Ticket-corpus non-mutation guard**: if Plan resolves the "known ticket ID" open question as
  requiring a real `tickets/inprogress/{id}.md` or `tickets/done/{id}.md` file check, that check
  must be strictly read-only — add a guard asserting no test run leaves any new/modified file
  under `tickets/`, mirroring `tools/agent_replay_codex/containment.py`'s
  `_WATCHED_GIT_PATHSPECS` porcelain-diff technique (reuse `capture_snapshot`/`assert_no_diff`
  from that module rather than re-deriving it).
