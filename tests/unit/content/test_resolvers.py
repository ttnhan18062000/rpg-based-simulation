"""
tests/unit/content/test_resolvers.py
───────────────────────────────────────────────────────────────────────────────
Phase 24 — Unit tests for the resolver layer.
Phase 25 — Entity archetype and population resolution tests.

Covers FoundationResolver, LivingDefaultsResolver, SocialDefaultsResolver,
ResolvedLivingDefaults, EntityArchetypeResolver, ResolvedEntityArchetype,
and PopulationRecipeResolver.
"""
from __future__ import annotations

import pytest

from src.content.repository import CatalogRepository
from src.content.resolver import (
    EntityArchetypeResolver,
    FoundationResolver,
    LivingDefaultsResolver,
    PopulationRecipeResolver,
    ResolvedEntityArchetype,
    ResolvedLivingDefaults,
    ResolverError,
    SocialDefaultsResolver,
)
from src.content.schema import (
    AttributeDefinition,
    BodyModelDefinition,
    CognitionProfileDefinition,
    DriveProfileDefinition,
    ElementDefinition,
    FactionDefinition,
    FactionRelationshipDefinition,
    MaterialDefinition,
    NeedProfileDefinition,
    PerspectiveDefinition,
    RelationshipAxisDefinition,
    RoleDefinition,
    SenseProfileDefinition,
    ThemeDefinition,
    TraitDefinition,
)


# ===========================================================================
# Fixtures
# ===========================================================================

@pytest.fixture(scope="module")
def loaded_repo() -> CatalogRepository:
    """Return a fully loaded CatalogRepository from the real catalog data."""
    repo = CatalogRepository("data/content")
    repo.load_all()
    return repo


@pytest.fixture(scope="module")
def foundation(loaded_repo: CatalogRepository) -> FoundationResolver:
    return FoundationResolver(loaded_repo)


@pytest.fixture(scope="module")
def social(loaded_repo: CatalogRepository) -> SocialDefaultsResolver:
    return SocialDefaultsResolver(loaded_repo)


@pytest.fixture(scope="module")
def living(loaded_repo: CatalogRepository) -> LivingDefaultsResolver:
    return LivingDefaultsResolver(loaded_repo)


# ===========================================================================
# ResolverError
# ===========================================================================

class TestResolverError:
    def test_is_key_error(self):
        err = ResolverError("trait", "nonexistent")
        assert isinstance(err, KeyError)

    def test_message_contains_family_and_id(self):
        err = ResolverError("attribute", "bad_id")
        msg = str(err)
        assert "attribute" in msg
        assert "bad_id" in msg

    def test_message_with_context(self):
        err = ResolverError("body_model", "ghost", context="referenced by race 'test_race'")
        msg = str(err)
        assert "test_race" in msg
        assert "ghost" in msg

    def test_attributes_accessible(self):
        err = ResolverError("material", "void_stone")
        assert err.family == "material"
        assert err.missing_id == "void_stone"


# ===========================================================================
# FoundationResolver — single-record resolution
# ===========================================================================

class TestFoundationResolverSingle:
    def test_resolve_attribute_known(self, foundation: FoundationResolver):
        attr = foundation.resolve_attribute("strength")
        assert isinstance(attr, AttributeDefinition)
        assert attr.id == "strength"

    def test_resolve_attribute_missing_raises(self, foundation: FoundationResolver):
        with pytest.raises(ResolverError) as exc_info:
            foundation.resolve_attribute("nonexistent_attribute")
        assert isinstance(exc_info.value, KeyError)
        assert "attribute" in str(exc_info.value)
        assert "nonexistent_attribute" in str(exc_info.value)

    def test_resolve_material_known(self, foundation: FoundationResolver):
        mat = foundation.resolve_material("wood")
        assert isinstance(mat, MaterialDefinition)
        assert mat.id == "wood"

    def test_resolve_material_missing_raises(self, foundation: FoundationResolver):
        with pytest.raises(ResolverError):
            foundation.resolve_material("void_stone_xxxx")

    def test_resolve_trait_known(self, foundation: FoundationResolver):
        trait = foundation.resolve_trait("humanoid")
        assert isinstance(trait, TraitDefinition)
        assert trait.id == "humanoid"

    def test_resolve_trait_missing_raises(self, foundation: FoundationResolver):
        with pytest.raises(ResolverError):
            foundation.resolve_trait("nonexistent_trait_xxxx")

    def test_resolve_theme_known(self, foundation: FoundationResolver):
        theme = foundation.resolve_theme("frontier")
        assert isinstance(theme, ThemeDefinition)
        assert theme.id == "frontier"

    def test_resolve_theme_missing_raises(self, foundation: FoundationResolver):
        with pytest.raises(ResolverError):
            foundation.resolve_theme("nonexistent_theme_xxxx")

    def test_resolve_element_known(self, foundation: FoundationResolver):
        elem = foundation.resolve_element("physical")
        assert isinstance(elem, ElementDefinition)
        assert elem.id == "physical"

    def test_resolve_element_missing_raises(self, foundation: FoundationResolver):
        with pytest.raises(ResolverError):
            foundation.resolve_element("void_element_xxxx")

    def test_resolve_relationship_axis_known(self, foundation: FoundationResolver):
        axis = foundation.resolve_relationship_axis("hostility")
        assert isinstance(axis, RelationshipAxisDefinition)
        assert axis.id == "hostility"

    def test_resolve_relationship_axis_missing_raises(self, foundation: FoundationResolver):
        with pytest.raises(ResolverError):
            foundation.resolve_relationship_axis("nonexistent_axis_xxxx")


