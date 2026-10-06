---
status: historical
layer: world
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261005-HAZARD-GROWTH-CAPPED-BELOW-EVERY-AUTHORED-COMBAT-REGION
phase: done
date: 2026-10-05
tags: [world]
---

# plan — TCK-20261005-HAZARD-GROWTH-CAPPED-BELOW-EVERY-AUTHORED-COMBAT-REGION

1. Direction (owner decision 12): `hazard_level` is open-ended. Drop the `min(1.0, ...)` cap in `WorldDynamicsSystem.resolve_dynamics`; growth is `hazard + 0.01` while trauma > 50.0, no ceiling invented.
2. Amend Bible 05 (Hazard Scaling, Hazard Impacts); DEV-013; parity-ledger WORLD-127.
3. Test: growth occurs for every authored value including >= 1.0 (fails on the old code for >= 1.0; passes below 1.0 as the positive control).
4. Measure the behavioural consequence and re-take the Scope 2 premise under the unified region lookup.
5. Readers: danger urgency (`events.py`) left saturating at 1.0; recorded as an open question, not changed.
