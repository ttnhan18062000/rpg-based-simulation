---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260730-CODEX-POSTTOOL-ADAPTER
phase: done
date: 2026-07-30
tags: [ai, hooks, agent-monitoring, observability, testing]
---

# TCK-20260730-CODEX-POSTTOOL-ADAPTER

## Title
Build the isolated Codex PostToolUse monitoring adapter

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Implement and test the smallest Codex-specific boundary that can normalize the captured `PostToolUse` payload into the shared monitoring writer and execution identity model. This is isolated activation evidence only: it must not enable a project hook or create real Codex traffic in the repository corpus.

## Scope
- Consume the hook-surface policy and the approved Claude identity conventions to define a Codex `PostToolUse` adapter input/output contract.
- Build a testable adapter/harness using captured payload fixtures, explicit injected paths, bounded timeout/failure behavior, and redacted summaries; do not route raw tool input/output into monitoring.
- Require an explicit `provider="codex"`, validated execution identity, and known ticket ID before an adapter is permitted to append a record in an approved later runtime path.
- Keep default/scratch verification non-writing against the repository monitoring corpus and committed config; use temporary directories and test doubles for writer behavior.
- Add failure-injection coverage proving malformed payloads, writer failures, timeouts, and diagnostic failures cannot block a Codex tool workflow.
- Produce a reviewable proposed hook command/config fragment, but leave `.codex/config.toml` byte-identical and hook-free.

## Out of Scope
- Enabling the proposed hook command in project configuration.
- Running Codex or writing `provider=codex` into real `agent-monitoring/*.jsonl` during ordinary implementation/test execution.
- Reusing Claude's `post_tool_hook.py` by assumption without validating the Codex payload boundary.
- Implementing the full `implement-ticket` runtime or selecting/executing a pilot.

## Acceptance Criteria
- [x] Captured Codex `PostToolUse` fixtures validate against the adapter's documented input model, and unsupported/malformed payloads fail safely without a repository write.
- [x] The adapter emits only redacted/minimal monitoring fields and uses the shared append writer interface rather than a new append mechanism.
- [x] Adapter tests prove non-blocking behavior for writer, parse, timeout, and diagnostic failure cases.
- [x] A project-config guard proves committed `.codex/config.toml` remains byte-identical/hook-free throughout the test suite.
- [x] The proposed activation fragment enables only `PostToolUse` and only after the policy's explicit human-approval gate; no test or normal run invokes it.

## Related Tickets
- TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC (parent)
- TCK-20260730-PROVIDER-HOOK-POLICY (must complete first)
- TCK-20260730-CLAUDE-EXECUTION-IDENTITY (must complete first; establishes new-record identity convention)
- TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE (DONE; source fixture)

## Related Docs
- docs/plans/archive/agent_infrastructure/current_codex_runtime_status_and_activation_plan.md
- docs/ai/codex_capability_matrix.md
- agent-orchestration/monitoring-schema.yaml

## Related Stored Artifacts
- stored_artifacts/TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE/

## Related Code Areas
- tests/fixtures/codex_hook_payloads/post_tool_use_stdin_capture.json
- tools/agent-monitoring/writer.py
- tools/agent-monitoring/post_tool_hook.py
- tools/agent_codex_pilot_guardrails/enabled_surface.py
- tools/agent_codex_pilot_guardrails/config_toggle.py
- .codex/config.toml
- tests/tools/test_codex_hook_payload_fixture.py
- tests/agent_codex_pilot_guardrails/test_enabled_surface.py

## Assumptions / Open Questions
- Investigate must choose a dedicated Codex adapter location that does not blur replay tooling, pilot guardrails, and a live writer boundary.
- Any later live hook command must be explicitly reviewed for project trust and hook trust in addition to this ticket's implementation evidence.

## Implementation Notes

