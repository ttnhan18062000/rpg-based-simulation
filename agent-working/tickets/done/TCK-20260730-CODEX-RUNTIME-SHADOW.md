---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260730-CODEX-RUNTIME-SHADOW
phase: done
date: 2026-07-30
tags: [ai, workflows, testing, process-improvement]
---

# TCK-20260730-CODEX-RUNTIME-SHADOW

## Title
Implement the minimal Codex ticket runtime and contained shadow parity

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Create a narrow, machine-checkable Codex `implement-ticket` runtime adapter and prove it in scratch/shadow mode. The existing Codex replay adapter is deterministic Scope-to-Review fixture replay only; it must not be relabeled as a live ticket runtime. This ticket establishes exactly which phases and tiers the first runtime supports, rejects everything else, and produces parity evidence before any pilot can be considered.

## Scope
- Define a dedicated runtime adapter package from `agent-orchestration/workflows/implement-ticket.yaml`, separate from the replay and pilot-guardrail packages.
- Support only a deliberately selected initial phase/tier slice; reject unsupported phases, tiers, and contract versions clearly rather than implying full Claude parity.
- Map a real ticket-shaped input through machine-checkable phase transition, gate, and required-artifact records in a scratch/shadow environment.
- Compare Codex output against the canonical fixture/runner for phase order, final status, gate result, and required artifacts. A mismatch requires a ratified intentional divergence before it is accepted.
- Add containment checks proving the shadow path creates no repository ticket/config mutation and no `provider=codex` monitoring corpus record.
- Preserve Claude as the default production executor and leave committed `.codex/config.toml` hook-free.

## Out of Scope
- A live ticket implementation, ticket ownership/finalization, autonomous execution, or a production cutover.
- Treating the existing Scope-to-Review replay result as evidence of complete runtime parity.
- A real hook registration, paid Codex invocation, or production monitoring write.
- Weakening current replay containment or pilot guardrail protections.

## Acceptance Criteria
- [x] The adapter has an explicit supported phase/tier matrix and deterministically rejects unsupported input.
- [x] Contract-version, phase-order, required-gate, and required-artifact validation are machine-checkable and covered by tests.
- [x] Scratch/shadow comparison validates phase order, final status, gate result, and artifacts against canonical fixture evidence; mismatches fail unless a matching RATIFIED divergence exists.
- [x] Process-level containment tests prove no unexpected ticket, monitoring, or committed config mutation and no real `provider=codex` corpus record.
- [x] Existing replay and pilot suites remain green, with consent-gated skips still classified as authorization gates rather than successful live runtime evidence.

## Related Tickets
- TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC (parent)
- TCK-20260730-PROVIDER-HOOK-POLICY (must complete first)
- TCK-20260730-CLAUDE-EXECUTION-IDENTITY (must complete first)
- TCK-20260730-CODEX-POSTTOOL-ADAPTER (must complete first)
- TCK-20260721-CODEX-REPLAY-PARITY (DONE; limited replay predecessor)

## Related Docs
- docs/plans/archive/agent_infrastructure/current_codex_runtime_status_and_activation_plan.md
- agent-orchestration/workflows/implement-ticket.yaml
- agent-orchestration/intentional-divergences.md
- docs/ai/replay_fixture_spec.md

## Related Stored Artifacts
None yet.

## Related Code Areas
- agent-orchestration/workflows/implement-ticket.yaml
- tools/agent_replay_codex/
- tools/agent_codex_pilot_guardrails/
- tests/agent_replay_codex/
- tests/fixtures/agent_replay/
- .codex/config.toml

## Assumptions / Open Questions
- Investigate must select the smallest useful phase/tier slice and document every intentionally unsupported lifecycle feature.
- The adapter package name is provisional; it must remain clearly distinct from `tools/agent_replay_codex/` and `tools/agent_codex_pilot_guardrails/`.

