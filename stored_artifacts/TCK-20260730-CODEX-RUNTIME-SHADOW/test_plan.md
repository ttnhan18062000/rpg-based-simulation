---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260730-CODEX-RUNTIME-SHADOW
artifact_type: test_plan
tags: [ai, workflows, testing, process-improvement]
---

# Test Plan — TCK-20260730-CODEX-RUNTIME-SHADOW

## Regression Surface

All counts confirmed via `pytest --collect-only -q` on this branch (`simulation_quality`) before
any implementation work for this ticket.

**Unit / contract (must stay green, unmodified by this ticket):**
- `tests/agent_replay/` — 25 tests (fixture envelope, runner branch logic, no-mutation snapshot,
  forbidden-call scan, fixture-spec-doc assertions). This is the canonical runner/fixture this
  ticket's new package must import, never modify.
- `tests/agent_replay_codex/` — 27 tests collected (21 run unconditionally; ~5-6 require
  `CODEX_REPLAY_PARITY_LIVE_CONSENT=1` + `codex` CLI on PATH and skip cleanly otherwise). This
  ticket must not touch `tools/agent_replay_codex/` source at all — a diff there is a scope
  violation.
- `tests/agent_codex_pilot_guardrails/` — 40 tests. Read-only dependency; must not be touched.
- `tests/agent_codex_posttool_adapter/` — 43 tests. Read-only dependency (imports
  `agent_codex_pilot_guardrails.enabled_surface.EVIDENCED_HOOK_EVENTS`); must not be touched.

**Integration (contract/conformance, must stay green):**
- `tests/agent_orchestration/` — validates `agent-orchestration/` contract structure, including
  `agent-orchestration/workflows/implement-ticket.yaml`'s own schema. This ticket reads that file;
  it must never write to it.
- `tests/agent_orchestration_claude_adapter/` — Claude-adapter conformance tests, including
  `tools/agent_orchestration_claude_adapter/divergence_log.py`'s own tests. This ticket imports
  `load_divergences`/`is_approved` from this module read-only.

