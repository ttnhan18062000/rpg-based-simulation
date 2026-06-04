# Compliance IDs: WORLD-CAT-024, WORLD-CAT-025
"""
src/content/resolver.py
───────────────────────────────────────────────────────────────────────────────
Phase 24 — Resolver layer for foundation, living, and social defaults.
Phase 25 — Entity archetype and population resolution.

Provides validated, deterministic access to static catalog data without running
any runtime simulation logic. All resolvers are instantiated with a loaded
CatalogRepository and raise ResolverError on any missing reference.
"""
from __future__ import annotations

from typing import Dict, Iterable, List, Optional, Tuple

from pydantic import BaseModel, ConfigDict

from src.content.repository import CatalogRepository
from src.content.schema import (
    AttributeDefinition,
    BodyModelDefinition,
    CognitionProfileDefinition,
    CombatProfileDefinition,
    DriveProfileDefinition,
    ElementDefinition,
    EntityArchetypeDefinition,
    FactionDefinition,
    FactionRelationshipDefinition,
    InventoryProfileDefinition,
    MaterialDefinition,
    NeedProfileDefinition,
    PerspectiveDefinition,
    RelationshipAxisDefinition,
    RoleDefinition,
    SenseProfileDefinition,
    SkillProfileDefinition,
    StatsProfileDefinition,
    ThemeDefinition,
    TraitDefinition,
    BiomeDefinition,
    BuildingDefinition,
    EcologyDefinition,
    ResourceDefinition,
    RuntimeRegionDefinition,
)


# ---------------------------------------------------------------------------
# Exception
# ---------------------------------------------------------------------------

class ResolverError(KeyError):
    """
    Raised when a resolver cannot find a referenced content catalog record.

    Inherits from KeyError so callers can catch it as a standard KeyError
    while still receiving a structured, informative message.
    """

    def __init__(self, family: str, missing_id: str, context: str = "") -> None:
        self.family = family
        self.missing_id = missing_id
        self.context = context
        detail = f"[{family}] '{missing_id}' not found in catalog"
        if context:
            detail += f" — {context}"
        super().__init__(detail)

    def __str__(self) -> str:
        return self.args[0]


# ---------------------------------------------------------------------------
# FoundationResolver
# ---------------------------------------------------------------------------

class FoundationResolver:
    """
    Provides validated access to foundation concepts: attributes, materials,
    traits, themes, elements, and relationship axes.

    Does not run behaviour. Only resolves stable dependency concepts.
    """

    def __init__(self, repo: CatalogRepository) -> None:
        self._repo = repo

    # --- Single-record resolution ---

    def resolve_attribute(self, attr_id: str) -> AttributeDefinition:
        """Resolve a single AttributeDefinition by ID. Raises ResolverError if missing."""
        record = self._repo.get_attribute(attr_id)
        if record is None:
            raise ResolverError("attribute", attr_id)
        return record

    def resolve_material(self, material_id: str) -> MaterialDefinition:
        """Resolve a single MaterialDefinition by ID. Raises ResolverError if missing."""
        record = self._repo.get_material(material_id)
        if record is None:
            raise ResolverError("material", material_id)
        return record

    def resolve_trait(self, trait_id: str) -> TraitDefinition:
        """Resolve a single TraitDefinition by ID. Raises ResolverError if missing."""
        record = self._repo.get_trait(trait_id)
        if record is None:
            raise ResolverError("trait", trait_id)
        return record

    def resolve_theme(self, theme_id: str) -> ThemeDefinition:
        """Resolve a single ThemeDefinition by ID. Raises ResolverError if missing."""
        record = self._repo.get_theme(theme_id)
        if record is None:
            raise ResolverError("theme", theme_id)
        return record

    def resolve_element(self, element_id: str) -> ElementDefinition:
        """Resolve a single ElementDefinition by ID. Raises ResolverError if missing."""
        record = self._repo.get_element(element_id)
        if record is None:
            raise ResolverError("element", element_id)
        return record

    def resolve_relationship_axis(self, axis_id: str) -> RelationshipAxisDefinition:
        """Resolve a single RelationshipAxisDefinition by ID. Raises ResolverError if missing."""
        record = self._repo.get_relationship_axis(axis_id)
        if record is None:
            raise ResolverError("relationship_axis", axis_id)
        return record

    # --- Batch helpers (preserve deterministic input order) ---

    def resolve_traits(self, ids: Iterable[str]) -> List[TraitDefinition]:
        """
        Resolve a sequence of trait IDs into TraitDefinition objects, preserving
        the original input order. Raises ResolverError on the first missing ID.
        """
        return [self.resolve_trait(tid) for tid in ids]

    def resolve_themes(self, ids: Iterable[str]) -> List[ThemeDefinition]:
        """
        Resolve a sequence of theme IDs into ThemeDefinition objects, preserving
        the original input order. Raises ResolverError on the first missing ID.
        """
        return [self.resolve_theme(tid) for tid in ids]

    def resolve_materials(self, ids: Iterable[str]) -> List[MaterialDefinition]:
        """
        Resolve a sequence of material IDs into MaterialDefinition objects,
        preserving the original input order. Raises ResolverError on the first
        missing ID.
        """
        return [self.resolve_material(mid) for mid in ids]