## Implementation Notes
Implemented per `staging_artifacts/TCK-20260730-CODEX-RUNTIME-SHADOW/plan.md`'s 12 ordered steps,
all in the new package `tools/agent_codex_runtime_shadow/`:

1. `errors.py` — the 7 typed exceptions exactly as specified (`UnsupportedTierError`,
   `UnsupportedPhaseError`, `ContractVersionMismatchError`, `PhaseOrderViolationError`,
   `RequiredGateMissingError`, `RequiredArtifactMissingError`, `ShadowMismatchError`).
2. `matrix.py` — `SupportedMatrix`, `load_supported_matrix()` (reads `workflow_version` from the
   real `agent-orchestration/workflows/implement-ticket.yaml`, hardcodes
   `tier=standard`/`phases=[Scope,Investigate,Plan,Review]`), `validate_tier`,
   `validate_phase_names`, `validate_contract_version`.
3. `phase_order.py` — `validate_phase_order()`, in-order-prefix check.
4. `gate_validation.py` — `validate_required_gate()`, Review-only.
5. `required_artifacts.py` — `REQUIRED_ARTIFACTS_BY_PHASE`, `check_required_artifacts()`,
   generic and path-parameterized.
6. `shadow_runner.py` — `CodexShadowOutcome`, `derive_codex_shadow_outcome()`. Never imports
   subprocess/`agent_replay_codex`; operates purely on the already-loaded fixture.
7. `shadow_comparison.py` — `ShadowComparisonResult`, `compare_to_canonical()`,
   `run_shadow_comparison()`. Compares the 4 documented axes
   (`terminal_status`/`phase_order`/`gate_policy`/`artifact_requirements`), with
   `divergence_log.is_approved()` as the RATIFIED-divergence escape hatch, imported unmodified.
8. `__init__.py` — substantial disambiguating docstring naming both `agent_replay_codex` and
   `agent_codex_pilot_guardrails` explicitly.
9. `tests/agent_codex_runtime_shadow/test_no_subprocess.py` — AST scan: no `subprocess`
   import/calls, no `os.system`/`os.popen`, no dynamic load of `invoker`/`wrapper_script`, no
   `["codex", "exec", ...]` argv-shaped literal construction anywhere in the package. Also
   contains `test_package_docstring_is_non_empty_and_disambiguates_from_siblings` (Step 8's
   verify) and the exact `test_shadow_comparison_never_invokes_codex_exec` name from
   test_plan.md's AC #3 list.
10. `tests/agent_codex_runtime_shadow/test_containment.py` — full shadow-run containment tests
    against a synthetic git repo, importing `tools.agent_replay_codex.containment.{capture_snapshot,
    assert_no_diff}`, `provenance_check.assert_no_codex_provider_writes`, and
    `codex_config_guard.{assert_committed_config_hook_free,snapshot_config_bytes,
    assert_config_bytes_unchanged}` unmodified.
