---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261005-SLOW-REGRESSION-GATE-SKIPS-ITS-ONLY-TEST-STEP-ON-MAIN
artifact_type: plan
tags: [testing]
---

# Plan — TCK-20261005-SLOW-REGRESSION-GATE-SKIPS-ITS-ONLY-TEST-STEP-ON-MAIN

Recorded at close; hand-orchestrated from `test-architecture-reviewer`'s brief (owner decision 2026-10-05: restore steps 6-7 now).

1. `.github/workflows/test.yml`, `slow` job: `id:` on the three test steps; `if: ${ !cancelled() }` on steps 6 and 7 (not `always()`: a cancelled run stays cancelled); a closing summary step writing each step's `outcome` to `$GITHUB_STEP_SUMMARY`.
2. `tests/static/test_ci_slow_job_step_gating.py`: pin the shape; mutation-check by removing step 6's `if:`.
3. Update the whole-job pin `_EXPECTED_SLOW_YAML` in `tests/static/test_ci_step_summary_reporting.py`.
4. Record the failed-vs-cancelled measurement; leave step 5's cause parked.
5. Fold in the batch's record-only edits and the two sibling tickets.

Not changed: job-level `if:`, `needs:`, concurrency group, the upload step, any test, threshold or anchor.
