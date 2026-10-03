---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260730-CODEX-POSTTOOL-ADAPTER
artifact_type: plan
tags: [ai, hooks, agent-monitoring, observability, testing]
---

# Implementation Plan — TCK-20260730-CODEX-POSTTOOL-ADAPTER

## Summary

Build a new, isolated package `tools/agent_codex_posttool_adapter/` that parses a captured Codex
`PostToolUse` hook stdin payload into the shared `tools.jsonl` record shape and delegates the
actual append to `tools/agent-monitoring/writer.py::write_line` — never a second append
mechanism, never a live Codex invocation, never a pilot-selection/signoff decision. The package is
built in narrow, independently-testable slices (input parsing → redaction → identity → live-gate →
writer bridge → assembly → config guard reuse → proposed activation fragment → architecture guards
→ full regression), mirroring the sibling packages `tools/agent_replay_codex/` and
`tools/agent_codex_pilot_guardrails/` in structure, gating discipline (strict-equality env var,
checked immediately before the write), and test layout. It is real, tested, importable code that
stays operationally inert: nothing in the committed `.codex/config.toml` invokes it, and its own
live-append gate defaults closed. The proposed hook activation fragment is delivered as a Python
constant (for architecture-guard tests to introspect) plus a markdown review doc — never a `.toml`
file near `.codex/`, never referenced by the committed config, never invoked by any test or normal
run.

## Steps

### Step 1 — Package scaffold, input payload model, and suite-level non-mutation guards
**Files:** `tools/agent_codex_posttool_adapter/__init__.py`, `tools/agent_codex_posttool_adapter/errors.py`,
`tools/agent_codex_posttool_adapter/input_model.py`, `tests/agent_codex_posttool_adapter/conftest.py`,
`tests/agent_codex_posttool_adapter/test_input_model.py`
**Change:**
- `__init__.py`: package docstring stating the exact responsibility boundary from
  investigation.md's resolved module-location decision ("parses/validates a captured Codex
  PostToolUse hook stdin payload into the shared tools.jsonl record shape... delegates the actual
  append to writer.py's write_line... never invokes codex exec... never governs pilot
  ticket-selection/rollback/signoff"), mirroring `tools/agent_codex_pilot_guardrails/__init__.py`'s
  docstring style.
- `errors.py`: one file for this package's exceptions (mirrors
  `tools/agent_replay_codex/errors.py`'s stated one-file convention): `PayloadValidationError`,
  `HookEventNotEvidencedError`, `IdentityValidationError`, `LiveAppendNotGrantedError`,
  `ActivationFragmentGuardError`.
- `input_model.py`: a `CodexPostToolUsePayload` dataclass (`session_id: str`, `tool_name: str`,
  `tool_input: dict`, `tool_response: object`, `hook_event_name: str`) and
  `parse_payload(raw: dict) -> CodexPostToolUsePayload`. Validation order: raw must be a `dict`
  (else `PayloadValidationError`); required keys `session_id`, `tool_name`, `hook_event_name`,
  `tool_input`, `tool_response` must be present (else `PayloadValidationError` naming the missing
  field); `tool_input` must itself be a `dict` (else `PayloadValidationError`); `hook_event_name`
  must be a member of `tools.agent_codex_pilot_guardrails.enabled_surface.EVIDENCED_HOOK_EVENTS`
  (import that frozenset directly — do not hardcode `"PostToolUse"` as a second source of truth)
  else `HookEventNotEvidencedError`. Only reads `raw_stdin_payload`'s own fields — never reads
  the fixture's outer envelope (`fixture_schema_version`, `capture_grade`, etc.); callers unwrap
  the envelope before calling `parse_payload`.
