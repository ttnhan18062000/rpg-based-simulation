---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261021-PYREFLY-ADVISORY-REPORT
phase: done
date: 2026-10-21
tags: [architecture, delivery]
---

# TCK-20261021-PYREFLY-ADVISORY-REPORT

## Title
Pyrefly as an advisory second type-checker opinion: a report-only Code health CI step and Makefile target that never block

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
Owner decision 2026-10-20 (via lead-planner): batch 2 of the code-craft round is a Pyrefly advisory report, report-only, never a gate. This follows the recommendation of `TCK-20261003-TYPE-CHECKER-TRIAL` (`docs/plans/codebase_health/python_code_craft_type_checker_trial.md`): keep mypy + mypy-baseline as the primary, blocking checker; consider Pyrefly as a cheap advisory second opinion after the M4 soak, not as a gate. Pyrefly 1.3.2 ran in about 2 s and 207 MB on `src/`, needs one dependency-free binary wheel, and flagged 100 lines that neither mypy nor basedpyright reported.

## Scope
1. **Pin.** Add `pyrefly==1.3.2` to the `lint` dependency group in `pyproject.toml` and regenerate `uv.lock` (`uv lock`, no other package may move). 1.3.2 is the trial version and is more than two weeks old (released 2026-09-28); 1.4.0 (2026-10-15) is too new. lead-planner reviews the pin line and the `uv.lock` diff before push.
2. **Config.** A `[tool.pyrefly]` table in `pyproject.toml` that matches the mypy scope: `src/` only, the same five excluded V1 packages as `[tool.mypy] exclude`, Python 3.12, missing or untyped imports not reported. Start from the trial's config (trial doc, "Reproduce" section) and record any key that differs, with the reason, in plan.md.
3. **Baseline.** `codebase/baselines/pyrefly_baseline.json`, written by Pyrefly's own `--baseline ... --update-baseline` (no source edits). `pyrefly suppress` is forbidden: it writes inline comments into `src/`.
4. **Report module.** `codebase/gates/pyrefly_report.py`, modelled on `codebase/gates/mypy_gate.py`. It runs Pyrefly against the baseline and prints, and with `--summary-out` writes to the job summary: the Pyrefly version, the count of errors not in the baseline, the baseline size, and the first N new errors with file:line and the error kind. Exit 0 whether or not there are new errors (report-only). Exit 2 only when Pyrefly cannot run or its output cannot be parsed. No `--annotate` (inline PR annotations would make an advisory tool look like a failure).
5. **Makefile.** `typecheck-pyrefly` (runs the report) and `typecheck-pyrefly-baseline-sync` (rewrites the baseline; codebase domain only, on main, alongside `typecheck-baseline-sync`), both in `.PHONY` and with `##` help text that says "advisory, never blocks".
6. **CI.** *Changed 2026-10-21 (codebase-planner, lead-planner approved): a step, not a job.* A separate job would take `test.yml` to 22 jobs, over testing's `MAX_JOB_COUNT = 21` ceiling (#659, `TCK-20261019-CI-PR-WAIT-XDIST-IN-EXISTING-JOBS`), which this domain does not raise. So: one new step "Pyrefly (advisory, never blocks)" at the END of the `code-health` job, after every gating step, with step-level `continue-on-error: true` and `timeout-minutes: 3`, running `python3 -m codebase.gates.pyrefly_report --summary-out "$GITHUB_STEP_SUMMARY"`. No annotations, no new action, exit code ignored, the summary section headed "Pyrefly (advisory, never blocks)". Nothing else in the job changes (name, needs, if, permissions, env, other steps), and the `Type check` job is untouched. A comment on the step says report-only, never a gate, and cites this ticket and the owner decision.
7. **Tests** (`tests/codebase/test_pyrefly_report.py`): summary and count from a recorded Pyrefly JSON fixture; exit 0 with new errors present; exit 2 when the binary is missing or the output is not JSON; the Pyrefly step is last in `code-health`, has `continue-on-error: true` and a timeout, and the job has no job-level `continue-on-error`; there is no `pyrefly` job; the `[tool.pyrefly]` excludes equal `[tool.mypy] exclude`. Update the existing pins that this change trips. Known: `tests/static/test_ci_uv_install.py` (the `lint` group set; the code-health step pin) and `tests/codebase/test_import_contracts.py` (the Import contracts step is now second to last). Find the rest by running the scoped suites, not by guessing.
8. **Parity ledger.** Add `INFRA-TYPE-002` next to `INFRA-TYPE-001` in `docs/parity_ledger/infrastructure.yaml` through `tools/parity_ledger_writer.py`: Pyrefly advisory report, report-only, `test_path` = the new test file.
9. **Docs.** Roadmap `python_code_craft_roadmap.md`: one line in the 6.2 Types row and the M4 row saying Pyrefly runs as an advisory report (this ticket). Trial doc: one `**Outcome:**` line under Recommendation. `docs/guidelines/python_code_standard.md`, if it names the type checkers: one sentence that Pyrefly output is advice, mypy is the gate.
10. **8.11 notice.** This edits `test.yml` and tests that pin CI, which belong to testing (roadmap decision 11). codebase-planner files the notice issue to testing-planner BEFORE the PR opens, at the SHA that carries the CI job. The implementer tells codebase-planner when that SHA exists.

## Out of Scope
- Any blocking use of Pyrefly: required check, ruleset change, ratchet entry, `codebase.health` tool, pre-commit hook. Owner decision: never a gate.
- Any edit under `src/`, including `pyrefly suppress` and inline ignore comments.
- Changing mypy, its baseline, its config or the `Type check` job.
- Triage or fixes of Pyrefly findings (later work, if wanted, is a new ticket).
- basedpyright or `ty` (rejected by the trial).
- Moving to Pyrefly 1.4.x (a later bump once it is two weeks old, same as other tool pins).