# ---------------------------------------------------------------------------
# ResolvedLivingDefaults — output model for LivingDefaultsResolver
# ---------------------------------------------------------------------------

class ResolvedLivingDefaults(BaseModel):
    """
    The fully-resolved defaults bundle for a single race.

    All referenced profiles and traits have been validated against the catalog.
    attribute_tendencies keys are validated attribute IDs; values are the
    free-form tendency strings defined in the races catalog.
    """
    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    body_model: BodyModelDefinition
    need_profile: NeedProfileDefinition
    sense_profile: SenseProfileDefinition
    cognition_profile: CognitionProfileDefinition
    drive_profile: DriveProfileDefinition
    natural_traits: List[TraitDefinition]
    attribute_tendencies: Dict[str, str]
    compatible_roles: List[RoleDefinition]


# ---------------------------------------------------------------------------
# LivingDefaultsResolver
# ---------------------------------------------------------------------------

class LivingDefaultsResolver:
    """
    Resolves a race ID into a ResolvedLivingDefaults bundle.

    This is the first place where a race becomes more than a string label;
    it is validated and expanded into a fully-typed structure ready for
    downstream consumption by the archetype resolver (Phase 25).
    """

    def __init__(self, repo: CatalogRepository) -> None:
        self._repo = repo
        self._foundation = FoundationResolver(repo)
        self._social = SocialDefaultsResolver(repo)

    def resolve_living_defaults(self, race_id: str) -> ResolvedLivingDefaults:
        """
        Resolve all living defaults for the given race ID.

        Raises ResolverError if the race itself or any of its referenced
        body model, need/sense/cognition/drive profiles, traits,
        attribute axes, or compatible roles are missing from the catalog.
        """
        race = self._repo.get_race(race_id)
        if race is None:
            raise ResolverError("race", race_id)

        # Resolve profile references
        body_model = self._repo.get_body_model(race.body_model)
        if body_model is None:
            raise ResolverError(
                "body_model", race.body_model,
                context=f"referenced by race '{race_id}'"
            )

        need_profile = self._repo.get_need_profile(race.need_profile)
        if need_profile is None:
            raise ResolverError(
                "need_profile", race.need_profile,
                context=f"referenced by race '{race_id}'"
            )

        sense_profile = self._repo.get_sense_profile(race.sense_profile)
        if sense_profile is None:
            raise ResolverError(
                "sense_profile", race.sense_profile,
                context=f"referenced by race '{race_id}'"
            )

        cognition_profile = self._repo.get_cognition_profile(race.cognition_profile)
        if cognition_profile is None:
            raise ResolverError(
                "cognition_profile", race.cognition_profile,
                context=f"referenced by race '{race_id}'"
            )

        drive_profile = self._repo.get_drive_profile(race.drive_profile)
        if drive_profile is None:
            raise ResolverError(
                "drive_profile", race.drive_profile,
                context=f"referenced by race '{race_id}'"
            )

        # Resolve natural traits (preserving order)
        natural_traits = self._foundation.resolve_traits(race.natural_traits)

        # Validate attribute tendency keys against the attribute catalog
        for attr_key in race.attribute_tendencies:
            self._foundation.resolve_attribute(attr_key)
        attribute_tendencies: Dict[str, str] = dict(race.attribute_tendencies)

        # Resolve compatible roles (preserving order)
        compatible_roles = [
            self._social.resolve_role_defaults(role_id)
            for role_id in race.compatible_roles
        ]

        return ResolvedLivingDefaults(
            body_model=body_model,
            need_profile=need_profile,
            sense_profile=sense_profile,
            cognition_profile=cognition_profile,
            drive_profile=drive_profile,
            natural_traits=natural_traits,
            attribute_tendencies=attribute_tendencies,
            compatible_roles=compatible_roles,
        )


