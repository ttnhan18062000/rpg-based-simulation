---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260930-RESOURCE-NODE-YIELDS-ITEM-COLLIDES-WITH-RESOURCE-KIND
phase: done
date: 2026-09-30
tags: [world]
---

# TCK-20260930-RESOURCE-NODE-YIELDS-ITEM-COLLIDES-WITH-RESOURCE-KIND

## Title
`WorldCompiler` sets `ResourceNodeState.yields_item` from a module's `resource_type`, which names a resource *kind* (`herb_patch`), not an item id (`herb`) — so compile-time resource nodes yield an unregistered item and harvesting them silently never completes

## Status
INPROGRESS

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
- [x] Compile-time resource nodes for `herb_patch`, `wood_node` and `iron_vein` yield `herb`,
      `wood` and `iron_ore` respectively.
- [x] A test asserts every compiled `ResourceNodeState.yields_item` is a registered item id, across
      the real corpus compositions.
- [x] Re-run of the unknown-id measurement in `frontier_living_world` and `crowded_frontier` shows
      zero `herb_patch` misses.
- [x] Any behaviour shift from herb (and possibly wood/iron) harvesting starting to work is stated
      as such, not presented as neutral; SimQ or determinism baselines that move are named.

## Related Tickets
- `TCK-20260914-ITEM-REGISTRY-DUAL-CLASS-DIVERGENT-FAILURE-SEMANTICS` (surfaced this)

## Related Docs
- `docs/mechanics/03_economic_laws.md` (harvesting)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260930-RESOURCE-NODE-YIELDS-ITEM-COLLIDES-WITH-RESOURCE-KIND/` (investigation.md, plan.md, test_plan.md)

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
**Shape chosen and why.** The item is resolved where the correct resolution already lives, not re-derived in
the compiler: `WorldResolver` already looks up the catalog resource definition for `required_ticks`, so it now also
records `yield_item` (`runtime_kind or resource_type`, the rule `registries.py` and `ecology.py` use) on
`ResolvedResourceProfile`; `WorldCompiler` consumes it, falling back to `ResourceRegistry` when compiled with no
context, and to the declared string only for a kind with no catalog definition. A local mapping in the compiler would
duplicate the catalog rule a third time; patching the module YAML would leave the collision for the next author.

**wood_node / iron_vein: fixed in the same change** (compiled nodes yield `wood` / `iron_ore`, pinned per corpus world by
test). They were not observed being harvested in the 400-600 tick windows sampled, so the claim is "fixed and verified
statically", not "observed completing". `ResourceNodeState.kind` was already a resource kind; unchanged.

**Before/after (probe: production loader, real Kernel, PROD_SMALL, seed 42, same probe both sides; `ItemRegistry.get`
wrapped, positive control passed).** ItemRegistry misses (all `herb_patch`): frontier_living_world 104 -> 0 (600t),
crowded_frontier 72 -> 0 (400t), quest_dense_frontier 0 -> 0. Presence of the intended effect: herb charges spent and
herb held in inventories 0 -> 5 / 5 in both worlds (charges and inventory agree). Other before-counts recorded with
their conditions: the same probe with `flags={}` gave 134 / 69; this ticket's earlier harness gave 109 / 45. Counts vary
run to run (wall-clock tick-budget aborts), so the robust claim is nonzero -> zero, not any single number.

**Behaviour shift (not neutral).** Herb harvesting completes for the first time; corpus baselines taken before this
batch are not comparable to ones taken after. Named movers: slow-tier SimQ `unit_selfmodel_pilot_seed42_1000t` ECONOMY
0.1465 -> ~0.287 (up) and NARRATIVE 0.0 -> ~0.05 (marginal); re-baseline deferred to
`TCK-20261001-SIMQ-UNIT-SELFMODEL-PILOT-ECONOMY-ANCHOR-REBASELINE` (user decision; anchors not edited). Control: of the
16 failing `test_corpus_diversity.py` tests, 11 also fail on untouched origin/main 73cbf116b; of the other 5, two pass on
re-run, one is a per-test TimeoutError, one (`frontier_marches` population) is noise (5 trials each, final alive fix
46/36/47/41/43 vs main 42/46/47/36/39, floor 37.2), and one is the real shift above.

## Test Summary
- New: `tests/unit/worldbuilding/test_compiled_node_yields_item.py` (context path, no-context fallback, unknown kind,
  every corpus world yields a registered item).
- Scoped non-slow run (`worldbuilding worldassembly resource engine core docs world` + `tests/integrity`,
  `-m "not slow and not extra_slow"`): 1294 passed, 3 skipped, 1 xfailed.
- Slow tier (`test_corpus_diversity.py`) vs untouched origin/main: see Implementation Notes.

## Files Changed
- `src/worldassembly/models.py`, `src/worldassembly/resolver.py`, `src/worldbuilding/compiler.py`
- `tests/unit/worldbuilding/test_compiled_node_yields_item.py` (new)
- `docs/guidelines/intentional_divergences.md` (section 2.60), `docs/parity_ledger/town_resource.yaml` (TOWN-194)
- Same batch, documentation only, no ticket of its own: `docs/simulation/domains/perception_contract.md` relabeled
  (`status: active -> historical`, `authority: P1 -> P2`, plus a "designed, not in effect" header note; nothing deleted;
  the distance-vs-attention model choice stays deferred to a future perception-foundation epic; see
  `TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-INSTANTIATED`)
- Same batch: `tickets/todos/TCK-20260928-PASSIVE-BIOLOGICAL-DEATH-DETECTION-GAP.md` (death-reason decision note),
  `tickets/todos/TCK-20260930-CONSERVATION-REJECTION-PATH-ASSERTION-GAP.md` (filed, with the AC6 scope note),
  `tickets/todos/TCK-20261001-SIMQ-UNIT-SELFMODEL-PILOT-ECONOMY-ANCHOR-REBASELINE.md` (new follow-up)

## Completion Summary
Compile-time resource nodes now yield the catalog item of their kind (`herb_patch` -> `herb`, `wood_node` -> `wood`,
`iron_vein` -> `iron_ore`). ItemRegistry misses from herb nodes went to zero in all three measured worlds and herb
harvests now complete (0 -> 5 harvested, matching inventory). wood/iron are fixed by the same change and verified
statically, not observed completing. One slow-tier SimQ anchor moves because of this and is named with a follow-up
ticket (not edited here). Not checked-clean-by-omission: nothing is left as "statically the same shape, unmeasured".

