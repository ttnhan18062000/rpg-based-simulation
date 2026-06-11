---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260604-PHASE24-RESOLVER-LAYER
artifact_type: test_plan
tags: [phase24, resolver, layer]
---

# Test Plan: Phase 24 — Resolver Layer

## Scope
`tests/unit/content/test_resolvers.py`

---

## Fixtures
- `loaded_repo` — a `CatalogRepository` with real content data loaded from `data/content/`
- `foundation_resolver` — `FoundationResolver(loaded_repo)`
- `social_resolver` — `SocialDefaultsResolver(loaded_repo)`
- `living_resolver` — `LivingDefaultsResolver(loaded_repo)`

---

## FoundationResolver Tests

| Test | Expected |
|------|----------|
| `resolve_attribute("strength")` | Returns `AttributeDefinition(id="strength")` |
| `resolve_attribute("nonexistent_attr")` | Raises `ResolverError` (subclass of `KeyError`) |
| `resolve_material` resolves a known material | Returns `MaterialDefinition` |
| `resolve_trait` resolves a known trait | Returns `TraitDefinition` |
| `resolve_theme` resolves a known theme | Returns `ThemeDefinition` |
| `resolve_element` resolves a known element | Returns `ElementDefinition` |
| `resolve_relationship_axis` resolves a known axis | Returns `RelationshipAxisDefinition` |
| `resolve_traits(["humanoid", "tool_user"])` | Returns 2 `TraitDefinition` objects in input order |
| `resolve_traits(["humanoid", "bad_id"])` | Raises `ResolverError` |
| `resolve_themes` batch preserves input order | Output order matches input ids |
| `resolve_materials` batch preserves input order | Output order matches input ids |

---

## LivingDefaultsResolver Tests

| Test | Expected |
|------|----------|
| `resolve_living_defaults("human")` | Returns `ResolvedLivingDefaults` with all fields populated |
| All profile references resolve | `body_model`, `need_profile`, `sense_profile`, `cognition_profile`, `drive_profile` are correct types |
| `natural_traits` all resolve | List of `TraitDefinition` objects |
| `attribute_tendencies` keys are valid attribute IDs | No error raised |
| `compatible_roles` all resolve | List of `RoleDefinition` objects |
| `resolve_living_defaults("nonexistent_race")` | Raises `ResolverError` |
| Partial missing profile raises `ResolverError` | Artificial incomplete race yields resolver error |

---

## SocialDefaultsResolver Tests

| Test | Expected |
|------|----------|
| `resolve_role_defaults("hero")` | Returns `RoleDefinition(id="hero")` |
| `resolve_role_defaults("nonexistent")` | Raises `ResolverError` |
| `resolve_faction_defaults("town_council")` | Returns `FactionDefinition` |
| `resolve_faction_defaults("nonexistent")` | Raises `ResolverError` |
| `resolve_faction_relationship("town_council", "wild_beast_pack")` | Returns `FactionRelationshipDefinition` |
| `resolve_faction_relationship("nonexistent", "town_council")` | Raises `ResolverError` (source not found) |
| `resolve_faction_relationship("town_council", "nonexistent")` | Raises `ResolverError` (target not found) |
| `resolve_faction_relationship("town_council", "goblin_warband")` where no record exists | Raises `ResolverError` (no record) |
| `resolve_perspective` resolves a known perspective | Returns `PerspectiveDefinition` |
| `resolve_perspective("nonexistent")` | Raises `ResolverError` |

---

## Regression Tests
- Run `pytest tests/unit/content/` to verify all existing catalog tests pass.
