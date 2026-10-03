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
`.claude/` (agent definitions, workflows): the search found NO live reference, only `.claude/handover/*` notes (git-ignored). So no `.claude/` edit is needed, the acceptance criterion holds, and PR #308 (edits test-scoper.md / implement-ticket.js) does not overlap. If the final grep finds one, I stop and ask rather than edit.
CI test collection: `tests/codebase` goes into the `arch-docs` job's pytest path list (beside `tests/static`, fastest job, no tools-job rebalancing); the CI coverage test must then show it covered, and `tests/tools/test_ci_workflow_test_coverage.py` fixtures are checked for a hard-coded dir list. Both `tools-*` halves lose tests, which is fine (globs).
Mypy baseline: `mypy_baseline` reads `baseline_path` from pyproject; the file moves with that edit in the same commit.

## 3. `codebase` shadowing check
Done in investigation: `importlib.util.find_spec("codebase")` is None, no `codebase/` dir, nothing named `codebase` in the environment or `pyproject`. Repeated as a guard test (`tests/codebase/test_codebase_package.py`): `codebase.__file__` resolves inside the repo root, so a future installed distribution of that name cannot silently win. `[tool.setuptools.packages.find] include = ["src*"]` is unchanged, so `codebase/` is not packaged.

## 4. prek re-install
The pre-commit shim generated by prek reads `.pre-commit-config.yaml` at commit time, so moved hook script paths take effect from the config edit alone; the installer needs no constant change: `REPO_ROOT = Path(__file__).resolve().parent.parent.parent` is the repo root from `codebase/hooks/` exactly as from `tools/hooks/` (same depth), and `POST_COMMIT_SOURCE` stays `tools/hooks/post-commit-reindex.sh`; only its usage docstrings/`GUARD_MARKER` text change to the new path. Nobody has installed the hooks into the shared `.git` (verified 2026-10-03), so no stale shim exists on this machine; a re-install test installs, then asserts an install over an existing prek-generated shim is idempotent and the uninstall still recognises the post-commit hook (it compares against the unchanged post-commit source). The Git-hooks guide says to re-run `make install-prek-hooks` after pulling this change.

## 5. Names unchanged
Makefile target names, CI job names/ids and `-m` markers stay byte-identical; only command bodies change. A guard test diffs the set of Makefile targets and `jobs:` keys against the base (`git show origin/main:...`) in my verification, not as a permanent test.

## 6. Soak dates
Start `2026-10-03` (PR #305 merge, 16:47Z per handover; confirm with `gh pr view 305 --json mergedAt` before writing), end `2026-10-17`. Placeholder lines to replace: epic line 35, FLIP-BLOCKING line 70 (and its "Explicit step" bullet at 69 marked done), roadmap Section 7 line 230. Also tick the epic's soak criterion note at line 34/44 only to the extent the dates are recorded (not the flip).

## Steps (one commit per step, each leaves `make code-health`-equivalent working)
1. `codebase/` skeleton + `git mv` health/gates + import rewrite + `pyproject` baseline path + baselines move + Makefile/CI/precommit command bodies for them; baselines `registries/` → `codebase/baselines/`.
2. reports + hooks moves, sibling-import fixes, Makefile install/report targets.
3. jscpd config decision.
4. Tests move to `tests/codebase/`, CI `arch-docs` path, coverage test.
5. Guard tests (reappearance of `tools/code_health/` and the moved flat files; package-shadow guard), orphan-check extension to `codebase/**`, `repo_tooling_layout.md` amendment, `codebase/README.md`.
6. Doc/ticket reference updates, soak dates, parity INFRA-TYPE-001 evidence, `make knowledge-index-update`, `make docs-registry`.
7. Verify (scoped tests, never full suite), reseed check (`code-health seed` count unchanged, 3,617), `graphify update .`, closure by `record_hand_orchestrated_closure.py --tier standard`.

## Risks
- Reseed counts: findings are keyed by path; the exceptions file keys point at `src/` paths, not tool paths, so it should be unchanged. Verified by `python3 -m codebase.health check` reporting zero new and 3,617 unchanged.
- Running heavy commands one at a time under the `systemd-run` memory cap; `tests/tools` halves sequentially; `test_pr_impact_report` real-repo target deselected locally (graph.json 510 MB).
- Parity-ledger entry INFRA-TYPE-001 evidence is the only parity-ledger edit; no mechanics change, no `docs/mechanics` or `docs/engine` edit.