- `conftest.py`: one autouse, session-scoped fixture for the whole
  `tests/agent_codex_posttool_adapter/` run that (a) snapshots
  `agent-monitoring/{runs,events,tools}.jsonl` via
  `tools.agent_codex_pilot_guardrails.config_toggle.snapshot_rollback_scope`-equivalent hashing
  (reuse that function directly if its signature fits a 3-file subset, otherwise call
  `hashlib.sha256` the same way it does — do not re-derive different logic) and asserts
  byte-identity at teardown; (b) snapshots `.codex/config.toml` bytes via
  `tools.agent_replay_codex.codex_config_guard.snapshot_config_bytes` and asserts unchanged via
  `assert_config_bytes_unchanged` at teardown; (c) captures a `tickets/` git-porcelain-diff
  baseline via `tools.agent_replay_codex.containment`'s existing snapshot/assert-no-diff helpers
  and asserts no diff at teardown. All three reused, none reimplemented.
**Do NOT touch:** `tools/agent_codex_pilot_guardrails/enabled_surface.py` (import only — the
frozenset is read, never modified or widened); `tools/agent-monitoring/post_tool_hook.py` (do not
import or call `_input_summary` from it — it is not designed as a shared helper and Out of Scope
forbids reusing it "by assumption").
**Verify:** `tests/agent_codex_posttool_adapter/test_input_model.py` —
`test_real_fixture_parses_into_adapter_input_model`,
`test_missing_required_field_fails_safely_no_write` (parse-level: asserts the raised exception,
full no-write proof comes at Step 6), `test_non_post_tool_use_hook_event_name_rejected`,
`test_malformed_json_or_wrong_shape_fails_safely`.

### Step 2 — Redaction and record construction
**Files:** `tools/agent_codex_posttool_adapter/redaction.py`, `tools/agent_codex_posttool_adapter/record_builder.py`
**Change:**
- `redaction.py`: `summarize_tool_input(tool_name: str, tool_input: dict) -> str`, structurally
  parallel to `post_tool_hook.py::_input_summary` but built fresh (no import — none exists as a
  shared helper): `Bash` → `tool_input.get("command", "")[:80]`; `Read`/`Edit`/`Write`/`MultiEdit`
  → `tool_input.get("file_path", "")[:120]`; `Agent` → `description` or `prompt`, `[:80]`;
  `mcp__*` prefix → `query`/`q`/`text`, formatted and `[:120]`; fallback → `str(tool_input)[:80]`.
  `derive_status(tool_response: object) -> str` returning `"failed"` if `tool_response` is a dict
  with a truthy `is_error`/`error` key, or a string starting with `"ERROR"`; `"ok"` otherwise —
  mirrors `post_tool_hook.py` lines 65-71 exactly. Neither function returns, logs, or stores
  `tool_response` content itself — only the derived `"ok"`/`"failed"` flag ever leaves this module.
- `record_builder.py`: `build_record(payload: CodexPostToolUsePayload, *, execution_id: str,
  provider: str, ticket_id: str, run_id: str | None = None, seq: int | None = None,
  phase: str | None = None, agent: str | None = None, now: str | None = None) -> dict` producing
  exactly the 13-field shape `post_tool_hook.py` produces: `session_id, run_id, seq, phase, agent,
  ts, tool, input_summary, status, duration_ms, execution_id, provider, ticket_id`. `ts` defaults
  to `datetime.now(timezone.utc).isoformat().replace("+00:00","Z")` if `now` is not injected (test
  determinism). `duration_ms` is always `None` — the Codex payload carries no pre-hook-start
  timestamp sidecar equivalent to `.claude/.tool_start`; fabricating one would violate the Hard
  Rule against inventing durable meaning that isn't real. `tool = payload.tool_name`,
  `input_summary = redaction.summarize_tool_input(...)`, `status = redaction.derive_status(...)`.
  The 6 Codex-only envelope/payload fields (`transcript_path`, `cwd`, `model`, `permission_mode`,
  `turn_id`, `tool_use_id`) are never read by this function at all — there is no parameter for
  them, so there is nothing to accidentally pass through.