# ===========================================================================
# FoundationResolver — batch helpers
# ===========================================================================

class TestFoundationResolverBatch:
    def test_resolve_traits_returns_list(self, foundation: FoundationResolver):
        traits = foundation.resolve_traits(["humanoid", "tool_user"])
        assert len(traits) == 2
        assert all(isinstance(t, TraitDefinition) for t in traits)

    def test_resolve_traits_preserves_order(self, foundation: FoundationResolver):
        ids = ["tool_user", "humanoid", "pack_hunter"]
        traits = foundation.resolve_traits(ids)
        assert [t.id for t in traits] == ids

    def test_resolve_traits_empty_input(self, foundation: FoundationResolver):
        assert foundation.resolve_traits([]) == []

    def test_resolve_traits_missing_raises(self, foundation: FoundationResolver):
        with pytest.raises(ResolverError):
            foundation.resolve_traits(["humanoid", "nonexistent_trait_xxxx"])

    def test_resolve_themes_returns_list(self, foundation: FoundationResolver):
        themes = foundation.resolve_themes(["frontier", "village"])
        assert len(themes) == 2
        assert all(isinstance(t, ThemeDefinition) for t in themes)

    def test_resolve_themes_preserves_order(self, foundation: FoundationResolver):
        ids = ["village", "frontier", "forest"]
        themes = foundation.resolve_themes(ids)
        assert [t.id for t in themes] == ids

    def test_resolve_themes_missing_raises(self, foundation: FoundationResolver):
        with pytest.raises(ResolverError):
            foundation.resolve_themes(["frontier", "nonexistent_theme_xxxx"])

    def test_resolve_materials_returns_list(self, foundation: FoundationResolver):
        materials = foundation.resolve_materials(["wood", "herb"])
        assert len(materials) == 2
        assert all(isinstance(m, MaterialDefinition) for m in materials)

    def test_resolve_materials_preserves_order(self, foundation: FoundationResolver):
        ids = ["herb", "wood"]
        materials = foundation.resolve_materials(ids)
        assert [m.id for m in materials] == ids

    def test_resolve_materials_missing_raises(self, foundation: FoundationResolver):
        with pytest.raises(ResolverError):
            foundation.resolve_materials(["wood", "nonexistent_material_xxxx"])


# ===========================================================================
# FoundationResolver — no runtime simulation imports
# ===========================================================================

class TestFoundationResolverIsolation:
    def test_module_does_not_import_runtime(self):
        """The resolver module must not import runtime simulation systems."""
        import src.content.resolver as resolver_mod
        import sys
        runtime_modules = [
            "src.engine",
            "src.domains",
            "src.core.conservation",
        ]
        for mod in runtime_modules:
            # The resolver itself must not cause these to be imported
            # (they might already be loaded from other tests, so check direct imports)
            resolver_source = resolver_mod.__file__
            assert resolver_source is not None
            with open(resolver_source) as f:
                source_text = f.read()
            for rt_mod in runtime_modules:
                assert f"import {rt_mod}" not in source_text, (
                    f"resolver.py must not import {rt_mod}"
                )


# ===========================================================================
# LivingDefaultsResolver
# ===========================================================================

