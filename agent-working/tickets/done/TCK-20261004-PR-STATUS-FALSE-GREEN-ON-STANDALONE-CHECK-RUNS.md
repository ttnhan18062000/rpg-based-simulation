---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261004-PR-STATUS-FALSE-GREEN-ON-STANDALONE-CHECK-RUNS
phase: done
date: 2026-10-04
tags: [ai, process-improvement, governance]
---

# TCK-20261004-PR-STATUS-FALSE-GREEN-ON-STANDALONE-CHECK-RUNS

## Title
`tools/delivery/pr_status.py` reports GREEN while a required standalone check run (`ruff`) is failing

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Reported by `rpg-feature-planning` and **reproduced here** (2026-10-04, PR #291, head `65731e0c9b72fa5258a41234884f2ef238fda10b`, state OPEN, mergeable): `python3 tools/delivery/pr_status.py --pr 291` prints `verdict: GREEN`, `reason: all checks completed successfully against 65731e0c...`, while `gh pr checks 291` lists `ruff fail` among 21 contexts (`complexipy` passes). The false GREEN was already relayed once as fact to another session; the user caught it.

Cause, confirmed from the code (`compute_pr_status`, lines 295-349): the only CI source is `gh api repos/{owner}/{repo}/actions/runs?head_sha=<sha>`, partitioned to the one target workflow path. Check runs contributed outside that workflow (a different app, or code-scanning) are never read, so they cannot turn the verdict red. This is the second false-green class on this tool (the first: a TLS-blocked poll with no positive completion signal), and the standing lesson applies at a new layer: the examined set must be complete, and an unevaluated context must never read as success.

## Scope
- Enumerate **all** contexts for the head SHA: `commits/<sha>/check-runs` (paginated, all pages) plus the combined commit status (`commits/<sha>/status`). A pagination or fetch failure is UNKNOWN, never an empty list (reuse `_gh_json`'s error-before-parse rule).
- Verdict rules: any context with a failing conclusion (`failure`, `timed_out`, `cancelled`, `action_required`, `startup_failure`) -> FAILING naming it; any non-completed context -> PENDING; GREEN only if every context completed with `success`, `neutral` or `skipped` **and** the target workflow's own runs (existing logic) agree. Keep the existing UNKNOWN/ABSENT branches.
- Completeness assertion: print the count of contexts examined and, where the repo's required checks can be read (branch rules or `gh pr checks --required`), treat a required context absent from the examined set as not-green (UNKNOWN), not as green. If required checks cannot be read, say so in the output.
- Cross-check: when `gh pr checks <pr> --json name,state` is available, any context it reports as failing that the tool did not see must make the verdict UNKNOWN or FAILING (defence in depth against a third enumeration gap).
- Failure detail: for a failing standalone check run, fetch `check-runs/<id>/annotations` (the code-scanning alerts query was reported empty for the same failure; do not rely on it) and list the first annotations.
- Docs: update `docs/guides/delivery_process.md` "CI Failure Triage" so it no longer implies the tool covers only workflow jobs, and state the completeness rule. Add a mechanism-registry check per the closing advisory if it applies.

## Out of Scope
- Changing which checks are required, CI workflow files, merging or any write call to GitHub. The tool stays read-only and advisory; `gh pr checks` remains ground truth for humans.

## Acceptance Criteria
1. A frozen minimal fixture shaped like #291 (21 contexts; one standalone check run `ruff` with conclusion `failure`, the target workflow's runs all green) yields FAILING naming `ruff`; before the fix the same fixture yields GREEN (positive control recorded in the ticket).
2. A required context absent from the examined set yields UNKNOWN, not GREEN; a paginated second page containing a failure is seen.
3. A fetch error or malformed payload on the check-runs or status endpoint yields UNKNOWN (never GREEN, never an empty pass).
4. A pending standalone check run yields PENDING; `skipped`/`neutral` do not block GREEN.
5. Existing tests for the workflow-scoping, TLS-block and ABSENT cases stay green and unchanged in meaning.
6. Re-run against PR #291 (while it still has the failing `ruff`) or an equivalent live PR, output pasted into the ticket. Scoped tests (`tests/tools/` pr_status tests) green; docs and `docs/REGISTRY.yaml` regenerated.

## Related Tickets
- The tool's origin ticket and the TLS-block false-green ticket (find via `tools/delivery/pr_status.py` module docstring and memory `project_ci_poll_tls_block_false_green`)

## Related Docs
- `tools/delivery/pr_status.py` (module docstring), `docs/guides/delivery_process.md` ("CI Failure Triage")

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261004-PR-STATUS-FALSE-GREEN-ON-STANDALONE-CHECK-RUNS/` (plan, investigation, test_plan)

## Related Code Areas
- `tools/delivery/pr_status.py`, its tests, `docs/guides/delivery_process.md`

## Assumptions / Open Questions
- The code-scanning alerts query returning empty while annotations return four is a peer observation, not verified here; the ticket avoids depending on either by using the annotations endpoint, and says so.
- Reading required checks may need a ruleset or branch-protection API that this account cannot access; the fallback (state that required checks are unreadable and keep the all-contexts rule) is acceptable.

## Implementation Notes
Draft by `agent-working-design`, 2026-10-04, from a relayed and reproduced report. Activated and implemented 2026-10-04 (hand-orchestrated). `_evaluate_contexts` runs after the workflow verdict: `commits/<sha>/check-runs` and `commits/<sha>/status` paginated by hand (`gh api --paginate` emits concatenated JSON documents, not one parseable value; short/over-cap pagination is an error), cross-check and required-check read via `gh pr checks` **text** output (gh 2.45 has no `--json` for it; parsed regardless of exit code because it exits 1 while anything fails or pends). Check runs belonging to another workflow's run (details_url run id) keep the existing "reported separately, does not vote" rule, including in the gh cross-check. `FAILURE_CONCLUSIONS` gained `startup_failure`.

Verified live (AC1/AC6): replaying PR #291's reported head `65731e0c9b72` against the real GitHub API with only `pr view` overridden: **old code GREEN, new code FAILING** naming `ruff (check-run)` with annotations (`src/ai/goals/scorers.py:105`, "`import` should be at the top-level of a file"). Positive control in tests: the same 21-context fixture read through the workflow-runs view alone is GREEN.

Test change to flag: `test_no_git_or_gh_mutating_command_ever_issued` flagged the substring `commit` and so rejected the read endpoint `commits/<sha>/check-runs`; for `gh api` calls it now asserts no write flag (`-X/--method/-f/-F/--field/--raw-field/--input`) instead, substring check unchanged for all other commands. The fake runner gained default empty responses for the new calls so older tests keep their meaning.

## Test Summary
`tests/tools/test_delivery_pr_status.py`: 51 pass (32 existing unchanged in meaning, 19 new covering AC1-AC4 plus status, cross-check, other-workflow and failing-plus-standalone cases).

## Files Changed
- `tools/delivery/pr_status.py`, `tests/tools/test_delivery_pr_status.py`
- `docs/guides/delivery_process.md`

## Completion Summary
Implemented and verified live; closed in PR #316. Residual: required checks were unreadable on this repo's branches (no branch protection), so the required-check completeness branch is covered by tests only, not live.
