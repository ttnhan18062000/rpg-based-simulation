---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260929-RETIRE-SCRIPTS-DIR
phase: open
date: 2026-09-29
tags: [architecture, documentation, testing]
---

# TCK-20260929-RETIRE-SCRIPTS-DIR

## Title
Retire scripts/: move live files into tools/perf, tools/release and tools/maintenance, delete orphans, document the tooling-layout rule

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P2

## Request Summary
The repo keeps tooling in two homes, scripts/ and tools/. That split lets files go orphaned without anyone noticing, and there is no rule for where a new tool belongs. On 2026-09-29 the user decided to retire scripts/ entirely. Its 23 live files move into domain subpackages under tools/: tools/perf/ (profiling, benchmarks, perf baselines, memory probes, turbo runs), tools/release/ (release/certification gates, proof generation, and the still-live scripts/archive/ledger_validator.py that release_gate.py:93 calls) and tools/maintenance/ (audit_logs, cleanup_tests, auto_convert_builder_usage, protocol_validator). Each subpackage is a real package with __init__.py and uses package imports, following the TCK-20260916-MECHANISM-REGISTRY-TOOLS-PACKAGE precedent. The user chose delete-not-archive, so the 8 confirmed orphans (6 in scripts/, plus tools/extract_defs.py and tools/test_docker.py) and the 4 dead scripts/archive/* files are deleted outright, and no tools/archive/ is recreated. This ticket's disposition table is the only record of each deletion. scripts/turbo_run.py moves to tools/perf/ with its broken src_legacy.utils.logging import fixed and a smoke run proving it works, so the turbo_run -> audit_logs pair stays usable. Every live reference (Makefile, tests, .claude/ workflows, docs, the test-scope map) is rewritten in the same change, so scripts/ no longer exists afterwards. One guideline doc records the rule that tools/ is the only home for repo tooling and that new tools go into a domain subpackage. These pieces are merged into one ticket because the move, the reference rewrites, the scope-map update and the deletions have to land atomically: removing scripts/ is only possible once all of them are done, and 6 of the 8 orphans live there.

## Scope
- Create tools/release/__init__.py and tools/maintenance/__init__.py, and add tools/perf/__init__.py (tools/perf/ already exists) without breaking script-invoked tools/perf/live_map_ws_payload_measure.py.
- git mv to tools/perf/: scripts/check_perf_regression.py, memory_probe.py, perf_baseline.py, perf_ci.py, perf_report.py, profile_api_payload.py, profile_engine.py, profile_memory.py, profile_sweep.py, run_benchmarks.py, run_perf_baseline.py, turbo_run.py, turbo_run_and_audit.ps1.
- git mv to tools/release/: scripts/release_gate.py, generate_release_proof.py, generate_optimization_proof.py, verify_production_profiles.py, behavior_observability_rollout_gate.py, phase10_enhanced_rollout_gate.py, scripts/archive/ledger_validator.py.
- git mv to tools/maintenance/: scripts/audit_logs.py, cleanup_tests.py, auto_convert_builder_usage.py, protocol_validator.py (after confirming protocol_validator has a live caller; if it has none, give it a delete disposition in the table instead).
- Delete the 4 dead archive files scripts/archive/apply_traceability.py, remediate_checklist.py, report_coverage.py, validate_checklist.py.
- Delete the 8 orphans: scripts/certification_long_run.py, merge_documents.py, process_pytest_report.py, refresh_proofs.py, run_perf_optimized.py, split_milestone.py, tools/extract_defs.py, tools/test_docker.py. Record a disposition table (file, last commit, reason, superseded-by) in the ticket as the only record. Findings to seed it: certification_long_run.py (bc3915c00, likely broken EntityState(position=), superseded by tests/integration/kernel/test_certification_scenarios.py); merge_documents.py (4598e744a, never referenced); process_pytest_report.py (6fe08820d, never referenced); refresh_proofs.py (562116889, likely broken, superseded by generate_release_proof.py + release_gate.py); run_perf_optimized.py (562116889, superseded by run_benchmarks/perf_baseline); split_milestone.py (562116889, only a pasted chat log in docs/archive references it); tools/extract_defs.py (bfdf91a6c, provably broken: src/core/traits.py missing, names undefined); tools/test_docker.py (bfdf91a6c, working docker smoke run, unreferenced, Makefile docker-up/docker-down cover most; user chose delete).
- Change repo-root resolution in moved files to parents[2] (generate_optimization_proof.py:19, memory_probe.py:23, profile_api_payload.py:24, profile_engine.py:17, profile_sweep.py:49-50 including its <root>/tools insert, turbo_run.py:35), following the tools/perf/live_map_ws_payload_measure.py:90 precedent.
- Rewrite subprocess and internal path references: perf_ci.py:18,26; release_gate.py:93,102; perf_report.py:17; turbo_run.py:75; turbo_run_and_audit.ps1:27; usage docstrings in memory_probe.py, profile_api_payload.py, profile_memory.py, profile_sweep.py, auto_convert_builder_usage.py:13,16.
- Fix turbo_run.py's src_legacy.utils.logging import to a live module and smoke-run it (plus the turbo_run -> audit_logs pair). Check whether this changes the python-json-logger unused-dependency result noted at tools/codebase_health_baseline.py:52.
- Makefile: repoint profile-api (line 265) and memray-profile (line 268) to tools/perf/. Remove or repoint the dead profile/profile-full/profile-memory targets (lines 256, 259, 262) that point at the nonexistent scripts/profile_simulation.py.
- Tests: switch tests/certification/test_phase10_enhanced_rollout_gate.py, tests/certification/test_phase28_behavior_observability_rollout_gate.py, tests/perf/test_optimization_proof_report.py, tests/unit/perf/test_profiling_harness_modes.py, tests/perf/test_profile_sweep.py and tests/unit/cli/test_profile_memory_script.py to tools.perf.* / tools.release.* package imports or paths, with no scripts/ sys.path insert. Repoint the subprocess call in tests/certification/test_final_gate.py:100,104.
- tools/gate_checks/test_scope_coverage_static.py: add _TOOLS_SUBDIR_EXPLICIT_MAP entries for tools/release/ and tools/maintenance/, and widen the tools/perf/ mapping to cover tests/perf/, tests/unit/perf/ and tests/unit/cli/ while keeping tests/static/. Pin this with new cases in tests/tools/test_test_scope_coverage_static.py.
- Docs and agent prompts: update docs/engine/contracts/regression_and_verification.md:116 (and the nonexistent scripts/test_harness.py citations at :35-43), docs/compliance/checklist.md:302,303,3291 (drop the absolute file:///home/vboxuser link),3298, docs/optimization_audit_ledger.md:30, docs/testing/observability_coverage.md:98, the open ticket tickets/todos/intention-log-first-class/TCK-20260822-STRATEGIC-INTENTION-RING-BUFFER.md:45,80, the .claude/workflows/prepare-simulation-execution.js:86 prompt text, and the cosmetic tools/codebase_health_baseline.py:52 docstring.
- Write one new guideline doc (e.g. docs/guidelines/repo_tooling_layout.md) with valid frontmatter. It states: tools/ is the only home for repo tooling, and new tools go into a domain subpackage (the tools/gate_checks/ and tools/mechanism_registry/ precedent). Then run make knowledge-index-update.

## Out of Scope
- Regrouping the ~70 existing flat top-level tools/ files into subpackages; they stay where they are and move later, one domain at a time.
- Codex subtrees (tools/agent_codex_*, agent_orchestration_*, agent_replay_*).
- Editing CLAUDE.md to carry the tooling-layout rule. CLAUDE.md edits need the user to confirm the literal text directly; this is at most a follow-up.
- Any CI wiring or new .github/workflows change (no .github/workflows file references scripts/ today).
- Recreating a tools/archive/ directory or writing a docs/archive note for deleted files.
- Rewriting historical references in tickets/done/*, tickets/working_log.csv, docs/archive/*, stored_artifacts/*, agent-monitoring/*, docs/REGISTRY.yaml, tests/tools/fixtures/*.json.
- Building the tools/ orphan-file check (separate ticket TCK-20260929-TOOLS-ORPHAN-FILE-CHECK).
- Renaming the phase10_/phase28 process-labelled file names (optional adjacent cleanup, not required).

## Acceptance Criteria
- [ ] `test -e scripts` fails (the scripts/ directory no longer exists).
- [ ] `git grep -nE 'scripts/[a-z_]+\.(py|ps1)|from scripts\.|scripts/archive'`, excluding tickets/done/, tickets/working_log.csv, docs/archive/, stored_artifacts/, agent-monitoring/, docs/REGISTRY.yaml and tests/tools/fixtures/, returns zero hits.
- [ ] tools/perf/__init__.py, tools/release/__init__.py and tools/maintenance/__init__.py exist, and tools/perf/live_map_ws_payload_measure.py still runs when invoked as a script.
- [ ] The 7 affected test files (test_phase10_enhanced_rollout_gate.py, test_phase28_behavior_observability_rollout_gate.py, test_optimization_proof_report.py, test_profiling_harness_modes.py, test_profile_sweep.py, test_profile_memory_script.py, test_final_gate.py) contain no scripts/ sys.path insert or path, and pass with the same pass/skip counts as before the move.
- [ ] test_scope_coverage_static.expected_test_dirs_for returns non-None for tools/release/release_gate.py and tools/maintenance/cleanup_tests.py. The tools/perf/ mapping covers the moved perf files' real test dirs and still maps tools/perf/live_map_ws_payload_measure.py to tests/static/. All of this is pinned by new cases in tests/tools/test_test_scope_coverage_static.py.
- [ ] `make profile-api` and `make memray-profile` invoke tools/perf/ paths. The profile/profile-full/profile-memory targets no longer reference scripts/profile_simulation.py.
- [ ] tools/perf/perf_ci.py and tools/release/release_gate.py resolve their subprocess targets (run_benchmarks.py, check_perf_regression.py, ledger_validator.py) at the new locations, and moved files that insert the repo root use parents[2].
- [ ] tools/perf/turbo_run.py has no src_legacy import, and a recorded smoke run of it (and of the turbo_run -> audit_logs pair) completes without ImportError.
- [ ] A word-bounded grep for the 8 orphan basenames (certification_long_run, merge_documents, process_pytest_report, refresh_proofs, run_perf_optimized, split_milestone, extract_defs, and the path form tools/test_docker) over src tests tools .claude Makefile pyproject.toml docs returns no hits outside docs/REGISTRY.yaml, docs/archive/ and docs/plans/scripts_tools_governance_epic.md.
- [ ] The ticket contains a disposition table that lists every deleted file (the 8 orphans and the 4 dead scripts/archive/* files) with its last commit and deletion reason. No tools/archive/ directory exists.
- [ ] `pytest --collect-only -q tests/architecture tests/tools` collects the same count as before the change.
- [ ] Exactly one new docs/guidelines/ doc states the tooling-layout rule and passes validate_frontmatter.py, and make knowledge-index-update has been run.

## Related Tickets
- TCK-20260820-SCRIPTS-TOOLS-GOVERNANCE-EPIC
- TCK-20260916-MECHANISM-REGISTRY-TOOLS-PACKAGE
- TCK-20260928-TEST-SCOPE-MAP-MISSES-TOOLS-SUBPACKAGES
- TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE
- TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY
- TCK-20260818-HOTFIX-PROFILE-SWEEP-EXPORT-TOOL
- TCK-20260822-STRATEGIC-INTENTION-RING-BUFFER
- TCK-20260819-STANDARD-PARITY-LEDGER-HYGIENE-SWEEP
- TCK-20260910-HOTFIX-WRITE-PATH-GUARD-STALE-ARCHIVE-COMMENTS

## Related Docs
- docs/plans/scripts_tools_governance_epic.md
- docs/engine/contracts/regression_and_verification.md
- docs/compliance/checklist.md
- docs/optimization_audit_ledger.md
- docs/testing/observability_coverage.md
- docs/guidelines/frontmatter_schema.md

## Related Stored Artifacts
None.

## Related Code Areas
- scripts/check_perf_regression.py
- scripts/memory_probe.py
- scripts/perf_baseline.py
- scripts/perf_ci.py
- scripts/perf_report.py
- scripts/profile_api_payload.py
- scripts/profile_engine.py
- scripts/profile_memory.py
- scripts/profile_sweep.py
- scripts/run_benchmarks.py
- scripts/run_perf_baseline.py
- scripts/turbo_run.py
- scripts/turbo_run_and_audit.ps1
- scripts/release_gate.py
- scripts/generate_release_proof.py
- scripts/generate_optimization_proof.py
- scripts/verify_production_profiles.py
- scripts/behavior_observability_rollout_gate.py
- scripts/phase10_enhanced_rollout_gate.py
- scripts/archive/ledger_validator.py
- scripts/audit_logs.py
- scripts/cleanup_tests.py
- scripts/auto_convert_builder_usage.py
- scripts/protocol_validator.py
- scripts/archive/apply_traceability.py
- scripts/archive/remediate_checklist.py
- scripts/archive/report_coverage.py
- scripts/archive/validate_checklist.py
- scripts/certification_long_run.py
- scripts/merge_documents.py
- scripts/process_pytest_report.py
- scripts/refresh_proofs.py
- scripts/run_perf_optimized.py
- scripts/split_milestone.py
- tools/extract_defs.py
- tools/test_docker.py
- tools/perf/live_map_ws_payload_measure.py
- tools/gate_checks/test_scope_coverage_static.py
- tools/codebase_health_baseline.py
- Makefile
- .claude/workflows/prepare-simulation-execution.js
- tests/certification/test_phase10_enhanced_rollout_gate.py
- tests/certification/test_phase28_behavior_observability_rollout_gate.py
- tests/certification/test_final_gate.py
- tests/perf/test_optimization_proof_report.py
- tests/perf/test_profile_sweep.py
- tests/unit/perf/test_profiling_harness_modes.py
- tests/unit/cli/test_profile_memory_script.py
- tests/tools/test_test_scope_coverage_static.py
- expected: tools/perf/__init__.py
- expected: tools/release/__init__.py
- expected: tools/maintenance/__init__.py
- expected: docs/guidelines/repo_tooling_layout.md

## Assumptions / Open Questions
- protocol_validator.py is assumed to have a live caller. The investigation flagged that it overlaps the dead archive/validate_checklist.py; if no live caller exists, it gets a delete disposition instead of moving to tools/maintenance/.
- The live module turbo_run.py's logging import should be repointed to is not yet chosen. Fixing it may change the python-json-logger unused-dependency result in tools/codebase_health_baseline.py:52, and whether that dependency then becomes removable is open.
- Adding tools/perf/__init__.py is assumed not to break script invocation of live_map_ws_payload_measure.py (note the editable-install trap at its line 90).
- CWD-relative paths in moved files (reports/..., tests/perf/baselines) keep their existing works-from-repo-root-only behavior; each moved file needs a smoke run to confirm.
- Whether the 3 dead Makefile profile targets are removed or repointed (to tools/perf/profile_engine.py, for example) is the implementer's call.
- Putting the tooling-layout rule into CLAUDE.md is a possible follow-up that needs the user to confirm the literal text directly; it is not done here.
- The exact guideline doc filename (repo_tooling_layout.md) is a recommendation, not fixed.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
