# SimQ Uplift — Implementation Sequence

Tickets derived from `make evaluate` output (2026-07-02). All three are independent and can be implemented in any order; no intra-batch dependency.

| Order | Ticket | Why this order |
|---|---|---|
| 1 | TCK-20260702-SIMQ-UPLIFT-SOCIAL-ZERO | Broadest impact — if root cause is engine-structural, findings inform the other two tickets |
| 2 | TCK-20260702-SIMQ-UPLIFT-GRADE-DECAY | Decision-only ticket (doc or formula fix); can run in parallel with #1 |
| 3 | TCK-20260702-SIMQ-UPLIFT-DUNGEON-ECON-COG | World-spec investigation; findings depend on understanding activation mechanics (informed by #1) |

## Dependency Notes
- TCK-SOCIAL-ZERO may reveal that engine-level mechanics simply don't trigger in any world. If confirmed, this sheds light on whether dungeon_crawl's ECONOMY gap (ticket #3) is also engine-structural or world-specific.
- TCK-GRADE-DECAY decision (D1 vs D2) may require grade_anchors.json to be updated. Ensure `make evaluate --dry-run` passes after each ticket's completion before starting the next.
