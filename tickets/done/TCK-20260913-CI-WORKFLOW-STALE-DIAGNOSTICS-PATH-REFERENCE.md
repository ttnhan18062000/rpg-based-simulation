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

The sibling `Base branch test collection` step (`test.yml:190-212`) also references
`tests/unit/diagnostics`, but runs against `/tmp/base-checkout` (a checkout of the PR's base branch,
`origin/main`, which still has the directory) with `|| true` making it non-fatal either way — left
untouched, it is correct as-is.

## Scope
- Remove `tests/unit/diagnostics` from the `unit-infra` job's `Run` step path list
  (`.github/workflows/test.yml:160-179`) — the only real reference to a now-deleted path.
- Confirm no other CI-workflow or `Makefile` reference to the deleted `diagnostics.py`/
  `memory_limits.py` modules or their test paths exists.

## Out of Scope
- The `Base branch test collection` step's own reference to `tests/unit/diagnostics`
  (`test.yml:190-212`) — correct as-is, operates against the base branch's own (unaffected)
  checkout.
- Re-litigating `TCK-20260912-OPTIMIZATION-DIAGNOSTICS-DEAD-CODE-DELETION`'s own disposition — the
  deletion itself is correct; this ticket only fixes the CI reference it broke.

## Acceptance Criteria
- [x] `tests/unit/diagnostics` removed from the `unit-infra` job's pytest invocation.
- [x] Grep confirms no other CI-workflow/Makefile reference to the deleted paths/modules beyond the
      intentionally-untouched base-branch-collection step.
- [x] CI re-run on the same PR head confirms the job passes.

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
Caught during CI Failure Triage on PR #175 — pulled the real check-run annotation
(`gh api repos/.../check-runs/{id}/annotations`) rather than assuming root cause from the job name
or a guess, per standing CI-triage discipline. The annotation ("Process completed with exit code
4") plus a direct local repro (confirming the *different* exit code a genuinely missing path
produces vs. a locally-lingering-but-empty one) confirmed the exact mechanism before editing
anything. Removed the one real stale reference; left the base-branch-collection step's own
reference untouched since it targets an unaffected checkout.

## Test Summary
Local repro: `pytest tests/unit/diagnostics` returns exit 5 locally (path exists, empty, due to a
leftover `__pycache__`) vs. the real CI exit 4 (path genuinely absent on a clean checkout) — same
underlying cause, different local-vs-CI presentation, confirmed rather than assumed identical.
CI re-run on PR #175 after the fix: `unit-infra` job passes.

## Files Changed
- `.github/workflows/test.yml` — removed `tests/unit/diagnostics` from `unit-infra`'s `Run` step
  path list.

## Completion Summary
A real CI regression caused by `TCK-20260912-OPTIMIZATION-DIAGNOSTICS-DEAD-CODE-DELETION`'s own
incomplete verification (checked Python-level references, not CI-workflow path references).
Root-caused via real logs/annotations, not assumed. Fixed by removing the one stale reference;
confirmed the sibling base-branch-collection reference is correct as-is and left it untouched.
