---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261003-CODEBASE-DOMAIN-ROOT-MOVE
artifact_type: plan
tags: [architecture, delivery]
---

# Plan — TCK-20261003-CODEBASE-DOMAIN-ROOT-MOVE

Pure move, no behaviour change. Base: `3c8eb71f0` (origin/main `b11619a4e` + planning commit). All paths below were found by search on that head (see investigation.md), not from memory.

## 1. Old → new path map

| Old | New |
|---|---|
| `tools/code_health/{__init__,__main__,adapters,findings,line_count,metrics,ratchet,registry,scan}.py` | `codebase/health/` (same names) |
| `tools/code_health/{mypy_gate,sarif_feedback,staged_ratchet}.py` | `codebase/gates/` |
| `tools/hooks/{code_health_pre_commit.sh,uv_lock_pre_commit.sh,install_git_hooks.py}` | `codebase/hooks/` |
| `tools/codebase_health_baseline.py`, `codebase_health_snapshot.py`, `code_health_impact.py`, `pr_impact_report.py`, `audit_unreachable_code.py` | `codebase/reports/` |
| `registries/code_health_exceptions.jsonl`, `registries/mypy_baseline.txt` | `codebase/baselines/` |
| `.jscpd.json` | `codebase/config/.jscpd.json` (decision below) |
| `tests/tools/test_code_health_*.py` (9), `test_codebase_health_*.py` (3), `test_mypy_gate.py`, `test_pr_impact_report.py` | `tests/codebase/` |
| `tests/static/test_ci_code_health_sarif.py`, `test_typecheck_gate_configured.py` | `tests/codebase/` (domain static guards); `test_ci_uv_install.py` stays (cross-domain), edited in place |

Stay put: `tools/hooks/post-commit-reindex.sh`, `registry_post_merge_regen.sh`, `agent-working/agent-monitoring/codebase_health_history.jsonl`, `tools/agent_working_paths.py`, all other `registries/*`.
`git mv` everywhere so history follows. `codebase/` and each subpackage get `__init__.py` (`tools/` has none; it is a namespace package, `visual_assets/` has one). `tests/codebase/__init__.py` added (every tests dir has one).

Flat-file sibling imports become package imports: `import code_health_impact as chi` → `from codebase.reports import code_health_impact as chi`; `from codebase_health_baseline import ...` → `from codebase.reports.codebase_health_baseline import ...`; `from tools.code_health.X` → `from codebase.health.X` (gates: `codebase.gates.X`). The `sys.path` insert hacks in those files and their tests are removed where the package import makes them dead (`pythonpath = ["."]` already covers the root). `from tools.agent_working_paths import ...` stays (codebase may import tools; not the reverse).

jscpd config: scan.py passes `--config .jscpd.json` relative to the scan cwd, and adapters tests copy `.jscpd.json` to a scratch dir. Step 3 checks that jscpd accepts `--config codebase/config/.jscpd.json` (run it); if it does, move and pass the path; if not, `.jscpd.json` stays at root and is listed in the README as a root-pinned file. Decision recorded in Implementation Notes either way.

## 2. Reference sites (search, not memory)

Live, to edit (tracked, outside closed history): `Makefile` (lines 273, 281, 283-292, 458-470, 532-535), `.github/workflows/test.yml` (873-878, 912-913, 942, 985), `pyproject.toml` (`[tool.mypy_baseline] baseline_path` 97, comments 61/201/219), `.pre-commit-config.yaml` (11, 17), `tools/gate_checks/tools_orphan_check.py` (+ its test), `tests/static/test_ci_uv_install.py`, `tests/static/test_typecheck_gate_configured.py`, the moved tests (14 files with path/import refs), `docs/guidelines/{python_code_standard,agent_working_environment,artifact_retention_classification,subsystem_ownership_lifecycle,repo_tooling_layout}.md`, `docs/parity_ledger/infrastructure.yaml` (INFRA-TYPE-001 evidence), `docs/agent-monitoring/codebase_health_history_schema.md`, `docs/audits/unreachable_code_inventory.md`, `docs/plans/codebase_health/*` (roadmap, M4/foundation briefs; the decision record already describes the move), `agent-working/tickets/todos/python-code-craft-gates/{EPIC,FLIP-BLOCKING}.md`.
Not edited, by rule: `agent-working/tickets/done/`, `stored_artifacts/`, monitoring shards, `working_log.csv` (history), `docs/plans/archive/*`, `docs/plans/simulation_execution_census_initiative.md` (historical plan; will be checked in Step 6 and left if its mention is history), `uv.lock` (matches the `mypy_baseline` PyPI package name, false positive). `docs/REGISTRY.yaml` is regenerated, not hand-edited.
`.claude/` (agent definitions, workflows): the search found NO live path reference, only `.claude/handover/*` notes (git-ignored). Planner REQUIRED 4 adds one cross-domain edit anyway: a `codebase/` row in `.claude/agents/test-scoper.md`'s Directory Map plus `codebase/**` -> `tests/codebase/` in `tools/gate_checks/test_scope_coverage_static.py::expected_test_dirs_for()` (with pins), because `codebase/**` would otherwise return None (SKIP) and a later change would pass the done-gate without running tests/codebase. The acceptance criterion is amended to allow exactly that one `.claude/` file, and PR #308 (edits test-scoper.md / implement-ticket.js) does not overlap. If the final grep finds one, I stop and ask rather than edit.
CI test collection (planner review, required 1+2): `tests/codebase` goes into **tools-a-e** as an extra path beside `tests/tools --ignore-glob=...` (NOT arch-docs: `uv sync --no-group lint` there has no ruff/complexipy, so tool-dependent tests would skip silently). Verification compares pass/skip counts of the moved files before (on head, in tests/tools) and after: skip count must not rise. The job's "Base branch test collection" step runs the same list in `/tmp/base-checkout`, where `tests/codebase` does not exist; the path is added to the base command only if the dir exists (`$( [ -d tests/codebase ] && echo tests/codebase )`), and `tests/static` (which pins these workflow lines) is run. The CI coverage test must show `tests/codebase` covered by a job.
Mypy baseline: `mypy_baseline` reads `baseline_path` from pyproject; the file moves with that edit in the same commit.

