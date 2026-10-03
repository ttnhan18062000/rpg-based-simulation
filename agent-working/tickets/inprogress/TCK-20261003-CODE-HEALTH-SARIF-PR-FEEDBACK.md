---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261003-CODE-HEALTH-SARIF-PR-FEEDBACK
phase: open
date: 2026-10-03
tags: [delivery, security]
---

# TCK-20261003-CODE-HEALTH-SARIF-PR-FEEDBACK

## Title
M4b: Changed-line PR feedback through SARIF upload to GitHub code scanning (advisory)

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Owner decision 2026-10-03: PRs get changed-line feedback through SARIF upload to GitHub code scanning, not reviewdog comments. ruff and complexipy emit SARIF; findings already held in the code-health registry must be filtered out so a PR shows only what it introduced. Advisory during the soak.

## Scope
- Produce SARIF for ruff and complexipy on the PR's changed `.py` files, filter out findings that match an existing registry row (same key the ratchet uses), and upload with `github/codeql-action/upload-sarif` pinned by version
- Grant `security-events: write` only on the job that uploads; no other permission change
- May be steps in the `code-health` job from TCK-20261003-CODE-HEALTH-RESEED-AND-ADVISORY-CI-JOB if wall time allows, else its own advisory job
- A small, tested filter in tools/code_health/ (SARIF in, SARIF out)
- Document where agents read results (job summary first, code-scanning tab second) in the environment guide

## Out of Scope
- Any file under src/ (roadmap decision 8.7): no autofix, no reformat, no `# noqa` / `# type: ignore`
- CLAUDE.md, .claude/settings.json, Claude Code hooks, .claude/agents/, .claude/workflows/, .claude/skills/
- Making any check required or blocking (that is TCK-20261003-CODE-HEALTH-GATES-FLIP-BLOCKING, after the soak)
- reviewdog, diff-quality, PR comments
- jscpd and line-count SARIF (no native SARIF; report-only)

## Acceptance Criteria
- [ ] On a PR that adds one new ruff violation in a changed file, code scanning shows exactly that finding and none of the registry's existing rows (demonstrated on the real PR run or a recorded test PR)
- [ ] Unit tests for the SARIF filter cover: matching row filtered, new finding kept, worse-than-row finding kept, malformed SARIF reported not swallowed
- [ ] Only the uploading job has `security-events: write`; a static test asserts it
- [ ] The step cannot fail the PR during the soak
- [ ] Green PR run link recorded
- [ ] `git diff --stat <base>...HEAD` lists no path under src/, none under .claude/, and not CLAUDE.md

## Related Tickets
- TCK-20261003-PYTHON-CODE-CRAFT-GATES-EPIC
- TCK-20261003-CODE-HEALTH-RESEED-AND-ADVISORY-CI-JOB (depends on)

## Related Docs
- docs/plans/codebase_health/python_code_craft_roadmap.md
- docs/plans/codebase_health/python_code_craft_m4_gates_ticket_brief.md
- docs/guidelines/agent_working_environment.md

## Related Stored Artifacts
None.

## Related Code Areas
- .github/workflows/test.yml
- tools/code_health/
- registries/code_health_exceptions.jsonl

## Assumptions / Open Questions
- Depends on the reseed ticket (the filter reads the reseeded registry)
- Security-tagged: workflow permissions change, so the Security-Review phase runs
- Code scanning on a public repo needs no licence; Investigate confirms the repository setting is enabled (owner action if not)
- complexipy SARIF output support and its symbol keys must be confirmed against complexipy 8.0.1