# ---------------------------------------------------------------------------
# SocialDefaultsResolver
# ---------------------------------------------------------------------------

class SocialDefaultsResolver:
    """
    Resolves role/faction defaults, faction relationships, and perspectives.

    This is the clean resolver path. Legacy bucket mapping in FactionDefinition
    remains available but is not this resolver's source of truth.
    """

    def __init__(self, repo: CatalogRepository) -> None:
        self._repo = repo

    def resolve_role_defaults(self, role_id: str) -> RoleDefinition:
        """Resolve a RoleDefinition by ID. Raises ResolverError if missing."""
        record = self._repo.get_role(role_id)
        if record is None:
            raise ResolverError("role", role_id)
        return record

    def resolve_faction_defaults(self, faction_id: str) -> FactionDefinition:
        """Resolve a FactionDefinition by ID. Raises ResolverError if missing."""
        record = self._repo.get_faction(faction_id)
        if record is None:
            raise ResolverError("faction", faction_id)
        return record

    def resolve_faction_relationship(
        self, source: str, target: str
    ) -> FactionRelationshipDefinition:
        """
        Resolve the relationship record between two factions.

        Both faction IDs are validated against the catalog first.
        Raises ResolverError if either faction is missing or if no relationship
        record exists for the given source/target pair.
        """
        # Validate source and target factions exist
        if self._repo.get_faction(source) is None:
            raise ResolverError("faction", source, context="source of requested relationship")
        if self._repo.get_faction(target) is None:
            raise ResolverError("faction", target, context="target of requested relationship")

        # Scan relationships for a matching record
        for rel in self._repo.faction_relationships.values():
            if rel.source_faction == source and rel.target_faction == target:
                return rel

        raise ResolverError(
            "faction_relationship",
            f"{source}->{target}",
            context="no relationship record found for this source/target pair",
        )

    def resolve_perspective(self, perspective_id: str) -> PerspectiveDefinition:
        """Resolve a PerspectiveDefinition by ID. Raises ResolverError if missing."""
        record = self._repo.get_perspective(perspective_id)
        if record is None:
            raise ResolverError("perspective", perspective_id)
        return record


# ---------------------------------------------------------------------------
# ResolvedEntityArchetype — Phase 25 output model
# ---------------------------------------------------------------------------

class ResolvedEntityArchetype(BaseModel):
    """
    The fully-resolved, compile-ready template for a single entity archetype.

    Resolution order:
      race defaults → role defaults → faction defaults
        → explicit archetype profiles → explicit archetype traits/themes
      = ResolvedEntityArchetype

    Explicit archetype fields always override race/role/faction defaults.
    Traits are merged deterministically: archetype traits first, then any race
    natural_traits not already present (stable deduplication).
    No enemy/boss labels are stored here.
    """
    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    # --- Identity ---
    archetype_id: str
    race_id: str
    faction_id: str
    role_id: str

    # --- Resolved profiles (explicit archetype values; race/role defaults fill gaps) ---
    stat_profile: StatsProfileDefinition
    combat_profile: CombatProfileDefinition
    cognition_profile: CognitionProfileDefinition
    drive_profile: DriveProfileDefinition
    need_profile: NeedProfileDefinition        # from race defaults
    sense_profile: SenseProfileDefinition      # from race defaults
    inventory_profile: InventoryProfileDefinition
    skill_profile: Optional[SkillProfileDefinition]  # may be absent

    # --- Merged traits / themes (deterministic, deduplicated) ---
    traits: List[TraitDefinition]
    themes: List[ThemeDefinition]

    # --- Projection (catalog string IDs for legacy adapters; no runtime enums) ---
    legacy_engine_role: str    # from RoleDefinition.legacy_engine_role
    legacy_engine_bucket: str  # from FactionDefinition.legacy_engine_bucket


# ---------------------------------------------------------------------------
# EntityArchetypeResolver — Phase 25
# ---------------------------------------------------------------------------

