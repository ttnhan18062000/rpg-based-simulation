---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20261004-GENERATOR-AUTHORS-UNASSEMBLABLE-COMPOSITION-ON-REGION-ID-COLLISION
artifact_type: plan
tags: [world, content, root-cause]
---

# Plan — TCK-20261004-GENERATOR-AUTHORS-UNASSEMBLABLE-COMPOSITION-ON-REGION-ID-COLLISION

## Approach
Option 1 (namespace), already ruled by `world-rule-catalog-design` (see the ticket's RULING section). The generator assigns `namespace` to colliding modules when it authors `ModuleRefSpec`.

## Steps
1. `ProceduralCompositionGenerator._assign_region_namespaces(selected_ids, mod_by_id)` in `src/worldgeneration/generator.py`: walk selected modules in `module_id` order; a module declaring a region id already claimed by an earlier module gets `namespace=<its module_id>`. Result depends on the module SET only (Condition 1).
2. Emit `namespace=` on every `ModuleRefSpec`. Residual collisions after namespacing raise `GenerationCompositionError` (validation, never a selection fallthrough).
3. Condition 2 needs no code: the resolver already prefixes region, place, `spawn_region` and recipe ids from `ref.namespace`; it is asserted by test.
4. Tests, docs (DEV-008, substrate parity entry).

## Scope guards
- No edit to `frontier_village_core.yaml` / `trading_company_hub.yaml` (out of scope).
- Do not change module selection or ranking.
- AC-3 (remove two strict xfails) is deferred: the marks exist only on #328. Sequence: #328 merges, `origin/main` is merged here, the xfails XPASS, they are removed in this PR.
