# Plan — TCK-20260916-CI-PER-DIRECTORY-STEPS-FOR-BLOCKED-LOGS

1. Verify on ONE job first, per the ticket's own explicit constraint: `unit-infra` only, not a
   repo-wide rollout.
2. Capture the before baseline: run the existing combined 17-path pytest command locally and
   record pass/fail/skip/deselect counts.
3. Split `unit-infra`'s single `Run` step into one step per listed test path (17 steps, matching
   the ticket's own title/AC wording "unit-infra's steps name their own directories" for maximum
   diagnostic specificity — cost is near-zero since steps share checkout/pip-install), each
   `if: always()`, each writing its own `reports/junit/unit-infra-<name>.xml`.
4. Add a `Merge JUnit XML` step (`if: always()`) recombining the per-directory files into the
   same `reports/junit/unit-infra.xml` path the existing "Job summary" step already reads —
   confirmed via grep that this is the only downstream consumer of that filename.
5. Capture the after counts: run each of the 17 paths separately with the identical marker
   filter, sum, and compare against the baseline.
6. Document the technique and its partial-fetch caveat in CLAUDE.md's CI Failure Triage section
   — only after direct user authorization (obtained via `AskUserQuestion`, matching the precedent
   set for `TCK-20260915-CI-TRIAGE-HAS-NO-ABSENT-RUN-BRANCH`).
7. Add a pinning test file (`tests/docs/test_ci_per_directory_steps_documented.py`) asserting the
   CLAUDE.md addition's real content, matching the existing precedent test's shape.
8. Leave the wider rollout to other combined jobs for a follow-up once this trial has run in real
   CI, per the ticket's own "verify on ONE job first" constraint.
