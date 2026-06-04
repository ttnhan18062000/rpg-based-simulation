# Investigation: Phase 24 — Resolver layer for foundation, living, and social defaults

We need to design and implement a clean, decoupled resolver layer that retrieves, resolves, and validates static content relationships from the `CatalogRepository`.

## 1. Core Objectives & Constraints

- **Decoupling**: Resolvers must solely resolve static content relations. They must not run runtime simulation systems or behavior, nor import active domain systems.
- **Repository Binding**: Resolvers must be instantiated with a loaded `CatalogRepository` instance.
- **Error Boundaries**: If any referenced entity, profile, or foundation ID does not exist in the repository, the resolver must raise a descriptive exception. To satisfy requirements, we will define a custom exception:
  ```python
  class ResolverError(KeyError):
      """Raised when a referenced content catalog record is not found."""
      pass
  ```
  Since `ResolverError` inherits from `KeyError`, it behaves as a `KeyError` to satisfy generic exception catching while carrying a detailed message about what failed and where.
- **Deterministic Ordering**: Batch resolution helpers must preserve the exact input order of IDs.

---

## 2. Resolver Specifications

### 2.1. FoundationResolver

Provides validated access and batch helpers for the foundation layer:
- `resolve_attribute(id: str) -> AttributeDefinition`
- `resolve_material(id: str) -> MaterialDefinition`
- `resolve_trait(id: str) -> TraitDefinition`
- `resolve_theme(id: str) -> ThemeDefinition`
- `resolve_element(id: str) -> ElementDefinition`
- `resolve_relationship_axis(id: str) -> RelationshipAxisDefinition`

Batch helpers (must preserve order):
- `resolve_traits(ids: Iterable[str]) -> List[TraitDefinition]`
- `resolve_themes(ids: Iterable[str]) -> List[ThemeDefinition]`
- `resolve_materials(ids: Iterable[str]) -> List[MaterialDefinition]`

### 2.2. LivingDefaultsResolver

Resolves race defaults into a reusable structured `ResolvedLivingDefaults` object.

```python
class ResolvedLivingDefaults(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    body_model: BodyModelDefinition
    need_profile: NeedProfileDefinition
    sense_profile: SenseProfileDefinition
    cognition_profile: CognitionProfileDefinition
    drive_profile: DriveProfileDefinition
    natural_traits: List[TraitDefinition]
    attribute_tendencies: Dict[str, str]  # Keyed by validated AttributeDefinition ID
    compatible_roles: List[RoleDefinition]
```

- When `resolve_living_defaults(race_id: str)` is called:
  1. Retrieve `RaceDefinition` by `race_id`. Raise `ResolverError` if missing.
  2. Resolve individual profiles (`body_model`, `need_profile`, `sense_profile`, `cognition_profile`, `drive_profile`) via the repo. Raise `ResolverError` if any is missing.
  3. Resolve each ID in `natural_traits` to `TraitDefinition` via `FoundationResolver`. Raise `ResolverError` if any trait ID is missing.
  4. Validate each key in `attribute_tendencies` as a valid attribute ID via `FoundationResolver`. Raise `ResolverError` if any attribute ID is missing.
  5. Resolve each ID in `compatible_roles` to `RoleDefinition` via `SocialDefaultsResolver`. Raise `ResolverError` if any role ID is missing.

### 2.3. SocialDefaultsResolver

Resolves role, faction, and perspective defaults.

APIs:
- `resolve_role_defaults(role_id: str) -> RoleDefinition`
- `resolve_faction_defaults(faction_id: str) -> FactionDefinition`
- `resolve_faction_relationship(source: str, target: str) -> FactionRelationshipDefinition`
- `resolve_perspective(perspective_id: str) -> PerspectiveDefinition`

For `resolve_faction_relationship(source, target)`:
- We must verify that `source` and `target` faction IDs exist in the catalog.
- We must find the relationship record where `source_faction == source` and `target_faction == target`.
- Raise `ResolverError` if the relationship record or either faction is missing.

---

## 3. Reference and Usage Mapping

As of Phase 24, all content definitions will have explicit resolvers:
- **FoundationResolver** maps `materials`, `traits`, `themes`, `relationship_axes`, `attributes`, and `elements`.
- **LivingDefaultsResolver** maps `races` and their profiles.
- **SocialDefaultsResolver** maps `roles`, `factions`, `faction_relationships`, and `perspectives`.
