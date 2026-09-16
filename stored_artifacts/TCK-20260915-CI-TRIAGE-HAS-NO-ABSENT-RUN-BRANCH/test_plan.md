# Test Plan — TCK-20260915-CI-TRIAGE-HAS-NO-ABSENT-RUN-BRANCH

- `tests/docs/test_ci_triage_absent_run_branch.py` (new, 8 tests): section exists; the
  `mergeable`/trigger-block check content is present; the re-trigger/force-push/branch-recreation
  prohibition is present; the `git ls-remote`/`headRefOid` disambiguator is present; the general
  principle ("diagnosed differently") is stated, not only the specific `CONFLICTING` case; the
  absent-run branch appears before the failing-job branch (you cannot triage logs for a run that
  never existed); the numbered list stays consistently numbered 1-5 after the insertion (no
  duplicate/skipped number).
- Full `tests/docs/` suite (67 passed, 1 skipped, 1 xfailed — pre-existing, unaffected) re-run for
  regression.
- The handful of `tests/tools/` files that reference "CLAUDE.md" in prose/docstrings (not this
  section's exact content) re-run clean (176 passed) to confirm none of them assert on the exact
  numbering or text this ticket changed.
