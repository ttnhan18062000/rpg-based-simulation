---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260913-CI-WORKFLOW-STALE-DIAGNOSTICS-PATH-REFERENCE
phase: done
date: 2026-09-13
tags: [testing]
---

# TCK-20260913-CI-WORKFLOW-STALE-DIAGNOSTICS-PATH-REFERENCE

## Title
`.github/workflows/test.yml`'s "Unit · infra / observability" job hardcodes `tests/unit/diagnostics` as a pytest path argument — broke when that directory was deleted

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
Real CI regression caught on PR #175 (`worker-utilization-degraded-mistrigger-batch`, head
`9bc2d286328a4197d4989cb33019a7aa963d32da`) after
`TCK-20260912-OPTIMIZATION-DIAGNOSTICS-DEAD-CODE-DELETION` deleted `tests/unit/diagnostics/` in
full (its only real test file plus the now-hollow `__init__.py`). That ticket's own zero-references
grep only checked Python-level imports of `DeveloperDiagnostics`/`DiagnosticIssue` — it did not
check whether the test **directory path itself** was referenced anywhere outside Python source,
and it was: the `unit-infra` job's `Run` step (`.github/workflows/test.yml:160-179`) passes
`tests/unit/diagnostics` as a literal positional pytest path argument.

**Root-caused via direct log/annotation pull, not assumed**: the job failed in 28s with "Process
completed with exit code 4" (pytest's own usage-error exit code). Locally, `pytest
tests/unit/diagnostics` returns exit 5 ("no tests collected") because this workspace's own
`__pycache__` directory (a local, untracked leftover) still makes the path exist on disk — but a
genuinely clean CI checkout has no such directory at all once the deletion is on the branch, so
pytest hits "file or directory not found" (exit 4) instead. Confirmed this distinction directly
rather than assuming the local exit code matched CI's.

**Correction (same investigation, caught by a second real CI failure on re-push, not a separate
finding)**: the sibling `Base branch test collection` step (`test.yml:190-212`) also references
`tests/unit/diagnostics`. It was initially reasoned to be correct as-is, since it runs against
`/tmp/base-checkout` (the PR's base branch, `origin/main`, which still has the directory) with
`|| true` making it non-fatal — that reasoning was **wrong**, caught by a fresh CI run on the very
next push: `tests/static/test_ci_step_summary_reporting.py::test_all_fastlane_jobs_have_base_branch_collect_only_step`
asserts, by design, that a job's `Run` step path list and its own base-branch-collect-only step's
path list must be **identical sets** (so the collect-only diff genuinely reflects the same test
scope the head run measures) — not merely "each individually valid for the branch it runs against."
Removed `tests/unit/diagnostics` from this step too. The wrong reasoning is left visible here
rather than silently corrected, since the mistake itself (assuming two path lists could differ
because each is individually defensible, without checking whether anything enforces they must
match) is worth a future reader seeing, not just the final fix.

## Scope
- Remove `tests/unit/diagnostics` from the `unit-infra` job's `Run` step path list
  (`.github/workflows/test.yml:160-179`) — the only real reference to a now-deleted path.
- Remove `tests/unit/diagnostics` from the same job's `Base branch test collection` step
  (`test.yml:190-212`) too — required for the two path lists to stay identical sets, per
  `test_all_fastlane_jobs_have_base_branch_collect_only_step`'s own real invariant (initially
  missed; see Request Summary's correction).
- Confirm no other CI-workflow or `Makefile` reference to the deleted `diagnostics.py`/
  `memory_limits.py` modules or their test paths exists.

## Out of Scope
- Re-litigating `TCK-20260912-OPTIMIZATION-DIAGNOSTICS-DEAD-CODE-DELETION`'s own disposition — the
  deletion itself is correct; this ticket only fixes the CI references it broke.

## Acceptance Criteria
- [x] `tests/unit/diagnostics` removed from both the `unit-infra` job's `Run` step and its own
      `Base branch test collection` step's pytest invocations.
- [x] Grep confirms no other CI-workflow/Makefile reference to the deleted paths/modules.
- [x] `tests/static/test_ci_step_summary_reporting.py::test_all_fastlane_jobs_have_base_branch_collect_only_step`
      passes (the real invariant that was missed on the first pass).
- [x] CI re-run on the same PR head confirms both the `unit-infra` and `Architecture / docs /
      static` jobs pass.

## Related Tickets
- `TCK-20260912-OPTIMIZATION-DIAGNOSTICS-DEAD-CODE-DELETION` (the deletion that caused this —
  correct disposition, incomplete verification)

## Related Docs
None.

## Related Stored Artifacts
None — hotfix tier, no staging artifacts required.

## Related Code Areas
- `.github/workflows/test.yml` (`unit-infra` job)

## Assumptions / Open Questions
None.

## Implementation Notes
**First pass**: caught during CI Failure Triage on PR #175 — pulled the real check-run annotation
(`gh api repos/.../check-runs/{id}/annotations`) rather than assuming root cause from the job name
or a guess, per standing CI-triage discipline. The annotation ("Process completed with exit code
4") plus a direct local repro (confirming the *different* exit code a genuinely missing path
produces vs. a locally-lingering-but-empty one) confirmed the exact mechanism before editing
anything. Removed the one reference from `unit-infra`'s `Run` step, reasoned (wrongly, see below)
that the sibling base-branch-collection step's own reference was fine to leave.

**Second pass, after re-push**: a fresh CI run surfaced a NEW failure,
`Architecture / docs / static`, that hadn't failed on the first push. Same discipline applied —
pulled the annotation, then reproduced locally rather than guessing. The real cause:
`test_all_fastlane_jobs_have_base_branch_collect_only_step` asserts a job's `Run` step path set and
its own base-branch-collect-only path set must be identical — the first pass's "each is
individually correct for the branch it targets" reasoning didn't check whether anything actually
required the two lists to match, and something did. Removed the same path from the
base-branch-collection step too; re-verified `tests/static/` in full (249 passed) before
considering this closed.

## Test Summary
- Local repro: `pytest tests/unit/diagnostics` returns exit 5 locally (path exists, empty, due to a
  leftover `__pycache__`) vs. the real CI exit 4 (path genuinely absent on a clean checkout) — same
  underlying cause, different local-vs-CI presentation, confirmed rather than assumed identical.
- `tests/static/test_ci_step_summary_reporting.py::test_all_fastlane_jobs_have_base_branch_collect_only_step`
  — failed before the second fix, passes after.
- `pytest tests/architecture tests/docs tests/integrity tests/static tests/refactor` — 249 passed,
  2 skipped, 1 deselected, 2 xfailed (full local reproduction of the `Architecture / docs / static`
  CI job, clean).
- CI re-run on PR #175 after both fixes: `unit-infra` and `Architecture / docs / static` both pass.

## Files Changed
- `.github/workflows/test.yml` — removed `tests/unit/diagnostics` from both `unit-infra`'s `Run`
  step path list and its own `Base branch test collection` step's path list.

## Completion Summary
A real CI regression caused by `TCK-20260912-OPTIMIZATION-DIAGNOSTICS-DEAD-CODE-DELETION`'s own
incomplete verification (checked Python-level references, not CI-workflow path references).
Root-caused via real logs/annotations across two passes, not assumed either time — the first pass's
own "the other reference is fine to leave" reasoning turned out to be wrong, caught by a real CI
invariant test on the next push rather than by re-checking it myself first. Both stale references
now removed; the underlying consistency invariant they violated is independently tested and green.
