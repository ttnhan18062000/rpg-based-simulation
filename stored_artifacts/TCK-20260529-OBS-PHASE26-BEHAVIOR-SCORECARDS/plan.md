# Proposed Plan

Introduce EntityBehaviorScorecard, RunBehaviorScorecard, CohortAnalyzer, and RunBehaviorComparison to evaluate feature performance and capability deltas post-run.

## Design Decisions
1. Aggregations run post-run only to preserve pure hot-path execution speed.
2. Enforce logic verifying that higher event volume alone does not equal behavioral improvement.
