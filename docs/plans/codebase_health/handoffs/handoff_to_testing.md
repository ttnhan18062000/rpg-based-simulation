---
status: active
layer: testing
authority: P2
audience: agent
tags: [planning, testing]
---

# Handoff — Codebase domain to the test-architecture sessions

**From:** `codebase-planner`, 2026-10-04, at `origin/main` `c049b9d65`.
**To:** `testing-planner` (`test-architecture-reviewer`).
**Reply:** comment on the PR that adds this file, or commit an answer under "Responses" at the bottom. The codebase
sessions run on a different machine and do not see your handover notes.

Section 3 is the only item that blocks codebase work. The rest is notice and findings for you to decide on. The
codebase domain edits no test in your domain except tests that pin CI and the Makefile (owner decision 8.11, which
also says you are told before such an edit lands; no testing session was reachable, so sections 1 and 4 arrive late).

## 1. Edits already merged to tests that pin CI and the Makefile (decision 8.11)

Install, cache and job-list lines only. The reasons are in each ticket's Files Changed.
- **#288:** `tests/static/test_ci_narrow_path_filtered_jobs.py`, `tests/static/test_ci_step_summary_reporting.py`,
  `tests/tools/test_ci_workflow_test_coverage.py`; new `tests/tools/test_ci_split_tools_jobs.py`.
- **#297:** `test_ci_step_summary_reporting.py` (setup-uv + `uv sync` lines), `test_ci_split_tools_jobs.py` (pip pin →
  uv pin), `tests/tools/test_dashboard_makefile_targets.py` (`install-py` is `uv sync`). Additive: new
  `tests/static/test_ci_uv_install.py`, plus one test each in `test_ci_narrow_path_filtered_jobs.py` and
  `test_typecheck_gate_configured.py`.
- **#305 (M4):** `test_ci_step_summary_reporting.py` (job set gains `code-health`), `test_ci_uv_install.py`
  (`_LINT_JOBS` gains `code-health`), `test_typecheck_gate_configured.py` (mypy-baseline filter); new
  `tests/static/test_ci_code_health_sarif.py`. (The `tests/tools/test_code_health_*` and `test_mypy_gate.py` files it
  added are codebase-domain tests, since moved to `tests/codebase/`.)
- **#315:** `test_ci_uv_install.py::test_lint_group_holds_the_code_health_tools_and_is_a_default_group` now expects
  `{ruff, complexipy, ast-grep-cli}`. New, not an edit: `tests/codebase/test_package_registry.py`.

**Coming (gates flip, merge on or after 2026-10-18):** the tests that pin advisory status (check names
`Code health (advisory)` and `Type check (informational)`, `continue-on-error`), listed in
`docs/plans/codebase_health/python_code_craft_gates_flip_ticket_brief.md`. **Asked:** object on that PR if any edit
conflicts with a testing-domain rule.

## 2. Flaky tests/api tests: fixed 3 s server wait (unticketed)

`tests/api/test_live_entity_inspection.py:23`, `test_live_observability_status.py:23` and `test_rest_parity.py:22,87`
start the API server and `time.sleep(3)` before the first request (re-verified on `c049b9d65`). PR #288's CI saw
`test_live_entity_inspection` and `test_rest_parity::test_api_compression` fail intermittently on a loaded runner.
Likely fix: poll a readiness endpoint with a timeout. **Asked:** decide whether to ticket it.

## 3. Import-linter adoption needs your agreement (blocks `TCK-20261004-IMPORT-LINTER-ADOPTION`)

`docs/plans/codebase_health/import_linter_evaluation.md` (M5) recommends adding import-linter: a `layers` contract
generated from the package registry, advisory first, plus contracts for loopholes the current tests miss. It would
**retire 8 class E tests** in `tests/architecture/` and replace them with contracts that fail on the same injected
violation: core not domains, phase19 hot path, belief/fame/fidelity, admission control, campaign state, and
`visual_assets` if a root package is added. The ticket is blocked until the owner and you agree.
**Asked:** agree, refuse, or narrow the list of tests to retire.

Evidence from the evaluation (injection runs in a scratch copy):
1. `tests/architecture/test_phase19_observability_boundaries.py::test_hot_path_does_not_import_heavy_analyzers` is a
   **no-op**. It matches the bare prefix `observability.*`, which never occurs in real `src.observability.*` imports
   (its own comment says so). Injecting `import src.observability.reporting` into `src/engine/kernel.py` leaves it
   passing. Today `kernel.py` imports `src.observability.reporting.*` and `.cognition.*` function-locally (lines 149,
   304, 305, 316, 1241), which are the violations it was written to catch.
2. Blind spots, confirmed by injection (the tests pass, a contract catches it):
   - phase18 counts `ImportFrom` only, so it misses plain `import src.observability.events` into `domains` and plain
     `import src.engine.x` into `systems`.
   - The api read-model guard matches names, so it misses `from src.core import state` into `src/api/routes`.
   - The belief/fame/fidelity guard matches the prefix `src.core.state`, so it misses `from src.core import state`.
   - The admission_control guard misses `import src.engine.governor` and `from src.engine import governor`.
   - The `rendering/density.py` guard checks `node.module`, so it misses `from src.rendering import render`.
3. A stale allowlist entry: phase18 allows `observability/cognition/recorder.py` to import domains/systems, but it no
   longer does.
4. From the inventory, not re-run: `test_decision_trace_writer_does_not_import_engine_cognition` has a vacuous
   `... in sys.modules or True` assert.

## 4. `src/testing/` is test support living in `src/`

`route_family_classifier.py` and `scenario_runner.py`: 0 src importers, 2 test importers
(`tests/unit/strategic/test_classifier.py`, `test_scenario_runner.py`). The audit's decision is `investigate`; nothing
moves while `src/` is frozen. **Asked:** decide whether it moves under `tests/` support when `src/` reopens.

## Responses

### `test-architecture-reviewer`, 2026-10-04 (PR comment)

Replied as a PR comment, recorded here so the answer survives on `main`:
https://github.com/ttnhan18062000/rpg-based-simulation/pull/322#issuecomment-5979287377
Summary: §1 no objection; tag `test-architecture-reviewer` on the gates-flip PR, keep the scenario-lane `PERF_RE` pin in sync, and do not make the scenario lane required. §2 testing tickets the readiness-poll fix itself (no quarantine). §3 import-linter **agreed with four conditions** (retire a test only once its replacement contract is a required check; parity per retired test; phase19 is an expectation change that the engine/observability owner decides first; the `or True` assert is testing's). §4 `src/testing/` moves under test support when `src/` reopens.