class EntityArchetypeResolver:
    """
    Resolves a single EntityArchetypeDefinition (by ID or object) into a
    ResolvedEntityArchetype.

    Resolution strategy:
      - Race provides: need_profile, sense_profile, natural_traits (baseline).
      - Role provides: cognition_profile fallback (if archetype omits it).
      - Explicit archetype profiles always override race/role defaults.
      - Traits: archetype traits first, then race natural_traits not already
        present, preserving stable order (no duplicates).
      - Themes: exactly as declared in the archetype (no merging from other layers).
    """

    def __init__(self, repo: CatalogRepository) -> None:
        self._repo = repo
        self._foundation = FoundationResolver(repo)
        self._living = LivingDefaultsResolver(repo)
        self._social = SocialDefaultsResolver(repo)

    def resolve(self, archetype_id: str) -> ResolvedEntityArchetype:
        """
        Resolve the archetype with the given ID.

        Raises ResolverError if the archetype, or any of its referenced
        profiles, traits, or themes, is missing from the catalog.
        """
        arch = self._repo.get_entity_archetype(archetype_id)
        if arch is None:
            raise ResolverError("entity_archetype", archetype_id)
        return self._resolve_from_definition(arch)

    def resolve_all(self) -> Dict[str, ResolvedEntityArchetype]:
        """
        Resolve every archetype in the catalog.

        Returns a dict keyed by archetype ID, preserving catalog iteration order.
        Raises ResolverError on the first archetype that cannot be resolved.
        """
        return {
            arch_id: self._resolve_from_definition(arch)
            for arch_id, arch in self._repo.entity_archetypes.items()
        }

    def _resolve_from_definition(
        self, arch: EntityArchetypeDefinition
    ) -> ResolvedEntityArchetype:
        archetype_id = arch.id
        ctx = f"archetype '{archetype_id}'"

        # --- Race defaults ---
        race_defaults = self._living.resolve_living_defaults(arch.race)

        # --- Role defaults ---
        role_def = self._social.resolve_role_defaults(arch.role)

        # --- Faction defaults ---
        faction_def = self._social.resolve_faction_defaults(arch.faction)

        # --- Stat profile (must be explicit on archetype; no default fallback) ---
        stat_profile = self._repo.get_stats_profile(arch.stat_profile)
        if stat_profile is None:
            raise ResolverError(
                "stat_profile", arch.stat_profile, context=ctx
            )

        # --- Combat profile (must be explicit on archetype) ---
        combat_profile = self._repo.get_combat_profile(arch.combat_profile)
        if combat_profile is None:
            raise ResolverError(
                "combat_profile", arch.combat_profile, context=ctx
            )

        # --- Cognition profile: archetype explicit, else role default ---
        cognition_profile_id = arch.cognition_profile or (
            role_def.default_cognition_profile if role_def else None
        )
        if not cognition_profile_id:
            raise ResolverError(
                "cognition_profile", "<none>",
                context=f"{ctx} — no explicit or role-default cognition profile"
            )
        cognition_profile = self._repo.get_cognition_profile(cognition_profile_id)
        if cognition_profile is None:
            raise ResolverError("cognition_profile", cognition_profile_id, context=ctx)

        # --- Drive profile: archetype explicit (required field) ---
        drive_profile = self._repo.get_drive_profile(arch.drive_profile)
        if drive_profile is None:
            raise ResolverError("drive_profile", arch.drive_profile, context=ctx)

        # --- Need/sense profiles: always from race defaults ---
        need_profile = race_defaults.need_profile
        sense_profile = race_defaults.sense_profile

        # --- Inventory profile: archetype explicit (required field) ---
        inventory_profile = self._repo.get_inventory_profile(arch.inventory_profile)
        if inventory_profile is None:
            raise ResolverError(
                "inventory_profile", arch.inventory_profile, context=ctx
            )

        # --- Skill profile: optional ---
        skill_profile: Optional[SkillProfileDefinition] = None
        if arch.skill_profile:
            skill_profile = self._repo.get_skill_profile(arch.skill_profile)
            if skill_profile is None:
                raise ResolverError(
                    "skill_profile", arch.skill_profile, context=ctx
                )

        # --- Trait merge: archetype traits first, then race natural_traits not already present ---
        seen: set = set()
        merged_trait_ids: List[str] = []
        for tid in arch.traits:
            if tid not in seen:
                seen.add(tid)
                merged_trait_ids.append(tid)
        for td in race_defaults.natural_traits:
            if td.id not in seen:
                seen.add(td.id)
                merged_trait_ids.append(td.id)
        traits = self._foundation.resolve_traits(merged_trait_ids)

        # --- Theme resolution: exactly as declared in archetype ---
        themes = self._foundation.resolve_themes(arch.themes)

        return ResolvedEntityArchetype(
            archetype_id=archetype_id,
            race_id=arch.race,
            faction_id=arch.faction,
            role_id=arch.role,
            stat_profile=stat_profile,
            combat_profile=combat_profile,
            cognition_profile=cognition_profile,
            drive_profile=drive_profile,
            need_profile=need_profile,
            sense_profile=sense_profile,
            inventory_profile=inventory_profile,
            skill_profile=skill_profile,
            traits=traits,
            themes=themes,
            legacy_engine_role=role_def.legacy_engine_role,
            legacy_engine_bucket=faction_def.legacy_engine_bucket,
        )