## Implementation Notes
- Filter `tools/code_health/sarif_feedback.py`: runs `ruff check <files> --output-format sarif` and `complexipy <files> -q --output-format sarif` on the PR's changed `src/**/*.py` files, drops every result the registry already holds, and writes one SARIF 2.1.0 file for `upload-sarif`. Per ratchet unit (SARIF results have no identity): a ruff (file, code) group is dropped when its count is at or below the row's ceiling and kept **whole** when above the ceiling or without a row; a complexipy function is dropped when its complexity is at or below its row's ceiling. ruff names some rules by code (`E722`) and others by name (`blind-except`); the name -> code map comes from `ruff rule --all --output-format json` (971 rules) and an unknown id falls back to itself (so `invalid-syntax` matches a registry row of that name). ruff's absolute `file://` uris become repository-relative; a uri outside the repository or with `..` is rejected. Results are capped at 1000 per upload (code scanning accepts 5000 per run) and the omitted count is stated.
- Planner condition B: the job summary line says "N findings not in the baseline in changed files (ruff N in M over-ceiling groups; complexipy N). Dropped as already in the baseline: ... Groups are shown whole: an over-ceiling (file, rule) group includes its older findings, so do not read every finding of such a group as new." The same caveat is in `docs/guidelines/agent_working_environment.md` ("Reading code-health results on a PR", which also gives the read order: job summary first, code-scanning second).
- Planner condition A: when no `src/**/*.py` file changed the filter writes a valid SARIF with one run and an empty `results` array, and the upload step has **no** `hashFiles` guard, so the batch PR (which changes no `src/` file) still exercises the upload, `security-events: write` and code-scanning acceptance. The upload step runs when the filter step's outcome is `success`; if the filter could not run (tool missing or malformed SARIF, or an unusable registry) it writes no SARIF, a "could not run" summary line and warning, and exits 2, so the upload is skipped (an empty upload would wrongly clear existing alerts). Record the upload outcome on the PR run here.
- Planner condition C: the job runs on `pull_request` from the same repository only (`github.event.pull_request.head.repo.full_name == github.repository`), not on push to main or the schedule. A main upload would add a second alert stream; none was added.
- Workflow job `code-health-sarif` ("Code health SARIF (advisory)"): job-level `permissions: {contents: read, security-events: write}`; the repository default token permission is `read` and `test.yml` has no workflow-level `permissions:` block, so no other job changed. `continue-on-error` on the job, the filter step and the upload step. Checkout with `fetch-depth: 0` and `persist-credentials: false`. The only `${{ }}` interpolated into `run:` are the base and head commit SHAs. `github/codeql-action/upload-sarif@2892aa5e19bbd11bc0cff5427e3b750a04d9e3c2 # v4.38.2` (full commit SHA; tag v4.38.2 is annotated and resolves to that commit, checked twice).
- Repository facts (investigation): public repository, so code scanning needs no licence; code-scanning default setup is `not-configured` and there is no analysis yet, which does not block a third-party SARIF upload. Only the first PR run proves acceptance; if the upload is rejected, enabling code scanning is an owner setting (job stays green either way).
- Local end-to-end (planner: recorded, replaces a throwaway src/ PR): scratch root with the real `pyproject.toml` and the real registry plus a copy of `src/engine/kernel.py`: unchanged file -> 0 results (154 ruff and 7 complexipy findings dropped as baseline), wall 0.5 s; the same file with one added bare `except` -> exactly 1 result (`bare-except`, `src/engine/kernel.py`, line 1421), the 154 + 7 still dropped. The `src/` tree was not touched.
- **Security-Review** (`security-reviewer` agent, planner condition D): verdict **PASS WITH FINDINGS**, no Critical or High. Sound: no option or argument injection (path regex `fullmatch` with the `src/` prefix and `.py` suffix, `..` rejected, argv lists, no shell); the trigger is `pull_request` (never `pull_request_target`); the only `${{ }}` in `run:` steps are the base and head commit SHAs; permissions are job-scoped; `persist-credentials: false`; the token is not placed in any env and only the upload action receives it; the upload action is pinned by full SHA. Findings and dispositions:
  1. Medium, **accepted residual risk, documented**: the PR's own `uv.lock`, `pyproject.toml` and `tools/` run in a job that holds `security-events: write` (a PR could add a dependency whose build runs code, or edit `tools/code_health`). Not an escalation: the fork guard means the author already has write access, and the token can only upload code-scanning data and read contents. Recorded in the workflow comment above the job, the module docstring and the environment guide ("do not widen the `if`, for example to `pull_request_target`, without a new security review"). Reviewer's optional defence in depth (generate the SARIF in a `contents: read` job and upload from a second job through an artifact) is not taken now; it would double the jobs for a risk that needs write access to exploit.
  2. Low, **fixed**: `is_file()` followed symlinks, so a `src/x.py` symlink to a file outside the checkout would have been linted. `changed_python_files` now requires a regular file that is not a symlink and resolves inside the checkout (test added).
  3. Low, **fixed**: a tool emitting `message` as a string would have raised `AttributeError` (traceback, exit 1). `parse_sarif` now rejects a malformed `message` or `locations`, and the run also converts `KeyError`/`TypeError`/`AttributeError` into the "could not run" path (exit 2 with a summary line) (tests added).
  4. Low, accepted: up to 300 characters of tool error text go into the job summary (whitespace collapsed, `::warning::` prefix prevents workflow-command injection); Markdown injection affects only the PR's own summary.
  5. Low, accepted: no size limit on the changed list or tool output before the 1000-result cap; bounded by the PR's own changed `src` files and the runner; an oversized argv raises `OSError` and exits 2. Advisory job.
  6. Info: `enable-cache` in a PR job writes only the PR's own cache scope; no poisoning of main. 7. Info: a failed "Paths this PR changed" step leaves no `/tmp/changed.txt`, the run exits 2 and no SARIF is uploaded (fail closed, intended).

- Acceptance criterion "a PR that adds one new ruff violation shows exactly that finding in code scanning" is **left unticked**: demonstrated locally (above) and by `tests/tools/test_code_health_sarif_feedback.py`; its live proof is deferred to the first same-repository PR that touches `src/` during the soak. That check is a soak-review checklist line in `TCK-20261003-CODE-HEALTH-GATES-FLIP-BLOCKING`.

## Test Summary

## Files Changed
`tools/code_health/sarif_feedback.py` (new), `.github/workflows/test.yml` (new job `code-health-sarif`), `docs/guidelines/agent_working_environment.md` (new section "Reading code-health results on a PR" plus the security note), `docs/REGISTRY.yaml`, the flip ticket (soak-review line for the deferred live proof). Tests: new `tests/tools/test_code_health_sarif_feedback.py` (27) and `tests/static/test_ci_code_health_sarif.py` (6).

Edits to existing tests (no assertion weakened):
- `tests/static/test_ci_step_summary_reporting.py`: `_PRE_EXISTING_USES` gains the pinned `github/codeql-action/upload-sarif@2892aa5e...` string, and the pinned job set gains `code-health-sarif`. Reason: a new job with a new `uses:` was added.
- `tests/static/test_ci_uv_install.py`: `_LINT_JOBS` gains `code-health-sarif`. Reason: the job runs ruff and complexipy, so it syncs `lint`.

## Completion Summary
