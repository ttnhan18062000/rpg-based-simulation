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

## Update 2026-10-04 (gates-flip PR): this is the flip PR

**From:** `codebase-planner`, riding in the gates-flip PR. Please review it (`test-architecture-reviewer` is tagged).

The gates-flip PR makes the ratchet, mypy, the package registry and the ast-grep N3/N4/E3 rules blocking (merge on or
after 2026-10-18). It honours your #322 constraints: it is tagged to you; the scenario lane's `PERF_RE` pin
(`tests/unit/tools/test_scenario_lane_paths.py`) is run before every push and job-list or path-filter edits keep the
workflow and `tools/test_architecture/scenario_lane_paths.py` in sync; the scenario lane stays non-required, and the
ruleset change names only `Code health` and `Type check`. Your four import-linter conditions are recorded in
`TCK-20261004-IMPORT-LINTER-ADOPTION` (still BLOCKED; condition 3 is routed to rpg in `handoff_to_rpg.md`).

FYI (cc): `tests/unit/tools/test_mechanism_registry_completeness_check.py:191` pins an exact `scope_files` count (296 at #331's runs; main has since moved it), so any PR that adds a `src/` file fails `Unit · infra / observability` until it is edited. The question goes to agent-working (`handoff_to_agent_working.md`, same update); it is in your test tree.

## Update 2026-10-05: import-linter adopted, advisory (batch `import-linter-adoption`)

**Contracts added, no test retired, flip ticket filed.** `codebase/structure/importlinter.toml` holds the registry
`layers` contract and 16 contracts for the class E rules and the loopholes of the evaluation (Sections 3 and 4); an
advisory `Import contracts` step runs them in the `code-health` job. Your condition 1 holds: every existing
`tests/architecture/` test still runs; retirement is `TCK-20261005-IMPORT-LINTER-FLIP-AND-TEST-RETIREMENT` (BLOCKED
until a two-week soak and the required check). Condition 2: the per-test parity table (34 injections, the contract
caught all 34, the test missed 11) is in `TCK-20261004-IMPORT-LINTER-ADOPTION`'s Test Summary. Condition 3: phase19's
five `kernel.py` imports are in `c06_hot_path_not_heavy`'s `ignore_imports`; its test is untouched. Condition 4: the
blind spots and the stale phase18 allowlist entry are covered; the `or True` assert is untouched.
For your awareness:
- **Decision 8.11 notice:** `tests/static/test_ci_uv_install.py` edited (the `lint` group now includes `import-linter`);
  the gates-flip PR (#329) edits the same file.
- Correction to the evaluation: only the belief test skips `TYPE_CHECKING`; the fame and fidelity tests count it.
- The contracts are stricter than the tests for a NEW `TYPE_CHECKING` import in core, phase18 and belief (the 7
  existing ones are pinned). Contracts run with `exclude_type_checking_imports = false`.
- The `visual_assets` test encodes about ten more rules than the two boundaries (`c14`, `c15`), so it can retire
  only partly.

FYI 2026-10-05: a `Frontend` flake on #351's `43d0f9493`: `src/test/useSimulation.test.tsx:152` (expected `CONNECTING_LIVE`, got `FETCHING_WORLD_DATA`), no frontend diff, passed on a rerun of that job. Yours to decide whether to ticket it.


## Update 2026-10-05 (gates-flip closure): the gates are blocking on `main` since 2026-10-05 (#329)

The flip merged early, by owner decision, on 2026-10-05T14:47Z (not on or after 2026-10-18 as stated above). The tests that
pinned advisory status were updated in that batch as listed in the earlier update. `Code health` and `Type check` now fail
the job on new findings; the two local `make`-target tests that exceed the 60 s budget are tracked by
`TCK-20261005-CODE-HEALTH-MAKE-TARGET-TESTS-LOCAL-TIMEOUT`. Adding the checks to ruleset 14220945 as required is the owner's
step. The import-linter flip and class E test retirement stay on `TCK-20261005-IMPORT-LINTER-FLIP-AND-TEST-RETIREMENT`
(soak ends 2026-10-19, your four conditions attached).


## Update 2026-10-08: decision 8.11 notice, repo-root cleanup batch A

Source: `docs/plans/codebase_health/repo_root_layout_ticket_brief.md`. Under owner decision 8.11 (the `src/` freeze only; tests that pin CI or the Makefile may be edited, with a notice to you), ticket `TCK-20261008-DROP-UNUSED-REQUIREMENTS-EXPORT` (A2) deletes `requirements.txt` and edits these tests:

- `tests/static/test_ci_narrow_path_filtered_jobs.py`: the PERF_RE/MIG_RE match check no longer expects `requirements.txt`.
- `tests/static/test_ci_requirements_no_ml_stack.py`: rewritten. It asserts the ML stack is absent from the default install closure (project dependencies plus `[tool.uv] default-groups`, walked in `uv.lock`) instead of reading `requirements.txt`; the `requirements-knowledge.txt` test is unchanged.
- `tests/static/test_ci_step_summary_reporting.py`: the banned-dependency check (`pytest-cov`, `pytest-html`) reads `pyproject.toml`; two test functions renamed (`..._no_new_dependency_entry_...`).
- `tests/unit/tools/test_scenario_lane_paths.py`: the `requirements.txt` trigger cases use `uv.lock`; `tools/test_architecture/scenario_lane_paths.py` drops `requirements.txt` from its regex (`uv.lock` and `pyproject.toml` stay).
- `tests/tools/test_evidence_cache_identity_contract.py` (candidate list), `tests/tools/test_delivery_ci_triage_classifier.py` (an inline sample workflow line), and comments in `tests/tools/test_knowledge_search.py` and `tests/codebase/test_code_health_impact.py`.

`.github/workflows/test.yml` loses `requirements\.txt$` from PERF_RE and MIG_RE (`pyproject.toml` and `uv.lock` were already in both). Scoped run: `tests/static` and the 42 files referencing the touched paths pass; the known local 60 s failure `test_codebase_health_snapshot.py::test_make_target_runs_successfully_end_to_end` was deselected. Batch B (after A merges) will also edit `tests/architecture/test_docker_compose_dependency_hygiene.py`, `tests/logging/test_loki_cardinality.py`, `tests/codebase/test_code_health_install_git_hooks.py`, and add `tests/codebase/test_repo_root_allowlist.py`; you will get a notice then.


## Update 2026-10-08 (batch B): decision 8.11 notice, repo-root layout

Source: `docs/plans/codebase_health/repo_root_layout_ticket_brief.md`. Batch B (after batch A, PR #447) edits tests under owner decision 8.11 (CI- and layout-pinning tests may be edited, with a notice to you):

- `TCK-20261008-OPS-FILES-INTO-DOCKER-DIR` (B1): `tests/architecture/test_docker_compose_dependency_hygiene.py` now reads `compose.yaml` and `pyproject.toml` anchored on the repo root (was cwd-relative `docker-compose.yml`); `tests/logging/test_loki_cardinality.py` reads `docker/promtail-config.yml` anchored on the repo root (was cwd-relative `promtail-config.yml`); `tests/unit/tools/test_scenario_lane_paths.py` gains two `docker/` cases (the scenario-lane gate treats `docker/` like the old `grafana/`: irrelevant to the lane), with `tools/test_architecture/scenario_lane_paths.py` updated.
- `TCK-20261008-DROP-MAKE-BAT` (B2): `tests/codebase/test_code_health_install_git_hooks.py` drops `make.bat` from its scan list.
- `TCK-20261008-GRAPH-HTML-JS-DEPS-BESIDE-TOOL` (B3): new `tests/tools/test_graphify_to_html_js_assets.py` (paths and a fake tree, no network or npm).
- `TCK-20261008-REPO-ROOT-ALLOWLIST-GUARD` (B4): new `tests/codebase/test_repo_root_allowlist.py` compares the tracked root entries (`git ls-files` first path components) with the allowlist in `docs/guidelines/repo_tooling_layout.md`, section "Repo root"; it fails on any new root file or directory and ignores everything below the root. Mutation-proved with an extra staged root file.

Scoped runs pass (169 passed, 1 skipped for B1's set; 97 for B2; 5 for B3; 4 for B4). The known local 60 s failure `test_codebase_health_snapshot.py::test_make_target_runs_successfully_end_to_end` is unrelated.
