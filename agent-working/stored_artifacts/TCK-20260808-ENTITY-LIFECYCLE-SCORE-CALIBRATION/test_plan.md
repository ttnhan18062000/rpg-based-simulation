---
status: active
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260808-ENTITY-LIFECYCLE-SCORE-CALIBRATION
artifact_type: test_plan
tags: [simulation-quality, observability, world]
---

# Test Plan — TCK-20260808-ENTITY-LIFECYCLE-SCORE-CALIBRATION

Extends `tests/tools/test_entity_lifecycle_score.py`.

1. `test_clustering_reliable_reflects_tick_count` — `ticks=500` → `clustering_reliable: False`;
   `ticks=1000` → `True` (the real `clustering_reliable_tick_threshold: 1000` derived in
   Investigate).
2. `test_minimum_sample_threshold_unchanged_at_6` — a real-content assertion (not a no-op):
   `weights["minimum_sample_threshold"] == 6`, with a comment citing this ticket's own real
   finding (no empirical knee found; kept unchanged, not raised or lowered arbitrarily).

## Acceptance-criteria map

| AC | Disposition |
|---|---|
| investigation.md reports real density-vs-volume correlation | Done — weak (r=0.495, n=6), no correction justified; strong secondary finding on dominant_shape_share (r=-0.734) documented |
| investigation.md reports real tick-length activity profile | Done — non-flat, plausibly consistent with D05's own precedented "settling" finding |
| investigation.md reports real minimum-sample threshold sweep | Done — no clean knee; kept at 6 |
| plan.md specifies what config changes this evidence justifies | plan.md |
| Sibling tool's config updated with measured values, or explicitly left unchanged with a documented finding | Implement — `clustering_reliable_tick_threshold` added; `minimum_sample_threshold` explicitly left at 6 |
| Scoped pytest passes | Tests 1-2 + full existing suite |
