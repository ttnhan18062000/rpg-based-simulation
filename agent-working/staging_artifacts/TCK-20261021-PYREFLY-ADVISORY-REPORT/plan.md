---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261021-PYREFLY-ADVISORY-REPORT
artifact_type: plan
tags: [delivery]
---

# Plan — TCK-20261021-PYREFLY-ADVISORY-REPORT

Order (one writer, branch `codebase-pyrefly-advisory`):

1. Pin `pyrefly==1.3.2` in the `lint` group, then `uv lock`. Check the `uv.lock` diff: only pyrefly is added. Send the pin line and the lock diff stat to codebase-planner, who sends them on to lead-planner.
2. Add `[tool.pyrefly]` to `pyproject.toml`, mirroring `[tool.mypy]`: `src/`, the five V1 excludes, Python 3.12, import errors off. Start from the trial doc's config and list any key that differs here, with the reason.
3. Run Pyrefly once under `systemd-run --user --scope -p MemoryMax=2G` (light: about 2 s and 207 MB in the trial). Write `codebase/baselines/pyrefly_baseline.json`. Record the error count, wall time and peak RSS here.
4. Make one trivial local edit (a blank line at the top of a `src/` file), re-run, record whether the baseline churns, then revert the edit. Do not commit it.
5. Write `codebase/gates/pyrefly_report.py`, modelled on `mypy_gate.py`: run, parse the JSON, diff against the baseline (or use Pyrefly's own `--baseline` filtering), print or write the summary. Exit 0 on findings, exit 2 when it cannot run.
6. Add the Makefile targets `typecheck-pyrefly` and `typecheck-pyrefly-baseline-sync`, with `.PHONY` entries and help text.
7. Add the CI step (changed 2026-10-21: a last step in the `code-health` job with step-level `continue-on-error: true` and `timeout-minutes: 3`, not a job, because of testing's `MAX_JOB_COUNT = 21`, #659). Commit, then tell codebase-planner the SHA so the 8.11 notice can be filed before the PR.
8. Write tests (see test_plan.md) and update the tripped pins.
9. Add `INFRA-TYPE-002` via `tools/parity_ledger_writer.py`, plus the doc lines (roadmap 6.2 and the M4 row, the trial outcome, the code standard if it names the checkers).
10. Scoped tests: `tests/codebase`, `tests/static` and `tests/docs` are light; `tests/tools` needs lead's heavy slot. Then the hand closure (standard tier: move the staging artifacts to `stored_artifacts/`), `pr_render`, and the SHA to codebase-planner.

## Measurements (implementer fills)
- Pyrefly errors on `src/` at branch base (origin/main 68850fda1): 709 errors (9 suppressed, 95 warnings not shown), 193,621-byte baseline.
- Wall time / peak RSS: 2.45 s / 215,832 KB (`/usr/bin/time -v`, under `systemd-run --user --scope -p MemoryMax=2G`).
- Baseline churn on a one-line edit: none. Baseline entries carry no line number; a blank line inserted at the top of `src/core/registries.py` gave 0 errors against the baseline, and a re-run of `--update-baseline` was byte-identical (`cmp`). The edit was reverted (`git checkout -- src`). The baseline is only re-synced with each mypy re-sync, not per edit.
- Config keys that differ from the trial: `project-includes`/`project-excludes` are repo-relative globs in `[tool.pyrefly]` (the trial used absolute clone paths); `search-path = ["."]` (the clone root); `python-version = "3.12"` (the trial used 3.11; matches `[tool.mypy]` since the 2026-10-09 floor change); `python-interpreter-path` is not in the config, the report passes `--python-interpreter-path sys.executable` instead; `ignore-missing-imports = ["*"]` is unchanged.
- Interpreter dependence: with a bare interpreter (no project dependencies) Pyrefly reports 6 extra errors, so the result depends on the environment it resolves imports in. That is why `pyrefly_report` passes the running interpreter; `make` uses `$(PYTHON3)` and CI an activated `uv sync` environment.
- CI placement: a separate job would make test.yml 22 jobs, over the `MAX_JOB_COUNT = 21` ceiling that testing set in #659. Not raised (testing's ratchet). Decision (codebase-planner, lead approved): one last step in `code-health`, step-level `continue-on-error: true`, `timeout-minutes: 3`, no annotations.