class TestLivingDefaultsResolver:
    def test_resolve_human_returns_resolved_defaults(self, living: LivingDefaultsResolver):
        result = living.resolve_living_defaults("human")
        assert isinstance(result, ResolvedLivingDefaults)

    def test_resolve_human_body_model(self, living: LivingDefaultsResolver):
        result = living.resolve_living_defaults("human")
        assert isinstance(result.body_model, BodyModelDefinition)
        assert result.body_model.id == "standard_humanoid"

    def test_resolve_human_need_profile(self, living: LivingDefaultsResolver):
        result = living.resolve_living_defaults("human")
        assert isinstance(result.need_profile, NeedProfileDefinition)
        assert result.need_profile.id == "humanoid_survival"

    def test_resolve_human_sense_profile(self, living: LivingDefaultsResolver):
        result = living.resolve_living_defaults("human")
        assert isinstance(result.sense_profile, SenseProfileDefinition)
        assert result.sense_profile.id == "normal_humanoid_senses"

    def test_resolve_human_cognition_profile(self, living: LivingDefaultsResolver):
        result = living.resolve_living_defaults("human")
        assert isinstance(result.cognition_profile, CognitionProfileDefinition)
        assert result.cognition_profile.id == "practical_humanoid"

    def test_resolve_human_drive_profile(self, living: LivingDefaultsResolver):
        result = living.resolve_living_defaults("human")
        assert isinstance(result.drive_profile, DriveProfileDefinition)
        assert result.drive_profile.id == "cautious_commoner"

    def test_resolve_human_natural_traits(self, living: LivingDefaultsResolver):
        result = living.resolve_living_defaults("human")
        assert isinstance(result.natural_traits, list)
        assert len(result.natural_traits) == 3  # humanoid, tool_user, social_humanoid
        assert all(isinstance(t, TraitDefinition) for t in result.natural_traits)
        trait_ids = [t.id for t in result.natural_traits]
        assert "humanoid" in trait_ids
        assert "tool_user" in trait_ids

    def test_resolve_human_natural_traits_order_preserved(self, living: LivingDefaultsResolver):
        """Natural traits must be returned in the same order as declared in the race definition."""
        result = living.resolve_living_defaults("human")
        trait_ids = [t.id for t in result.natural_traits]
        assert trait_ids == ["humanoid", "tool_user", "social_humanoid"]

    def test_resolve_human_attribute_tendencies_dict(self, living: LivingDefaultsResolver):
        result = living.resolve_living_defaults("human")
        assert isinstance(result.attribute_tendencies, dict)
        assert "strength" in result.attribute_tendencies
        assert "intelligence" in result.attribute_tendencies

    def test_resolve_human_attribute_tendencies_values(self, living: LivingDefaultsResolver):
        result = living.resolve_living_defaults("human")
        assert result.attribute_tendencies["strength"] == "medium"
        assert result.attribute_tendencies["intelligence"] == "medium_high"

    def test_resolve_human_compatible_roles(self, living: LivingDefaultsResolver):
        result = living.resolve_living_defaults("human")
        assert isinstance(result.compatible_roles, list)
        assert all(isinstance(r, RoleDefinition) for r in result.compatible_roles)
        role_ids = [r.id for r in result.compatible_roles]
        assert "hero" in role_ids
        assert "worker" in role_ids

    def test_resolve_human_compatible_roles_order_preserved(self, living: LivingDefaultsResolver):
        """Compatible roles must be in the same order as declared in the race definition."""
        result = living.resolve_living_defaults("human")
        role_ids = [r.id for r in result.compatible_roles]
        # human's compatible_roles as declared in races.yaml (first few entries)
        assert role_ids[0] == "hero"
        assert role_ids[1] == "worker"
        assert role_ids[2] == "citizen"

    def test_resolve_wolf_defaults(self, living: LivingDefaultsResolver):
        result = living.resolve_living_defaults("wolf")
        assert result.body_model.id == "quadruped_predator"
        assert result.cognition_profile.id == "instinctive_animal"
        trait_ids = [t.id for t in result.natural_traits]
        assert "pack_hunter" in trait_ids
        assert "territorial" in trait_ids

    def test_resolve_missing_race_raises(self, living: LivingDefaultsResolver):
        with pytest.raises(ResolverError) as exc_info:
            living.resolve_living_defaults("nonexistent_race_xxxx")
        assert "race" in str(exc_info.value)
        assert "nonexistent_race_xxxx" in str(exc_info.value)

    def test_resolve_living_defaults_returns_frozen_model(self, living: LivingDefaultsResolver):
        """ResolvedLivingDefaults must be immutable (frozen Pydantic model)."""
        result = living.resolve_living_defaults("human")
        with pytest.raises(Exception):
            result.attribute_tendencies = {}  # type: ignore[misc]


# ===========================================================================
# SocialDefaultsResolver
# ===========================================================================

