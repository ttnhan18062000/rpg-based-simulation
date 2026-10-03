---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261003-CODE-HEALTH-SARIF-PR-FEEDBACK
artifact_type: plan
tags: [delivery, security]
---

# Plan — TCK-20261003-CODE-HEALTH-SARIF-PR-FEEDBACK

Same branch (`python-code-craft-gates`), after tickets 1 and 2. Security-tagged: a Security-Review pass (the `security-reviewer` agent) runs on the diff before the ticket commit. No `src/`, `.claude/`, `CLAUDE.md` edits.

1. **Filter module** `tools/code_health/sarif_feedback.py` (not src/), pure functions plus a CLI `python3 -m tools.code_health.sarif_feedback --changed FILE --out SARIF [--summary-out PATH] [--annotate]`:
   - `changed_python_files(paths)`: keep `src/**/*.py` that still exist, sorted, deduplicated.
   - `filter_sarif(sarif, rows, rule_codes, root)`: for each run, drop results the registry already holds (rules above), normalise ruff uris to repository-relative, keep the rest; malformed SARIF raises `SarifError` (never swallowed); results capped at 1000 with the truncation counted.
   - CLI: runs `ruff check <files> --output-format sarif` and `complexipy <files> -q --output-format sarif --output` on the changed files, loads the registry, merges the two runs into one SARIF 2.1.0 file (`--out`), appends a job-summary section (kept/dropped per tool, truncation) to `--summary-out`, with `::warning::` for kept findings with `--annotate`. If a tool cannot run or its SARIF is malformed: write a "could not run" summary line and warning, write no SARIF, exit 2 (the ticket 1/2 rule: a broken tool never looks like a clean pass). No changed `src` Python files: exit 0, no SARIF, one-line summary.
2. **Workflow**: a new job `code-health-sarif` ("Code health SARIF (advisory)") in `test.yml`:
   - `if: github.event_name == 'pull_request' && github.event.pull_request.head.repo.full_name == github.repository` (same-repo PRs only; forks are read-only and would fail).
   - `permissions: { contents: read, security-events: write }` at **job level only**; no workflow-level `permissions:` and no change to any other job.
   - `continue-on-error: true` on the job and the steps; checkout `fetch-depth: 0`; setup-uv + `uv sync --locked --no-install-project` (lint kept); changed-files step as in `code-health`; the filter step; `github/codeql-action/upload-sarif@2892aa5e19bbd11bc0cff5427e3b750a04d9e3c2 # v4.38.2` with `sarif_file`, `category: code-health`, guarded by `hashFiles(...) != ''`. A separate job (not steps in `code-health`) so the write permission is limited to the one job that uploads.
3. **Tests**: `tests/tools/test_code_health_sarif_feedback.py` (matching row filtered; new finding kept; worse-than-row finding kept; ruff name -> code mapping; relative uris; cap and truncation count; malformed SARIF raises `SarifError` and the CLI reports could-not-run with exit 2; no changed files; tool unavailable); static tests in `tests/static/test_ci_uv_install.py` or a new `tests/static/test_ci_code_health_sarif.py`: only the uploading job has `security-events: write`, there is no workflow-level `permissions:` write, the job is fork-guarded, advisory, and the action is pinned to a 40-character SHA. Edits to existing tests, each listed with its reason: `_PRE_EXISTING_USES` gains the pinned `upload-sarif` string; `_LINT_JOBS` gains the new job; the pinned job set gains `code-health-sarif`.
4. **Docs**: `docs/guidelines/agent_working_environment.md`: where agents read results (job summary first, code-scanning tab second), what the filter does and does not claim, fork behaviour; `python_code_standard.md` one line.
5. **Security-Review**: spawn the `security-reviewer` agent on the diff (injection through file names in the changed list, path traversal in uri handling, permissions scope, action pinning, fork guard, untrusted PR content in `run:` steps). Record its verdict and any change in the ticket.
6. **Risk to record**: the upload needs code scanning to accept third-party SARIF on this repository; only the first PR run proves it. If the upload step fails with a repository-setting error, that is an owner action (enable code scanning), recorded in the ticket, and the job still stays green (advisory).
7. **Close** in the batch closure commit after the green PR run (run link; the acceptance criterion "one new ruff violation shows exactly that finding" needs a recorded test PR or the PR run itself; if the batch PR adds no `src` change the demonstration is a throwaway test PR the owner approves, otherwise the criterion is recorded as not demonstrable on this PR).

## Scope guards
No check becomes required or blocking. No registry row is changed. jscpd and line_count have no SARIF and are not part of this. Nothing under `src/`.

## Acceptance-criteria map
| Criterion | Step |
|---|---|
| New ruff violation shows exactly that finding, none of the registry's rows | 1 (rules), 2, 7 |
| Filter unit tests: matching row, new, worse, malformed | 3 |
| Only the uploading job has `security-events: write`, static test | 2, 3 |
| Cannot fail the PR | 2 |
| Green PR run link | 7 |
| No src/.claude/CLAUDE.md in diff | scope guards |

## Questions for the planner
- The "exactly that finding" criterion cannot be proven on the batch PR itself (it changes no `src/` file). OK to demonstrate it on a throwaway same-repo PR that adds one violation to a `src/` file, opened and closed by the owner's say-so, or to accept the unit tests plus a recorded local run?
- Pin by full commit SHA (with the version in a comment) instead of the tag: OK?
