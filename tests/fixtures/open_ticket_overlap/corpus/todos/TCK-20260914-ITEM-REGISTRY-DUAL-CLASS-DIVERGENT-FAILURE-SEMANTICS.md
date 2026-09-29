---
status: active
layer: core
authority: P1
audience: agent
ticket_id: TCK-20260914-ITEM-REGISTRY-DUAL-CLASS-DIVERGENT-FAILURE-SEMANTICS
phase: open
date: 2026-09-14
tags: [core]
---

# TCK-20260914-ITEM-REGISTRY-DUAL-CLASS-DIVERGENT-FAILURE-SEMANTICS

## Title
Two parallel `ItemRegistry` classes exist (`src.core.items.ItemRegistry`,
`src.core.registries.ItemRegistry`) with different consumers AND different failure semantics — one
raises `KeyError` on an unregistered id, the other returns `None` — meaning whether an unregistered
item bug is loud or silent depends entirely on which import a given call site happens to use

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
Found while chasing the `ancient_core` loot-item question in
`TCK-20260914-LAIR-WORLD-BOSS-MATURITY-GATE-REACHABILITY`. Two independent `ItemRegistry` classes
exist in this codebase, both plausible-looking, both actively imported by real code:

- `src.core.items.ItemRegistry` — a hardcoded ~10-item dict (`iron_ore`, `wood`, `WOOD`, `herb`,
  `bread`, `healing_potion`, etc.). `.get(item_id) -> Optional[ItemDefinition]` returns `None` for
  an unknown id, never raises. This is the one actually used by the real, authoritative
  inventory/equipment apply-path: `src/core/inventory.py`, `src/core/equipment.py`.
- `src.core.registries.ItemRegistry` — content-catalog-backed. `.get()` raises a real `KeyError`
  for an unregistered id. Imported by `src/world/providers/{information,services,resources}.py`
  and `src/engine/intent/action_intent.py` — none of which are in the real loot/inventory pipeline.

This is a **dual-mechanism divergence with different failure semantics**, the most dangerous
variety of the silence-as-failure-mode pattern named repeatedly this week (this is the 7th real
instance): which class a given call site happens to import silently determines whether a bug
involving an unregistered item id is a loud crash (the `registries.py` version) or an invisible
no-op (the `items.py` version). `ancient_core` being unregistered in the safe one is exactly why
world-boss loot silently vanishes instead of crashing — a future engineer fixing a similar bug
elsewhere could get the opposite behavior from an outwardly identical-looking `ItemRegistry.get()`
call, depending on which module they imported from.

## Scope
- Map every real call site of both classes (not just the ones already found in this week's
  investigation) to understand the full blast radius before proposing a fix.
- Determine which registry should be authoritative going forward — likely `src.core.items` since
  it's the one actually wired into the real inventory/equipment pipeline, but confirm rather than
  assume, and check whether `src.core.registries.ItemRegistry`'s content-catalog backing is itself
  something the codebase needs to move toward (i.e. whether `items.py`'s hardcoded ~10-item dict is
  itself the actually-wrong half, now that the content catalog appears to be the more complete/
  current source of truth).
- Propose a consolidation (single registry, single failure semantic) or, if a real justification
  exists for two coexisting registries, a documented, enforced boundary for which one governs which
  call sites — not two registries that merely happen to share a class name today.
- Bring findings + a proposed direction for review before implementing, given the cross-cutting
  blast radius (touches inventory, equipment, world providers, action intents).

## Out of Scope
- The `ancient_core` item registration itself — handled directly in the sibling ticket
  (`TCK-20260914-LAIR-WORLD-BOSS-MATURITY-GATE-REACHABILITY`) as part of making the world-boss
  encounter real; this ticket is about the registry architecture, not any one item id.
- Any other registry pair (resource registries, entity registries, etc.) — scoped specifically to
  `ItemRegistry`; a broader audit of other registry-name collisions is a separate concern if it
  turns out to exist.

## Acceptance Criteria
- [ ] A complete call-site map for both `ItemRegistry` classes.
- [ ] A real, evidence-backed recommendation on consolidation vs. a documented dual-registry
      boundary, with the failure-semantics risk explicitly addressed either way.
- [ ] Findings brought to peer/user review before implementation, given the cross-cutting scope.

## Related Tickets
- `TCK-20260914-LAIR-WORLD-BOSS-MATURITY-GATE-REACHABILITY` (the investigation that surfaced this)

## Related Docs
- None yet.

## Related Stored Artifacts
None yet — standard tier, staging artifacts created when picked up.

## Related Code Areas
- `src/core/items.py` (`ItemRegistry`, the real pipeline's registry)
- `src/core/registries.py` (`ItemRegistry`, the catalog-backed, raising registry)
- `src/core/inventory.py`, `src/core/equipment.py` (real consumers of the `items.py` version)
- `src/world/providers/{information,services,resources}.py`,
  `src/engine/intent/action_intent.py` (consumers of the `registries.py` version)

## Assumptions / Open Questions
- Whether the content-catalog-backed registry (`registries.py`) is a newer, intended-to-be-canonical
  replacement for the hardcoded one (`items.py`) that the inventory/equipment pipeline simply never
  got migrated onto, versus two registries that were always meant to serve different purposes, is
  the central open question for whoever picks this up.

## Implementation Notes
_(not started)_

## Test Summary
_(not started)_

## Files Changed
_(not started)_

## Completion Summary
_(not started)_
