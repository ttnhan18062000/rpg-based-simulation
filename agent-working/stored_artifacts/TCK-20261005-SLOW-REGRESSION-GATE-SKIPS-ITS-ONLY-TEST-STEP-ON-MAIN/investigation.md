---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261005-SLOW-REGRESSION-GATE-SKIPS-ITS-ONLY-TEST-STEP-ON-MAIN
artifact_type: investigation
tags: [testing]
---

# Investigation — TCK-20261005-SLOW-REGRESSION-GATE-SKIPS-ITS-ONLY-TEST-STEP-ON-MAIN

## Findings
- Mechanism: steps 6 and 7 of the `slow` job had no `if:`, so the default `success()` skipped them after any step-5 failure.
- Reviewer's measurement (REST jobs API, 40 `main` push runs up to run 37278526329): 19 failed at step 5, 17 cancelled at step 5, 1 in progress, 3 no step data; steps 6-7 `skipped` in all 36 with step data. Cancellations come from the workflow `concurrency` group's `cancel-in-progress`. Nightlies: 14 of the last 15 show the same pattern.
- Step 5's failure cause is parked by the owner (`TCK-20260822-STANDARD-SLOW-REGRESSION-CI-JOB-EXIT-CODE-2`) and was not investigated.
- `tests/static/test_ci_step_summary_reporting.py` pins the whole `slow` job as YAML, so the change had to update that pin.
- Context scan: `search_docs` was unavailable in this session and the fallback `tools/knowledge_search.py` had no index in the new worktree; files were read directly.