**Do NOT touch:** `post_tool_hook.py` (no import, no shared extraction of `_input_summary` — Out
of Scope forbids assuming reuse without validating the Codex boundary, and this ticket's own
Anti-Drift hazard from investigation.md warns against a naive "copy the payload into the summary"
shortcut).
**Verify:** `tests/agent_codex_posttool_adapter/test_redaction.py` —
`test_output_record_omits_transcript_path_cwd_model_permission_mode_turn_id_tool_use_id`,
`test_tool_response_content_never_appears_in_output_record`,
`test_tool_input_summary_is_truncated_and_field_allowlisted`.

### Step 3 — Execution identity validation
**Files:** `tools/agent_codex_posttool_adapter/identity.py`
**Change:** `TICKET_ID_PATTERN = re.compile(r"^TCK-\d{8}-[A-Z][A-Z0-9-]*$")` — **format-valid
only, no filesystem existence check** (see "Resolution — what makes a ticket_id 'known'" below for
the justification this step implements). `validate_identity(provider: str, execution_id: str,
ticket_id: str) -> None`, pure and I/O-free: raises `IdentityValidationError` unless (a)
`provider == "codex"` exactly (no case-folding, no truthy coercion — a caller-supplied
`"claude"` or `"Codex"` is rejected, never silently corrected); (b) `TICKET_ID_PATTERN.fullmatch(ticket_id)`
succeeds; (c) `execution_id` matches `rf"^codex-{re.escape(ticket_id)}-\d+-[0-9a-f]{{8}}$"` —
i.e. it is checked against the *specific* `ticket_id` argument, not a generic wildcard, per
`agent-orchestration/monitoring-schema.yaml`'s
`f"{provider}-{ticket_id}-{unix_ts_ms}-{token_hex_8}"` format. This module does not import
`pathlib`/`os.path`/anything from `tickets/` — that absence is itself part of what Step 9's
architecture guard can later confirm.
**Do NOT touch:** no access to `tickets/inprogress/` or `tickets/done/` from this module or
anywhere else in the package (see Resolution below).
**Verify:** `tests/agent_codex_posttool_adapter/test_identity_validation.py` —
`test_execution_id_shape_validated_against_monitoring_schema`,
`test_provider_field_must_be_exactly_codex_literal`.

### Step 4 — Live-append gate
**Files:** `tools/agent_codex_posttool_adapter/live_gate.py`
**Change:** `LIVE_APPEND_ENV_VAR = "CODEX_POSTTOOL_ADAPTER_LIVE_APPEND"`;
`require_live_append(env: Mapping[str, str] | None = None) -> None` raising
`LiveAppendNotGrantedError` unless `env.get(LIVE_APPEND_ENV_VAR) == "1"` exactly (no truthy
coercion — `"true"`, `"yes"`, unset, empty all refuse). Implemented as a fresh, standalone
function in this package — **not imported** from `consent_gate.py` or `signoff_gate.py` — mirroring
`signoff_gate.py`'s own explicit precedent that structurally distinct gates ("this adapter is
permitted to append" vs. "a human consented to real Codex CLI use" vs. "a human signed off on one
pilot execution") are reused by re-implementing the pattern, never by importing across packages,
so that satisfying one gate can never be mistaken for satisfying another.
**Do NOT touch:** `tools/agent_replay_codex/consent_gate.py`,
`tools/agent_codex_pilot_guardrails/signoff_gate.py` (read as pattern precedent only, never
imported from or modified).
**Verify:** unit-level pass/fail behavior of `require_live_append` against
`{}`, `{"CODEX_POSTTOOL_ADAPTER_LIVE_APPEND": "true"}`, and
`{"CODEX_POSTTOOL_ADAPTER_LIVE_APPEND": "1"}` — folded into
`tests/agent_codex_posttool_adapter/test_live_gate.py` alongside Step 6's end-to-end assertion.

