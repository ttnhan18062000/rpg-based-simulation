# Plan — TCK-20260929-RETIRE-SCRIPTS-DIR

Ordered steps. The ticket's own Scope/Acceptance Criteria list every exact line number to touch
— this plan sequences the work, it doesn't restate every citation.

1. Create `tools/perf/__init__.py`, `tools/release/__init__.py`, `tools/maintenance/__init__.py`.
2. `git mv` the 24 files (23 + `ledger_validator.py`) into their target subpackage (see
   investigation.md for the reconciled list — `protocol_validator.py` moves to *delete*, not
   `tools/maintenance/`).
3. Delete the 12 dead files (6 scripts/ orphans, 4 dead archive/, `tools/extract_defs.py`,
   `tools/test_docker.py`, plus `scripts/protocol_validator.py` as a 9th orphan found live).
4. Fix repo-root resolution (`parents[2]`) in the 6 files that need it, including `turbo_run.py`.
5. Fix `turbo_run.py`'s `src_legacy` import → `src.logging.formatter.JsonFormatter`/`ContextFilter`,
   and its `audit_logs.py` invocation message.
6. Rewrite the remaining internal path/subprocess references (`perf_ci.py`, `release_gate.py`,
   `perf_report.py`, `turbo_run_and_audit.ps1`, usage docstrings).
7. Delete `scripts/` entirely once empty (including `__pycache__/`).
8. Makefile: repoint `profile-api`/`memray-profile`, remove/repoint the 3 dead `profile*` targets.
9. Update the 7 affected test files' imports/paths (no `scripts/` `sys.path` inserts).
10. `tools/gate_checks/test_scope_coverage_static.py`: add `tools/release/`, `tools/maintenance/`
    map entries, widen `tools/perf/`; pin with new cases in
    `tests/tools/test_test_scope_coverage_static.py`.
11. Update the 8 cited doc/prompt locations.
12. Write `docs/guidelines/repo_tooling_layout.md` (valid frontmatter) stating the tools/-only rule.
13. Run `make knowledge-index-update` (docs changed).
14. Smoke-run `turbo_run.py` (short) piped into `audit_logs.py`, confirm no `ImportError`.
15. Run the scoped test suites; run the 4 acceptance-criteria greps/collects.
16. Fill in the ticket's disposition table, Implementation Notes, Test Summary, Files Changed,
    Completion Summary. Move ticket to `tickets/done/`; delete it from
    `tickets/todos/scripts-tools-governance/` (already done via the initial `git mv`); when the
    sibling `TOOLS-ORPHAN-FILE-CHECK` ticket also closes, move the whole folder to
    `tickets/done/scripts-tools-governance/`.

## Scope guards
- No regrouping of the ~70 flat top-level `tools/` files (out of scope, stated in ticket).
- No CLAUDE.md edit (out of scope, stated in ticket).
- No `tools/archive/` recreation.
- Historical references (`tickets/done/`, `docs/archive/`, `stored_artifacts/`,
  `agent-monitoring/`, `docs/REGISTRY.yaml`, `tests/tools/fixtures/*.json`) are left untouched.

## Acceptance-criteria map
Every AC in the ticket maps 1:1 to a step above (grep/collect/pytest checks run in step 15 after
the moves/edits in steps 1-13 are complete); no AC is deferred to the sibling ticket except the
orphan-check mechanism itself (explicitly out of scope here).