class TestSocialDefaultsResolver:
    # --- Role ---

    def test_resolve_role_known(self, social: SocialDefaultsResolver):
        role = social.resolve_role_defaults("hero")
        assert isinstance(role, RoleDefinition)
        assert role.id == "hero"

    def test_resolve_role_worker(self, social: SocialDefaultsResolver):
        role = social.resolve_role_defaults("worker")
        assert isinstance(role, RoleDefinition)
        assert role.id == "worker"

    def test_resolve_role_missing_raises(self, social: SocialDefaultsResolver):
        with pytest.raises(ResolverError) as exc_info:
            social.resolve_role_defaults("nonexistent_role_xxxx")
        assert "role" in str(exc_info.value)
        assert isinstance(exc_info.value, KeyError)

    # --- Faction ---

    def test_resolve_faction_known(self, social: SocialDefaultsResolver):
        faction = social.resolve_faction_defaults("town_council")
        assert isinstance(faction, FactionDefinition)
        assert faction.id == "town_council"

    def test_resolve_faction_missing_raises(self, social: SocialDefaultsResolver):
        with pytest.raises(ResolverError) as exc_info:
            social.resolve_faction_defaults("nonexistent_faction_xxxx")
        assert "faction" in str(exc_info.value)
        assert isinstance(exc_info.value, KeyError)

    # --- Faction Relationship ---

    def test_resolve_faction_relationship_known(self, social: SocialDefaultsResolver):
        rel = social.resolve_faction_relationship("town_council", "wild_beast_pack")
        assert isinstance(rel, FactionRelationshipDefinition)
        assert rel.source_faction == "town_council"
        assert rel.target_faction == "wild_beast_pack"

    def test_resolve_faction_relationship_returns_correct_record(self, social: SocialDefaultsResolver):
        rel = social.resolve_faction_relationship("wild_beast_pack", "town_council")
        assert rel.source_faction == "wild_beast_pack"
        assert rel.target_faction == "town_council"

    def test_resolve_faction_relationship_missing_source_raises(self, social: SocialDefaultsResolver):
        with pytest.raises(ResolverError) as exc_info:
            social.resolve_faction_relationship("nonexistent_faction_xxxx", "town_council")
        assert "faction" in str(exc_info.value)
        assert "nonexistent_faction_xxxx" in str(exc_info.value)

    def test_resolve_faction_relationship_missing_target_raises(self, social: SocialDefaultsResolver):
        with pytest.raises(ResolverError) as exc_info:
            social.resolve_faction_relationship("town_council", "nonexistent_faction_xxxx")
        assert "faction" in str(exc_info.value)
        assert "nonexistent_faction_xxxx" in str(exc_info.value)

    def test_resolve_faction_relationship_no_record_raises(self, social: SocialDefaultsResolver):
        """Two valid factions with no defined relationship record should raise ResolverError."""
        with pytest.raises(ResolverError) as exc_info:
            # Both are valid factions but may not have a relationship defined between them
            # Using factions known to not have a direct relationship to test the "no record" path
            social.resolve_faction_relationship("hero_guild", "dwarven_mine_clan")
        assert "faction_relationship" in str(exc_info.value)

    # --- Perspective ---

    def test_resolve_perspective_known(self, social: SocialDefaultsResolver):
        perspective = social.resolve_perspective("hero_guild_perspective")
        assert isinstance(perspective, PerspectiveDefinition)
        assert perspective.id == "hero_guild_perspective"

    def test_resolve_perspective_another(self, social: SocialDefaultsResolver):
        perspective = social.resolve_perspective("wild_beast_pack_perspective")
        assert isinstance(perspective, PerspectiveDefinition)
        assert perspective.id == "wild_beast_pack_perspective"

    def test_resolve_perspective_missing_raises(self, social: SocialDefaultsResolver):
        with pytest.raises(ResolverError) as exc_info:
            social.resolve_perspective("nonexistent_perspective_xxxx")
        assert "perspective" in str(exc_info.value)
        assert isinstance(exc_info.value, KeyError)


# ===========================================================================
# EntityArchetypeResolver — Phase 25
# ===========================================================================

@pytest.fixture(scope="module")
def archetype_resolver(loaded_repo: CatalogRepository) -> EntityArchetypeResolver:
    return EntityArchetypeResolver(loaded_repo)