### Step 5 — Writer bridge (single import point for the shared writer)
**Files:** `tools/agent_codex_posttool_adapter/writer_bridge.py`
**Change:** loads `tools/agent-monitoring/writer.py` via
`importlib.util.spec_from_file_location` / `module_from_spec` / `spec.loader.exec_module` —
exactly `tools/agent_replay_codex/entry_criterion.py`'s existing technique for importing a
module from the hyphenated, non-package `tools/agent-monitoring/` directory (never renamed, never
`sys.path.insert`-hacked). Re-exports `write_line` as `writer_bridge.write_line`. This is the
**only** file in the new package permitted to reference `tools/agent-monitoring/writer.py` or open
any file in append mode.
**Do NOT touch:** `tools/agent-monitoring/writer.py` itself (import only, zero modification —
Anti-Drift hazard explicitly forbids reimplementing its lock protocol).
**Verify:** `tests/agent_codex_posttool_adapter/test_uses_shared_writer.py` —
`test_adapter_calls_write_line_not_a_new_append_mechanism` (source/AST scan: the package imports
`write_line` only through this bridge, and no `.py` file in the package contains a direct
`open(..., "a")` / `os.open(..., os.O_APPEND...)` call).

### Step 6 — Adapter entrypoint assembly
**Files:** `tools/agent_codex_posttool_adapter/adapter.py`
**Change:** `process_post_tool_use(raw_payload: dict, *, target_path: Path, execution_id: str,
ticket_id: str, provider: str = "codex", run_id: str | None = None, seq: int | None = None,
phase: str | None = None, agent: str | None = None, env: Mapping[str, str] | None = None,
now: str | None = None) -> bool`. Whole body wrapped in a top-level `try/except Exception: return
False` (mirrors `post_tool_hook.py`'s whole-body wrap — this function must never raise to its
caller). Sequence, each stage's exception caught and short-circuiting to `return False` with **no
call to `writer_bridge.write_line` reached**: (1) `input_model.parse_payload(raw_payload)`; (2)
`identity.validate_identity(provider, execution_id, ticket_id)`; (3)
`live_gate.require_live_append(env)`; (4) `record_builder.build_record(payload, execution_id=...,
provider=provider, ticket_id=ticket_id, run_id=run_id, seq=seq, phase=phase, agent=agent,
now=now)`; (5) `ok = writer_bridge.write_line(target_path, json.dumps(record,
separators=(",", ":")))` — this call is itself wrapped in its own inner `try/except Exception:
return False`, as defense-in-depth against `write_line` violating its own documented no-raise
contract (this is what `test_writer_raising_unexpected_exception_does_not_propagate` proves); (6)
`return bool(ok)`. **No separate diagnostic-write mechanism is added in this package.**
`writer.py::write_line`'s own internal `_write_diagnostic` sidecar (`.writer_health.jsonl`,
triggered automatically on any write failure) already satisfies the policy's
`out_of_band_diagnostics` prerequisite for this call site — adding a second diagnostic writer here
would violate the Anti-Drift hazard against reimplementing writer machinery. Document this
delegation explicitly in the module docstring so a future reader does not mistake the absence of a
second diagnostic path for an oversight.
**Do NOT touch:** does not import from `tools.agent_codex_pilot_guardrails` at all (ticket
selection, signoff, baseline-manifest gate are structurally unrelated concerns per Anti-Drift
hazards).
**Verify:** `tests/agent_codex_posttool_adapter/test_no_write_on_failure.py`
(`test_malformed_payload_never_invokes_write_line`, using a monkeypatched/spy `writer_bridge.write_line`);
`tests/agent_codex_posttool_adapter/test_failure_injection.py`
(`test_writer_returning_false_does_not_raise`, `test_writer_raising_unexpected_exception_does_not_propagate`,
`test_parse_failure_does_not_block_tool_workflow`, `test_bounded_timeout_behavior` — narrowed, per
the Resolution below, to an architecture guard proving `adapter.py` performs no filesystem I/O
beyond the injected `target_path` write itself, since identity validation is format-only and
introduces no I/O to bound); `tests/agent_codex_posttool_adapter/test_live_gate.py`
(`test_append_refused_without_explicit_live_gate`, full end-to-end);
`tests/agent_codex_posttool_adapter/test_redaction.py`
(`test_output_record_carries_provider_codex_literal`).

