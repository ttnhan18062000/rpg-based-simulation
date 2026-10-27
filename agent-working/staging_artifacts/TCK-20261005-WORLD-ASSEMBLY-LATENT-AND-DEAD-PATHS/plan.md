---
status: active
layer: world
authority: P2
audience: agent
ticket_id: TCK-20261005-WORLD-ASSEMBLY-LATENT-AND-DEAD-PATHS
artifact_type: plan
tags: [world, investigation]
---

# Plan (Scope step only; implementation waits for rpg-planner's decisions)

1. Re-derive sites and record the per-check counts (done; see investigation.md).
2. Stop and send rpg-planner: (d) fix or declare unsupported; the `order` item (now non-latent); the dangling `requires` item (now non-latent); (g) fix (needs no decision); (i) delete or keep.
3. After the decisions: implement only the items that stay in the ticket, one regression test each, no resolved corpus world may change (`test_resolved_snapshot_freshness` stays green), then the hash-neutral proof (paired --neutral, 3 worlds, 1000t, RPG_MEASURE_CACHE set explicitly, heavy slot from lead-planner).
