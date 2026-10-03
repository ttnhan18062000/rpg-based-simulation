---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261003-CODE-HEALTH-RESEED-AND-ADVISORY-CI-JOB
artifact_type: investigation
tags: [delivery]
---

# Investigation — TCK-20261003-CODE-HEALTH-RESEED-AND-ADVISORY-CI-JOB

Context scan: `search_docs` (no relevant hit beyond older CI tickets) and `graphify query` (no code-health nodes) first; the facts below come from the follow-up reads.

## Registry and CLI
- `registries/code_health_exceptions.jsonl` has 3617 rows today: ruff 2892, line_count 283, complexipy 384, jscpd 58; none `reviewed`. Seeded on the python-code-craft branch, so src/ changes merged since appear as NEW.
- `python3 -m tools.code_health seed --force` rewrites the registry from a fresh scan and, through `registry.seed_rows(previous=...)`, keeps `reviewed`, `retiring_ticket` and `added_date` for keys that persist (a key is `(file, symbol, tool, rule)`, never a line). Output line: `seeded N rows ...`.
- `check` scans (ruff, complexipy, jscpd via `npx`, line_count), compares with `ratchet.compare` and prints `ratchet.format_report` (NEW / WORSE / improved / gone, then one verdict line). Exit 1 on NEW/WORSE, 2 on unusable tool or registry, else 0. `RatchetResult` holds the findings; the report has no notion of "files this PR changed".
- jscpd runs `npx --yes jscpd@$(JSCPD_VERSION)` (5.4.0) and needs Node and network; transitive deps are unpinned (owner decision: report-only, no lockfile here).

## CI shape
- 15 Python jobs on `setup-uv` (only `tools-a-e` syncs `lint`); `frontend` already uses `actions/setup-node@v4` (node 20), so no new `uses:` string is needed.
- Tests that pin the job set: `tests/static/test_ci_step_summary_reporting.py:450` asserts `set(_jobs().keys()) == expected_job_names` (new name must be added); `tests/static/test_ci_uv_install.py` (`_LINT_JOBS` must include the new job; it runs one locked `uv sync` per Python job); `tests/static/test_ci_narrow_path_filtered_jobs.py` `_OUT_OF_SCOPE_JOBS` lists the jobs it treats as ungated (check whether it must include the new job); `tests/tools/test_ci_workflow_test_coverage.py` reads pytest paths per job, and the new job runs no pytest, so it should be unaffected (confirm by running it).
- `typecheck` is the existing advisory pattern: `continue-on-error: true` on the step with `|| true`.

## Open measurements (done at implementation, not yet)
- Wall time of `make code-health` / `check` under `systemd-run MemoryMax=2G`; it cannot be trusted while the machine is loaded (a knowledge-index job is running, load average above 10). Integration (~324 s) is the longest PR job to compare with.
- Per-tool row counts before and after the reseed.
