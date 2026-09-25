---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260924-DELIVERY-STATUS-TOOL-WORKFLOW-SCOPE
phase: done
date: 2026-09-24
tags: [delivery, testing, documentation]
---

# TCK-20260924-DELIVERY-STATUS-TOOL-WORKFLOW-SCOPE

## Title

`pr_status.py` counts every workflow's runs toward its verdict while its docstring claims it does not

## Status

DONE

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
**Decision: partition (Open Question 1's recommended option), on the evidence in Assumption 1** —
it matches the originating ticket's own Assumption 3 wording ("reported separately") and loses no
information for `TCK-20260924-DELIVERY-CI-TRIAGE-CLASSIFIER` (ticket 5), which can now see a
docs-publish failure exists without it being misread as a code regression. Filter was rejected
because it would silently discard information a downstream consumer might legitimately want.

Identified a run's workflow via the `path` field on each `actions/runs` entry (Open Question 2's
recommendation), compared against `str(workflow_path)` — no extra `gh` fetch needed, matching the
`--workflow-path` value directly (default `.github/workflows/test.yml`).

`compute_pr_status()` now partitions `sha_matching` (runs at the current head SHA, any workflow)
into `applicable` (target workflow only, drives the verdict) and `other_workflow_runs` (everything
else at that SHA, attached to every returned verdict — including `ABSENT` and the early
fetch-failure `UNKNOWN`s, via `_verdict()`'s new default `[]`). Added a third case the original
ticket's scope didn't explicitly enumerate: a head SHA with runs from *only* another workflow (none
yet from the target) is `UNKNOWN`, not `ABSENT` (a run does exist, just not the target's) and not
`FAILING` (the other workflow's conclusion must never vote) — covered by
`test_only_other_workflow_ran_at_current_sha_yields_unknown_not_absent_or_failing`.

Corrected the module docstring's Assumption-3 paragraph to describe partitioning instead of the
filtering it falsely claimed. No change to the five verdict names, the `UNKNOWN`-over-empty rule,
the `ABSENT` disambiguation branches, or the exit-0 contract, per this ticket's Out of Scope.

## Test Summary
- `python3 -m pytest tests/tools/test_delivery_pr_status.py -v` (via the repo's own venv): **32
  passed** — the original 28 (12 of whose fixtures gained a `path` field so they keep matching the
  now-partitioned `applicable` set; none weakened) plus 4 new tests covering AC1–AC3: a failing
  other-workflow run not turning `GREEN`→`FAILING`, the symmetric case (target fails, other
  succeeds, still `FAILING`), the only-other-workflow-ran case (`UNKNOWN`, not `ABSENT`/`FAILING`),
  and `other_workflow_runs` being present-and-empty on ordinary single-workflow verdicts.
- Full regression: `python3 -m pytest tests/tools/ -m "not slow"` — **2937 passed, 25 skipped, 28
  deselected, 1 xfailed, 0 failed** (4 more passed than the prior ticket's close, matching the 4
  new tests added here; no regressions).

## Files Changed
- `tools/delivery/pr_status.py` — `compute_pr_status()` partitions by workflow `path`;
  `_verdict()` gained `other_workflow_runs`; `_print_human()` surfaces it; docstring corrected.
- `tests/tools/test_delivery_pr_status.py` — 12 existing fixtures gained a `path` field; 4 new
  tests added.
- `docs/REGISTRY.yaml` — auto-regenerated as part of Finalize's post-migration self-check; no
  manual content change, unrelated to this ticket's own scope.

## Completion Summary
Fixed the doc/code disagreement: `compute_pr_status()` now partitions `actions/runs` results by
workflow `path` instead of silently letting every workflow at a SHA vote on the verdict. Chose
partition over filter on Assumption 1's own evidence (ticket 5's classifier benefits from seeing
the separated other-workflow data), identified a run's workflow via `path` (no extra fetch) per
Assumption 2, and added a third verdict case (`UNKNOWN` when only a non-target workflow has run at
the current SHA) that the original scope didn't explicitly name but the partition design makes
necessary. Docstring now matches implementation. No change to verdict names, the `UNKNOWN`-over-
empty rule, `ABSENT` branches, or the exit-0 contract — verified unchanged by the untouched
original 28 tests all still passing. `data_runs_clean` is expected to FAIL again on this close for
the same reason as the prior ticket (shared-worktree `data/runs/` content not attributable to this
ticket, and now also explained structurally by `TCK-20260924-DONE-CHECKER-DATA-RUNS-CLEAN-NO-START-TS`,
filed separately, not picked up here) — reported, not routed around.