# ---------------------------------------------------------------------------
# PopulationRecipeResolver — Phase 25
# ---------------------------------------------------------------------------

class PopulationRecipeResolver:
    """
    Expands a PopulationRecipeDefinition into a deterministic list of
    (ResolvedEntityArchetype, count) pairs.

    Preferred authoring path::

        members:
          hungry_wolf: 4
          alpha_wolf: 1

    All archetype IDs must exist in the catalog; preferred_regions are
    validated for non-emptiness but not resolved (region resolution is
    handled by WorldAssemblyResolver at assembly time).
    """

    def __init__(self, repo: CatalogRepository) -> None:
        self._repo = repo
        self._archetype_resolver = EntityArchetypeResolver(repo)

    def resolve(
        self, population_id: str
    ) -> Tuple[List[Tuple[ResolvedEntityArchetype, int]], List[str]]:
        """
        Resolve the population recipe with the given ID.

        Returns:
            (expanded, preferred_regions) where:
            - ``expanded`` is a list of (ResolvedEntityArchetype, count) tuples
              in the same order as the ``members`` dict.
            - ``preferred_regions`` is the list of preferred region IDs from the
              recipe (not resolved here; passed through for assembly use).

        Raises ResolverError if the population recipe or any member archetype
        is missing from the catalog.
        """
        recipe = self._repo.get_population_recipe(population_id)
        if recipe is None:
            # Fallback check: is it a direct archetype ID?
            archetype = self._repo.get_entity_archetype(population_id)
            if archetype is not None:
                resolved_arch = self._archetype_resolver.resolve(population_id)
                return [(resolved_arch, 1)], []
            raise ResolverError("population_recipe", population_id)

        expanded: List[Tuple[ResolvedEntityArchetype, int]] = []
        for arch_id, count in recipe.members.items():
            resolved_arch = self._archetype_resolver.resolve(arch_id)
            expanded.append((resolved_arch, count))

        return expanded, list(recipe.preferred_regions)

    def resolve_all_members(
        self, population_id: str
    ) -> List[Tuple[ResolvedEntityArchetype, int]]:
        """
        Convenience wrapper — returns only the expanded member list.

        Raises ResolverError if the population recipe or any member archetype
        is missing from the catalog.
        """
        expanded, _ = self.resolve(population_id)
        return expanded


# ---------------------------------------------------------------------------
# Biome and Ecology resolvers — Phase 27
# ---------------------------------------------------------------------------

class BiomeResolver:
    def __init__(self, repo: CatalogRepository) -> None:
        self._repo = repo

    def resolve(self, biome_id: str) -> BiomeDefinition:
        biome = self._repo.get_biome(biome_id)
        if biome is None:
            raise ResolverError("biome", biome_id)
        return biome


class EcologyResolver:
    def __init__(self, repo: CatalogRepository) -> None:
        self._repo = repo

    def resolve(self, ecology_id: str) -> EcologyDefinition:
        eco = self._repo.get_ecology(ecology_id)
        if eco is None:
            raise ResolverError("ecology", ecology_id)
        return eco


class RegionResolver:
    def __init__(self, repo: CatalogRepository) -> None:
        self._repo = repo

    def resolve(self, region_id: str) -> RuntimeRegionDefinition:
        reg = self._repo.get_region(region_id)
        if reg is None:
            raise ResolverError("region", region_id)
        return reg


class ResourceResolver:
    def __init__(self, repo: CatalogRepository) -> None:
        self._repo = repo

    def resolve(self, resource_id: str) -> ResourceDefinition:
        res = self._repo.get_resource(resource_id)
        if res is None:
            raise ResolverError("resource", resource_id)
        return res


class BuildingResolver:
    def __init__(self, repo: CatalogRepository) -> None:
        self._repo = repo

    def resolve(self, building_id: str) -> BuildingDefinition:
        bld = self._repo.get_building(building_id)
        if bld is None:
            raise ResolverError("building", building_id)
        return bld


class RelationshipResolver:
    def __init__(self, repo: CatalogRepository) -> None:
        self._repo = repo

    def resolve(self, relationship_id: str) -> FactionRelationshipDefinition:
        rel = self._repo.get_faction_relationship(relationship_id)
        if rel is None:
            raise ResolverError("relationship", relationship_id)
        return rel
