---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260930-RESOURCE-NODE-YIELDS-ITEM-COLLIDES-WITH-RESOURCE-KIND
phase: open
date: 2026-09-30
tags: [world]
---

# TCK-20260930-RESOURCE-NODE-YIELDS-ITEM-COLLIDES-WITH-RESOURCE-KIND

## Title
`WorldCompiler` sets `ResourceNodeState.yields_item` from a module's `resource_type`, which names a resource *kind* (`herb_patch`), not an item id (`herb`) — so compile-time resource nodes yield an unregistered item and harvesting them silently never completes

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Found by measurement while pricing the "raise" option for
`TCK-20260914-ITEM-REGISTRY-DUAL-CLASS-DIVERGENT-FAILURE-SEMANTICS`. Wrapping both `ItemRegistry.get`
classes over real `Kernel` runs (production loader, `PROD_SMALL`, seed 42) recorded **109 unknown-id
lookups in 600 ticks of `frontier_living_world` and 45 in 400 ticks of `crowded_frontier`, 100% of
them `herb_patch`** (positive control passed), all via `inventory.py:73` (`can_add_items`) ←
`interaction.py:127`, which resets the entity's interaction every time. Herb harvesting from
compile-time nodes never completes.

**Root cause (traced by `rpg-feature-planning`): a field-meaning collision, not bad content.**
`resource_type` means "which resource kind" in module authoring and "which item to yield" in the
compiler:
- `src/worldbuilding/compiler.py:511` — `yields_item=res_spec.resource_type`, from the module's
  `resource_recipes`. `frontier_village_core.yaml:37` declares `resource_type: "herb_patch"` (the
  resource kind) → yields `herb_patch`, which is not an item id.
- `src/core/registries.py:485` — `yield_item = res.runtime_kind or res.resource_type` from the
  *catalog* def, where `herb_patch` declares `material: "herb"` / `resource_type: "herb"`
  (`data/content/world/resources.yaml:35-38`) → yields `herb`, correct. `ecology.py:139` uses this
  path. So ecology-spawned nodes are right and compile-time nodes are wrong, which is why it
  survived.

Same family as the dual `ItemRegistry`, one layer down: one name, two meanings.

## Scope
- Fix at `compiler.py:511`: resolve the yielded item the way `registries.py:485`/`ecology.py:139`
  do (through the resource definition's material/item), rather than copying the module's
  resource-kind string. **Do not** patch `frontier_village_core.yaml` alone — that fixes one symptom
  and leaves the collision for the next module author.
- Audit every module `resource_recipes` entry. Static check found three module-declared kinds, none
  of which is an item id: `wood_node` and `herb_patch` (`frontier_village_core.yaml:34,37`) and
  `iron_vein` (`trading_company_hub.yaml:40`). Their catalog materials are `wood`, `herb`,
  `iron_ore`. Only `herb_patch` was *measured* to fail; `wood_node`/`iron_vein` are a static
  finding, and their nodes may simply not have been harvested in the sampled worlds.
- Add a regression test that compile-time nodes yield a registered item id.
- Decide whether `ResourceNodeState.kind` (also set from `resource_type`, `compiler.py:510`) is
  affected; it is a resource kind, so likely correct — confirm.

## Out of Scope
- The `ItemRegistry` failure-semantics diagnostic — tracked in
  `TCK-20260914-ITEM-REGISTRY-DUAL-CLASS-DIVERGENT-FAILURE-SEMANTICS`.
- Renaming the module-authoring field. That is a schema change; raise it only if the compiler fix
  proves the collision cannot be resolved locally.

## Acceptance Criteria
- [ ] Compile-time resource nodes for `herb_patch`, `wood_node` and `iron_vein` yield `herb`,
      `wood` and `iron_ore` respectively.
- [ ] A test asserts every compiled `ResourceNodeState.yields_item` is a registered item id, across
      the real corpus compositions.
- [ ] Re-run of the unknown-id measurement in `frontier_living_world` and `crowded_frontier` shows
      zero `herb_patch` misses.
- [ ] Any behaviour shift from herb (and possibly wood/iron) harvesting starting to work is stated
      as such, not presented as neutral; SimQ or determinism baselines that move are named.

## Related Tickets
- `TCK-20260914-ITEM-REGISTRY-DUAL-CLASS-DIVERGENT-FAILURE-SEMANTICS` (surfaced this)

## Related Docs
- `docs/mechanics/03_economic_laws.md` (harvesting)

## Related Stored Artifacts
None yet — standard tier, staging artifacts created when picked up.

## Related Code Areas
- `src/worldbuilding/compiler.py:510-511`
- `src/core/registries.py:485`, `src/world/ecology.py:139`
- `src/engine/interaction.py:119-129`, `src/core/inventory.py:73`
- `data/content/world_modules/frontier_village_core.yaml`, `trading_company_hub.yaml`
- `data/content/world/resources.yaml`

## Assumptions / Open Questions
- Fixing this makes herb harvesting complete for the first time in these worlds, which changes
  economy and combat-adjacent behaviour (healing supply). Baselines may move; measure, don't assume.
- `wood_node`/`iron_vein` may be masked for a different reason (no harvest attempts) — unmeasured.

## Implementation Notes
Measurement harness: production loader, wraps `ItemRegistry.get` on both classes, counts misses
with the calling line, with a positive control. Results in the Request Summary.
_(not started)_

## Test Summary
_(not started)_

## Files Changed
_(not started)_

## Completion Summary
_(not started)_