## Acceptance Criteria
- `uv lock --check` passes. The `uv.lock` diff adds only `pyrefly` 1.3.2 and its `lint` requires-dev line, and no other package version changes.
- `make typecheck-pyrefly` exits 0 on the branch and prints "0 new" against the freshly written baseline. Record its wall time and peak RSS (from `/usr/bin/time -v`) in plan.md.
- The report exits 0 when given new errors, and 2 when Pyrefly cannot run (tests).
- `.github/workflows/test.yml` has the one new last step in `code-health` with step-level `continue-on-error: true` and `timeout-minutes: 3`; the job count is unchanged (`MAX_JOB_COUNT` untouched), and `Type check` is byte-identical to origin/main and `Code health` differs only by that step and its comment.
- On the PR, the Pyrefly step runs and writes its summary. Every required check is green.
- `INFRA-TYPE-002` exists and the parity ledger schema check does not rise.
- `git diff origin/main -- src/` is empty.
- Scoped suites pass: `tests/codebase`, `tests/static`, `tests/docs`, and `tests/tools` (heavy slot: the Makefile changes).
- The 8.11 notice issue exists before the PR opens.

## Related Tickets
- `TCK-20261003-TYPE-CHECKER-TRIAL` (the recommendation this implements)
- `TCK-20261003-MYPY-BASELINE-ADVISORY` (pattern for the gate module and baseline)
- `TCK-20261004-IMPORT-LINTER-ADOPTION` (pattern for adding a `lint` group tool)
- `TCK-20261020-RATCHET-TIGHTEN-ROUND-2`, `TCK-20261020-CODEBASE-ROADMAP-TRUTH-PASS` (batch 1, merged #706)

## Related Docs
- `docs/plans/codebase_health/python_code_craft_type_checker_trial.md`
- `docs/plans/codebase_health/python_code_craft_roadmap.md` (6.2, M4 row, decisions 10 and 11, decision 7 amendment: M7 waits for this batch)
- `docs/guidelines/python_code_standard.md`

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261003-TYPE-CHECKER-TRIAL/` (if present)
- `agent-working/stored_artifacts/TCK-20261003-MYPY-BASELINE-ADVISORY/`

## Related Code Areas
- `codebase/gates/mypy_gate.py`, `codebase/gates/` (new `pyrefly_report.py`)
- `codebase/baselines/` (new `pyrefly_baseline.json`)
- `pyproject.toml`, `uv.lock`, `Makefile`, `.github/workflows/test.yml`
- `tests/codebase/test_typecheck_gate_configured.py`, `tests/static/test_ci_uv_install.py`
- `docs/parity_ledger/infrastructure.yaml`

## Assumptions / Open Questions
- Assumed: Pyrefly 1.3.2's `--baseline` keeps working with no source edits, as the trial measured. If it does not, stop and report. Do not fall back to `suppress`.
- Assumed: the CI runner's Python is 3.13 while the config targets 3.12, the same as mypy. Note it in plan.md if Pyrefly behaves differently under that split.
- Open: whether the baseline is keyed by line number (churn on every unrelated edit). Measure it on one trivial local edit and record the result. If it churns, the report still never blocks; the plan says how often `typecheck-pyrefly-baseline-sync` runs (with each mypy re-sync).

## Implementation Notes
Staging artifacts moved to `agent-working/stored_artifacts/TCK-20261021-PYREFLY-ADVISORY-REPORT/` (plan.md holds the measurements).
- CI placement changed from a job to a last step in `code-health` (testing's `MAX_JOB_COUNT = 21`, #659; codebase-planner + lead approved); 8.11 notice #708.
- The report passes `--python-interpreter-path sys.executable`: with a bare interpreter Pyrefly reports 6 extra errors.
- Baseline is written by `codebase.gates.pyrefly_report --update-baseline` (Pyrefly's own `--update-baseline`); no `pyrefly suppress`, nothing under `src/`.

## Test Summary
- Pyrefly 1.3.2 on `src/`: 709 errors, 2.45 s wall, 216 MB peak RSS; `make typecheck-pyrefly` prints 0 new against the fresh baseline. Baseline does not churn on a one-line edit.
- `tests/codebase` + `tests/docs` + `tests/static`: 723 passed, 2 skipped, 1 xfailed (one pin fixed afterwards, re-run green); touched files re-run: 131 passed.
- `tests/tools` (lead's slot, MemoryMax=3G, 980 s): 5196 passed, 56 skipped, 1 xfailed.
- Parity schema check: 2844, 0 rose. `git diff origin/main -- src/` empty. `uv lock` diff: pyrefly only.

## Files Changed
pyproject.toml, uv.lock, Makefile, .github/workflows/test.yml (+8/-0), codebase/gates/pyrefly_report.py, codebase/baselines/pyrefly_baseline.json, tests/codebase/test_pyrefly_report.py, tests/codebase/test_import_contracts.py, tests/static/test_ci_uv_install.py, docs/parity_ledger/infrastructure.yaml (INFRA-TYPE-002), roadmap, trial doc, python_code_standard.md, this ticket, stored artifacts, REGISTRY, monitoring shards.

## Completion Summary
Pyrefly 1.3.2 runs as an advisory, never-blocking report: pin, `[tool.pyrefly]`, own baseline, `pyrefly_report` module, two Makefile targets, and one last step in the Code health job with step-level `continue-on-error`. Nothing blocking changed.
