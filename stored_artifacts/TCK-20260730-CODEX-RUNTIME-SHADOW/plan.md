---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260730-CODEX-RUNTIME-SHADOW
artifact_type: plan
tags: [ai, workflows, testing, process-improvement]
---

# Implementation Plan — TCK-20260730-CODEX-RUNTIME-SHADOW

## Summary

Build a new package, `tools/agent_codex_runtime_shadow/`, that (1) reads the `standard`-tier,
`Scope→Investigate→Plan→Review` phase/tier support matrix directly from
`agent-orchestration/workflows/implement-ticket.yaml` and deterministically rejects anything
outside it (tier, phase name, `workflow_version`); (2) validates a ticket-shaped input — reusing
`tools.agent_replay.fixture_envelope.FixtureEnvelope` as that input's shape, not a new schema —
for phase order, a required Review-phase gate (`verdict`), and required per-phase artifacts on
disk; (3) derives an entirely in-process "Codex shadow outcome" from that input (never spawning
`codex exec`) and shadow-compares it against `tools.agent_replay.runner.replay_slice()`'s real
output — the canonical Claude-side ground truth — on the 4 axes
`agent-orchestration/intentional-divergences.md` already documents (`terminal_status`,
`phase_order`, `gate_policy`, `artifact_requirements`), raising on any unratified mismatch; and
(4) proves containment (no ticket/monitoring/config mutation, no `provider=codex` corpus write) by
reusing `tools/agent_replay_codex/{containment,provenance_check,codex_config_guard}.py` unmodified.
Every module is new; nothing in `tools/agent_replay/`, `tools/agent_replay_codex/`,
`tools/agent_codex_pilot_guardrails/`, or `agent-orchestration/workflows/implement-ticket.yaml`
is edited. The scratch artifact-location convention for tests of the new required-artifact checker
is `staging_artifacts/{ticket_id}/` (CLAUDE.md's live in-flight convention); the checker itself is
generic and path-parameterized, so the "matches canonical fixture" integration test points the
same function at the one real fixture's `source.stored_artifacts_dir` instead — no special-casing.

## Steps

### Step 1 — Typed exceptions
**Files:** `tools/agent_codex_runtime_shadow/errors.py` (new)
**Change:** One exception per rejection category, mirroring `tools/agent_replay_codex/errors.py`'s
one-file-for-the-package precedent (not per-module):
- `UnsupportedTierError` — tier is not `standard`.
- `UnsupportedPhaseError` — a phase name outside `{Scope, Investigate, Plan, Review}` is present.
- `ContractVersionMismatchError` — input's declared `workflow_version` != the real
  `implement-ticket.yaml`'s `workflow_version`.
- `PhaseOrderViolationError` — phases arrive out of the declared supported order.
- `RequiredGateMissingError` — Review phase entry has no `output.verdict`.
- `RequiredArtifactMissingError` — a required artifact file is absent for a completed phase.
- `ShadowMismatchError` — shadow comparison found an axis mismatch with no covering RATIFIED
  divergence. Carries the mismatched axis name(s) so callers/tests can assert on them.
**Do NOT touch:** `tools/agent_replay_codex/errors.py` (read-only precedent, not shared/imported —
each package owns its own exception hierarchy per that file's own stated rationale).
**Verify:** No standalone test file for this step; exercised indirectly by every later step's
tests (each rejection test asserts one of these types is raised).

### Step 2 — Phase/tier support matrix
**Files:** `tools/agent_codex_runtime_shadow/matrix.py` (new)
**Change:**
- `SupportedMatrix` frozen dataclass: `tier: str`, `phases: list[str]`, `workflow_version: int`.
- `load_supported_matrix(workflow_yaml_path: Path = <repo>/agent-orchestration/workflows/implement-ticket.yaml) -> SupportedMatrix` —
  parses the YAML with `yaml.safe_load`, and derives the supported slice as the hardcoded
  constants `_SUPPORTED_TIER = "standard"` and `_SUPPORTED_PHASES = ["Scope", "Investigate",
  "Plan", "Review"]` (per investigation.md's Resolved Open Question 1 — this ticket does not
  attempt to auto-derive "the smallest useful slice" from the YAML's `tiers`/`condition` fields;
  it hardcodes the ticket's own explicit decision and only reads `workflow_version` from the file
  for the contract-version check). Raise `ContractVersionMismatchError` at load time if the parsed
  file's `workflow_version` is missing or not an `int`.
- `validate_tier(tier: str, matrix: SupportedMatrix) -> None` — raises `UnsupportedTierError` if
  `tier != matrix.tier`.
- `validate_phase_names(phase_names: list[str], matrix: SupportedMatrix) -> None` — raises
  `UnsupportedPhaseError` naming the first offending phase if any name in `phase_names` is not in
  `matrix.phases`. Whole-input rejection, not partial: called before any phase-by-phase processing
  proceeds.
- `validate_contract_version(declared_version: int, matrix: SupportedMatrix) -> None` — raises
  `ContractVersionMismatchError` if `declared_version != matrix.workflow_version`.
**Do NOT touch:** `agent-orchestration/workflows/implement-ticket.yaml` itself — read-only.
**Verify:** `tests/agent_codex_runtime_shadow/test_phase_tier_matrix.py` —
`test_phase_tier_matrix_reads_real_implement_ticket_yaml`, `test_rejects_hotfix_tier`,
`test_rejects_unsupported_phase[Implement]` / `[Architecture-Verify]` / `[Test]` / `[Parity]` /
`[Security-Review]` / `[Verify]` / `[Finalize]`, `test_accepts_the_one_supported_slice`,
`test_contract_version_mismatch_rejected`.

### Step 3 — Phase order validation
**Files:** `tools/agent_codex_runtime_shadow/phase_order.py` (new)
**Change:** `validate_phase_order(phase_names: list[str], matrix: SupportedMatrix) -> None` —
raises `PhaseOrderViolationError` if `phase_names` is not exactly a prefix, in order, of
`matrix.phases` (e.g. `[Scope, Plan, Investigate]` or `[Investigate, Scope]` both reject; `[Scope,
Investigate]` — a valid partial-but-in-order prefix — passes). No reordering, no best-effort
partial validation — matches the anti-drift hazard against silent partial validation.
**Do NOT touch:** `matrix.py`'s own validators (this is a separate, sequencing-only concern from
matrix membership, imported alongside it, not merged into it).
**Verify:** `tests/agent_codex_runtime_shadow/test_phase_order_validation.py` —
`test_phase_order_violation_detected`.

### Step 4 — Required gate validation
**Files:** `tools/agent_codex_runtime_shadow/gate_validation.py` (new)
**Change:** `validate_required_gate(phase_entry: PhaseEntry) -> None` (takes one
`tools.agent_replay.fixture_envelope.PhaseEntry`) — if `phase_entry.phase == "Review"` and
`phase_entry.output.get("verdict")` is falsy/missing, raise `RequiredGateMissingError`. No-op for
every other phase (only Review carries a required-gate concept in this ticket's supported slice —
matches `tools.agent_replay.runner.replay_slice()`'s own Review-only gate branch).
**Do NOT touch:** `tools/agent_replay/runner.py`'s own Review-verdict branch — this is a
standalone pre-check, not a call into or modification of `replay_slice()`.
**Verify:** `tests/agent_codex_runtime_shadow/test_gate_validation.py` —
`test_required_gate_missing_detected`.

### Step 5 — Required artifact validation
**Files:** `tools/agent_codex_runtime_shadow/required_artifacts.py` (new)
**Change:**
- `REQUIRED_ARTIFACTS_BY_PHASE: dict[str, list[str]]` constant = `{"Investigate":
  ["investigation.md", "test_plan.md"], "Plan": ["plan.md"]}` (Scope and Review have no required
  artifact in this ticket's slice — matches test_plan.md's parametrization, which only covers
  `Investigate`/`Plan`).
- `check_required_artifacts(phase: str, ticket_id: str, artifacts_dir: Path) -> list[str]` —
  generic and path-parameterized (mirrors `containment.py`'s `repo_root`-parameterization
  precedent): looks up `REQUIRED_ARTIFACTS_BY_PHASE.get(phase, [])`, and for each required
  filename checks `(artifacts_dir / ticket_id / filename).exists()` (if `phase` has no entry,
  returns `[]` — no-op). Raises `RequiredArtifactMissingError` naming the first missing filename
  if any is absent. On success, returns the list of filenames found present, in
  `REQUIRED_ARTIFACTS_BY_PHASE[phase]` order — this return value is what Step 6/7 use as the
  "artifacts satisfied" record on both sides of the shadow comparison (filenames only, never
  absolute paths, so the Claude side under `stored_artifacts/{ticket_id}/` and the Codex-shadow
  side under `staging_artifacts/{ticket_id}/` remain directly comparable).
- Does not hardcode which root (`staging_artifacts/` vs. `stored_artifacts/`) — callers pass
  `artifacts_dir` explicitly. Document in the module docstring that the scratch/shadow convention
  callers should default to is `<repo_root>/staging_artifacts/` (per CLAUDE.md's live in-flight
  artifact convention), while shadow-comparison-against-a-DONE-ticket's-fixture callers pass that
  fixture's own `source["stored_artifacts_dir"]` instead — both are legitimate uses of the same
  function, not a special case.
**Do NOT touch:** `tools/agent_replay/fixture_envelope.py` — do not add an artifact-path field to
`FixtureEnvelope`/`PhaseEntry`; this check is additive and external to that schema, per the
anti-drift hazard against extending the fixture envelope format.
**Verify:** `tests/agent_codex_runtime_shadow/test_required_artifact_validation.py` —
`test_required_artifact_missing_detected[Investigate]`, `[Plan]`,
`test_required_artifact_present_passes`.

### Step 6 — In-process Codex shadow outcome derivation
**Files:** `tools/agent_codex_runtime_shadow/shadow_runner.py` (new)
**Change:**
- `CodexShadowOutcome` frozen dataclass: `final_status: str`, `phases_completed: list[str]`,
  `gate_result: str`, `artifacts_verified: dict[str, list[str]]` (phase name → filenames Step 5
  confirmed present for that phase; empty list for phases with no required artifact).
- `derive_codex_shadow_outcome(fixture: FixtureEnvelope, artifacts_dir: Path) -> CodexShadowOutcome` —
  the in-process functional replacement for `agent_replay_codex.invoker.run_codex_replay()`,
  operating entirely on the already-loaded `fixture` and never spawning a subprocess:
  1. Build `phase_names = [p.phase for p in fixture.phases]`; call
     `matrix.validate_phase_names(phase_names, matrix)`,
     `matrix.validate_contract_version(fixture.version, matrix)`,
     `matrix.validate_tier(fixture.source.get("tier"), matrix)`, and
     `phase_order.validate_phase_order(phase_names, matrix)` up front — whole-input rejection
     before any phase-by-phase work, matching Step 2/3's fail-closed design.
  2. Walk `fixture.phases` in order (same iteration shape as `replay_slice()`, but never importing
     or calling it — this must stay a structurally independent, non-Claude-side derivation so the
     comparison in Step 7 is meaningful): for each phase, call `gate_validation.
     validate_required_gate(entry)`, then `required_artifacts.check_required_artifacts(entry.phase,
     fixture.source["ticket_id"], artifacts_dir)`, accumulating into `artifacts_verified`.
  3. `final_status`/`gate_result` vocabulary: normalize the Review phase's `output["verdict"]` the
     same way `tools.agent_replay.runner.replay_slice()` does — `"ok"` when `verdict == "APPROVED"`,
     else the raw verdict string — reusing that exact normalization rule (re-implemented here, not
     imported, since `replay_slice()` has no standalone normalization function to import) to avoid
     reintroducing the vocabulary bug `tickets/done/TCK-20260721-CODEX-REPLAY-PARITY.md`'s
     Implementation Notes Step 11 already found and fixed once in `shadow_mode.py`. `gate_result`
     is this same normalized value; `final_status` equals `gate_result` for this ticket's slice
     (no separate terminal-status source exists once Review is the last supported phase).
**Do NOT touch:** `tools/agent_replay_codex/invoker.py`, `tools/agent_replay_codex/shadow_mode.py`
— read for the vocabulary-bug precedent only, never imported or modified. This function must never
import `subprocess`, `os.system`, or any `agent_replay_codex` module that itself shells out.
**Verify:** Exercised by Step 7's `test_shadow_comparison_matches_canonical_fixture` (no
standalone test file of its own — `shadow_runner.py`'s only consumer is `shadow_comparison.py`).

### Step 7 — Shadow comparison against the canonical runner, with divergence escape hatch
**Files:** `tools/agent_codex_runtime_shadow/shadow_comparison.py` (new)
**Change:**
- `_SUPPORTED_AXES = {"terminal_status", "phase_order", "gate_policy", "artifact_requirements"}` —
  the 4 axes `agent-orchestration/intentional-divergences.md`'s own `## Entry Format` section
  documents (per investigation.md's divergence-axis recommendation; this ticket does not use the
  predecessor's undocumented `"codex_parity"` axis).
- `ShadowComparisonResult` frozen dataclass: `ticket_id: str`, `phase_order_match: bool`,
  `terminal_status_match: bool`, `gate_policy_match: bool`, `artifact_requirements_match: bool`,
  `suppressed_axes: list[str]` (axes that mismatched but were suppressed by a RATIFIED
  divergence).
- `compare_to_canonical(fixture: FixtureEnvelope, claude_outcome: ReplayOutcome, codex_outcome:
  CodexShadowOutcome, claude_artifacts_verified: dict[str, list[str]], divergences_path: Path) ->
  ShadowComparisonResult` —
  1. Compute raw per-axis booleans: `phase_order_match = claude_outcome.phases_completed ==
     codex_outcome.phases_completed`; `terminal_status_match = claude_outcome.final_status ==
     codex_outcome.final_status`; `gate_policy_match` — normalize `claude_outcome.final_status` the
     same way Step 6 does (already "ok"/raw-verdict vocabulary, so this is a direct
     `claude_outcome.final_status == codex_outcome.gate_result` comparison, not a second
     re-derivation from `fixture.output.verdict` — this is the fix for the vocabulary-bug class,
     and also the fix for `agent_replay_codex.shadow_mode.ShadowModeComparison.match`'s known gap
     of excluding artifacts); `artifact_requirements_match = claude_artifacts_verified ==
     codex_outcome.artifacts_verified`.
  2. For each axis whose raw boolean is `False`: call
     `tools.agent_orchestration_claude_adapter.divergence_log.load_divergences(divergences_path)`
     and `is_approved(divergences, axis, fixture.source["ticket_id"])`. If approved, record the
     axis in `suppressed_axes` and treat that axis as passing for the purposes of raising; if not
     approved, collect it as a hard failure.
  3. If any axis both mismatched and was not suppressed, raise `ShadowMismatchError` naming every
     such axis. Otherwise return the `ShadowComparisonResult` (with `suppressed_axes` populated for
     any axis that mismatched-but-was-ratified).
  4. Reject (raise `ValueError`, a plain programmer-error signal, not a domain `errors.py` type) if
     called with any axis name outside `_SUPPORTED_AXES` anywhere internally — defends against a
     future edit silently reintroducing an undocumented axis string like `"codex_parity"`.
- `run_shadow_comparison(fixture_path: Path, artifacts_dir: Path, divergences_path: Path) ->
  ShadowComparisonResult` — the single public top-level entry point tying Steps 2-7 together:
  loads the fixture via `tools.agent_replay.fixture_envelope.load_fixture`, computes
  `claude_outcome = tools.agent_replay.runner.replay_slice(fixture)` (the one and only import of
  the canonical runner in this whole package — read-only call, no modification), computes
  `claude_artifacts_verified` by calling `required_artifacts.check_required_artifacts()` per
  completed phase against `Path(fixture.source["stored_artifacts_dir"])`, computes `codex_outcome
  = shadow_runner.derive_codex_shadow_outcome(fixture, artifacts_dir)`, and calls
  `compare_to_canonical(...)`. This is the function Step 10's containment tests wrap with a
  before/after snapshot.
**Do NOT touch:** `tools/agent_replay/runner.py::ReplayOutcome` — do not add a `gate_result` or
`artifacts` field to it; this step's `ShadowComparisonResult` is the new, separate comparison type
the investigation already decided on (wrap, don't extend — `ReplayOutcome` is a shared type other
consumers depend on and stays a 2-field dataclass). `tools/agent_orchestration_claude_adapter/
divergence_log.py` — imported read-only, never modified; never confuse
`agent-orchestration/intentional-divergences.md` (this package's divergence log) with
`docs/guidelines/intentional_divergences.md` (the unrelated Mechanics Bible divergence log — do
not read from or write to that file anywhere in this package).
**Verify:** `tests/agent_codex_runtime_shadow/test_shadow_comparison.py` —
`test_shadow_comparison_matches_canonical_fixture` (also asserts `match is False` when artifacts
are made to differ but phases/gate/status agree — the artifacts-included-in-match anti-drift
guard), `test_shadow_comparison_mismatch_without_ratified_divergence_fails`,
`test_shadow_comparison_mismatch_with_ratified_divergence_passes` (using axis `phase_order` or
`artifact_requirements`, not `codex_parity`).

### Step 8 — Package docstring
**Files:** `tools/agent_codex_runtime_shadow/__init__.py` (new)
**Change:** Non-empty module docstring using the exact responsibility statement investigation.md's
Resolved Open Question 2 already drafted (minimal Codex `implement-ticket` phase/tier support
matrix, in-process ticket-shaped-input validation with typed rejection, shadow-comparison against
`tools/agent_replay`'s canonical fixture/runner, RATIFIED-divergence escape hatch; explicitly
distinguishing this package from `tools/agent_replay_codex/`'s real-`codex exec` integration proof
and `tools/agent_codex_pilot_guardrails/`'s pilot sign-off/rollback governance) — mirrors
`agent_codex_pilot_guardrails/__init__.py` and `agent_codex_posttool_adapter/__init__.py`'s
substantial-docstring precedent, not `agent_replay_codex/__init__.py`'s empty one.
**Do NOT touch:** The two sibling `__init__.py` files themselves — read as precedent, not edited.
**Verify:** A new small test in `tests/agent_codex_runtime_shadow/test_no_subprocess.py` (see Step
9) or its own trivial assertion — `tools.agent_codex_runtime_shadow.__doc__` is non-empty and
mentions both `agent_replay_codex` and `agent_codex_pilot_guardrails` by name (the
empty-`__init__.py`-regression guard from test_plan.md's Anti-Drift Test Guards).

### Step 9 — No-`codex exec` architecture guard
**Files:** `tests/agent_codex_runtime_shadow/test_no_subprocess.py` (new; no source changes)
**Change:** AST scan over every `.py` file in `tools/agent_codex_runtime_shadow/`, directly
mirroring `tests/agent_replay/test_runner_no_forbidden_calls.py` and
`tests/agent_codex_posttool_adapter/test_no_subprocess_and_no_live_wiring.py`'s existing
technique (reuse the technique, not the code — a fresh, package-scoped copy): no `import
subprocess`, no `subprocess.run/Popen/call/check_call/check_output`, no `os.system`/`os.popen`,
and no string constant anywhere in the package containing `"codex exec"` or the bare literal
`"codex"` as a CLI-invocation-shaped substring (widen to whole-file string-constant scan per the
`tests/agent_replay/` precedent's own advisory, not just call-argument-scoped nodes).
**Do NOT touch:** Any file outside `tools/agent_codex_runtime_shadow/` — this scan must not touch
`.claude/workflows/implement-ticket.js` or `tools/agent_replay_codex/`, which legitimately
reference Codex-CLI strings in their own unrelated, already-covered code paths.
**Verify:** `test_shadow_comparison_never_invokes_codex_exec` (per test_plan.md's AC #3 test list;
this is the file it lives in per test_plan.md's own stated location).

### Step 10 — Containment integration tests
**Files:** `tests/agent_codex_runtime_shadow/test_containment.py` (new; no source changes)
**Change:** Reusing `tools.agent_replay_codex.containment.{capture_snapshot,assert_no_diff}`,
`tools.agent_replay_codex.provenance_check.assert_no_codex_provider_writes`, and
`tools.agent_replay_codex.codex_config_guard.{assert_committed_config_hook_free,
snapshot_config_bytes,assert_config_bytes_unchanged}` unmodified (imported, not reimplemented):
1. A local `_init_synthetic_repo(tmp_path)` helper mirroring
   `tests/agent_replay_codex/test_containment.py`'s own helper (fresh copy in this file, not a
   shared import — matches that file's own precedent of defining it locally rather than in a
   `conftest.py`): creates `tickets/`, `agent-monitoring/*.jsonl`, `staging_artifacts/{ticket_id}/`
   with the required artifact files, and a `.codex/config.toml` (hook-free), then `git init`+commit.
2. `test_shadow_run_produces_zero_diff_in_tickets_and_monitoring` — snapshot before/after a full
   `run_shadow_comparison(...)` call against the synthetic repo's fixture + `staging_artifacts/`
   dir; `assert_no_diff` must not raise.
3. `test_shadow_run_writes_no_codex_provider_record` — calls
   `assert_no_codex_provider_writes(agent_monitoring_dir)` against the real repo's
   `agent-monitoring/` dir after running the new package's own test suite, plus a negative-control
   test with a synthetic `provider="codex"` line in a `tmp_path` monitoring dir (mirrors
   `tests/agent_replay_codex/test_monitoring_provenance.py`'s existing pattern).
4. `test_committed_codex_config_remains_hook_free_and_byte_identical` — snapshot
   `.codex/config.toml` bytes before/after a `run_shadow_comparison(...)` call;
   `assert_config_bytes_unchanged` must not raise, and `assert_committed_config_hook_free` must
   pass on the real repo's committed file.
**Do NOT touch:** `tools/agent_replay_codex/{containment,provenance_check,codex_config_guard}.py`
— import only.
**Verify:** The 3 tests named above, per test_plan.md AC #4.

### Step 11 — No-live-consent-dependency architecture guard
**Files:** `tests/agent_codex_runtime_shadow/test_no_live_consent_dependency.py` (new; no source
changes)
**Change:** `test_new_package_test_suite_never_requires_live_consent` — programmatically collects
`tests/agent_codex_runtime_shadow/` (e.g. via `pytest.main(["--collect-only", "-q", ...])` in a
subprocess-free in-process collection, or by scanning source for `pytest.mark.skipif`/`pytest.skip`
decorators referencing `CODEX_REPLAY_PARITY_LIVE_CONSENT` or any new consent env var) and asserts
zero matches — this package's entire suite must run unconditionally, unlike
`tests/agent_replay_codex/`'s ~5-6 consent-gated tests.
**Do NOT touch:** `tests/agent_replay_codex/conftest.py`'s `real_codex_replay` fixture — read as
the anti-pattern to avoid copying, never imported into this package's tests.
**Verify:** `test_new_package_test_suite_never_requires_live_consent`.

### Step 12 — Full regression run and scope-guard diff check
**Files:** None (verification only, no new files).
**Change:** Run the three scoped pytest commands from test_plan.md's "Scoped Pytest Commands"
section in order:
1. `.venv/bin/python3 -m pytest tests/agent_codex_runtime_shadow/ -v`
2. `.venv/bin/python3 -m pytest tests/agent_replay/ tests/agent_replay_codex/
   tests/agent_codex_pilot_guardrails/ tests/agent_codex_posttool_adapter/ -v`
3. `.venv/bin/python3 -m pytest tests/agent_orchestration/ tests/agent_orchestration_claude_adapter/ -v`
Then run `git diff --stat -- tools/agent_replay/ tools/agent_replay_codex/
tools/agent_codex_pilot_guardrails/ tools/agent_codex_posttool_adapter/
agent-orchestration/workflows/implement-ticket.yaml .codex/config.toml` and confirm it is empty
(mirrors `tickets/done/TCK-20260721-CODEX-REPLAY-PARITY.md`'s own Step 12 precedent).
**Do NOT touch:** Nothing to change here — this step only runs commands and reads their output.
The two pre-existing `tests/agent_orchestration_claude_adapter/` failures
(`test_terminal_status_conformance_finalize_incomplete_appears_once_on_both_sides`,
`test_extract_all_terminal_statuses_dedupes_by_value_not_call_site_count`) are expected and must
not be "fixed" as a drive-by.
**Verify:** All listed commands pass except the 2 named pre-existing baseline failures; the
`git diff --stat` scope-guard command outputs nothing.

## Scope Guards

- Do not modify `tools/agent_replay/runner.py` or `tools/agent_replay/fixture_envelope.py` —
  read-only canonical dependencies. In particular, do not add `gate_result` or `artifacts` fields
  to `ReplayOutcome`, and do not add an artifact-path field to `FixtureEnvelope`/`PhaseEntry`.
- Do not modify any file under `tools/agent_replay_codex/` (including `shadow_mode.py`,
  `invoker.py`, `containment.py`, `provenance_check.py`, `codex_config_guard.py`, `errors.py`) —
  import only.
- Do not modify any file under `tools/agent_codex_pilot_guardrails/` — no overlap in
  responsibility, read-only precedent for the `__init__.py` docstring style only.
- Do not modify `tools/agent_codex_posttool_adapter/` — unrelated monitoring-adapter, precedent
  reference only.
- Do not modify `agent-orchestration/workflows/implement-ticket.yaml` — read-only source of the
  phase/tier matrix and `workflow_version`.
- Do not modify `.codex/config.toml` — must remain hook-free and byte-identical; Step 10 proves
  this mechanically.
- Never invoke `codex exec`, `subprocess`, or `os.system` anywhere in
  `tools/agent_codex_runtime_shadow/` or its tests — Step 9 is the mechanical proof.
- Never write a `provider="codex"` record to the real `agent-monitoring/*.jsonl` files, including
  accidentally via a test that doesn't point at `tmp_path`.
- Do not add support for `hotfix` tier or any phase beyond `{Scope, Investigate, Plan, Review}` —
  every such input must be a deterministic, typed rejection, never a soft warning or partial pass.
- Do not attempt to fix the 2 pre-existing `tests/agent_orchestration_claude_adapter/` baseline
  failures (hardcoded line-number drift, unrelated to this ticket).
- Do not backfill a parity ledger entry for `TCK-20260721-CODEX-REPLAY-PARITY` — that is a
  pre-existing gap this ticket did not create and is not responsible for closing.
- Do not conflate `agent-orchestration/intentional-divergences.md` (this package's divergence log)
  with `docs/guidelines/intentional_divergences.md` (the Mechanics Bible's) — only the former is
  ever read by `shadow_comparison.py`.

## Dependency Map

- Step 1 (errors.py) has no dependencies; every other step depends on it.
- Steps 2, 3, 4, 5 (matrix, phase_order, gate_validation, required_artifacts) each depend only on
  Step 1; they are otherwise mutually independent and can be implemented/verified in any order
  relative to each other.
- Step 6 (shadow_runner.py) depends on Steps 2, 3, 4, 5.
- Step 7 (shadow_comparison.py) depends on Step 6, and externally on the unmodified
  `tools.agent_replay.{fixture_envelope,runner}` and
  `tools.agent_orchestration_claude_adapter.divergence_log` modules.
- Step 8 (`__init__.py`) depends on Steps 1-7 existing (so the docstring accurately describes the
  finished package) but has no code dependency.
- Step 9 (no-subprocess guard) depends on Steps 1-8 all existing (it scans the whole package dir).
- Step 10 (containment tests) depends on Step 7's `run_shadow_comparison()` entry point.
- Step 11 (no-live-consent guard) depends on Steps 9-10's test files existing (it scans the whole
  `tests/agent_codex_runtime_shadow/` directory).
- Step 12 (regression run) depends on all prior steps.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC #1 — explicit phase/tier matrix, deterministic rejection | Step 2 | `test_phase_tier_matrix_reads_real_implement_ticket_yaml`, `test_rejects_hotfix_tier`, `test_rejects_unsupported_phase[*]` (7 params), `test_accepts_the_one_supported_slice`, `test_contract_version_mismatch_rejected` |
| AC #2 — contract-version, phase-order, required-gate, required-artifact validation, machine-checkable and tested | Steps 2, 3, 4, 5 | `test_contract_version_mismatch_rejected`, `test_phase_order_violation_detected`, `test_required_gate_missing_detected`, `test_required_artifact_missing_detected[Investigate]`/`[Plan]`, `test_required_artifact_present_passes` |
| AC #3 — scratch/shadow comparison (phase order, final status, gate result, artifacts) vs. canonical fixture/runner; RATIFIED-divergence escape hatch | Steps 6, 7, 9 | `test_shadow_comparison_matches_canonical_fixture`, `test_shadow_comparison_mismatch_without_ratified_divergence_fails`, `test_shadow_comparison_mismatch_with_ratified_divergence_passes`, `test_shadow_comparison_never_invokes_codex_exec` |
| AC #4 — containment: no ticket/monitoring/config mutation, no `provider=codex` corpus record | Step 10 | `test_shadow_run_produces_zero_diff_in_tickets_and_monitoring`, `test_shadow_run_writes_no_codex_provider_record`, `test_committed_codex_config_remains_hook_free_and_byte_identical` |
| AC #5 — existing replay/pilot suites stay green; consent-gated skips classified as authorization gates, not live-runtime evidence | Step 11, Step 12 | `test_new_package_test_suite_never_requires_live_consent`; full regression run of `tests/agent_replay/`, `tests/agent_replay_codex/`, `tests/agent_codex_pilot_guardrails/`, `tests/agent_codex_posttool_adapter/`, `tests/agent_orchestration/`, `tests/agent_orchestration_claude_adapter/` |

## Anti-Drift Notes

- **The single highest-value test in this ticket is Step 9's no-`codex exec` guard.** Its failure
  is the earliest, cheapest signal that this package has regressed into a second copy of
  `tools/agent_replay_codex/`'s real-CLI responsibility — the exact collapse the ticket's Out of
  Scope forbids.
- **`ReplayOutcome` stays a 2-field dataclass.** The temptation to add `gate_result`/`artifacts`
  fields to it directly (since that would make Step 7's comparison code shorter) must be resisted
  — it is a shared canonical type; `ShadowComparisonResult` is the correct new, additive type.
- **Reuse `required_artifacts.check_required_artifacts()` for both sides of the comparison**
  (Claude side pointed at `stored_artifacts_dir`, Codex-shadow side pointed at
  `staging_artifacts/{ticket_id}/`) rather than writing two separate artifact-checking code paths
  — this is what makes the artifact comparison in Step 7 meaningful instead of comparing two
  independently-invented shapes.
- **Normalize `final_status`/`gate_result` vocabulary exactly once, the same way on both sides**
  (`"ok"` when Review verdict is `APPROVED`, else the raw verdict string) — this is the specific
  bug class `tickets/done/TCK-20260721-CODEX-REPLAY-PARITY.md` Step 11 already hit once in
  `shadow_mode.py`; Step 6/7 must not reintroduce it by deriving the two sides' vocabulary
  differently.
- **Divergence axis vocabulary is closed to the 4 documented values** (`terminal_status |
  phase_order | gate_policy | artifact_requirements`). Do not reintroduce the predecessor's
  undocumented `"codex_parity"` catch-all axis anywhere in this package's new code or tests.
- **A new parity ledger entry for this ticket is a downstream Parity-phase concern, not part of
  this Implement-phase plan.** It should follow INFRA-306's pattern (P2,
  agent-orchestration/developer-tooling `support_boundary` language) when that phase runs — this
  plan does not itself create the entry.
- **`tests/agent_codex_runtime_shadow/` must have zero tests skipped or gated on any live-consent
  env var.** Every test in this package's own suite runs unconditionally on every machine, with or
  without a `codex` CLI on `PATH` — a structural difference from `tests/agent_replay_codex/`'s
  ~5-6 consent-gated tests that Step 11 exists specifically to prove.

## Deviations

Recorded during Implement (2026-07-31). None change scope or architecture; all are either a
tightened interpretation of ambiguous plan prose or a bugfix in the plan's own literal wording.

1. **Step 9's no-`codex exec` guard, scope of the string-constant scan.** Plan text said "no
   string constant anywhere in the package containing 'codex exec' or the bare literal 'codex' as
   a CLI-invocation-shaped substring." Implemented as an AST scan for actual invocation-shaped
   code — `subprocess` import/calls, `os.system`/`os.popen`, dynamic-load of
   `invoker`/`wrapper_script`, and the literal `["codex", "exec", ...]` argv-list construction —
   rather than a blanket ban on the substring "codex exec"/"codex" in every string constant
   including docstrings. A blanket docstring ban is unworkable: this package's own
   `__init__.py`/`shadow_runner.py` docstrings must describe what they do NOT do (mirroring
   `tools/agent_replay_codex/invoker.py`'s own docstring, which already contains the phrase
   "codex exec" in prose without issue). The qualifier "CLI-invocation-shaped" in the plan's own
   wording is read as supporting this narrower, more precise interpretation over a literal
   whole-file substring ban.
2. **`shadow_comparison.py::run_shadow_comparison()`'s Claude-side artifacts root.** Plan Step 7
   said this computes `claude_artifacts_verified` "against `Path(fixture.source
   ["stored_artifacts_dir"])`" directly. Implemented as
   `Path(fixture.source["stored_artifacts_dir"]).parent` instead — the real fixture's
   `stored_artifacts_dir` field already ends in `<ticket_id>/`
   (`stored_artifacts/TCK-20260721-ORCHESTRATION-CONTRACT-ADR/`), and
   `required_artifacts.check_required_artifacts()` (Step 5) itself appends `ticket_id` when
   joining with the required filename. Using the literal value as written would have double-
   joined `ticket_id` and looked for
   `stored_artifacts/TCK-.../TCK-.../investigation.md`, which does not exist — confirmed by direct
   listing of `stored_artifacts/TCK-20260721-ORCHESTRATION-CONTRACT-ADR/`, which contains
   `investigation.md` directly, not a nested `TCK-.../` subdirectory. This is a bugfix in the
   plan's literal wording, not a scope or design change — the intent (compare against the real
   fixture's real stored-artifacts location) is unchanged.
3. **A third pre-existing baseline failure was found during Step 12,** beyond the 2 plan.md
   already names:
   `tests/agent_codex_pilot_guardrails/test_concurrent_claim.py::
   test_provider_field_coverage_against_real_corpus_is_currently_zero`. Root cause: the
   prerequisite ticket TCK-20260730-CLAUDE-EXECUTION-IDENTITY's own real `implement-ticket`
   workflow run (timestamped 2026-07-31T07:50:11Z in `agent-monitoring/runs.jsonl:777`, before
   this ticket's Implement pass started) wrote the first real `provider="claude"` record into the
   corpus, which this test's hardcoded `== 0` assertion predates. Confirmed unrelated to this
   ticket's own work (md5sum of `agent-monitoring/*.jsonl` before/after this ticket's own test
   suite run is identical) and left unfixed per the same discipline already applied to the 2
   named `tests/agent_orchestration_claude_adapter/` failures — out of this ticket's scope
   (touching `tools/agent_codex_pilot_guardrails/` is forbidden by the Scope Guards above).
