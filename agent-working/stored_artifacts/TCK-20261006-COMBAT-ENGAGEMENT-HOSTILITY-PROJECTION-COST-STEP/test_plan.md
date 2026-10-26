---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20261006-COMBAT-ENGAGEMENT-HOSTILITY-PROJECTION-COST-STEP
artifact_type: test_plan
tags: [performance, combat]
---

# Test plan

- Unit (done, 28 pass in `tests/unit/content_semantics`; 354 pass in the 18 test files that reference the hostility services): indexed vs scanned results over all faction pairs and perspective ids incl. missing and empty; species pairs; duplicate keys resolve to the first record; index follows a growing table; shared service vs a fresh service per call give identical hostility and projections over all pairs and several contexts.
- Host-gated: 3-world canonical hash equal before/after under `audit_mode`; `--neutral` IDENTICAL; `combat_engagement` ms before/after at one pinned method; bisect timing.
