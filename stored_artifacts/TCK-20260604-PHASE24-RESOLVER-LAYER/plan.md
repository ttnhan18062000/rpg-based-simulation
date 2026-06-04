# Plan: Phase 24 — Resolver Layer

## Goal
Create `src/content/resolver.py` containing:
- `ResolverError(KeyError)` — clean exception with resolver context
- `FoundationResolver` — validated access + batch helpers
- `ResolvedLivingDefaults` — Pydantic output model for race defaults
- `LivingDefaultsResolver` — resolves race to `ResolvedLivingDefaults`
- `SocialDefaultsResolver` — resolves role, faction, relationship, perspective

Then write `tests/unit/content/test_resolvers.py` with full coverage.

---

## File Changes

### [NEW] src/content/resolver.py
Structure:
1. `ResolverError(KeyError)`
2. `FoundationResolver(repo)` — single and batch resolution
3. `ResolvedLivingDefaults` — frozen Pydantic model
4. `LivingDefaultsResolver(repo)` — uses `FoundationResolver` and `SocialDefaultsResolver`
5. `SocialDefaultsResolver(repo)` — role/faction/perspective/relationship

### [NEW] tests/unit/content/test_resolvers.py
Tests grouped by resolver class.

---

## Architecture Decisions

### ResolverError
- Inherits `KeyError` (satisfies requirements for `KeyError`-compatible catching)
- Constructor takes `(family, missing_id, context_msg=None)` so error messages are structured

### `resolve_faction_relationship(source, target)`
- First validate both faction IDs exist.
- Then scan `repo.faction_relationships` dict for a record matching `source_faction==source` and `target_faction==target`.
- Raise `ResolverError` if not found.

### `LivingDefaultsResolver` composition
- Internally instantiates a `FoundationResolver` and `SocialDefaultsResolver` to avoid duplication.
- These are stateless over `repo`, so re-use is safe.

### `ResolvedLivingDefaults.attribute_tendencies`
- Kept as `Dict[str, str]` (attribute_id -> tendency string).
- Each key is validated against `FoundationResolver.resolve_attribute(key)`.
- Values are copied verbatim (tendency strings are free-form descriptors in the catalog).