**Known pre-existing baseline failures (do not attempt to fix under this ticket; do not let
Verify misattribute them to this ticket's changes):**
- `tests/agent_orchestration_claude_adapter/test_terminal_status_conformance.py::
  test_terminal_status_conformance_finalize_incomplete_appears_once_on_both_sides`
- `tests/agent_orchestration_claude_adapter/test_terminal_status_extractor.py::
  test_extract_all_terminal_statuses_dedupes_by_value_not_call_site_count`
  (both fail on hardcoded expected `implement-ticket.js` line numbers that have drifted from
  unrelated tickets landing; confirmed via direct read of the live file's current line numbers)

## New Tests Required

Target package: `tools/agent_codex_runtime_shadow/` (new). Target test directory:
`tests/agent_codex_runtime_shadow/` (new, mirroring the sibling `tests/agent_replay_codex/`
layout: one test file per source module + a `conftest.py` if a shared scratch-repo fixture is
needed, per `tests/agent_replay_codex/test_containment.py`'s `_init_synthetic_repo(tmp_path)`
precedent).

Per acceptance criterion:

**AC #1 — explicit supported phase/tier matrix, deterministic rejection**
- `test_phase_tier_matrix_reads_real_implement_ticket_yaml` — unit — verifies the matrix reader
  loads `agent-orchestration/workflows/implement-ticket.yaml` and derives exactly
  `{tier: standard, phases: [Scope, Investigate, Plan, Review]}` as supported. Location:
  `tests/agent_codex_runtime_shadow/test_phase_tier_matrix.py`.
- `test_rejects_hotfix_tier` — unit — a ticket-shaped input with `tier=hotfix` raises a typed
  rejection error (never silently downgrades to `standard` or partially validates). Same file.
- `test_rejects_unsupported_phase[Implement]` / `[Architecture-Verify]` / `[Test]` / `[Parity]` /
  `[Security-Review]` / `[Verify]` / `[Finalize]` — parametrized unit — each named phase present in
  an input raises the same typed rejection, not a silent skip. Same file.
- `test_accepts_the_one_supported_slice` — unit — a `tier=standard`,
  `phases=[Scope,Investigate,Plan,Review]` input passes matrix validation. Same file.
- `test_contract_version_mismatch_rejected` — unit — an input declaring a `workflow_version` other
  than `implement-ticket.yaml`'s real `workflow_version: 1` is rejected (AC #1's "contract-version"
  half, shared with AC #2). Same file.

**AC #2 — contract-version, phase-order, required-gate, required-artifact validation, machine-checkable and tested**
- `test_phase_order_violation_detected` — unit — an input whose phases arrive out of the declared
  `Scope→Investigate→Plan→Review` order is rejected/flagged, not silently reordered. Location:
  `tests/agent_codex_runtime_shadow/test_phase_order_validation.py`.
- `test_required_gate_missing_detected` — unit — Review phase input missing a `verdict` (the
  required gate output) is rejected. Location: `tests/agent_codex_runtime_shadow/
  test_gate_validation.py`.
- `test_required_artifact_missing_detected[Investigate]` (expects
  `staging_artifacts/{ticket_id}/investigation.md` + `test_plan.md`) /
  `[Plan]` (expects `staging_artifacts/{ticket_id}/plan.md`) — parametrized unit — a scratch input
  claiming a phase completed without its required artifact file present on disk (in the scratch
  dir) is rejected. Location: `tests/agent_codex_runtime_shadow/test_required_artifact_validation.py`.
- `test_required_artifact_present_passes` — unit — same phases, artifact files present, passes.
  Same file.

**AC #3 — scratch/shadow comparison: phase order, final status, gate result, artifacts vs. canonical fixture/runner; RATIFIED-divergence escape hatch**
- `test_shadow_comparison_matches_canonical_fixture` — integration — runs the new adapter's
  in-process (no `codex exec`) validation over the same
  `tests/fixtures/agent_replay/TCK-20260721-ORCHESTRATION-CONTRACT-ADR.yaml`-derived input, and
  asserts the resulting comparison's `match is True` against `tools.agent_replay.runner.
  replay_slice()`'s real output on `phases_completed`, `final_status`, gate result, and (unlike
  `agent_replay_codex.shadow_mode.ShadowModeComparison`) **artifacts** included in `match`.
  Location: `tests/agent_codex_runtime_shadow/test_shadow_comparison.py`.
- `test_shadow_comparison_mismatch_without_ratified_divergence_fails` — unit — a synthetic mismatch
  (mirroring `tests/agent_replay_codex/test_divergence_registration.py`'s pattern) with no matching
  entry in a `tmp_path` divergence-log file fails. Same file.
- `test_shadow_comparison_mismatch_with_ratified_divergence_passes` — unit — same synthetic
  mismatch, but a `tmp_path` divergence-log file has a matching `RATIFIED` entry (using this
  ticket's chosen axis — recommend the 4 documented axes `phase_order`/`terminal_status`/
  `gate_policy`/`artifact_requirements` per investigation.md's Risk note, not the undocumented
  `codex_parity` catch-all the predecessor ticket used) — comparison is accepted. Same file.
- `test_shadow_comparison_never_invokes_codex_exec` — architecture guard — AST/string-constant scan
  (mirroring `tests/agent_replay/test_runner_no_forbidden_calls.py` and `tests/
  agent_codex_posttool_adapter/test_no_subprocess_and_no_live_wiring.py`'s existing precedent)
  proving no `subprocess`, `os.system`, or literal `"codex exec"`/`"codex"` CLI-invocation string
  appears anywhere in `tools/agent_codex_runtime_shadow/`. Location: `tests/
  agent_codex_runtime_shadow/test_no_subprocess.py`.

**AC #4 — containment: no ticket/monitoring/config mutation, no `provider=codex` corpus record**
- `test_shadow_run_produces_zero_diff_in_tickets_and_monitoring` — integration — reuses
  `tools.agent_replay_codex.containment.capture_snapshot`/`assert_no_diff` around a full
  shadow-adapter run against a `tmp_path` synthetic repo (mirroring `tests/agent_replay_codex/
  test_containment.py::_init_synthetic_repo`). Location: `tests/agent_codex_runtime_shadow/
  test_containment.py`.
- `test_shadow_run_writes_no_codex_provider_record` — unit — reuses
  `tools.agent_replay_codex.provenance_check.assert_no_codex_provider_writes` against the real
  `agent-monitoring/` dir after a shadow run, plus a negative-control test with a synthetic
  `provider="codex"` record (mirroring `tests/agent_replay_codex/test_monitoring_provenance.py`'s
  existing pattern exactly). Same file.
- `test_committed_codex_config_remains_hook_free_and_byte_identical` — unit — reuses
  `tools.agent_replay_codex.codex_config_guard.assert_committed_config_hook_free`/
  `snapshot_config_bytes`/`assert_config_bytes_unchanged` around a shadow run. Same file.

**AC #5 — existing suites stay green; consent-gated skips classified as authorization gates, not live-runtime evidence**
- `test_new_package_test_suite_never_requires_live_consent` — architecture guard — collects
  `tests/agent_codex_runtime_shadow/` via `pytest --collect-only` and asserts zero tests are marked
  `skipif`/`skip` on `CODEX_REPLAY_PARITY_LIVE_CONSENT` or any new consent env var — this package's
  core tests must all run unconditionally, unlike `tests/agent_replay_codex/`'s ~5-6 consent-gated
  tests. Location: `tests/agent_codex_runtime_shadow/test_no_live_consent_dependency.py`.
- Regression re-run of `tests/agent_replay_codex/`, `tests/agent_codex_pilot_guardrails/`,
  `tests/agent_codex_posttool_adapter/`, `tests/agent_replay/`, `tests/agent_orchestration/`,
  `tests/agent_orchestration_claude_adapter/` (see Scoped Pytest Commands) — no new failures beyond
  the two pre-existing baseline failures documented above.

## Scoped Pytest Commands

```bash
# New package's own suite
.venv/bin/python3 -m pytest tests/agent_codex_runtime_shadow/ -v

# Direct read-only dependencies this ticket's new package imports from
.venv/bin/python3 -m pytest tests/agent_replay/ tests/agent_replay_codex/ \
  tests/agent_codex_pilot_guardrails/ tests/agent_codex_posttool_adapter/ -v

# Contract/conformance surface (agent-orchestration/workflows/implement-ticket.yaml,
# agent-orchestration/intentional-divergences.md consumers)
.venv/bin/python3 -m pytest tests/agent_orchestration/ tests/agent_orchestration_claude_adapter/ -v
```

Never `pytest tests/` — scope stays to the agent-orchestration/Codex-adjacent domain named above.

## Anti-Drift Test Guards

- **No-`codex exec` guard** (`test_shadow_comparison_never_invokes_codex_exec` above) — the single
  highest-value anti-drift test in this ticket. Its failure is the earliest, cheapest signal that
  the new package has silently regressed into duplicating `tools/agent_replay_codex/`'s real-CLI
  responsibility.
- **No-live-consent-dependency guard** (`test_new_package_test_suite_never_requires_live_consent`
  above) — catches a future contributor accidentally copy-pasting `tests/agent_replay_codex/
  conftest.py`'s `real_codex_replay` session fixture pattern into this new package's tests, which
  would silently reintroduce a paid-invocation dependency this ticket's Out of Scope forbids.
- **Untouched-sibling-package guard** — a `git diff --stat -- tools/agent_replay/ tools/
  agent_replay_codex/ tools/agent_codex_pilot_guardrails/ tools/agent_codex_posttool_adapter/
  agent-orchestration/workflows/implement-ticket.yaml .codex/config.toml` check (run manually at
  Verify, not a pytest test) must be empty — mirrors the predecessor ticket's own Step 12
  "Scope-guard `git diff --stat` checks" precedent recorded in `tickets/done/
  TCK-20260721-CODEX-REPLAY-PARITY.md`.
- **Artifacts-included-in-match guard** (part of `test_shadow_comparison_matches_canonical_fixture`
  above) — explicitly assert the new comparison's `match` computation is `False` when artifacts
  differ but phases/gate/status all agree, proving this ticket actually closes the gap found in
  `agent_replay_codex.shadow_mode.ShadowModeComparison.match` (which silently ignores artifacts
  today) rather than reproducing the same gap under a new name.
- **Divergence-log file guard** — a test asserting any new entries this ticket adds to
  `agent-orchestration/intentional-divergences.md` use one of the 4 documented axis values
  (`terminal_status | phase_order | gate_policy | artifact_requirements`), not a new undocumented
  axis string, catching silent axis-vocabulary drift the way the predecessor ticket's own
  `"codex_parity"` axis quietly introduced one.
- **Empty-`__init__.py` regression guard** — a test asserting `tools/agent_codex_runtime_shadow/
  __init__.py` has a non-empty module docstring stating its responsibility and explicitly
  distinguishing it from `agent_replay_codex`/`agent_codex_pilot_guardrails` (mirroring
  `agent_codex_pilot_guardrails/__init__.py` and `agent_codex_posttool_adapter/__init__.py`'s own
  precedent) — cheap, catches the package shipping without the disambiguating documentation this
  ticket's own Assumptions/Open Questions section demands.