Implemented `plan.md`'s 10 steps in order, following `staging_artifacts/TCK-20260730-CODEX-POSTTOOL-ADAPTER/plan.md` exactly (no step-level deviation — see `plan.md`'s new "Deviations" section for two narrow style notes that do not change behavior or scope).

**New package `tools/agent_codex_posttool_adapter/`:**
- `__init__.py` — responsibility-boundary docstring, mirrors `agent_codex_pilot_guardrails/__init__.py`'s style.
- `errors.py` — `PayloadValidationError`, `HookEventNotEvidencedError`, `IdentityValidationError`, `LiveAppendNotGrantedError`, `ActivationFragmentGuardError`.
- `input_model.py` — `CodexPostToolUsePayload` dataclass + `parse_payload(raw: dict)`, validating dict-shape, 5 required fields, `tool_input` dict-shape, and `hook_event_name` against `agent_codex_pilot_guardrails.enabled_surface.EVIDENCED_HOOK_EVENTS` (imported, not hardcoded).
- `redaction.py` — `summarize_tool_input` (per-tool-type truncate/allowlist, structurally parallel to but not imported from `post_tool_hook.py::_input_summary`) and `derive_status` (never touches `tool_response` content, only structurally inspects it).
- `record_builder.py` — `build_record` producing the exact 13-field `tools.jsonl` shape; `duration_ms` always `None`; the 6 Codex-only envelope fields have no parameter at all.
- `identity.py` — `TICKET_ID_PATTERN` + `validate_identity(provider, execution_id, ticket_id)`, format-only (no filesystem check), pure/I/O-free, per plan.md's "Resolution — what makes a ticket_id 'known'".
- `live_gate.py` — `LIVE_APPEND_ENV_VAR = "CODEX_POSTTOOL_ADAPTER_LIVE_APPEND"` + `require_live_append`, strict-equality (`== "1"`), re-implemented locally (not imported from `consent_gate.py`/`signoff_gate.py`).
- `writer_bridge.py` — the sole file referencing `tools/agent-monitoring/writer.py`, loaded via `importlib.util.spec_from_file_location` exactly as `entry_criterion.py` does; re-exports `write_line`.
- `adapter.py` — `process_post_tool_use(...)`: parse → validate identity → **live-gate check before any write** → build record → write via `writer_bridge` (own inner try/except as defense-in-depth). Whole body wrapped in `try/except Exception: return False`; never raises to caller.
- `activation_fragment.py` — `PROPOSED_HOOK_BLOCK` (inert `command = "true"` placeholder), `render_proposed_fragment` (pure byte-append, never called against a real path anywhere in package source), `assert_scratch_target` (independently implemented, refuses `repo_root/.codex/config.toml`).
- `docs/ai/codex_posttool_adapter_activation_fragment.md` — human-reviewable doc quoting the fragment and all 9 unmet `hook-surface-policy.yaml` prerequisites as an unchecked checklist.

**New tests `tests/agent_codex_posttool_adapter/`** (41 tests total, all passing): `conftest.py` (suite-level autouse session fixture snapshotting real `agent-monitoring/{runs,events,tools}.jsonl` via sha256, `.codex/config.toml` bytes via `codex_config_guard`, and a `tickets/`-scoped git-porcelain diff via `containment` — all reused, none reimplemented), `test_input_model.py`, `test_redaction.py`, `test_identity_validation.py`, `test_live_gate.py`, `test_uses_shared_writer.py`, `test_no_write_on_failure.py`, `test_failure_injection.py`, `test_config_guard.py`, `test_activation_fragment.py`, `test_no_subprocess_and_no_live_wiring.py` (Step 9's AST-based guard, mirroring `test_no_live_execution_path.py`'s exact denylist technique: no static import of `invoker`, no dynamic load referencing `invoker`/`agent_replay_codex`, no `subprocess`/`os.system` calls or `subprocess` import anywhere in the package, no execution-shaped function names, committed config stays hook-free).

