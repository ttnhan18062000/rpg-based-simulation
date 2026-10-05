---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261003-CODE-HEALTH-GATES-FLIP-BLOCKING
artifact_type: investigation
tags: [architecture, delivery]
---

# Investigation — TCK-20261003-CODE-HEALTH-GATES-FLIP-BLOCKING

## Facts (measured 2026-10-04 on `origin/main` 053f459e4)
- `python3 -m codebase.health check`: exit 0, "0 new, 0 worse, 6 improved, 4 gone, 3718 unchanged". `python3 -m codebase.gates.mypy_gate`: exit 0. The #319 debt was fixed by perf in #320.
- Improved: `engine/legality.py` I001 (2<3) and PLC0415 (4<5), `perf/scenarios.py` F401 (1<4) and I001 (1<2), `LongRunStabilityHarness.execute_run` complexipy (47<50), `LegalityServiceV2` class-length (584<596). Gone: `validate_result_batch` complexipy, `engine/checkpoint.py` I001, `perf/scenarios.py` PLC0415, `build_metropolis_state` function-length.
- `_cmd_check` returns `1 if result.failed`; `ratchet.compare` treats every tool alike, so jscpd and ast_grep findings fail the check today and only the step's `continue-on-error` hides it.
- `scan._scan_jscpd` runs `npx --yes jscpd@<ver>` through `_run(..., (0,))`; any non-zero exit or missing npx raises `ToolUnavailableError`, which `main` turns into exit 2. `run_scan` loops the tools, so one jscpd failure aborts the scan before the other tools' output is used.
- Other users of the result: `edit_ratchet_hook` and `staged_ratchet` call `ratchet.compare`/`RatchetResult.failed` on ruff-only data; they must keep `failed`'s meaning. `metrics.py` (snapshot) uses `OFFLINE_TOOLS`.
- `seed` and `tighten` share `_findings`/`run_scan`; `tighten` deletes rows with no current finding (guarded only by `--yes`), so a silently skipped jscpd would make its rows "gone" and deletable.

## Decision (planner, 2026-10-04)
jscpd is exempt from exit 2 via a separate `SKIPPABLE_TOOLS`; skipped means "not measured", never "gone"; visible as summary line plus warning annotation; reseed/tighten refuse on any tool failure. Reason: a required check must not depend on npm availability for a tool that is report-only by decision 16.