class TestEntityArchetypeResolver:

    # --- Basic resolution ---

    def test_resolve_hungry_wolf_returns_type(
        self, archetype_resolver: EntityArchetypeResolver
    ):
        result = archetype_resolver.resolve("hungry_wolf")
        assert isinstance(result, ResolvedEntityArchetype)

    def test_resolve_hungry_wolf_identity(
        self, archetype_resolver: EntityArchetypeResolver
    ):
        result = archetype_resolver.resolve("hungry_wolf")
        assert result.archetype_id == "hungry_wolf"
        assert result.race_id == "wolf"
        assert result.faction_id == "wild_beast_pack"
        assert result.role_id == "predator_hunter"

    def test_resolve_wolf_stat_profile(
        self, archetype_resolver: EntityArchetypeResolver
    ):
        result = archetype_resolver.resolve("hungry_wolf")
        assert result.stat_profile.id == "wolf_predator_base"

    def test_resolve_wolf_combat_profile(
        self, archetype_resolver: EntityArchetypeResolver
    ):
        result = archetype_resolver.resolve("hungry_wolf")
        assert result.combat_profile.id == "predator_melee"

    def test_resolve_wolf_cognition_profile_from_archetype(
        self, archetype_resolver: EntityArchetypeResolver
    ):
        """Archetype's explicit cognition_profile should override role default."""
        result = archetype_resolver.resolve("hungry_wolf")
        assert result.cognition_profile.id == "instinctive_animal"

    def test_resolve_wolf_drive_profile(
        self, archetype_resolver: EntityArchetypeResolver
    ):
        result = archetype_resolver.resolve("hungry_wolf")
        assert result.drive_profile.id == "territorial_predator"

    # --- Race defaults propagated ---

    def test_resolve_wolf_need_profile_from_race(
        self, archetype_resolver: EntityArchetypeResolver
    ):
        """need_profile comes from race defaults, not the archetype directly."""
        result = archetype_resolver.resolve("hungry_wolf")
        # wolf race has need_profile = "carnivore_survival"
        assert result.need_profile.id == "carnivore_survival"

    def test_resolve_wolf_sense_profile_from_race(
        self, archetype_resolver: EntityArchetypeResolver
    ):
        """sense_profile comes from race defaults."""
        result = archetype_resolver.resolve("hungry_wolf")
        assert result.sense_profile.id == "predator_smell_senses"

    # --- Trait merge ---

    def test_resolve_wolf_traits_include_archetype_traits(
        self, archetype_resolver: EntityArchetypeResolver
    ):
        result = archetype_resolver.resolve("hungry_wolf")
        trait_ids = [t.id for t in result.traits]
        # Archetype declares: pack_hunter, territorial, carnivore
        assert "pack_hunter" in trait_ids
        assert "territorial" in trait_ids
        assert "carnivore" in trait_ids

    def test_resolve_wolf_traits_archetype_first_in_order(
        self, archetype_resolver: EntityArchetypeResolver
    ):
        """Archetype traits appear before appended race natural_traits."""
        result = archetype_resolver.resolve("hungry_wolf")
        trait_ids = [t.id for t in result.traits]
        # First three are archetype-declared
        assert trait_ids[0] == "pack_hunter"
        assert trait_ids[1] == "territorial"
        assert trait_ids[2] == "carnivore"

    def test_resolve_wolf_traits_no_duplicates(
        self, archetype_resolver: EntityArchetypeResolver
    ):
        result = archetype_resolver.resolve("hungry_wolf")
        trait_ids = [t.id for t in result.traits]
        assert len(trait_ids) == len(set(trait_ids))

    def test_resolve_wolf_race_traits_appended_if_not_in_archetype(
        self, archetype_resolver: EntityArchetypeResolver
    ):
        """
        Wolf race has natural_traits: [pack_hunter, territorial, carnivore].
        All three are also in the hungry_wolf archetype, so no extras should be appended.
        The alpha_wolf has 'leader' plus the same wolf naturals — verify no duplicates.
        """
        result = archetype_resolver.resolve("alpha_wolf")
        trait_ids = [t.id for t in result.traits]
        # Should have pack_hunter, territorial, carnivore, leader (all from archetype)
        # Race naturals overlap; no duplicates expected
        assert len(trait_ids) == len(set(trait_ids))
        assert "leader" in trait_ids

    # --- Themes ---

    def test_resolve_wolf_themes(
        self, archetype_resolver: EntityArchetypeResolver
    ):
        result = archetype_resolver.resolve("hungry_wolf")
        theme_ids = [t.id for t in result.themes]
        assert "forest" in theme_ids
        assert "wolf_den" in theme_ids

    def test_resolve_themes_order_preserved(
        self, archetype_resolver: EntityArchetypeResolver
    ):
        result = archetype_resolver.resolve("hungry_wolf")
        theme_ids = [t.id for t in result.themes]
        assert theme_ids == ["forest", "wolf_den"]

    # --- Projection ---

    def test_resolve_wolf_legacy_engine_role(
        self, archetype_resolver: EntityArchetypeResolver
    ):
        result = archetype_resolver.resolve("hungry_wolf")
        assert isinstance(result.legacy_engine_role, str)
        assert result.legacy_engine_role == "MONSTER"  # predator_hunter -> MONSTER

    def test_resolve_wolf_legacy_engine_bucket(
        self, archetype_resolver: EntityArchetypeResolver
    ):
        result = archetype_resolver.resolve("hungry_wolf")
        assert isinstance(result.legacy_engine_bucket, str)
        assert result.legacy_engine_bucket == "MONSTER_HORDE"  # wild_beast_pack -> MONSTER_HORDE

    # --- Human worker ---

    def test_resolve_village_worker_identity(
        self, archetype_resolver: EntityArchetypeResolver
    ):
        result = archetype_resolver.resolve("village_worker")
        assert result.archetype_id == "village_worker"
        assert result.race_id == "human"
        assert result.role_id == "worker"
        assert result.faction_id == "town_council"

    def test_resolve_village_worker_need_profile_from_human_race(
        self, archetype_resolver: EntityArchetypeResolver
    ):
        result = archetype_resolver.resolve("village_worker")
        assert result.need_profile.id == "humanoid_survival"

    def test_resolve_village_worker_legacy_role(
        self, archetype_resolver: EntityArchetypeResolver
    ):
        result = archetype_resolver.resolve("village_worker")
        assert result.legacy_engine_role == "WORKER"

    def test_resolve_village_worker_legacy_faction(
        self, archetype_resolver: EntityArchetypeResolver
    ):
        result = archetype_resolver.resolve("village_worker")
        assert result.legacy_engine_bucket == "TOWN_COUNCIL"

    # --- Goblin raider ---

    def test_resolve_goblin_raider_explicit_profiles_override(
        self, archetype_resolver: EntityArchetypeResolver
    ):
        """Explicit archetype profiles override race defaults."""
        result = archetype_resolver.resolve("goblin_raider")
        assert result.stat_profile.id == "goblin_raider_base"
        assert result.combat_profile.id == "opportunist_raider"

    def test_resolve_goblin_raider_drive_profile(
        self, archetype_resolver: EntityArchetypeResolver
    ):
        result = archetype_resolver.resolve("goblin_raider")
        assert result.drive_profile.id == "opportunistic_raider"

    # --- Boss-like: goblin warlord ---

    def test_resolve_goblin_warlord_no_boss_class(
        self, archetype_resolver: EntityArchetypeResolver
    ):
        """Boss-like archetype resolves as a normal archetype with strong stats/traits."""
        result = archetype_resolver.resolve("goblin_warlord")
        assert isinstance(result, ResolvedEntityArchetype)
        # No special boss attribute — just regular fields
        assert not hasattr(result, "is_boss")
        assert not hasattr(result, "enemy_label")
        assert result.stat_profile.id == "warlord_base"
        assert "leader" in [t.id for t in result.traits]

    # --- Frozen model ---

    def test_resolve_archetype_result_is_frozen(
        self, archetype_resolver: EntityArchetypeResolver
    ):
        result = archetype_resolver.resolve("hungry_wolf")
        with pytest.raises(Exception):
            result.archetype_id = "mutated"  # type: ignore[misc]

    # --- Error cases ---

    def test_resolve_missing_archetype_raises(
        self, archetype_resolver: EntityArchetypeResolver
    ):
        with pytest.raises(ResolverError) as exc_info:
            archetype_resolver.resolve("nonexistent_archetype_xxxx")
        assert "entity_archetype" in str(exc_info.value)
        assert "nonexistent_archetype_xxxx" in str(exc_info.value)

    # --- resolve_all ---

    def test_resolve_all_returns_all_archetypes(
        self, loaded_repo: CatalogRepository, archetype_resolver: EntityArchetypeResolver
    ):
        all_archetypes = archetype_resolver.resolve_all()
        assert len(all_archetypes) == len(loaded_repo.entity_archetypes)
        assert all(isinstance(v, ResolvedEntityArchetype) for v in all_archetypes.values())

    def test_resolve_all_keys_match_archetype_ids(
        self, archetype_resolver: EntityArchetypeResolver
    ):
        all_archetypes = archetype_resolver.resolve_all()
        for arch_id, resolved in all_archetypes.items():
            assert resolved.archetype_id == arch_id

    def test_resolve_all_every_archetype_has_legacy_projection(
        self, archetype_resolver: EntityArchetypeResolver
    ):
        all_archetypes = archetype_resolver.resolve_all()
        for resolved in all_archetypes.values():
            assert isinstance(resolved.legacy_engine_role, str)
            assert isinstance(resolved.legacy_engine_bucket, str)


