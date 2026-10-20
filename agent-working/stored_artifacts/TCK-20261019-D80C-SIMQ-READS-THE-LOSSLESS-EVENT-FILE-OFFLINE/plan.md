---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261019-D80C-SIMQ-READS-THE-LOSSLESS-EVENT-FILE-OFFLINE
artifact_type: plan
tags: [observability]
---

# Plan — TCK-20261019-D80C-SIMQ-READS-THE-LOSSLESS-EVENT-FILE-OFFLINE

1. New `src/simulation_quality/offline.py` (refuse a run without the file, replay in file order, per-type counts, deterministic `generated_at`).
2. `QualityReportBuilder.build` / `QualityHub.get_quality_report` take an optional `generated_at`.
3. `calibrate_simq` and `simq_long_run_observation` score through the module; delete the private helpers; new `tools/simq_score_run.py`.
4. Tests; engine untouched.