### Step 7 — Project-config guard reuse (test-only)
**Files:** `tests/agent_codex_posttool_adapter/test_config_guard.py`
**Change:** no new `tools/` source. Imports and calls
`assert_committed_config_hook_free`, `snapshot_config_bytes`, `assert_config_bytes_unchanged` from
`tools.agent_replay_codex.codex_config_guard` — exactly as
`tests/agent_codex_pilot_guardrails/test_no_live_execution_path.py` already does — against the
real repo root, both directly in this test module and (already, from Step 1) via the
`conftest.py` autouse fixture.
**Do NOT touch:** `tools/agent_replay_codex/codex_config_guard.py` (import only).
**Verify:** `test_committed_config_hook_free_reused_not_reimplemented`,
`test_config_bytes_unchanged_across_full_adapter_suite`.

### Step 8 — Proposed activation fragment (reviewable, never-invoked artifact)
**Files:** `tools/agent_codex_posttool_adapter/activation_fragment.py` (new),
`docs/ai/codex_posttool_adapter_activation_fragment.md` (new)
**Change:**
- `activation_fragment.py`: `PROPOSED_HOOK_BLOCK: bytes` — exactly one `[[hooks.PostToolUse]]`
  table (`matcher = "*"`, `command = "true"`), the same deliberate inert no-op placeholder
  discipline `tools/agent_codex_pilot_guardrails/config_toggle.py::_HOOK_BLOCK` already uses, with
  a comment stating the real invocation command is deferred to a future activation ticket because
  `agent-orchestration/hook-surface-policy.yaml`'s `human_approval`, `project_trust_review`, and
  `hook_trust_review` prerequisites remain unmet by this ticket. `render_proposed_fragment(base_toml_bytes:
  bytes) -> bytes` — pure append, never called against a real path anywhere in this package's own
  source. A local, independently-implemented scratch-target guard (own function, own
  `ActivationFragmentGuardError`, same discipline as `config_toggle.py::_assert_scratch_target`
  but not imported from it — this package does not modify or import from
  `agent_codex_pilot_guardrails.config_toggle`, per the ticket's scope guard against touching that
  package's content) that refuses to ever target `repo_root/.codex/config.toml`.
- `docs/ai/codex_posttool_adapter_activation_fragment.md`: a markdown document (never parsed as
  TOML by any loader, never referenced by `.codex/config.toml` or any config-loading code) that
  quotes `PROPOSED_HOOK_BLOCK` in a fenced code block, states it registers only `PostToolUse`, and
  reproduces `hook-surface-policy.yaml`'s 9 `activation_prerequisites` as a checklist with all 9
  marked unmet — the human-reviewable deliverable AC #5 asks for. This file is documentation only;
  no code reads it.
**Do NOT touch:** `tools/agent_codex_pilot_guardrails/config_toggle.py` (read as precedent only,
never modified, never imported for its private `_HOOK_BLOCK`/`_assert_scratch_target`); `.codex/config.toml`
(never written by this step or any step).
**Verify:** `tests/agent_codex_posttool_adapter/test_activation_fragment.py` —
`test_proposed_fragment_registers_only_post_tool_use`,
`test_proposed_fragment_never_applied_to_real_config`,
`test_no_test_or_default_code_path_invokes_the_proposed_fragment`.

### Step 9 — No-subprocess / no-live-wiring architecture guard
**Files:** `tests/agent_codex_posttool_adapter/test_no_subprocess_and_no_live_wiring.py`
**Change:** test-only. AST scan over every `.py` file in `tools/agent_codex_posttool_adapter/`
(all files from Steps 1-8), mirroring
`tests/agent_codex_pilot_guardrails/test_no_live_execution_path.py`'s technique: denylist
`subprocess.run/Popen/call/check_call/check_output`, `os.system`, any dynamic load referencing
`invoker`/`agent_replay_codex`, any static import of `tools.agent_replay_codex.invoker`, and any
execution-shaped function name (`run_pilot`, `execute_pilot`, `invoke_codex`, `run_codex`,
`invoke_codex_exec`). Must run after Steps 1-8 since it scans already-written files on disk;
ordering within the pytest run itself is not correctness-sensitive.
**Do NOT touch:** nothing new — this step only adds a scanning test.
**Verify:** the new test file itself (no pre-existing test covers this package).

### Step 10 — Full scoped regression
**Files:** none (verification-only).
**Change:** run the three scoped pytest commands from `test_plan.md` in order:
```
python3 -m pytest tests/agent_codex_posttool_adapter/ -q
python3 -m pytest tests/agent_codex_pilot_guardrails/ tests/agent_replay_codex/ -q
python3 -m pytest tests/tools/test_codex_hook_payload_fixture.py tests/tools/test_post_tool_hook.py -q
```
Also confirm (via `ls tests/tools/ | grep -i writer`) whether a dedicated `writer.py` test file
exists; if so, add it to the second command per test_plan.md's note. Never run `pytest tests/`.
**Do NOT touch:** none of the regression-surface files listed in test_plan.md — this step is
read-only verification.
**Verify:** all commands above exit 0; zero modification to any file outside
`tools/agent_codex_posttool_adapter/`, `tests/agent_codex_posttool_adapter/`, and
`docs/ai/codex_posttool_adapter_activation_fragment.md`.

## Resolution — what makes a `ticket_id` "known"

**Decision: format-valid only** (`TICKET_ID_PATTERN` regex match against
`TCK-YYYYMMDD-SHORT-SCOPE` shape). **No filesystem existence check against `tickets/inprogress/`
or `tickets/done/` is performed anywhere in this package.**

Justification, per the investigation's explicit instruction to read
`.claude/workflows/implement-ticket.js` (~lines 202-216) before deciding: that file generates
Claude's own `execution_id` from `tid = ticketInfo.ticket_id` with the comment "after tid is
confirmed real by the ticket-scoper agent — never before." It performs **no independent
filesystem existence check at the point of identity generation** — it trusts the ticket-scoper
agent's own prior validation (which, by the workflow's design, only ever runs after a ticket file
already exists at `tickets/inprogress/{id}.md`). This is the established convention this ticket is
asked to parallel "for consistency across providers."