# ===========================================================================
# PopulationRecipeResolver — Phase 25
# ===========================================================================

@pytest.fixture(scope="module")
def pop_resolver(loaded_repo: CatalogRepository) -> PopulationRecipeResolver:
    return PopulationRecipeResolver(loaded_repo)


class TestPopulationRecipeResolver:

    def test_resolve_wolf_pack_returns_tuple(
        self, pop_resolver: PopulationRecipeResolver
    ):
        expanded, preferred_regions = pop_resolver.resolve("wolf_pack_small")
        assert isinstance(expanded, list)
        assert isinstance(preferred_regions, list)

    def test_resolve_wolf_pack_member_count(
        self, pop_resolver: PopulationRecipeResolver
    ):
        expanded, _ = pop_resolver.resolve("wolf_pack_small")
        # wolf_pack_small: hungry_wolf: 4, alpha_wolf: 1
        assert len(expanded) == 2

    def test_resolve_wolf_pack_members_are_archetype_tuples(
        self, pop_resolver: PopulationRecipeResolver
    ):
        expanded, _ = pop_resolver.resolve("wolf_pack_small")
        for resolved_arch, count in expanded:
            assert isinstance(resolved_arch, ResolvedEntityArchetype)
            assert isinstance(count, int)
            assert count > 0

    def test_resolve_wolf_pack_order_preserved(
        self, pop_resolver: PopulationRecipeResolver
    ):
        """Member order must match the YAML members dict insertion order."""
        expanded, _ = pop_resolver.resolve("wolf_pack_small")
        arch_ids = [a.archetype_id for a, _ in expanded]
        assert arch_ids == ["hungry_wolf", "alpha_wolf"]

    def test_resolve_wolf_pack_counts(
        self, pop_resolver: PopulationRecipeResolver
    ):
        expanded, _ = pop_resolver.resolve("wolf_pack_small")
        counts = {a.archetype_id: c for a, c in expanded}
        assert counts["hungry_wolf"] == 4
        assert counts["alpha_wolf"] == 1

    def test_resolve_wolf_pack_preferred_regions(
        self, pop_resolver: PopulationRecipeResolver
    ):
        _, preferred_regions = pop_resolver.resolve("wolf_pack_small")
        assert "wolf_den" in preferred_regions
        assert "near_forest" in preferred_regions

    def test_resolve_goblin_raiding_party_expands_four_archetypes(
        self, pop_resolver: PopulationRecipeResolver
    ):
        expanded, _ = pop_resolver.resolve("goblin_raiding_party")
        arch_ids = [a.archetype_id for a, _ in expanded]
        # goblin_raiding_party: goblin_scout:2, goblin_raider:4, goblin_archer:2, goblin_warlord:1
        assert len(expanded) == 4
        assert "goblin_scout" in arch_ids
        assert "goblin_raider" in arch_ids
        assert "goblin_archer" in arch_ids
        assert "goblin_warlord" in arch_ids

    def test_resolve_all_members_convenience_method(
        self, pop_resolver: PopulationRecipeResolver
    ):
        expanded = pop_resolver.resolve_all_members("wolf_pack_small")
        assert len(expanded) == 2
        assert all(isinstance(a, ResolvedEntityArchetype) for a, _ in expanded)

    def test_resolve_missing_population_raises(
        self, pop_resolver: PopulationRecipeResolver
    ):
        with pytest.raises(ResolverError) as exc_info:
            pop_resolver.resolve("nonexistent_population_xxxx")
        assert "population_recipe" in str(exc_info.value)
        assert "nonexistent_population_xxxx" in str(exc_info.value)
        assert isinstance(exc_info.value, KeyError)

    def test_resolve_deterministic_across_calls(
        self, pop_resolver: PopulationRecipeResolver
    ):
        """Two calls to the same population recipe must return the same result."""
        expanded1, regions1 = pop_resolver.resolve("wolf_pack_small")
        expanded2, regions2 = pop_resolver.resolve("wolf_pack_small")
        ids1 = [(a.archetype_id, c) for a, c in expanded1]
        ids2 = [(a.archetype_id, c) for a, c in expanded2]
        assert ids1 == ids2
        assert regions1 == regions2

    # --- Three-case contract (documented in resolver.py docstring) ---

    def test_case1_valid_recipe_expands_members(
        self, pop_resolver: PopulationRecipeResolver
    ):
        """Case 1: valid recipe ID → expands to full member list."""
        expanded, preferred_regions = pop_resolver.resolve("wolf_pack_small")
        assert len(expanded) >= 1
        assert isinstance(expanded[0][0], ResolvedEntityArchetype)

    def test_case2_direct_archetype_id_returns_single_entity(
        self, pop_resolver: PopulationRecipeResolver
    ):
        """Case 2: population_id is a valid archetype ID (not a recipe) → single-entity shorthand.

        Returns [(archetype, 1)] with empty preferred_regions.
        This is the intentional direct-archetype shorthand documented in the resolver.
        """
        # "hungry_wolf" is a known archetype (used inside wolf_pack_small recipe) but is not itself a recipe
        expanded, preferred_regions = pop_resolver.resolve("hungry_wolf")
        assert len(expanded) == 1
        resolved_arch, count = expanded[0]
        assert isinstance(resolved_arch, ResolvedEntityArchetype)
        assert resolved_arch.archetype_id == "hungry_wolf"
        assert count == 1
        assert preferred_regions == []

    def test_case3_unknown_id_raises_resolver_error(
        self, pop_resolver: PopulationRecipeResolver
    ):
        """Case 3: population_id is neither a recipe nor an archetype → raises ResolverError."""
        with pytest.raises(ResolverError) as exc_info:
            pop_resolver.resolve("totally_nonexistent_id_xxxx")
        assert "population_recipe" in str(exc_info.value)
        assert "totally_nonexistent_id_xxxx" in str(exc_info.value)


