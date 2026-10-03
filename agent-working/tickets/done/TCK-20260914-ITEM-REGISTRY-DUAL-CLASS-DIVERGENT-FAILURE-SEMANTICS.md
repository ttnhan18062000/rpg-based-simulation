---
status: historical
layer: core
authority: P1
audience: agent
ticket_id: TCK-20260914-ITEM-REGISTRY-DUAL-CLASS-DIVERGENT-FAILURE-SEMANTICS
phase: done
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
INPROGRESS

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
- [x] A complete call-site map for both `ItemRegistry` classes.
- [x] A real, evidence-backed recommendation on consolidation vs. a documented dual-registry
      boundary, with the failure-semantics risk explicitly addressed either way.
- [x] Findings brought to peer/user review before implementation, given the cross-cutting scope.

## Related Tickets
- `TCK-20260914-LAIR-WORLD-BOSS-MATURITY-GATE-REACHABILITY` (the investigation that surfaced this)

## Related Docs
- None yet.

## Related Stored Artifacts
- `stored_artifacts/TCK-20260914-ITEM-REGISTRY-DUAL-CLASS-DIVERGENT-FAILURE-SEMANTICS/` (investigation.md, plan.md, test_plan.md)

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

### 2026-09-30 — Measured; decision: option 3 (user-approved)

**Measurement** (production loader `WorldRepository.load_world_with_context`, real `Kernel` ticks,
`PROD_SMALL`, seed 42; both `ItemRegistry.get` wrapped, positive control passed — a bogus id
incremented both counters before reset; both registries held 37 items after compile):

| world | ticks | entities | `None`-class lookups | misses | `KeyError`-class lookups |
|---|---|---|---|---|---|
| `frontier_living_world` | 600 | 49 | 109 | 109 (all `herb_patch`) | 0 |
| `crowded_frontier` | 400 | 38 | 45 | 45 (all `herb_patch`) | 0 |
| `quest_dense_frontier` | 400 | 6 | 0 | 0 | 0 |

All misses come from `inventory.py:73` (`can_add_items`) via `interaction.py:127`. The `KeyError`
class was never reached in these worlds (its four callers are static-only findings here).

**Consequence:** "raise" is priced out — it would throw on the authoritative apply path on the first
herb interaction in two corpus worlds. **Decision: keep the non-fatal `None` on the apply path and
add a loud diagnostic**, so silence becomes visible without being fatal. The same probe found a real
live defect, tracked in `TCK-20260930-RESOURCE-NODE-YIELDS-ITEM-COLLIDES-WITH-RESOURCE-KIND`.

**Open design point, to be reviewed before any code:** the diagnostic's shape — a hard-law check
versus an observability event. It lands on the authoritative apply path, so it must read state and
emit typed records only, and must not itself mutate durable state or break determinism. Also decide
whether the diagnostic lives at the `items.py` `get` boundary or at the consuming call sites
(`can_add_items` returns False for two different reasons today: unknown id and capacity).

**Scope after this decision:** consolidation is no longer the goal — in catalog mode both
registries already hold the same data, with one bootstrap authority. Remaining work: the
diagnostic, and documenting which class governs which call sites.
**Implemented (option 3).** The diagnostic lives at the consuming call site, `InteractionSystem.enforce`, where
`can_add_items` returns False; `InventoryService.unknown_item_ids` (pure read) separates the unknown-id case from the
capacity case, which a single `get`-boundary log could not. It is recorded through the existing authoritative
rejection audit: `rejections_delta["INTERACTION_UNKNOWN_ITEM"]` (-> `state.rejection_registry`) plus a typed
`RejectionEvent` with new `ReasonCode.UNKNOWN_ITEM`. The interaction reset stays non-fatal; `enforce` still reads
state and returns a refined update only, so no durable mutation outside the apply path and no determinism change.
Call-site governance (which class governs which consumer) is documented in the staging investigation and parity
TOWN-195. Only the interaction call site is instrumented; equipment, shop, leveling and possession still return None
silently on an unknown id (recorded as TOWN-195's support boundary).

**Post-fix check.** After `TCK-20260930-RESOURCE-NODE-YIELDS-ITEM-COLLIDES-WITH-RESOURCE-KIND`, unknown-id misses are 0 in
all three measured worlds, as predicted; no residual misses, so no new ticket.

## Test Summary
- New: `tests/unit/engine/test_interaction_unknown_item_diagnostic.py` (5 tests: unknown recorded and non-fatal,
  capacity not reported as unknown, success records nothing, purity and determinism, helper).
- Regression: `tests/unit/core/test_interaction_recovery.py`, `tests/integrity/test_logic_guards.py`, and the scoped
  non-slow run (1294 passed, 3 skipped, 1 xfailed).

## Files Changed
- `src/core/inventory.py`, `src/core/enums.py`, `src/engine/interaction.py`
- `tests/unit/engine/test_interaction_unknown_item_diagnostic.py` (new)
- `docs/parity_ledger/town_resource.yaml` (TOWN-195), `docs/guidelines/intentional_divergences.md` (section 2.60)

## Completion Summary
Consolidation was not the goal: in catalog mode both registries hold the same data, and the divergence is only in
failure semantics for genuinely unknown ids. Decision (user-approved): keep the non-fatal None on the apply path and
make the silence visible. An interaction rejected for an unknown item id is now counted and recorded as a typed
rejection; the raise option was priced out by measurement. Call-site governance is documented. The KeyError-class
callers remain static-only findings (never reached in measured worlds).