The Codex adapter has no equivalent upstream step: the captured `PostToolUse` fixture itself
carries no `ticket_id` field at all (confirmed by direct read of
`tests/fixtures/codex_hook_payloads/post_tool_use_stdin_capture.json` — only `session_id`,
`turn_id`, `transcript_path`, `cwd`, `hook_event_name`, `model`, `permission_mode`, plus the 4
`PostToolUse` fields). `ticket_id` must always be an explicitly injected caller argument (per
Scope's "explicit injected paths"), never derived from the payload. Requiring this package to
additionally verify that argument against the real `tickets/` filesystem would:
1. Add an I/O dependency the parallel Claude convention does not have at the identical point in
   its own pipeline.
2. Work against Scope's "explicit injected paths" testability requirement and widen the package's
   footprint into `tickets/` for no safety gain — the actual authorization boundary for a real
   append is Step 4's strict-equality live-append env var gate, not ticket-realness.
3. Force `test_bounded_timeout_behavior` (test_plan.md) into a real timeout-injection test against
   filesystem I/O that otherwise does not need to exist.

This directly resolves test_plan.md's own conditional framing: `test_bounded_timeout_behavior`
narrows to an architecture guard (no unbounded I/O exists in `adapter.py`/`identity.py` at all),
and the test_plan's "ticket-corpus non-mutation guard" (for the case Plan required a real file
check) is not needed — Step 3's `identity.py` never touches `tickets/`.

