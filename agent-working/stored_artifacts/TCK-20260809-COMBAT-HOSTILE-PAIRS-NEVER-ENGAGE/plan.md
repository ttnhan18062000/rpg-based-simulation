---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260809-COMBAT-HOSTILE-PAIRS-NEVER-ENGAGE
artifact_type: plan
tags: [combat, simulation-quality]
---

# Plan — TCK-20260809-COMBAT-HOSTILE-PAIRS-NEVER-ENGAGE

## Real fix: `EntityIdentityResolver.resolve()` Path 1 no longer requires `role_id`

**Current (buggy) gate** (`src/entities/identity_resolver.py:76-90`):
```python
faction_id = props.get("faction_id")
role_id = props.get("role_id")
if faction_id and role_id:
    return ResolvedEntityIdentity(..., faction_id=faction_id, role_id=role_id, source="clean_metadata")
```

**Fix**: split the gate — trust a real, present `faction_id` on its own, deriving `role_id` from
the existing `_ROLE_COMPAT` legacy map (the same one Path 3 already uses) only when the caller
didn't supply one, instead of falling through to Path 3 (which would also discard the correct
`faction_id`). Confirmed via grep that `ResolvedEntityIdentity.role_id` has **zero real
consumers** anywhere in `src/` (only `.faction_id`/`.archetype_id` are ever read, in
`tactical.py`/`quests.py`) — so a derived-not-authored `role_id` carries no downstream risk; this
is purely about not letting a missing, unconsumed field discard a correct, consumed one.

```python
faction_id = props.get("faction_id")
role_id = props.get("role_id") or _ROLE_COMPAT.get(entity.identity.role)
if faction_id:
    return ResolvedEntityIdentity(
        entity_id=entity.id,
        archetype_id=props.get("archetype_id"),
        race_id=props.get("race_id"),
        faction_id=faction_id,
        role_id=role_id or "unresolved",
        profession_id=props.get("profession_id"),
        legacy_faction=_try_faction(entity.identity.faction),
        legacy_role=_try_role(entity.identity.role),
        source="clean_metadata",
    )
```
Real, minimal, additive change: entities that already have both fields keep the exact same
behavior (source stays `clean_metadata`). Entities with a real `faction_id` but no `role_id`
(confirmed: 100% of `dungeon_crawl`'s roster, 43% of `urban_political`'s) now correctly resolve
their real faction instead of being collapsed to `"neutral"` via Path 3's coarse legacy-enum
projection. `source` field stays `"clean_metadata"` since the identity itself IS clean (content-
driven `faction_id`) — only `role_id` is legacy-derived, which is already true of every other
resolution path's own worst-case behavior.

## What is deliberately NOT touched
- Path 2 (`runtime_identity_extension`), Path 3 (`compatibility_projection`), Path 4
  (`legacy_enum`) — unchanged. Path 3/4 still serve entities with genuinely no `faction_id` at
  all (if any such entities exist; none found in the 2 corpus worlds probed, but the fallback
  chain stays intact for robustness).
- `worldbuilding/compiler.py`'s own `role_id`-never-set gap — the resolver-side fix is
  sufficient and protects every caller/compile-path, not just this one; a compiler-side `role_id`
  population is real, valuable, future defense-in-depth but not required to close this ticket's
  own real bug, and touching the compiler is a larger, separate risk surface for a narrower
  marginal benefit (the resolver already has to tolerate missing `role_id` per its own 4-path
  design intent).
- `resolve_attack()`/`calculate_damage()`/any real combat-resolution logic — untouched;
  this fix is entirely in target *detection*, not damage application.

## Rejected alternative
- **Fix `worldbuilding/compiler.py` to populate `role_id` at compile time** (matching
  `archetype_factory.py`/`entity_spawner.py`'s own existing precedent): rejected as the *sole*
  fix — it would only protect the specific compile path used for these 2 worlds, leaving the
  resolver's own Path 1 gate exploitable by any other current or future caller that sets
  `faction_id` without `role_id`. The resolver-side fix is strictly more defensive and is the
  correct place to own graceful degradation, per its own docstring ("Single identity access
  layer... falls back... only when necessary").

## Verification plan
1. Unit tests for `EntityIdentityResolver.resolve()`: `faction_id` present + `role_id` absent →
   `source="clean_metadata"`, correct `faction_id` preserved, `role_id` derived from
   `_ROLE_COMPAT` when the legacy role enum maps, `"unresolved"` when it doesn't. Existing
   behavior (both fields present, both absent) unchanged — regression-covered.
2. Real corpus re-verification: re-run the same real 2000-tick `Kernel.tick_once()` loop against
   `dungeon_crawl`/`urban_political` (seed 42) used throughout this investigation, confirming
   `is_hostile_compat` now gets called with real faction strings (not `"neutral"`) for
   `bandit_company`/`wild_beast_pack`/etc., and that real combat volume
   (`combat_damage`/`combat_initiated`/`entity_killed`/`combat_engagement_started`) becomes
   non-zero in at least one world — the concrete falsifiable claim this whole investigation exists
   to test. If volume is still zero after this fix, disclose that honestly (a further blocker
   would remain, e.g. actual legality/range/readiness at the point of real detected hostility) —
   not force a "verified" claim.
3. Full scoped pytest: `tests/unit/entities/`, `tests/unit/tactical/`, `tests/unit/combat/`,
   `tests/unit/strategic/`, `tests/unit/core/` (identity-resolver's own real consumers).
