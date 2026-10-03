---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260929-UNREACHABLE-CLASSIFY-WAVE-CONFIRM
artifact_type: plan
tags: [investigation, root-cause, corpus, world, simulation-quality]
---

# Plan — TCK-20260929-UNREACHABLE-CLASSIFY-WAVE-CONFIRM

Scope-only. (1) Record the two wave verdicts in their tickets' bodies citing PR #258 and the wave's stored artifact, with one
freshness check each and no re-investigation. (2) Classify the boss-gate half of `COMBAT-GATE-DOWNSTREAM-STARVATION` by
measurement: reuse the canonical `Kernel.tick_once()` harness from the boss-reachability proof and vary only
`ENABLE_COMBAT_ENGAGEMENT`; add tick arithmetic for the horizon. (3) Do not cite combat-volume numbers. (4) Confirm
`registries/mechanisms.yaml` unchanged against `origin/main`.
