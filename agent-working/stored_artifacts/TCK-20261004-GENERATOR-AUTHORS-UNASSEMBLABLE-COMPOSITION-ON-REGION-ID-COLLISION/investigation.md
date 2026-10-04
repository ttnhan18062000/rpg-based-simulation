---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20261004-GENERATOR-AUTHORS-UNASSEMBLABLE-COMPOSITION-ON-REGION-ID-COLLISION
artifact_type: investigation
tags: [world, content, root-cause]
---

# Investigation — TCK-20261004-GENERATOR-AUTHORS-UNASSEMBLABLE-COMPOSITION-ON-REGION-ID-COLLISION

## Findings
- Collision confirmed: `frontier_village_core` and `trading_company_hub` both declare region `hometown` (different bounds, hazard).
- Sweep over all 22 modules: **5 region ids collide** (`hometown` x3 incl. `settled_quarter`, `haunted_battlefield`, `near_forest`, `wolf_den`, `bandit_road`). A class, not one pair.
- The resolver already namespaces region, place, `spawn_region`, building, resource and population ids from `ref.namespace`, so Condition 2 holds without resolver changes.
- Hand-authored precedent uses `namespace: "trading"`; the generator uses the module id (a short default-namespace field would be a module-content change, out of scope).
- Committed `generated_frontier_3_42/world.yaml` was authored before the surfacing ticket and omits `trading_company_hub`; it is not asserted reproducible here.

## Docs Requiring Update
- `docs/guidelines/intentional_divergences.md` — DEV-008, region ids in generated worlds change.
- `docs/parity_ledger/substrate.yaml` — SUBSTRATE-NEW-010 rule (6).

## Risks and Open Questions
- AC-3 deferred until #328 merges (see plan).
- Ranking determinism across runs was not measured separately; namespace assignment orders by `module_id`, which is deterministic regardless.
