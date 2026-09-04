import ast
import inspect
import sys
import importlib

import pytest

from src.entities.runtime_contract import ResolvedEntityRuntimeContract
from src.core.enums import EntityRole, Faction


def _make_contract(**overrides):
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
        inventory_items={"basic_tool": 1},
        starting_gold=5.0,
        traits=("hard_working",),
        themes=("frontier",),
    )
    defaults.update(overrides)
    return ResolvedEntityRuntimeContract(**defaults)


def test_contract_construction_minimal():
    c = _make_contract()
    assert c.archetype_id == "human_worker"
    assert c.species_id == "human"
    assert c.faction_id == "town_council"
    assert c.role_id == "worker"
    assert c.kind == "humanoid"
    assert c.hp == 80
    assert c.atk == 8
    assert c.readiness == 100.0


def test_contract_optional_fields_default_none():
    c = _make_contract()
    assert c.profession_id is None
    assert c.legacy_role is None
    assert c.legacy_faction is None
    assert c.cognition_profile_id is None
    assert c.drive_profile_id is None
    assert c.need_profile_id is None
    assert c.sense_profile_id is None
    assert c.skill_profile_id is None


def test_contract_legacy_fields_are_optional_only():
    c = _make_contract(
        legacy_role=EntityRole.HERO,
        legacy_faction=Faction.HERO_GUILD,
    )
    assert c.legacy_role == EntityRole.HERO
    assert c.legacy_faction == Faction.HERO_GUILD


def test_contract_is_immutable():
    c = _make_contract()
    with pytest.raises(Exception):
        c.hp = 999  # type: ignore[misc]


def test_contract_json_serializable():
    c = _make_contract(
        legacy_role=EntityRole.HERO,
        cognition_profile_id="cognition_basic",
    )
    data = c.model_dump()
    assert data["archetype_id"] == "human_worker"
    assert data["hp"] == 80
    assert data["traits"] == ("hard_working",)
    assert data["inventory_items"] == {"basic_tool": 1}


def test_contract_model_dump_json_round_trip():
    c = _make_contract()
    json_str = c.model_dump_json()
    assert "human_worker" in json_str
    assert "town_council" in json_str


def test_contract_no_catalog_imports():
    import src.entities.runtime_contract as mod
    source = inspect.getsource(mod)
    tree = ast.parse(source)
    forbidden_prefixes = ("CatalogRepository", "catalog_repo", "src.content.repository")
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            module = getattr(node, "module", "") or ""
            for alias in getattr(node, "names", []):
                name = alias.name or ""
                full = f"{module}.{name}".strip(".")
                for prefix in forbidden_prefixes:
                    assert prefix not in full, (
                        f"Forbidden import '{full}' found in runtime_contract.py"
                    )


def test_contract_no_enemy_ally_fields():
    c = _make_contract()
    dumped = c.model_dump()
    forbidden = {"is_enemy", "is_ally", "enemy_type", "target_type", "hostile_flag"}
    assert not (forbidden & set(dumped.keys())), (
        f"Enemy/ally source-truth fields found: {forbidden & set(dumped.keys())}"
    )


def test_contract_with_all_profile_ids():
    c = _make_contract(
        cognition_profile_id="cog_basic",
        drive_profile_id="drive_survival",
        need_profile_id="need_basic",
        sense_profile_id="sense_human",
        skill_profile_id="skill_worker",
    )
    assert c.cognition_profile_id == "cog_basic"
    assert c.drive_profile_id == "drive_survival"
    assert c.need_profile_id == "need_basic"
    assert c.sense_profile_id == "sense_human"
    assert c.skill_profile_id == "skill_worker"
