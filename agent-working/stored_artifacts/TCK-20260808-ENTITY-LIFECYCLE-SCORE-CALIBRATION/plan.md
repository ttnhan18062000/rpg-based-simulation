---
status: active
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260808-ENTITY-LIFECYCLE-SCORE-CALIBRATION
artifact_type: plan
tags: [simulation-quality, observability, world]
---

# Plan — TCK-20260808-ENTITY-LIFECYCLE-SCORE-CALIBRATION

## Steps

1. `config/simulation_quality/entity_lifecycle_weights.yaml`: add
   `clustering_reliable_tick_threshold: 1000` (real, derived value from Investigate's own tick-
   length sweep). `minimum_sample_threshold` stays `6`, with an updated comment explaining the
   real sweep that confirmed it (no change to the value itself).
2. `tools/entity_lifecycle_score.py`: `run_metadata()` gains `clustering_reliable: bool`
   (`ticks >= clustering_reliable_tick_threshold`), matching the existing
   `stall_detector_reachable` pattern exactly.
3. `tests/tools/test_entity_lifecycle_score.py`: the 2 new tests from test_plan.md.
4. `docs/simulation_quality/entity_lifecycle_score.md`: add the real correlation tables (density
   vs. path metrics, tick-length profile, minimum-sample sweep) from investigation.md.
5. `docs/guides/entity_lifecycle_score.md`: update the "Interpreting a value" section with the
   real `clustering_reliable` caveat and the density-vs-dominant_shape_share context.

## Acceptance-criteria map

| AC | Disposition |
|---|---|
| investigation.md real correlation data | Done |
| plan.md specifies config changes | This file |
| Config updated with measured values or explicit no-change finding | Steps 1-2 |
| Scoped pytest passes | Step 3 |