**Explicit verifications performed (per orchestrator instruction):**
- (a) `grep -rn "codex exec\|subprocess" tools/agent_codex_posttool_adapter/` returns only two doc-prose hits inside `__init__.py`'s docstring (one stating the package "never invokes `codex exec`", one naming the guard test file) — zero actual imports/calls. A stricter `grep -rn "import subprocess\|subprocess\.\|os\.system("` returns nothing. `test_no_subprocess_and_no_live_wiring.py` proves this structurally via AST, not string-match.
- (b) `git diff --stat -- .codex/config.toml` and `git status --porcelain -- .codex/config.toml` are both empty — byte-identical, untouched.
- (c) Bracketed before/after line-count check (`wc -l` on the real `agent-monitoring/{runs,events,tools}.jsonl` immediately before and after running `pytest tests/agent_codex_posttool_adapter/ -q`) showed **zero new lines** from this ticket's own suite (779/4264/76553 before and after). Note: the real `tools.jsonl` line count grows independently *between* separate command invocations during this implementation session because Claude Code's own live `post_tool_hook.py` logs every tool call I make while implementing — that is the harness's normal background behavior, unrelated to and not caused by this ticket's adapter code or test suite, and the suite's own autouse `conftest.py` fixture (which brackets the *entire* `tests/agent_codex_posttool_adapter/` session, not just one invocation) confirms zero drift for its own run.

**Pre-existing, unrelated regression-surface failure observed:** `tests/agent_codex_pilot_guardrails/test_concurrent_claim.py::test_provider_field_coverage_against_real_corpus_is_currently_zero` fails on this branch (`assert 1 == 0`) because the real `agent-monitoring/runs.jsonl` now contains one `provider="claude"` record — a consequence of `TCK-20260730-CLAUDE-EXECUTION-IDENTITY` (a "must complete first" dependency ticket, already landed) making the real Claude hook populate `provider` for the first time. This is **not caused by this ticket's code or test suite** (confirmed: `tests/agent_codex_posttool_adapter/`'s own suite writes zero lines to the real corpus, per (c) above) and this ticket's scope guards forbid touching `tools/agent_codex_pilot_guardrails/` or its tests. Flagging as observed, out-of-scope, pre-existing drift rather than silently ignoring it.

**Verify-phase finding and fix:** The first Verify pass (`done-checker`) correctly found `BLOCKED` — `test_plan.md`'s "Anti-Drift Test Guards" section committed to an "Evidenced-surface guard" test (importing `tools.agent_codex_pilot_guardrails.enabled_surface.assert_enabled_surface_subset` and calling it against the adapter's actual chosen hook-event/writer-function set), which was silently omitted from the original 10-step implementation and left undocumented as a deviation. This was a real, disclosed-nowhere gap, not a false positive. Fixed by adding `tests/agent_codex_posttool_adapter/test_evidenced_surface_guard.py` (2 new tests): one proving the adapter's real surface — `{"PostToolUse"}` (the only value `input_model.py::parse_payload` accepts) and `{writer_bridge.write_line.__name__}` (the only function `writer_bridge.py` binds) — passes `assert_enabled_surface_subset` cleanly; one proving a surface that exceeds evidence (e.g. adding `PreToolUse`) is correctly rejected. Reuses the existing guardrails function by import, per the same "import and call, never reimplement" pattern `test_config_guard.py` (Step 7) already established — no new tools/ source added. Full adapter suite re-run: 43/43 passing (41 original + 2 new).

## Test Summary