11. `tests/agent_codex_runtime_shadow/test_no_live_consent_dependency.py` — proves the whole suite
    runs unconditionally (no `skipif`/`skip` decorator or `os.environ.get`/`os.getenv` call
    referencing any consent marker anywhere in the package's tests; no `conftest.py`).
12. Full regression run (below) + scope-guard `git diff --stat` check — empty, confirming
    `tools/agent_replay/`, `tools/agent_replay_codex/`, `tools/agent_codex_pilot_guardrails/`,
    `tools/agent_codex_posttool_adapter/`, `agent-orchestration/workflows/implement-ticket.yaml`,
    and `.codex/config.toml` are all byte-identical/untouched.

Also added the additional unit tests test_plan.md's "New Tests Required" section calls for per
module: `tests/agent_codex_runtime_shadow/test_phase_tier_matrix.py`,
`test_phase_order_validation.py`, `test_gate_validation.py`,
`test_required_artifact_validation.py`, `test_shadow_comparison.py` — each with both the named
rejection-case test(s) and a positive/pass-case test.

**Deviations from plan.md (recorded in full in
`staging_artifacts/TCK-20260730-CODEX-RUNTIME-SHADOW/plan.md`'s new Deviations section):**
- Step 9's no-`codex exec` guard scans for actual invocation-shaped code (subprocess
  import/calls, `os.system`/`os.popen`, dynamic-load of `invoker`/`wrapper_script`, and the
  literal `["codex", "exec", ...]` argv-list construction) rather than banning any occurrence of
  the substring "codex exec"/"codex" in every string constant including docstrings — a blanket
  docstring ban would false-positive on this package's own `__init__.py`/`shadow_runner.py`
  docstrings (which must describe what they do NOT do) and contradicts
  `tools/agent_replay_codex/invoker.py`'s own docstring, which already uses the phrase "codex
  exec" in prose without issue.
- `shadow_comparison.py::run_shadow_comparison()` computes the Claude-side artifacts-verified
  root as `Path(fixture.source["stored_artifacts_dir"]).parent`, not
  `Path(fixture.source["stored_artifacts_dir"])` literally as plan.md's prose states — because
  the real fixture's `stored_artifacts_dir` field already ends in `<ticket_id>/`, and
  `required_artifacts.check_required_artifacts()` itself appends `ticket_id` when joining with
  the filename (per Step 5's own design); using the literal value would have double-joined
  `ticket_id` and looked in a nonexistent nested directory. Verified directly:
  `stored_artifacts/TCK-20260721-ORCHESTRATION-CONTRACT-ADR/investigation.md` exists on disk;
  `stored_artifacts/TCK-20260721-ORCHESTRATION-CONTRACT-ADR/TCK-20260721-ORCHESTRATION-CONTRACT-ADR/investigation.md`
  does not.
- A third pre-existing baseline test failure was found during Step 12's regression run, beyond
  the 2 plan.md already documents:
  `tests/agent_codex_pilot_guardrails/test_concurrent_claim.py::
  test_provider_field_coverage_against_real_corpus_is_currently_zero`. Root cause confirmed via
  direct read of `agent-monitoring/runs.jsonl:777`: the prerequisite ticket
  TCK-20260730-CLAUDE-EXECUTION-IDENTITY's own real `implement-ticket` workflow run (timestamped
  2026-07-31T07:50:11Z, i.e. landed before this ticket's Implement pass started) wrote the first
  real `provider="claude"` record into the corpus, which the test's hardcoded `== 0` assertion
  predates. This is unrelated to this ticket's own changes (confirmed: this ticket never writes
  to `agent-monitoring/*.jsonl`, verified by an md5sum before/after this ticket's own test suite
  run showing zero new lines) and out of this ticket's scope to fix (scope guard forbids touching
  `tools/agent_codex_pilot_guardrails/`). Not fixed as a drive-by, per the same discipline plan.md
  already applies to the 2 named `tests/agent_orchestration_claude_adapter/` failures.

**Verification performed (all confirmed directly, not assumed):**
- (a) `git diff --stat -- tools/agent_replay/ tools/agent_replay_codex/
  tools/agent_codex_pilot_guardrails/ tools/agent_codex_posttool_adapter/
  agent-orchestration/workflows/implement-ticket.yaml .codex/config.toml` → empty output.
