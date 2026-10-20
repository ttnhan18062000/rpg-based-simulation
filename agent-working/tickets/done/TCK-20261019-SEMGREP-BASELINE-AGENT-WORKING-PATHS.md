---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261019-SEMGREP-BASELINE-AGENT-WORKING-PATHS
phase: done
date: 2026-10-19
tags: [ai, governance]
---

# TCK-20261019-SEMGREP-BASELINE-AGENT-WORKING-PATHS

## Title
The two Semgrep baseline findings on agent-working paths are resolved: pr-body-lint.yml's checkout is pinned by SHA, and launch.py's exec carries a justified nosemgrep

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
This comes from a finding by platform-planner-u24 (2026-10-19). The new report-only `security-scan.yml` (#665) scanned main
(run 39233931697, SARIF artifact "semgrep") and reported baseline findings. Two are on agent-working-owned paths
(checked with `tools.sessions.route`):

1. `.github/workflows/pr-body-lint.yml:17`: mutable-action-tag (`actions/checkout@v7`). This is a real finding.
2. `tools/sessions/launch.py:516`: dangerous-os-exec-tainted-env-args (`os.execvpe(cmd[0], cmd, {**os.environ, **env})`).
   agent-working-planner triaged it as an accepted risk. It's the user's own local launcher, run by hand. `cmd` comes from the role
   registry plus the user's CLI, the env is the user's own, and there is no network or untrusted input.

platform-planner-u24 owns security-scan.yml and decided the convention: suppressions go in code as
`# nosemgrep: <full rule id>` with a one-line reason, never as a Security-tab dismissal. That way the decision is
reviewable in git.

The suppression records a triage decision that was made before this ticket. It is not a way to make the scan pass: the
scan is report-only.

## Scope
- `pr-body-lint.yml`: `uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1`. This is the same pin
  security-scan.yml uses. Keep the `sparse-checkout` input unchanged.
- `launch.py:516`: add `# nosemgrep: <full rule id>` on the `os.execvpe` line, with the reason on the same line or the
  line above. For example: "local launcher run by hand; cmd from the role registry plus the user's CLI; no untrusted input".
  Take the full rule id from the SARIF (`ruleId`) of the latest main security-scan run, not from memory.

## Out of Scope
- The other findings in the baseline. platform-planner-u24 routed them to asset, testing and lead-planner-u24
  (ci_aseprite_skip_line, test_architecture reports, ci_junit_*, handover_transit, tools/search/Dockerfile).
- Pinning the `@v7` tags in other workflows (test.yml etc. are testing's).
- Any behaviour change in launch.py.

## Acceptance Criteria
1. `git grep -n "uses:" .github/workflows/pr-body-lint.yml` shows only SHA-pinned actions, each with a `# vX.Y.Z` comment.
2. The `os.execvpe` line in launch.py carries `nosemgrep: <full rule id>` and a reason. The rule id is quoted from the
   SARIF in Implementation Notes.
3. If `semgrep` is installed locally, `semgrep --config <the same rulesets security-scan.yml uses>` on the two files reports
   neither finding. Otherwise, the PR's own security-scan run shows both are gone. Record which one in Test Summary.
4. `pytest tests/tools -k "launch or pr_body" -p no:randomly` passes, with the same count as before.

## Related Tickets
None (first security-scan baseline triage).

## Related Docs
- `docs/guides/delivery_process.md` (pr-body-lint)

## Related Stored Artifacts
None.

## Related Code Areas
- `.github/workflows/pr-body-lint.yml`
- `tools/sessions/launch.py` (`main`, the final `os.execvpe`)
- `.github/workflows/security-scan.yml` (read only; platform's)

## Assumptions / Open Questions
- The pr-body-lint workflow must still run on the PR itself. Check that its run on the PR is green.

## Implementation Notes
SARIF `semgrep` artifact of the latest main security-scan run (39367942743), `ruleId` values:
- `yaml.github-actions.security.github-actions-mutable-action-tag.github-actions-mutable-action-tag` at `.github/workflows/pr-body-lint.yml:17`
- `python.lang.security.audit.dangerous-os-exec-tainted-env-args.dangerous-os-exec-tainted-env-args` at `tools/sessions/launch.py:516`
`pr-body-lint.yml` checkout is now pinned to `3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1`. `launch.py` carries a reason line above the `os.execvpe` call and `# nosemgrep: python.lang.security.audit.dangerous-os-exec-tainted-env-args.dangerous-os-exec-tainted-env-args` on it. No behaviour change.

## Test Summary
`semgrep` is not installed locally, so AC 3 rests on the PR's own security-scan run (to be read on the batch PR).
`pytest tests/tools -k "launch or pr_body" -p no:randomly -q`: 116 passed. `git grep -n "uses:" .github/workflows/pr-body-lint.yml` shows one SHA-pinned action with a `# v7.0.1` comment.

## Files Changed
- `.github/workflows/pr-body-lint.yml`
- `tools/sessions/launch.py`

## Completion Summary
The two agent-working-owned baseline findings are addressed in code: a SHA pin and a reviewable nosemgrep suppression with its reason. The scan stays report-only.
