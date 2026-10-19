---
status: historical
layer: engine
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261014-EVERY-DEATH-CARRIES-A-TYPED-CAUSE-RECORDED-AT-DEATH
date: 2026-10-15
tags: []
---

# Investigation: TCK-20261014-EVERY-DEATH-CARRIES-A-TYPED-CAUSE-RECORDED-AT-DEATH

Written at close. `death_reason` was already durable but a string; hazard kind lived only on the region and the last attacker only on the transient combat update. The 2 hp a cave guard lost that no update's hp_delta accounts for is the starving passive drain, taken inside the apply path's passive branch (src/engine/apply.py): in a 5000-tick frontier_living_world seed 42 probe every residual hp loss (215) was at or above the starving line, none below.

Docs to update: docs/mechanics/01_entity_anatomy.md (Death Record), docs/parity_ledger/progression.yaml (PROG-137). Both done.
