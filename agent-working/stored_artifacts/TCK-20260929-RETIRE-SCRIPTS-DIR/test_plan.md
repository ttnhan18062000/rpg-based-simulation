# Test Plan — TCK-20260929-RETIRE-SCRIPTS-DIR

Derived directly from the ticket's Acceptance Criteria.

1. `test -e scripts` → non-zero (fails/absent).
2. `git grep -nE 'scripts/[a-z_]+\.(py|ps1)|from scripts\.|scripts/archive'` excluding
   `tickets/done/`, `tickets/working_log.csv`, `docs/archive/`, `stored_artifacts/`,
   `agent-monitoring/`, `docs/REGISTRY.yaml`, `tests/tools/fixtures/` → zero hits.
3. `tools/perf/__init__.py`, `tools/release/__init__.py`, `tools/maintenance/__init__.py` exist;
   `python3 tools/perf/live_map_ws_payload_measure.py --help` (or equivalent no-op invocation)
   still runs as a script.
4. Scoped pytest run over the 7 affected test files — same pass/skip counts as pre-move baseline
   captured before the moves. No `scripts/` `sys.path.insert` remains in any of them.
5. New cases in `tests/tools/test_test_scope_coverage_static.py` pinning
   `expected_test_dirs_for` for `tools/release/release_gate.py`,
   `tools/maintenance/cleanup_tests.py`, and the widened `tools/perf/` mapping (still covering
   `tools/perf/live_map_ws_payload_measure.py` → `tests/static/`).
6. `make profile-api` / `make memray-profile` dry-inspection (grep the Makefile) point at
   `tools/perf/`; the 3 dead `profile`/`profile-full`/`profile-memory` targets no longer cite
   `scripts/profile_simulation.py`.
7. Grep `perf_ci.py`/`release_gate.py` subprocess targets resolve to the new paths; grep the 6
   moved files for `parents[2]`.
8. Smoke run: `turbo_run.py` for a handful of ticks (short `max_ticks`), then
   `python3 -m tools.maintenance.audit_logs <its output>` (or direct path) — no `ImportError`,
   completes.
9. Word-bounded grep for the orphan basenames over
   `src tests tools .claude Makefile pyproject.toml docs` → zero hits outside
   `docs/REGISTRY.yaml`, `docs/archive/`, `docs/plans/scripts_tools_governance_epic.md`.
10. Ticket contains the disposition table (13 deletions total including the newly-found
    `protocol_validator.py`); no `tools/archive/` directory exists.
11. `pytest --collect-only -q tests/architecture tests/tools` — collected count matches the
    pre-change baseline (captured before starting step 2 of plan.md).
12. `python3 tools/validate_frontmatter.py docs/guidelines/repo_tooling_layout.md --content-type doc`
    passes; `make knowledge-index-update` has been run.

## Baselines to capture before touching files
- `pytest --collect-only -q tests/architecture tests/tools` current count.
- Pass/skip counts for the 7 affected test files, run once before any move.
