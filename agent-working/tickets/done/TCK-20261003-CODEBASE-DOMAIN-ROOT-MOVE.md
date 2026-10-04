---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261003-CODEBASE-DOMAIN-ROOT-MOVE
phase: done
date: 2026-10-03
tags: [architecture, delivery]
---

# TCK-20261003-CODEBASE-DOMAIN-ROOT-MOVE

## Title
Move the codebase domain's tooling and baselines into a top-level codebase/ domain root

## Status
DONE

## Tier
standard

## Type
refactor

## Priority
P1

## Request Summary
Owner decision 2026-10-03 (decision record `docs/plans/codebase_health/codebase_domain_root.md`, option B): the codebase domain's tooling is split across tools/code_health/, five flat tools/*.py files, tools/hooks/, registries/ and agent-working/. Move what the domain owns into one top-level `codebase/` root (precedents: agent-working/, visual_assets/) so ownership is one glob and M5's rule packs, contracts and package registry have a home. Pure move, no behaviour change. This ticket also fills in the M4 soak dates left as placeholders by PR #305.

## Scope
- Create `codebase/` as an importable package with `README.md` (owner, map, what lives elsewhere and why): `health/` (from tools/code_health: adapters, findings, scan, ratchet, registry, metrics, line_count, `__main__`), `gates/` (mypy_gate, sarif_feedback, staged_ratchet), `hooks/` (code_health_pre_commit.sh, uv_lock_pre_commit.sh, install_git_hooks.py), `reports/` (codebase_health_baseline, codebase_health_snapshot, code_health_impact, pr_impact_report, audit_unreachable_code), `baselines/` (code_health_exceptions.jsonl, mypy_baseline.txt), `config/` (.jscpd.json if jscpd accepts a config path)
- Move the matching tests to `tests/codebase/` (test_code_health_*, test_codebase_health_*, test_mypy_gate, test_pr_impact_report and the static guards that belong to this domain); keep CI collecting them (add `tests/codebase` to the right job and to the coverage test)
- Update every live reference: Makefile targets (names unchanged), .github/workflows/test.yml job commands (job names unchanged), pyproject.toml (`[tool.mypy_baseline] baseline_path`, any tool path), .pre-commit-config.yaml entries, docs (standard, plans, environment guide, parity INFRA-TYPE-001 evidence), open tickets in agent-working/tickets/todos/python-code-craft-gates/
- Amend docs/guidelines/repo_tooling_layout.md: a domain root may own its tooling (agent-working/ for data, visual_assets/ and codebase/ for their own Python); every other tool still goes in a tools/ subpackage; scripts/ stays retired
- Extend tools/gate_checks/tools_orphan_check.py (or its config) to cover `codebase/**`; add a guard test that fails if `tools/code_health/` or the moved flat files reappear
- Map `codebase/**` -> `tests/codebase/` in `tools/gate_checks/test_scope_coverage_static.py::expected_test_dirs_for()` (with pins in `tests/tools/test_test_scope_coverage_static.py`) and add a `codebase/` row to `.claude/agents/test-scoper.md`'s Directory Map; otherwise a later `codebase/` change returns None (a SKIP) and passes the done-gate without running `tests/codebase/`. Cross-domain edits (agent-working owns both files), approved by the owner's decision B
- Fill the M4 soak dates (start = PR #305 merge date, end = start + 14 days) in the epic, roadmap Section 7 and TCK-20261003-CODE-HEALTH-GATES-FLIP-BLOCKING

## Out of Scope
- Any behaviour change in the moved tools, their CLIs, exit codes or outputs (beyond paths)
- `agent-working/agent-monitoring/codebase_health_history.jsonl`: stays until agent-working agrees to move it (request sent separately); the snapshot keeps writing there
- tools/hooks/post-commit-reindex.sh and registry_post_merge_regen.sh (agent-working's hooks)
- The session-layer ownership table (agent-working owns it; an `owns: [codebase/**, ...]` request is sent separately)
- Cross-domain registries in registries/ (tags, layers, mechanisms, ...)
- Any file under src/

## Acceptance Criteria
- [x] `codebase/` exists with the layout above and a README naming the owner; `python3 -m codebase.health check` replaces `python3 -m tools.code_health check` everywhere it is referenced
- [x] `git grep` finds no live reference to `tools/code_health`, `tools.code_health`, the five moved flat files or `registries/code_health_exceptions.jsonl` / `registries/mypy_baseline.txt` outside closed history (tickets/done, stored_artifacts, monitoring shards)
- [ ] Makefile target names and CI job names are unchanged; on the PR run `Code health (advisory)` reports 3,617 unchanged (or the reseed count of the merged head), the mypy gate 0 new, and the SARIF job uploads (local verification done: names identical to origin/main, count 3,617 and mypy 0 new on the merged head; the PR run itself is still to be recorded after the push)
- [x] Moved tests pass from `tests/codebase/`, and the CI coverage test shows them collected by a job
- [x] repo_tooling_layout.md amended as in Scope; the orphan check covers `codebase/**`; the reappearance guard test passes
- [x] Soak start and end dates filled in the epic, roadmap and flip ticket
- [x] `git diff --stat <base>...HEAD` lists no path under src/ and not CLAUDE.md, and under .claude/ only `.claude/agents/test-scoper.md` (the one Directory Map row for `codebase/`, planner REQUIRED 4)

## Related Tickets
- TCK-20261003-PYTHON-CODE-CRAFT-GATES-EPIC
- TCK-20261003-CODE-HEALTH-GATES-FLIP-BLOCKING
- TCK-20260916-MECHANISM-REGISTRY-TOOLS-PACKAGE
- TCK-20260929-RETIRE-SCRIPTS-DIR

## Related Docs
- docs/plans/codebase_health/codebase_domain_root.md
- docs/guidelines/repo_tooling_layout.md
- docs/plans/codebase_health/python_code_craft_roadmap.md
- docs/guides/agent_working_path_map.md (precedent for a root move)

## Related Stored Artifacts
None.

## Related Code Areas
- tools/code_health/, tools/hooks/, tools/codebase_health_*.py, tools/code_health_impact.py, tools/pr_impact_report.py, tools/audit_unreachable_code.py
- registries/code_health_exceptions.jsonl, registries/mypy_baseline.txt
- Makefile, .github/workflows/test.yml, pyproject.toml, .pre-commit-config.yaml, .jscpd.json
- tests/tools/, tests/static/

## Assumptions / Open Questions
- Planner measured ~25 files to move and ~60 live referencing files on b4076b46 (15 in agent-working tickets, 14 in tests/tools); Investigate re-measures on the merged head
- Anyone who installed the prek hooks has a shim calling the old hook path; the installer must handle re-install, and the guide says to re-run `make install-prek-hooks` (nobody has installed it in the shared .git yet, verified 2026-10-03)
- Name `codebase` must not shadow any installed package; Investigate checks
- First ticket of the batch: the parity ratchet ticket puts its baseline under codebase/baselines/

## Implementation Notes
Seven steps on branch `codebase-domain-root`, each commit green for the tests it touches (module-move commits rewrite the covering tests' imports in the same commit; files relocated in step 4). Plan, investigation and test plan: `agent-working/staging_artifacts/TCK-20261003-CODEBASE-DOMAIN-ROOT-MOVE/` (moved to stored_artifacts at close).
- Moves with `git mv`, so history follows: `tools/code_health/*` -> `codebase/health/` + `codebase/gates/`; five flat tools -> `codebase/reports/`; three hook files -> `codebase/hooks/`; both baselines -> `codebase/baselines/`; `.jscpd.json` -> `codebase/config/`; 17 test files -> `tests/codebase/`.
- jscpd decision: jscpd 5.4.0 accepts `--config codebase/config/.jscpd.json` (verified on a planted clone, then a real `python -m codebase.health check`), so the config moved; `scan.py` and the Makefile pass the new path.
- Sibling-import `sys.path` hacks replaced by package imports; every invocation is `python3 -m codebase.<pkg>.<module>` (a path run puts `codebase/reports/` on `sys.path[0]` and fails). `tools/agent-monitoring` stays a sys.path insert (hyphenated dir, not a package).
- CI: `tests/codebase` runs in `tools-a-e` (lint group installed), not arch-docs. The base-collection step passes the path only when the directory exists on base. `tests/tools/test_ci_split_tools_jobs.py` pins `tools-a-e` = {tests/tools, tests/codebase}.
- Planner REQUIRED 4 (cross-domain, agent-working owns both files, owner decision B): `expected_test_dirs_for()` maps `codebase/**` (except README.md) -> `tests/codebase/`, with pins; `.claude/agents/test-scoper.md` Directory Map gains a `codebase/` row. Acceptance criterion amended to allow exactly this one `.claude/` file.
- `tools_orphan_check` classifies `codebase/**` `.py`/`.sh` files; guard tests assert the old locations do not reappear, `codebase` is not shadowed, every moved module imports, and no `tools/**/*.py` imports `codebase`.
- Soak dates filled: start 2026-10-03 (PR #305 merged 2026-10-03T16:47:13Z, checked with `gh pr view`), end 2026-10-17, in the epic, the flip ticket and roadmap Section 7.
- Merged origin/main (#307 to #310) into the branch before closing; no conflicts. Perf PR #311 (edits test-scoper.md and `test_test_scope_coverage_static.py`) was not merged at that time: rebase or merge before push.
- Prek: the shim reads `.pre-commit-config.yaml` at commit time, so existing installs pick up the new hook paths; installer needed no constant change (same depth); Git-hooks guide says re-running `make install-prek-hooks` is idempotent.
- Real CLI runs from the repo root (not pytest): `codebase.health check` (0 new, 3617 unchanged, on the merged head too), `codebase.gates.mypy_gate` (exit 0, 0 new), `codebase.gates.sarif_feedback` (SARIF written), `codebase.gates.staged_ratchet` (exit 0), both hook `.sh` scripts, `codebase.reports.codebase_health_baseline` (full report), `codebase.reports.codebase_health_snapshot scorecard`, and `--help` for every other module (`code_health_impact`, `pr_impact_report`, `audit_unreachable_code`, `install_git_hooks`). `code_health_impact`/`pr_impact_report` were NOT run against the real 510 MB graph (OOM risk at the 2 GB cap): their fixture-graph tests pass.

## Test Summary
Moved set, same files before (tests/tools + tests/static, venv with the lint group) and after (tests/codebase): before 235 passed / 6 failed / 0 skipped; after 235 passed / 6 failed / 0 skipped (+14 `test_pr_impact_report` tests, all passing). Skip count did not rise. The 6 failures are identical by name before and after and are the known local-environment ones (3 `test_real_path_*` graph tests, `test_compute_churn_target_pathspec_defaults_to_repo_wide`, and the two make-target tests that time out); CI decides.
New/updated: `tests/codebase/test_domain_root_layout.py` (guards), orphan-check codebase case, test-scope `codebase/**` pins, `test_ci_split_tools_jobs.py` path set. Scoped runs: tests/static, tests/docs, tests/parity, tests/architecture, the CI-coverage and split-job tests, orphan and test-scope tests: all pass (336 passed, 2 skipped, 1 xfailed in the final cheap run; the skips/xfail are existing tests/docs entries).
Counts: `code-health check` 0 new / 3617 unchanged; mypy gate 0 new; baselines 3617 and 1569 rows. Makefile target names and CI job ids and names are identical to origin/main.

## Files Changed
~70 files outside agent-working/docs-registry: `codebase/` (new root: README, `__init__` files, health/, gates/, hooks/, reports/, baselines/, config/), `tests/codebase/` (17 moved + new `test_domain_root_layout.py`, `__init__.py`), Makefile, pyproject.toml, `.pre-commit-config.yaml`, `.github/workflows/test.yml`, `tools/gate_checks/tools_orphan_check.py`, `tools/gate_checks/test_scope_coverage_static.py`, `tests/tools/{test_tools_orphan_check,test_test_scope_coverage_static,test_ci_split_tools_jobs}.py`, docs (python_code_standard, agent_working_environment, repo_tooling_layout, subsystem_ownership_lifecycle, codebase_health_history_schema, unreachable_code_inventory, artifact_retention_classification, parity ledger INFRA entries, roadmap/briefs, census initiative), the epic and flip ticket in todos/python-code-craft-gates.
Cross-domain edits (agent-working owns them; approved by owner decision B and planner REQUIRED 4): `tools/gate_checks/test_scope_coverage_static.py`, `tests/tools/test_test_scope_coverage_static.py`, `.claude/agents/test-scoper.md`. No `src/` and no `CLAUDE.md` path.

## Completion Summary
Done: the codebase domain's tooling, baselines and tests live under `codebase/` and `tests/codebase/`, with behaviour unchanged (same counts, same test results), names unchanged, guards against regression, and the M4 soak dates recorded. Known gaps stated: `code_health_impact` and `pr_impact_report` not run against the real graph; the 6 local-environment failures remain; perf PR #311 not yet merged (rebase before push).
