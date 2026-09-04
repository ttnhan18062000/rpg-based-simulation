import pytest

from src.core.enums import EntityRole, Faction
from src.entities.runtime_contract import ResolvedEntityRuntimeContract
from src.entities.archetype_factory import ArchetypeEntityFactory, EntitySpawnContext


def _contract(**overrides) -> ResolvedEntityRuntimeContract:
    defaults = dict(
        archetype_id="human_worker",
        species_id="human",
        faction_id="town_council",
        role_id="worker",
        kind="humanoid",
        hp=80,
        max_hp=80,
        atk=8,
        def_stat=4,
        attack_range=1,
        readiness=100.0,
        inventory_items={},
        starting_gold=0.0,
        traits=(),
        themes=(),
    )
    defaults.update(overrides)
    return ResolvedEntityRuntimeContract(**defaults)


def _spawn(**overrides) -> EntitySpawnContext:
    defaults = dict(position=(5.0, 5.0))
    defaults.update(overrides)
    return EntitySpawnContext(**defaults)


FACTORY = ArchetypeEntityFactory()


def test_build_human_worker_entity_from_contract():
    c = _contract(
        archetype_id="human_worker",
        kind="humanoid",
        hp=80,
        max_hp=80,
        atk=8,
        def_stat=4,
        legacy_role=EntityRole.HERO,
        legacy_faction=Faction.HERO_GUILD,
    )
    entity = FACTORY.build_entity(1, c, _spawn(position=(10.0, 10.0)))

    assert entity.id == 1
    assert entity.kind == "humanoid"
    assert entity.combat.hp == 80
    assert entity.combat.atk == 8
    assert entity.combat.def_stat == 4
    assert entity.combat.alive is True
    assert entity.navigation.position == (10.0, 10.0)


def test_build_wolf_entity_from_contract():
    c = _contract(
        archetype_id="wolf_alpha",
        species_id="wolf",
        faction_id="wilderness",
        role_id="predator",
        kind="beast",
        hp=60,
        max_hp=60,
        atk=15,
        def_stat=3,
        attack_range=1,
        readiness=100.0,
    )
    entity = FACTORY.build_entity(2, c, _spawn())
    assert entity.kind == "beast"
    assert entity.combat.hp == 60
    assert entity.combat.atk == 15


def test_build_goblin_raider_entity_from_contract():
    c = _contract(
        archetype_id="goblin_raider",
        species_id="goblin",
        faction_id="goblin_clan",
        role_id="raider",
        kind="goblinoid",
        hp=40,
        max_hp=40,
        atk=12,
        def_stat=2,
        traits=("aggressive", "nimble"),
    )
    entity = FACTORY.build_entity(3, c, _spawn())
    assert entity.kind == "goblinoid"
    assert "aggressive" in entity.identity.traits
    assert "nimble" in entity.identity.traits


def test_build_boss_like_entity_without_boss_class():
    c = _contract(
        archetype_id="orc_warchief",
        kind="orc",
        hp=300,
        max_hp=300,
        atk=45,
        def_stat=20,
    )
    entity = FACTORY.build_entity(4, c, _spawn())
    assert entity.combat.hp == 300
    assert entity.combat.atk == 45
    assert entity.id == 4


def test_entity_factory_does_not_require_enemy_type():
    c = _contract(
        archetype_id="frontier_guard",
        kind="humanoid",
        legacy_role=None,
        legacy_faction=None,
    )
    entity = FACTORY.build_entity(5, c, _spawn())
    assert entity is not None
    assert entity.identity.properties["archetype_id"] == "frontier_guard"


def test_combat_values_match_contract():
    c = _contract(hp=120, max_hp=150, atk=20, def_stat=10, attack_range=2, readiness=75.0)
    entity = FACTORY.build_entity(6, c, _spawn())
    assert entity.combat.hp == 120
    assert entity.combat.max_hp == 150
    assert entity.combat.atk == 20
    assert entity.combat.def_stat == 10
    assert entity.combat.range == 2
    assert entity.combat.readiness == 75.0


