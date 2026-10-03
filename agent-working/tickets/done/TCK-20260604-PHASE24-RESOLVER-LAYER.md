---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260604-PHASE24-RESOLVER-LAYER
phase: done
date: 2026-06-04
tags: [phase24, resolver, layer]
---

# TCK-20260604-PHASE24-RESOLVER-LAYER

## Title
Phase 24 — Resolver layer for foundation, living, and social defaults

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Implement the resolver layer to dynamically resolve lower-layer data relationships. Create `FoundationResolver`, `LivingDefaultsResolver`, and `SocialDefaultsResolver` to support structured and validated inheritance of traits, profiles, and relationships.

## Scope
- Implement `FoundationResolver` providing validated access and batch helpers for materials, traits, themes, relationship axes, attributes, and elements.
- Implement `LivingDefaultsResolver` resolving a race's default profiles and natural traits into a structured `ResolvedLivingDefaults` object.
- Implement `SocialDefaultsResolver` resolving role/faction defaults, faction relationships, and perspectives.
- Raise descriptive errors (e.g., `KeyError` or a specific resolver error) when referenced foundation/default IDs do not exist in the catalog.
- Write tests in `tests/unit/content/test_resolvers.py` to cover all three resolvers, including batching, deterministic ordering, and missing reference failures.

## Out of Scope
- Implementing archetype resolution (this is reserved for Phase 25).
- Modifying runtime simulation systems or loaders.

## Acceptance Criteria
- Foundation IDs resolve correctly through one component.
- Missing foundation IDs fail with descriptive errors.
- Batch resolution preserves deterministic input order.
- Resolvers do not import runtime simulation systems.
- Race defaults resolve into a single typed object.
- Faction relationships resolve by source/target.
- Perspectives resolve by ID.
- Existing tests pass without regression.

## Related Tickets
- TCK-20260604-PHASE23-REFERENCE-GRAPH

## Related Docs
- `world_phase_20_28.md`

## Related Stored Artifacts
- None

## Related Code Areas
- `src/content/`
- `tests/unit/content/`

## Assumptions / Open Questions
- We assume the resolvers should be instantiated with a loaded `CatalogRepository` instance.
- Missing reference checks should throw a standard Python exception like `KeyError` or a custom exception detailing the missing ID and family type.

## Implementation Notes
- Defined `ResolverError(KeyError)` with structured fields (`family`, `missing_id`, `context`) for clean, inspectable exceptions.
- `FoundationResolver` wraps the `CatalogRepository` with single-record and batch-helper methods; batch helpers use a simple list comprehension to preserve deterministic input order.
- `ResolvedLivingDefaults` is a frozen Pydantic model with `arbitrary_types_allowed=True` to hold fully-resolved schema objects.
- `LivingDefaultsResolver` composes `FoundationResolver` and `SocialDefaultsResolver` internally to avoid duplication; both are stateless over `repo` so reuse is safe.
- `SocialDefaultsResolver.resolve_faction_relationship` first validates both faction IDs, then performs a linear scan of `repo.faction_relationships.values()` for matching `source_faction`/`target_faction`.
- No runtime simulation systems are imported by the module.

## Test Summary
- 55 new tests added in `tests/unit/content/test_resolvers.py`.
- Tests cover: `ResolverError` structure, `FoundationResolver` single + batch resolution, isolation from runtime systems, `LivingDefaultsResolver` full resolution of `human` and `wolf`, frozen immutability, `SocialDefaultsResolver` role/faction/relationship/perspective resolution.
- All 1996 unit tests pass after implementation.

## Files Changed
- [NEW] `src/content/resolver.py`
- [NEW] `tests/unit/content/test_resolvers.py`

## Completion Summary
- Resolver layer for Phase 24 is fully implemented as specified in `world_phase_20_28.md`.
- All acceptance criteria met:
  - Foundation IDs resolve correctly through `FoundationResolver`.
  - Missing IDs raise `ResolverError` (a `KeyError` subclass) with structured context.
  - Batch resolution (`resolve_traits`, `resolve_themes`, `resolve_materials`) preserves deterministic input order.
  - No runtime simulation imports in `resolver.py` (verified by isolation test).
  - Race defaults resolve into a frozen `ResolvedLivingDefaults` object via `LivingDefaultsResolver`.
  - Faction relationships resolve by source/target pair via `SocialDefaultsResolver`.
  - Perspectives resolve by ID.
  - 1996 existing unit tests pass without regression.
