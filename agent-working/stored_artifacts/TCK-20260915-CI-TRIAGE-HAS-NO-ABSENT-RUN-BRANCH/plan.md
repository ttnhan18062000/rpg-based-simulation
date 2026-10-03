# Plan — TCK-20260915-CI-TRIAGE-HAS-NO-ABSENT-RUN-BRANCH

1. Verify the core claim by reading `.github/workflows/test.yml`'s own trigger block directly
   (done — investigation.md).
2. Obtain direct user authorization before touching CLAUDE.md (hard AC — not supplied by the
   batch-level "yes" or the peer's own report).
3. Add a new item 1 to CLAUDE.md's "CI Failure Triage" numbered list (renumbering the existing 4
   items to 2-5), covering: the general principle (absent vs. failing needs a different
   diagnostic path), the `mergeable`/trigger-block check, the explicit prohibition on
   re-trigger/force-push/branch-recreation, and the `git ls-remote` vs `headRefOid`
   push-landed disambiguator. Short and additive, not a rewrite of the section.
4. Add a new test file, `tests/docs/test_ci_triage_absent_run_branch.py`, pinning each of the
   ticket's own Acceptance Criteria as a real content check against CLAUDE.md, rather than trusting
   the prose was written as intended.
5. Run the new test file, the broader `tests/docs/` suite, and the handful of `tests/tools/` files
   that reference CLAUDE.md for regression.