def test_archetype_id_preserved_in_identity_properties():
    c = _contract(archetype_id="test_arch", species_id="test_species")
    entity = FACTORY.build_entity(7, c, _spawn())
    assert entity.identity.properties["archetype_id"] == "test_arch"
    assert entity.identity.properties["species_id"] == "test_species"


def test_inventory_items_and_gold_from_contract():
    c = _contract(
        inventory_items={"basic_tool": 1, "ration": 3},
        starting_gold=12.5,
    )
    entity = FACTORY.build_entity(8, c, _spawn())
    assert entity.inventory.gold == 12
    item_ids = {s.item_id for s in entity.inventory.items}
    assert "basic_tool" in item_ids
    assert "ration" in item_ids


def test_spawn_initial_alive_false():
    c = _contract()
    entity = FACTORY.build_entity(9, c, _spawn(initial_alive=False))
    assert entity.combat.alive is False


def test_spawn_initial_active_false():
    c = _contract()
    entity = FACTORY.build_entity(10, c, _spawn(initial_active=False))
    assert entity.lifecycle.active is False


def test_profile_ids_stored_in_properties():
    c = _contract(
        cognition_profile_id="cog_basic",
        drive_profile_id="drive_survival",
        need_profile_id="need_human",
        sense_profile_id="sense_human",
        skill_profile_id="skill_worker",
    )
    entity = FACTORY.build_entity(11, c, _spawn())
    props = entity.identity.properties
    assert props["cognition_profile_id"] == "cog_basic"
    assert props["drive_profile_id"] == "drive_survival"
    assert props["need_profile_id"] == "need_human"
    assert props["sense_profile_id"] == "sense_human"
    assert props["skill_profile_id"] == "skill_worker"


def test_build_entity_produces_real_nonzero_personality():
    """TCK-20260809-WORLDENTITYSPAWNER-ZERO-PERSONALITY: entities built via
    ArchetypeEntityFactory must no longer default to all-zero personality."""
    c = _contract(faction_id="wild_beast_pack")
    entity = FACTORY.build_entity(20, c, _spawn())
    p = entity.identity.personality
    assert p.bravery > 0.0 or p.greed > 0.0 or p.sociability > 0.0 or p.industry > 0.0


def test_build_entity_action_style_correlates_with_bravery():
    """A high-bravery-biased faction (wild_beast_pack, +0.35) should skew AGGRESSIVE more
    than a default-bias faction, activating the real, previously-dormant ActionStyle hooks."""
    from src.core.enums import ActionStyle
    predator_styles = [
        FACTORY.build_entity(eid, _contract(faction_id="wild_beast_pack"), _spawn()).combat.action_style
        for eid in range(30, 50)
    ]
    assert any(s == ActionStyle.AGGRESSIVE for s in predator_styles)


def test_build_entity_personality_is_deterministic_given_seed():
    """Same (entity_id, contract, spawn, seed) must produce bit-identical personality."""
    c = _contract(faction_id="goblin_clan")
    e1 = FACTORY.build_entity(50, c, _spawn(), seed=99)
    e2 = FACTORY.build_entity(50, c, _spawn(), seed=99)
    assert e1.identity.personality == e2.identity.personality


def test_build_entity_default_seed_backward_compatible():
    """build_entity's own seed parameter must default so all pre-existing positional-arg
    call sites (no seed) keep working."""
    c = _contract()
    entity = FACTORY.build_entity(51, c, _spawn())
    assert entity is not None


def test_factory_does_not_import_catalog_repository():
    import ast
    import inspect
    import src.entities.archetype_factory as mod

    source = inspect.getsource(mod)
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            module = getattr(node, "module", "") or ""
            for alias in getattr(node, "names", []):
                name = alias.name or ""
                full = f"{module}.{name}".strip(".")
                assert "CatalogRepository" not in full, (
                    f"CatalogRepository import found in archetype_factory: {full}"
                )
