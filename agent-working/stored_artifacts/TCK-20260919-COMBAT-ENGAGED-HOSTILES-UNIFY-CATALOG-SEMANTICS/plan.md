---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260919-COMBAT-ENGAGED-HOSTILES-UNIFY-CATALOG-SEMANTICS
artifact_type: plan
tags: [combat, faction, root-cause]
---

# Plan — TCK-20260919-COMBAT-ENGAGED-HOSTILES-UNIFY-CATALOG-SEMANTICS

## Steps

1. Extract a single, shared hostility test (`LegalityServiceV2._is_engagement_hostile()`) that
   resolves real `faction_id` via `EntityIdentityResolver` (falling back to `get_faction_id_str()`
   on resolution failure, matching `tactical.py`'s own established pattern) and delegates to
   `FactionSemanticsService.is_hostile_compat()`.
2. Replace the raw `my_faction != other.identity.faction` check in all three internal
   implementations of `get_engaged_hostiles_at_pos()` (occupancy-snapshot fast path,
   `SpatialQueryService` fallback, dict-iteration fallback) with a call to the shared helper —
   one definition, three call sites, per the ticket's own hard scope guard.
3. Write tests that exercise each of the three internal paths **separately and deterministically**
   (forcing which path executes via the state shape passed in), each with both a positive case
   (a same-legacy-bucket pair with a real, specific catalog rivalry — `bandit_company`/
   `goblin_warband`) and a negative case (a different-legacy-bucket pair with no real catalog
   hostility — `hero_guild`/`merchant_league`), so a fix landing in only one path would be
   visible as a test failure in the others.
4. Run the new tests. **Two of the six failed on the first pass** — both the "catches" cases for
   the occupancy-snapshot and `SpatialQueryService` paths (the dict-iteration fallback's "catches"
   case passed). Root-caused directly rather than assumed: `AuthoritativeState.__post_init__`
   computes a separate, upstream `_has_hostiles_or_dead_cache` field using the exact same raw
   legacy-enum comparison, as an early-exit gate at the very top of
   `get_engaged_hostiles_at_pos()` — a same-legacy-bucket pair reads as "no diversity, nothing to
   check" and short-circuits before the (now-correct) per-pair logic ever runs. This is a fourth
   place with the same bug, one level upstream of the three already found.
5. Fixed the cache computation (`src/core/state.py`) and its own duplicate recomputation path
   (`src/systems/strategic_systems/intelligence.py`, exercised when a "sliding" trial state resets
   the cache to `None`) to compare the real `identity.properties.get("faction_id")` first, falling
   back to the raw legacy enum only when absent — cheap, no new imports, no circular-dependency
   risk (`src/entities/identity_resolver.py` itself imports from `src/core/state.py`, so the full
   resolver/catalog machinery cannot be used inside `state.py`'s own `__post_init__`). A false
   "diverse" positive here only costs a wasted scan; a false negative was the actual bug — so this
   asymmetric, conservative fix is the correct direction to err in.
6. Re-ran all six new tests — all pass. Re-ran the full relevant regression scope.
7. Measured real before/after combat volume per world via a self-contained script that reproduces
   the true pre-fix runtime condition (both the old hostility test AND the old, unfixed cache
   value, forced via `object.__setattr__` after normal state construction) rather than a partial
   revert — so the "before" number is authentic to the original code's actual behavior, not just
   the hostility-test half of it.
8. Re-ran the original investigation's own divergence probe against the fixed code to directly
   confirm zero remaining disagreement between `get_engaged_hostiles_at_pos()`'s real
   classification and an independent `is_hostile_compat()` check, across all sampled worlds.