# ===========================================================================
# PopulationSpec.archetype_id field contract
# TCK-20260607-ARCHETYPE-METADATA-EXPLICIT
# ===========================================================================

class TestPopulationSpecArchetypeId:

    def test_population_spec_archetype_id_field_exists(self):
        """Explicit archetype_id is readable and holds the supplied value."""
        from src.worldbuilding.schema import PopulationSpec
        p = PopulationSpec(
            id="test_pop",
            count=3,
            role="raider",
            faction="goblin_warband",
            spawn_region="goblin_camp",
            archetype_id="hungry_wolf",
        )
        assert p.archetype_id == "hungry_wolf"

    def test_population_spec_archetype_id_defaults_to_none(self):
        """archetype_id defaults to None when not supplied."""
        from src.worldbuilding.schema import PopulationSpec
        p = PopulationSpec(
            id="test_pop",
            count=1,
            role="raider",
            faction="goblin_warband",
            spawn_region="goblin_camp",
        )
        assert p.archetype_id is None

    def test_population_spec_is_still_frozen_after_field_addition(self):
        """frozen=True invariant is preserved after adding the archetype_id field."""
        from src.worldbuilding.schema import PopulationSpec
        p = PopulationSpec(
            id="test_pop",
            count=1,
            role="raider",
            faction="goblin_warband",
            spawn_region="goblin_camp",
            archetype_id="hungry_wolf",
        )
        with pytest.raises(Exception):
            p.archetype_id = "alpha_wolf"  # type: ignore[misc]

    def test_case2_result_resolvedentityarchetype_has_archetype_id(
        self, pop_resolver: PopulationRecipeResolver
    ):
        """Case 2: resolver returns a ResolvedEntityArchetype whose archetype_id equals the input."""
        expanded, _ = pop_resolver.resolve("hungry_wolf")
        assert len(expanded) == 1
        resolved_arch, _ = expanded[0]
        assert resolved_arch.archetype_id == "hungry_wolf"

    def test_case1_recipe_members_each_have_archetype_id(
        self, loaded_repo: CatalogRepository, pop_resolver: PopulationRecipeResolver
    ):
        """Case 1: every expanded archetype carries a non-empty archetype_id present in catalog."""
        expanded, _ = pop_resolver.resolve("wolf_pack_small")
        for arch, _ in expanded:
            assert arch.archetype_id, "archetype_id must not be empty"
            assert loaded_repo.get_entity_archetype(arch.archetype_id) is not None, (
                f"archetype_id '{arch.archetype_id}' not found in catalog"
            )


