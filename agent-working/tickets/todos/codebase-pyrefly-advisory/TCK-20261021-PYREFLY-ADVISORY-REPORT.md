---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261021-PYREFLY-ADVISORY-REPORT
phase: open
date: 2026-10-21
tags: [architecture, delivery]
---

# TCK-20261021-PYREFLY-ADVISORY-REPORT

## Title
Pyrefly as an advisory second type-checker opinion: a report-only CI job and Makefile target that never block

## Status
OPEN

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
6. **CI.** A new job `pyrefly-advisory` named "Pyrefly (advisory)" in `.github/workflows/test.yml`: `continue-on-error: true` at job level, `timeout-minutes: 10`, the same checkout and setup-uv pins as the `Type check` job, syncing the `lint` group, running `python3 -m codebase.gates.pyrefly_report --summary-out "$GITHUB_STEP_SUMMARY"`. It is NOT added to the required checks, and it does not touch the `Type check` or `Code health` jobs. A header comment says report-only, never a gate, and cites this ticket and the owner decision.
7. **Tests** (`tests/codebase/test_pyrefly_report.py`): summary and count from a recorded Pyrefly JSON fixture; exit 0 with new errors present; exit 2 when the binary is missing or the output is not JSON; the CI job has job-level `continue-on-error: true` and no step without it fails the job; the job name is not "Type check" or "Code health"; the `[tool.pyrefly]` excludes equal `[tool.mypy] exclude`. Update the existing pins that this change trips. Known: `tests/static/test_ci_uv_install.py` (the `lint` group set and `_LINT_JOBS`). Find the rest by running the scoped suites, not by guessing.
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
- `.github/workflows/test.yml` has the `pyrefly-advisory` job with job-level `continue-on-error: true`. `Type check` and `Code health` are byte-identical to origin/main.
- On the PR, "Pyrefly (advisory)" runs and writes its summary. Every required check is green.
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
Staging artifacts are in `agent-working/staging_artifacts/TCK-20261021-PYREFLY-ADVISORY-REPORT/` (written by codebase-planner; the implementer updates them as the work changes).

## Test Summary

## Files Changed

## Completion Summary
