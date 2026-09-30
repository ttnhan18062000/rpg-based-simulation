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

### 2026-09-30 — Premise re-verified, and the consumer map is wider than filed

Re-verified before scoping, per the standing rule (today's sample produced two premise-false
closures, one duplicate, and one P0 whose severity claim didn't survive measurement).
**The premise holds exactly**, and unlike that P0 this one needed no runtime probe — the hazard is
static, and it has already produced one real silent failure (`ancient_core` loot).

Both classes exist, both are live, and their failure semantics diverge as described:
- `src/core/items.py:17` — `ItemRegistry.get()` at `:96-97` is `return cls._items.get(item_id)`.
  Returns `None` for an unknown id. **Never raises.**
- `src/core/registries.py:63` — `ItemRegistry.get()` at `:71-73` does
  `if item_id not in cls._items: raise KeyError(...)`. **Always raises.**

**Consumer split — 9 call sites, not the 4 the Request Summary lists.** The gameplay side is
larger than filed:

| importing | consumers |
|---|---|
| `src.core.items` (returns `None`) | `src/core/inventory.py:9`, `src/core/equipment.py:5`, `src/town/shop.py:6`, `src/progression/leveling.py:95`, `src/domains/progression/possession.py:98` |
| `src.core.registries` (raises `KeyError`) | `src/world/providers/services.py:7`, `information.py:6`, `resources.py:5`, `src/engine/intent/action_intent.py:9` |

`shop.py`, `leveling.py` and `possession.py` were not named in the ticket. The finding is
unchanged but broader: **five** real gameplay paths silently no-op on an unknown item id.

### A cross-link the ticket does not mention, and it changes the fix

`registries.py` **bootstraps the other registry**, in two places:
- `:616-617` (catalog mode) — `CoreItemRegistry.bootstrap(catalog_repo.items)`, seeding
  `items.py` with the **full catalog**.
- `:729-730` (legacy fallback) — `CoreItemRegistry.bootstrap({})`.

Checked what the empty-dict call does, because it looked like a wipe: it is not.
`items.py:100-105`'s `bootstrap` treats falsy `data` as "restore", assigning
`cls._items = dict(cls._backup_items)` — the ~10 hardcoded items. So legacy mode degrades to the
hardcoded set rather than emptying the registry.

**Consequence for scoping: in catalog mode the two registries hold the same data.** The divergence
is then purely in *failure semantics* for genuinely-unknown ids, not in coverage. That makes
consolidation cheaper than the ticket implies — there is already a single bootstrap authority — and
it relocates the real decision to **which semantics should win**, not which class should survive.

### The real decision, not yet made

Raise or return `None`? This is the same shape as the two-readers-disagreeing family catalogued
this week, and the answer is not obvious:
- **Raise** surfaces unregistered-content bugs loudly (it is why `ancient_core` should have
  crashed instead of silently vanishing), but converts today's silent no-ops on five gameplay
  paths into live exceptions — including `inventory.py` and `equipment.py`, on the authoritative
  apply path. Blast radius needs measuring before choosing it.
- **Return `None`** keeps current behaviour and requires every call site to check, which is what
  already failed.
- A third option: keep `None` on the apply path but add a loud diagnostic (a hard-law check or
  observability event) so the silence is visible without being fatal.

Recommend measuring how often an unknown id is actually requested in a corpus run before choosing —
same discipline that reduced the `stats_dirty` P0 from "invalidates everything" to "never fires".
_(not started)_

## Test Summary
_(not started)_

## Files Changed
_(not started)_

## Completion Summary
_(not started)_
