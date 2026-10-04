---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261003-CODEBASE-DOMAIN-ROOT-MOVE
phase: inprogress
date: 2026-10-03
tags: [architecture, delivery]
---

# TCK-20261003-CODEBASE-DOMAIN-ROOT-MOVE

## Title
Move the codebase domain's tooling and baselines into a top-level codebase/ domain root

## Status
INPROGRESS

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
- [ ] `codebase/` exists with the layout above and a README naming the owner; `python3 -m codebase.health check` replaces `python3 -m tools.code_health check` everywhere it is referenced
- [ ] `git grep` finds no live reference to `tools/code_health`, `tools.code_health`, the five moved flat files or `registries/code_health_exceptions.jsonl` / `registries/mypy_baseline.txt` outside closed history (tickets/done, stored_artifacts, monitoring shards)
- [ ] Makefile target names and CI job names are unchanged; on the PR run `Code health (advisory)` reports 3,617 unchanged (or the reseed count of the merged head), the mypy gate 0 new, and the SARIF job uploads
- [ ] Moved tests pass from `tests/codebase/`, and the CI coverage test shows them collected by a job
- [ ] repo_tooling_layout.md amended as in Scope; the orphan check covers `codebase/**`; the reappearance guard test passes
- [ ] Soak start and end dates filled in the epic, roadmap and flip ticket
- [ ] `git diff --stat <base>...HEAD` lists no path under src/ and not CLAUDE.md, and under .claude/ only `.claude/agents/test-scoper.md` (the one Directory Map row for `codebase/`, planner REQUIRED 4)

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

## Test Summary

## Files Changed

## Completion Summary