## Scope Guards

- Do not modify `.codex/config.toml` — never written, never touched by any step, code path, or
  test fixture. Every guard (`assert_committed_config_hook_free`, byte-snapshot fixtures) targets
  the real committed file read-only.
- Do not modify any existing file in `tools/agent_replay_codex/` or
  `tools/agent_codex_pilot_guardrails/` — both are import-only dependencies (`codex_config_guard.py`,
  `entry_criterion.py`'s technique, `enabled_surface.py`'s frozenset). Their gating patterns
  (`consent_gate.py`, `signoff_gate.py`, `config_toggle.py`) are read as precedent and
  re-implemented locally, never imported or edited.
- Do not modify `tools/agent-monitoring/writer.py` or `tools/agent-monitoring/post_tool_hook.py` —
  both are import-only/read-only precedent. `post_tool_hook.py`'s `_input_summary` is not imported
  or refactored into a shared helper.
- Do not write any real `provider="codex"` record to `agent-monitoring/{runs,events,tools}.jsonl`
  during implementation or test execution — every test injects a `tmp_path`-based `target_path`;
  the suite-level `conftest.py` fixture (Step 1) proves this mechanically via byte-snapshot.
  Never hardcode `Path("agent-monitoring/tools.jsonl")` as a default anywhere in the new package.
- Do not invoke `codex exec`, `subprocess`, or `os.system` anywhere in
  `tools/agent_codex_posttool_adapter/` — proven by Step 9's AST scan.
- Do not enable the proposed hook command in any project configuration — the fragment
  (`activation_fragment.py`) is rendered only against scratch/test-local byte buffers, never a
  real path, proven by Step 8's tests.
- Do not add filesystem access to `tickets/` from this package — resolved explicitly above.
- Do not build a live stdin-reading CLI entrypoint / hook-installable script in this ticket — out
  of scope per Out of Scope's "Enabling the proposed hook command in project configuration" and
  not required by any acceptance criterion or test in test_plan.md; deferred to a future
  activation ticket once `hook-surface-policy.yaml`'s prerequisites are met.
- Do not touch `docs/parity_ledger/infrastructure.yaml` — the new `INFRA-306` entry is a
  Parity-phase action item (see Anti-Drift Notes), not part of this plan's steps.

## Dependency Map

- Step 1 (input model + conftest) — independent; first step, establishes suite-wide non-mutation
  guards used by every later test.
- Step 2 (redaction + record_builder) — depends on Step 1 (`CodexPostToolUsePayload`).
- Step 3 (identity) — independent of Steps 1-2.
- Step 4 (live_gate) — independent of Steps 1-3.
- Step 5 (writer_bridge) — independent of Steps 1-4.
- Step 6 (adapter assembly) — depends on Steps 1-5 (wires all of them together).
- Step 7 (config guard reuse tests) — independent of adapter logic; can run any time after Step 1's
  `conftest.py` exists, but ordered after Step 6 for narrative continuity.
- Step 8 (activation fragment) — independent of Steps 1-7.
- Step 9 (no-subprocess/no-live-wiring scan) — depends on Steps 1-8 (scans their files on disk).
- Step 10 (regression) — depends on all prior steps.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC #1 — fixtures validate against input model; malformed payloads fail safely, no write | Steps 1, 6 | `test_input_model.py` (4 tests), `test_no_write_on_failure.py` |
| AC #2 — redacted/minimal fields only, via shared writer, no new append mechanism | Steps 2, 5, 6 | `test_redaction.py` (4 tests incl. provider-literal), `test_uses_shared_writer.py` |
| AC #3 — non-blocking for writer/parse/timeout/diagnostic failure | Step 6 | `test_failure_injection.py` (4 tests, `test_bounded_timeout_behavior` narrowed per Resolution above) |
| AC #4 — project-config guard proves committed config byte-identical/hook-free throughout suite | Steps 1, 7 | `test_config_guard.py` (2 tests), `conftest.py` teardown assertions |
| AC #5 — proposed fragment enables only PostToolUse, gated on approval, never invoked by test/normal run | Step 8 | `test_activation_fragment.py` (3 tests), `test_no_subprocess_and_no_live_wiring.py` (Step 9, cross-cutting) |