- (b) `grep -rn "subprocess\|os\.system\|os\.popen" tools/agent_codex_runtime_shadow/` → only 2
  hits, both prose in docstrings ("never spawns a subprocess", "never invoking a real `codex
  exec` subprocess"), zero actual imports/calls; `grep -rn '"codex"' tools/agent_codex_runtime_shadow/`
  → zero hits (no CLI-invocation-shaped string literal anywhere).
- (c) `md5sum agent-monitoring/{runs,events,tools}.jsonl` before and after a full
  `pytest tests/agent_codex_runtime_shadow/ -q` run are identical — zero new lines written to the
  real monitoring corpus by this ticket's own test suite.

No parity ledger entry was added in this Implement pass — per plan.md's own Anti-Drift Notes,
"a new parity ledger entry for this ticket is a downstream Parity-phase concern, not part of this
Implement-phase plan," to be added following INFRA-306's pattern (P2, agent-orchestration/
developer-tooling `support_boundary` language) when that phase runs.

## Test Summary
New suite: `.venv/bin/python3 -m pytest tests/agent_codex_runtime_shadow/ -v` → **38 passed**.

Regression (unmodified dependencies):
- `tests/agent_replay/ tests/agent_replay_codex/ tests/agent_codex_pilot_guardrails/
  tests/agent_codex_posttool_adapter/` → **129 passed, 5 skipped (consent-gated, expected), 1
  failed** (pre-existing baseline drift, see Deviations above — unrelated to this ticket).
- `tests/agent_orchestration/ tests/agent_orchestration_claude_adapter/` → **90 passed, 2 failed**
  (the 2 pre-existing baseline failures plan.md/test_plan.md already document — hardcoded
  `implement-ticket.js` line numbers that drifted from unrelated tickets landing since).

No test in this ticket's own suite is skipped or gated on a live-consent environment variable
(`test_new_package_test_suite_never_requires_live_consent` proves this mechanically).

## Files Changed
New files only — no existing file modified:
- `tools/agent_codex_runtime_shadow/__init__.py`
- `tools/agent_codex_runtime_shadow/errors.py`
- `tools/agent_codex_runtime_shadow/matrix.py`
- `tools/agent_codex_runtime_shadow/phase_order.py`
- `tools/agent_codex_runtime_shadow/gate_validation.py`
- `tools/agent_codex_runtime_shadow/required_artifacts.py`
- `tools/agent_codex_runtime_shadow/shadow_runner.py`
- `tools/agent_codex_runtime_shadow/shadow_comparison.py`
- `tests/agent_codex_runtime_shadow/__init__.py`
- `tests/agent_codex_runtime_shadow/test_phase_tier_matrix.py`
- `tests/agent_codex_runtime_shadow/test_phase_order_validation.py`
- `tests/agent_codex_runtime_shadow/test_gate_validation.py`
- `tests/agent_codex_runtime_shadow/test_required_artifact_validation.py`
- `tests/agent_codex_runtime_shadow/test_shadow_comparison.py`
- `tests/agent_codex_runtime_shadow/test_no_subprocess.py`
- `tests/agent_codex_runtime_shadow/test_containment.py`
- `tests/agent_codex_runtime_shadow/test_no_live_consent_dependency.py`

## Completion Summary
Implemented the minimal Codex `implement-ticket` phase/tier runtime contract and its in-process
shadow-parity proof as a new, self-contained package (`tools/agent_codex_runtime_shadow/`),
entirely additive — zero existing file touched. The package hardcodes the one supported
tier/phase slice (`standard`; `Scope→Investigate→Plan→Review`) sourced from the real
`agent-orchestration/workflows/implement-ticket.yaml`'s `workflow_version`, deterministically
rejects everything else via 7 typed exceptions, derives an in-process "Codex shadow outcome" that
never spawns a subprocess or real `codex exec` call, and shadow-compares that outcome against
`tools/agent_replay`'s canonical fixture/runner output on the 4 documented divergence axes, with
a RATIFIED-divergence escape hatch reused unmodified from
`tools.agent_orchestration_claude_adapter.divergence_log`. All 5 acceptance criteria are covered
by tests (38 new tests, all passing); containment against the real repo (no ticket/monitoring
mutation, no `provider=codex` write, `.codex/config.toml` byte-identical) is proven both by
synthetic-repo integration tests and by direct before/after verification against the real
repository state. All 4 required scope-guard dependencies remain byte-identical
(`git diff --stat` empty); the only regressions are the 2 already-documented pre-existing
`tests/agent_orchestration_claude_adapter/` failures plus 1 newly-discovered pre-existing
`tests/agent_codex_pilot_guardrails/` failure, all confirmed unrelated to this ticket's own
changes.
