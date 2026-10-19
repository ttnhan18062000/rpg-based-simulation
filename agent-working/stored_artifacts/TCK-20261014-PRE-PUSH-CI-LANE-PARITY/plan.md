---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261014-PRE-PUSH-CI-LANE-PARITY
artifact_type: plan
tags: [delivery, testing, workflows]
---

# plan — TCK-20261014-PRE-PUSH-CI-LANE-PARITY

1. `tools/delivery/ci_lanes.py`: load test.yml, derive lanes, evaluate filters and `if:`, resolve, list, run.
2. Check D in the hook, calling the resolver lazily and degrading to no finding.
3. `tests/tools/test_delivery_ci_lanes.py`: guards, #536 fixture, fail-open, hook check.
4. `docs/guides/delivery_process.md` PR Lifecycle step 2b. No edit to `.github/workflows/test.yml`.