# ===========================================================================
# TCK-20260810-COGNITION-PROFILE-ADVENTURE-ELIGIBILITY: supports_adventure_routing field
# ===========================================================================

def test_schema_supports_adventure_routing_field(loaded_repo: CatalogRepository):
    """CognitionProfileDefinition.supports_adventure_routing defaults False and all 7 authored
    profiles in data/content/living/cognition_profiles.yaml parse with their intended explicit
    value (no profile silently left at the schema default by omission)."""
    expected = {
        "practical_humanoid": True,
        "instinctive_animal": False,
        "opportunistic_humanoid": True,
        "disciplined_guard": True,
        "trade_pragmatist": True,
        "arcane_scholar": True,
        "undead_fixated": False,
    }
    for profile_id, expected_value in expected.items():
        profile = loaded_repo.get_cognition_profile(profile_id)
        assert profile is not None, f"cognition profile '{profile_id}' not found in catalog"
        assert isinstance(profile.supports_adventure_routing, bool)
        assert profile.supports_adventure_routing is expected_value, (
            f"{profile_id}.supports_adventure_routing expected {expected_value}, "
            f"got {profile.supports_adventure_routing}"
        )

    unauthored = CognitionProfileDefinition(id="unauthored_test_profile")
    assert unauthored.supports_adventure_routing is False
