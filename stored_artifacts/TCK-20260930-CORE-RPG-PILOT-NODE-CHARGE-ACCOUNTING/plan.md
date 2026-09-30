---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260930-CORE-RPG-PILOT-NODE-CHARGE-ACCOUNTING
artifact_type: plan
tags: [testing]
---

# Plan

1. Tests only: 4 unit tests (`ResourceTransactionResolver` NODE branch: regular -1, LOOT full consume, reserved last charge, sliding delta) and 1 kernel-integration test (two actors, one last charge, through `AuthoritativeApplyPipeline.refine`).
2. `TOWN-122` gets a `test_path` (evidence link, status unchanged).
3. Pilot evidence for capabilities 1-6 in `pilot/`; report in `docs/testing/core_rpg_test_pilot_2026-09-30.md`.
No `src/` edits. The rejection-path family (`accepted=False`/`True`) is left to `TCK-20260930-CONSERVATION-REJECTION-PATH-ASSERTION-GAP`.
