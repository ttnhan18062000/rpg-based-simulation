---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260924-DELIVERY-STATUS-TOOL-WORKFLOW-SCOPE
phase: open
date: 2026-09-24
tags: [delivery, testing, documentation]
---

# TCK-20260924-DELIVERY-STATUS-TOOL-WORKFLOW-SCOPE

## Title

`pr_status.py` counts every workflow's runs toward its verdict while its docstring claims it does not

## Status

OPEN

## Tier

hotfix

## Type

bug

## Priority

P1

## Request Summary

`tools/delivery/pr_status.py` (shipped by `TCK-20260924-DELIVERY-STATUS-TOOL` at `ed95e92d4`) has a
doc/code disagreement in its verdict scoping.

Its module docstring states:

> "`deploy-docs.yml` runs are never in scope, since this module only ever reasons about the single
> workflow file it is pointed at (ticket Assumption 3)."

**The code does no such filtering.** `compute_pr_status()` queries
`gh api repos/{owner}/{repo}/actions/runs?head_sha=<sha>` — which is repo-wide across *all*
workflows — and then filters the result on `head_sha` alone:

```python
applicable = [r for r in all_runs if r.get("head_sha") == head_sha]
```

`--workflow-path` / `DEFAULT_WORKFLOW_PATH` is consumed **only** by
`workflow_covers_branch_via_push()` inside the `ABSENT` reason branch. It never narrows the run set
that produces `GREEN` / `PENDING` / `FAILING`. Any run from any workflow at that SHA therefore votes
on the verdict, and a `failure` conclusion from a non-test workflow yields `FAILING` for a PR whose
code checks are green.

The originating ticket's **Assumption 3** asked this exact question and recorded a recommendation:

> "Whether `deploy-docs.yml` runs should count toward a PR's verdict or be reported separately.
> Recommend separately: a docs-publish failure is not a code regression."

Neither resolution was implemented — the code does the third thing (silently count them), and the
docstring asserts the first was done.

## Scope

- Decide and implement one scoping rule, then make the docstring state what the code actually does.
  The two defensible options (pick one; see Open Questions):
  1. **Filter** `applicable` to runs belonging to the workflow named by `--workflow-path`, so
     non-target workflows cannot vote on the verdict at all.
  2. **Partition** — keep the target workflow's runs as the verdict source, and report other
     workflows' runs at that SHA in a separate `other_workflow_runs` field of the result dict,
     matching Assumption 3's "reported separately" recommendation.
- Add the missing test coverage: a fixture where the SHA carries runs from **two** workflows, one
  passing and one failing, asserting the verdict reflects only the intended scoping rule. No
  existing test in `tests/tools/test_delivery_pr_status.py` exercises more than one workflow.
- Correct the module docstring's Assumption 3 paragraph to match the implemented behaviour.

## Out of Scope

- Any change to the five verdict names, the `UNKNOWN`-over-empty-result rule, the `ABSENT`
  disambiguation branches, or the advisory/exit-0 contract — all verified correct and must not
  regress.
- Reading the repo's configured required-status-checks list. Assumption 2's "every check that ran
  completed successfully" definition stands unchanged.
- Re-enabling `deploy-docs.yml`. That is `TCK-20260916-REENABLE-DOCS-PAGES-PUBLISHING`'s call, and
  this ticket must not depend on its outcome either way.

## Acceptance Criteria

1. The run set that produces `GREEN`/`PENDING`/`FAILING` is scoped by an explicit, tested rule —
   not by `head_sha` alone.
2. A run from a workflow other than the one `--workflow-path` names cannot, on its own, turn a
   verdict `FAILING`.
3. A test fixture supplies runs from two distinct workflows at one head SHA and asserts the verdict.
4. The module docstring's Assumption 3 paragraph describes the implemented behaviour, with no claim
   the code does not support.
5. All 28 existing tests in `tests/tools/test_delivery_pr_status.py` still pass unchanged, except
   any whose fixture must gain a workflow identifier — those may be updated, never weakened.
6. The tool remains read-only and exits 0 for every verdict.

## Related Tickets

- `TCK-20260924-DELIVERY-STATUS-TOOL` — shipped the defect; closed at `ed95e92d4`.
- `TCK-20260924-EPIC-GITHUB-DELIVERY-PROCESS` — parent epic.
- `TCK-20260924-DELIVERY-CI-TRIAGE-CLASSIFIER` — ticket 5, consumes this module's payload. It is
  the reason this is worth fixing now rather than later: a classifier built on a payload whose
  scope is wrong inherits the wrongness.
- `TCK-20260916-DISABLE-DOCS-PAGES-DEPLOY-WORKFLOW` — why the defect is latent today.
- `TCK-20260916-REENABLE-DOCS-PAGES-PUBLISHING` — queued; restoring a `deploy-docs.yml` trigger is
  the most likely path for this to stop being latent.

## Related Docs

- `docs/plans/agent_infrastructure/github_delivery_process/plan.md` §3.7 — the status-tool design.
- `CLAUDE.md` — "CI Failure Triage", the prose this module encodes.

## Related Stored Artifacts

- `stored_artifacts/TCK-20260924-DELIVERY-STATUS-TOOL/{investigation,plan,test_plan}.md`

## Related Code Areas

- `tools/delivery/pr_status.py` — `compute_pr_status()`, `_verdict_from_applicable_runs()`
- `tests/tools/test_delivery_pr_status.py`
- `.github/workflows/test.yml`, `.github/workflows/deploy-docs.yml`

## Assumptions / Open Questions

1. **Filter vs. partition (Scope options 1 and 2).** Partition matches Assumption 3's own wording
   ("reported separately") and loses no information; filter is simpler and smaller. The
   recommendation is **partition**, because ticket 5's classifier can then see a docs-publish
   failure exists without misreading it as a code regression — but either satisfies the acceptance
   criteria, and the implementer should pick on the evidence and say which and why.
2. **How to identify a run's workflow.** The `actions/runs` payload carries both `workflow_id` and
   `path` (e.g. `.github/workflows/test.yml`). `path` matches `--workflow-path` directly and needs
   no extra fetch; `workflow_id` would. Prefer `path` unless it proves unreliable.
3. **Severity is latent, not live.** `deploy-docs.yml` is currently `workflow_dispatch:`-only
   (`TCK-20260916-DISABLE-DOCS-PAGES-DEPLOY-WORKFLOW`, 2026-09-16), so it produces no PR-head-SHA
   runs today, and `test.yml` is the only workflow that does. This is filed as a real defect rather
   than a nit because the docstring is false *now*, the test gap is real *now*, and the behaviour
   becomes live the moment a second workflow triggers on a PR SHA — including via a manual
   `workflow_dispatch` against a branch. It is not filed as a live production break.

## Implementation Notes

_To be filled during implementation._

## Test Summary

_To be filled during implementation._

## Files Changed

_To be filled during implementation._

## Completion Summary

_To be filled during implementation._