## 3. `codebase` shadowing check
Done in investigation: `importlib.util.find_spec("codebase")` is None, no `codebase/` dir, nothing named `codebase` in the environment or `pyproject`. Repeated as a guard test (`tests/codebase/test_codebase_package.py`): `codebase.__file__` resolves inside the repo root, so a future installed distribution of that name cannot silently win. `[tool.setuptools.packages.find] include = ["src*"]` is unchanged, so `codebase/` is not packaged.

## 4. prek re-install
The pre-commit shim generated by prek reads `.pre-commit-config.yaml` at commit time, so moved hook script paths take effect from the config edit alone; the installer needs no constant change: `REPO_ROOT = Path(__file__).resolve().parent.parent.parent` is the repo root from `codebase/hooks/` exactly as from `tools/hooks/` (same depth), and `POST_COMMIT_SOURCE` stays `tools/hooks/post-commit-reindex.sh`; only its usage docstrings/`GUARD_MARKER` text change to the new path. Nobody has installed the hooks into the shared `.git` (verified 2026-10-03), so no stale shim exists on this machine; a re-install test installs, then asserts an install over an existing prek-generated shim is idempotent and the uninstall still recognises the post-commit hook (it compares against the unchanged post-commit source). The Git-hooks guide says to re-run `make install-prek-hooks` after pulling this change.

## 5. Names unchanged
Makefile target names, CI job names/ids and `-m` markers stay byte-identical; only command bodies change. A guard test diffs the set of Makefile targets and `jobs:` keys against the base (`git show origin/main:...`) in my verification, not as a permanent test.

## 6. Soak dates
Start `2026-10-03` (PR #305 merge, 16:47Z per handover; confirm with `gh pr view 305 --json mergedAt` before writing), end `2026-10-17`. Placeholder lines to replace: epic line 35, FLIP-BLOCKING line 70 (and its "Explicit step" bullet at 69 marked done), roadmap Section 7 line 230. Also tick the epic's soak criterion note at line 34/44 only to the extent the dates are recorded (not the flip).

## Script entry points (planner review, required 3)
After the sys.path hacks go, files use `from codebase.x import ...`; `python3 codebase/reports/x.py` puts `codebase/reports/` on sys.path[0] and fails. Every invocation (Makefile, CI, hook `.sh`, `.pre-commit-config.yaml`, doc examples) switches to `python3 -m codebase.reports.<x>` / `-m codebase.gates.<x>` / `-m codebase.hooks.install_git_hooks` / `-m codebase.health`. Each moved CLI is run once for real from the repo root (not via pytest) and recorded in test_plan.md; the hook `.sh` files and pre-commit entries get particular attention (they must run python from the repo root).

## Steps (one commit per step; commit granularity per note a: each module-move commit rewrites the imports of the tests covering it in the same commit so pytest stays green, files are relocated to tests/codebase in step 4)
1. `codebase/` skeleton + `git mv` health/gates + import rewrite + `pyproject` baseline path + baselines move + Makefile/CI/precommit command bodies for them; baselines `registries/` → `codebase/baselines/`.
2. reports + hooks moves, sibling-import fixes, Makefile install/report targets.
3. jscpd config decision.
4. Tests move to `tests/codebase/`, CI `arch-docs` path, coverage test.
5. Guard tests (also asserts no `tools/**/*.py` imports `codebase`; reappearance of `tools/code_health/` and the moved flat files; package-shadow guard), orphan-check extension to `codebase/**`, `repo_tooling_layout.md` amendment, `codebase/README.md`.
6. Doc/ticket reference updates, soak dates, parity INFRA-TYPE-001 evidence, `make knowledge-index-update`, `make docs-registry`.
7. Verify (scoped tests, never full suite), reseed check (`code-health seed` count unchanged, 3,617), `graphify update .`, closure by `record_hand_orchestrated_closure.py --tier standard`.

## Risks
- Reseed counts: findings are keyed by path; the exceptions file keys point at `src/` paths, not tool paths, so it should be unchanged. Verified by `python3 -m codebase.health check` reporting zero new and 3,617 unchanged.
- Running heavy commands one at a time under the `systemd-run` memory cap; `tests/tools` halves sequentially; `test_pr_impact_report` real-repo target deselected locally (graph.json 510 MB).
- Reseed counts must come out exactly 3,617 and 1,569 (SCAN_ROOT is `src`, no row keys on tools/).
- Parity-ledger entry INFRA-TYPE-001 evidence is the only parity-ledger edit; no mechanics change, no `docs/mechanics` or `docs/engine` edit.
