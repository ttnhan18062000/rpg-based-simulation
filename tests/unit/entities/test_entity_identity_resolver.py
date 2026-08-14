import pytest

from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole, Faction
from src.entities.archetype_factory import ArchetypeEntityFactory, EntitySpawnContext
from src.entities.runtime_contract import ResolvedEntityRuntimeContract
from src.entities.identity_resolver import EntityIdentityResolver, IdentityResolutionError


RESOLVER = EntityIdentityResolver()
FACTORY = ArchetypeEntityFactory()


def _make_contract(**kw) -> ResolvedEntityRuntimeContract:
    defaults = dict(
        archetype_id="human_worker",
        race_id="human",
        faction_id="town_council",
        role_id="worker",
        kind="humanoid",
        hp=80, max_hp=80, atk=8, def_stat=4,
        attack_range=1, readiness=100.0,
        inventory_items={}, starting_gold=0.0,
        traits=(), themes=(),
    )
    defaults.update(kw)
    return ResolvedEntityRuntimeContract(**defaults)


def test_clean_archetype_contract_resolves_clean_identity():
    contract = _make_contract(
        archetype_id="human_worker",
        race_id="human",
        faction_id="town_council",
        role_id="worker",
        legacy_role=EntityRole.HERO,
        legacy_faction=Faction.HERO_GUILD,
    )
    entity = FACTORY.build_entity(1, contract, EntitySpawnContext())
    identity = RESOLVER.resolve(entity)

    assert identity.source == "clean_metadata"
    assert identity.faction_id == "town_council"
    assert identity.role_id == "worker"
    assert identity.archetype_id == "human_worker"
    assert identity.race_id == "human"


def test_clean_faction_role_only_resolves_clean_identity():
    entity = (
        V2EntityBuilder(2)
        .kind("humanoid")
        .identity(properties={"faction_id": "merchant_league", "role_id": "trader"})
        .build()
    )
    identity = RESOLVER.resolve(entity)
    assert identity.source == "clean_metadata"
    assert identity.faction_id == "merchant_league"
    assert identity.role_id == "trader"


def test_legacy_only_arena_entity_resolves_via_legacy_enum():
    entity = (
        V2EntityBuilder(3)
        .kind("hero")
        .identity(role=EntityRole.HERO, faction=Faction.HERO_GUILD)
        .build()
    )
    identity = RESOLVER.resolve(entity)
    # Should resolve via compatibility_projection or legacy_enum
    assert identity.source in ("compatibility_projection", "legacy_enum")
    assert identity.entity_id == 3
    assert identity.faction_id is not None
    assert identity.role_id is not None


def test_legacy_enum_known_values_use_compatibility_projection():
    entity = (
        V2EntityBuilder(4)
        .kind("monster")
        .identity(role=EntityRole.MONSTER, faction=Faction.MONSTER_HORDE)
        .build()
    )
    identity = RESOLVER.resolve(entity)
    assert identity.source == "compatibility_projection"
    assert identity.role_id == "creature"
    assert identity.faction_id == "monster_horde"


def test_mixed_entity_prefers_clean_identity():
    # Entity has both clean properties and legacy enum values
    entity = (
        V2EntityBuilder(5)
        .kind("humanoid")
        .identity(
            role=EntityRole.MONSTER,
            faction=Faction.MONSTER_HORDE,
            properties={"faction_id": "town_council", "role_id": "guard"},
        )
        .build()
    )
    identity = RESOLVER.resolve(entity)
    assert identity.source == "clean_metadata"
    assert identity.faction_id == "town_council"
    assert identity.role_id == "guard"
    # Legacy fields still populated in result
    assert identity.legacy_role == EntityRole.MONSTER
    assert identity.legacy_faction == Faction.MONSTER_HORDE


def test_faction_id_alone_resolves_clean_not_collapsed_to_neutral():
    """TCK-20260809-COMBAT-HOSTILE-PAIRS-NEVER-ENGAGE: worldbuilding/compiler.py sets faction_id
    but never role_id -- confirmed via live corpus instrumentation to previously fall through to
    Path 3's compatibility_projection, which maps any faction outside the legacy 4-value Faction
    enum to "neutral", silently destroying real, correct faction identity for hostility checks.
    A real faction_id must now be trusted on its own."""
    entity = (
        V2EntityBuilder(7)
        .kind("monster")
        .identity(
            role=EntityRole.MONSTER,
            faction=Faction.NEUTRAL,
            properties={"faction_id": "goblin_warband"},
        )
        .build()
    )
    identity = RESOLVER.resolve(entity)
    assert identity.source == "clean_metadata"
    assert identity.faction_id == "goblin_warband"
    assert identity.role_id == "creature"  # derived from _ROLE_COMPAT[EntityRole.MONSTER]


def test_faction_id_alone_with_unmappable_legacy_role_gets_unresolved_role():
    entity = (
        V2EntityBuilder(8)
        .kind("goblin")
        .identity(role=999, faction=Faction.NEUTRAL, properties={"faction_id": "bandit_company"})
        .build()
    )
    identity = RESOLVER.resolve(entity)
    assert identity.source == "clean_metadata"
    assert identity.faction_id == "bandit_company"
    assert identity.role_id == "unresolved"


def test_missing_faction_role_fails_clearly():
    # Entity with no clean properties and no valid enum values (role=999, faction=999)
    entity = (
        V2EntityBuilder(6)
        .kind("unknown")
        .build()
    )
    # Default role=0 (HERO) and faction=0 (HERO_GUILD) from IdentityComponent defaults
    # so this will actually succeed — override with impossible values
    from dataclasses import replace
    from src.core.state import IdentityComponent
    bad_identity = replace(entity.identity, role=999, faction=999)
    from src.core.state import EntityState
    bad_entity = EntityState(
        id=6, kind="unknown",
        identity=bad_identity,
        combat=entity.combat,
        inventory=entity.inventory,
        navigation=entity.navigation,
        lifecycle=entity.lifecycle,
        social=entity.social,
        biological=entity.biological,
        strategic=entity.strategic,
        attributes=entity.attributes,
        aptitude=entity.aptitude,
        equipment=entity.equipment,
        interaction=entity.interaction,
        task=entity.task,
        stamina=entity.stamina,
        self_model=entity.self_model,
        cognition=entity.cognition,
    )
    with pytest.raises(IdentityResolutionError):
        RESOLVER.resolve(bad_entity)


def test_resolver_does_not_import_catalog_repository():
    import ast
    import inspect
    import src.entities.identity_resolver as mod

    source = inspect.getsource(mod)
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            module = getattr(node, "module", "") or ""
            for alias in getattr(node, "names", []):
                name = alias.name or ""
                full = f"{module}.{name}".strip(".")
                assert "CatalogRepository" not in full


def test_v2entitybuilder_tests_still_pass_unchanged():
    # Regression guard: V2EntityBuilder still works normally
    entity = (
        V2EntityBuilder(99)
        .kind("hero")
        .combat(hp=100, alive=True)
        .location(10.0, 10.0)
        .build()
    )
    assert entity.combat.hp == 100
    assert entity.navigation.position == (10.0, 10.0)