## Anti-Drift Notes

- The single most important guard in this whole suite is Step 9's AST scan (mirrors
  `test_no_live_execution_path.py`'s own stated priority for its sibling package) — do not weaken,
  skip, or defer any denylist entry in it.
- `duration_ms` is always `None` in every record this adapter produces — do not fabricate a
  pre-hook timestamp Codex's payload does not supply. This is an intentional, documented gap, not
  an oversight the implementer should try to "fix" by inventing a sidecar file.
- `provider` is always the literal `"codex"` string checked by `identity.validate_identity` — the
  adapter's own top-level `process_post_tool_use` should default its `provider` parameter to
  `"codex"` but must still route any caller-supplied value through `validate_identity` rather than
  trusting the default silently, so a caller cannot accidentally pass `"claude"` and have it
  overridden without an error.
- Do not let `record_builder.build_record` or `redaction.py` ever accept or return
  `tool_response` content itself — only the derived `"ok"`/`"failed"` string may leave those
  functions, matching `post_tool_hook.py`'s own precedent exactly.
- After this ticket's implementation lands, a **Parity-phase action item** (not part of this plan)
  is to add a new `INFRA-306` entry to `docs/parity_ledger/infrastructure.yaml` at `priority: P2`,
  cross-referencing `INFRA-281` (the Claude-side identity-model precedent this ticket parallels)
  and pointing `v2_evidence`/`test_path` at this ticket's new test suite. Do not add this entry
  during Implement — it belongs to the Parity phase per the investigation's own recommendation.
- Run `graphify update .` after `tools/` and `tests/` changes land (code changes only — the new
  `docs/ai/*.md` file does not require it, but does require `make knowledge-index-update` per the
  project's docs-change rule).

## Deviations

Two narrow, non-behavioral style notes — neither changes scope, output shape, or gating behavior:

1. **Step 8's scratch-target guard is named `assert_scratch_target` (public), not
   `_assert_scratch_target` (private-by-convention) like `config_toggle.py`'s own function.** The
   plan's language ("own function... same discipline... but not imported from it") did not specify
   visibility. Making it public lets `test_proposed_fragment_never_applied_to_real_config` exercise
   it directly and explicitly from the test module, which reads clearer than reaching into a
   name-mangled-by-convention private function from a test. Behavior (refuses
   `repo_root/.codex/config.toml`, raises `ActivationFragmentGuardError`) is identical to the
   plan's spec.
2. **Step 9's test module ends up covering one more denylist item than plan.md's own prose
   enumerated (`test_no_static_import_of_invoker`), matching `test_no_live_execution_path.py`'s
   full technique 1:1 rather than the trimmed summary in the Step 9 "Change" paragraph.** Plan's
   own Anti-Drift Notes state Step 9 "mirrors `test_no_live_execution_path.py`'s own stated
   priority" and instructs "do not weaken, skip, or defer any denylist entry in it" — the sibling
   file's denylist includes both a static-import test and a dynamic-load test as two separate
   assertions; Step 9's prose paragraph only named the dynamic-load half explicitly. Implemented
   both, consistent with the stated intent to mirror the sibling test's full technique, not a
   narrower reading of it.

No step required a real ticket-corpus filesystem check, no step needed to widen
`EVIDENCED_HOOK_EVENTS`/`EVIDENCED_WRITER_FUNCTIONS`, and no step touched any file under
`tools/agent_replay_codex/`, `tools/agent_codex_pilot_guardrails/`, or `.codex/config.toml` — all
Scope Guards held exactly as written.