```
python3 -m pytest tests/agent_codex_posttool_adapter/ -q
→ 43 passed

python3 -m pytest tests/agent_codex_pilot_guardrails/ tests/agent_replay_codex/ -q
→ 61 passed, 5 skipped, 1 failed (pre-existing, unrelated — see Implementation Notes)

python3 -m pytest tests/tools/test_codex_hook_payload_fixture.py tests/tools/test_post_tool_hook.py tests/tools/test_monitoring_writer.py tests/tools/test_monitoring_writer_lockfile_candidate.py tests/tools/test_monitoring_writer_single_source.py -q
→ 28 passed
```
(`ls tests/tools/ | grep -i writer` confirmed 3 dedicated writer test files; all 3 added to the third command per test_plan.md's note.)

## Files Changed
- `tools/agent_codex_posttool_adapter/__init__.py` (new)
- `tools/agent_codex_posttool_adapter/errors.py` (new)
- `tools/agent_codex_posttool_adapter/input_model.py` (new)
- `tools/agent_codex_posttool_adapter/redaction.py` (new)
- `tools/agent_codex_posttool_adapter/record_builder.py` (new)
- `tools/agent_codex_posttool_adapter/identity.py` (new)
- `tools/agent_codex_posttool_adapter/live_gate.py` (new)
- `tools/agent_codex_posttool_adapter/writer_bridge.py` (new)
- `tools/agent_codex_posttool_adapter/adapter.py` (new)
- `tools/agent_codex_posttool_adapter/activation_fragment.py` (new)
- `docs/ai/codex_posttool_adapter_activation_fragment.md` (new)
- `tests/agent_codex_posttool_adapter/__init__.py` (new)
- `tests/agent_codex_posttool_adapter/conftest.py` (new)
- `tests/agent_codex_posttool_adapter/test_input_model.py` (new)
- `tests/agent_codex_posttool_adapter/test_redaction.py` (new)
- `tests/agent_codex_posttool_adapter/test_identity_validation.py` (new)
- `tests/agent_codex_posttool_adapter/test_live_gate.py` (new)
- `tests/agent_codex_posttool_adapter/test_uses_shared_writer.py` (new)
- `tests/agent_codex_posttool_adapter/test_no_write_on_failure.py` (new)
- `tests/agent_codex_posttool_adapter/test_failure_injection.py` (new)
- `tests/agent_codex_posttool_adapter/test_config_guard.py` (new)
- `tests/agent_codex_posttool_adapter/test_activation_fragment.py` (new)
- `tests/agent_codex_posttool_adapter/test_no_subprocess_and_no_live_wiring.py` (new)
- `tests/agent_codex_posttool_adapter/test_evidenced_surface_guard.py` (new — added at Verify to close a real, disclosed-nowhere test_plan.md gap; see Implementation Notes)

## Completion Summary
Built and tested the isolated `tools/agent_codex_posttool_adapter/` package: it parses a captured Codex `PostToolUse` hook stdin payload, redacts it (never persisting `tool_response` content), validates a format-only execution identity, checks a strict-equality live-append env-var gate before any write, and delegates the actual append to the existing shared `writer.py::write_line` — never a second append mechanism. All 5 acceptance criteria are met and test-covered (43 tests, all passing — 41 from the original implementation pass plus 2 added at Verify). The package is real and fully exercised by its own suite but stays operationally inert: `.codex/config.toml` is untouched (verified byte-identical), no live wiring exists (AST-verified), and the proposed activation fragment is documented for future human review but never applied or invoked anywhere. One pre-existing, unrelated test failure in a sibling package's regression surface was observed and reported (not fixed, per scope guards).

The first Verify (`done-checker`) pass correctly returned `BLOCKED`: `test_plan.md`'s "Evidenced-surface guard" test commitment had been silently omitted from the original implementation and left undocumented as a deviation — a real, disclosed-nowhere gap, not a false positive (see Implementation Notes' "Verify-phase finding and fix" for the root cause and the fix). It was closed by adding `tests/agent_codex_posttool_adapter/test_evidenced_surface_guard.py` (2 tests, reusing `agent_codex_pilot_guardrails.enabled_surface.assert_enabled_surface_subset` by import rather than reimplementing it), after which a genuine re-verify pass confirmed all 5 acceptance criteria against the real implementation and test suite.
