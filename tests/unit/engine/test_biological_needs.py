"""SURV-05/SURV-06: biology follows the kind's need profile; services are reachable from adjacency;
rough rest recovers sleep debt; the meal place is the inn."""
from dataclasses import replace

import pytest

from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole
from src.core.state import AuthoritativeState, BuildingState
from src.core.updates import EntityUpdate, StateUpdate, TaskUpdate
from src.engine import behavior_consumers
from src.engine.biological_needs import need_rates, undeclared_need_kinds
from src.engine.domain.core_actions import CoreActions, ROUGH_REST_SLEEP_DEBT_RECOVERY
from src.engine.need_paths import need_path_report
from src.engine.service_reach import service_tile
from src.engine.town_resolution import TownResolutionSystem


@pytest.fixture(scope="module")
def catalog():
    behavior_consumers.reset_behavior_consumers()
    behavior_consumers._auto_init()
    yield behavior_consumers._catalog
    behavior_consumers.reset_behavior_consumers()


def _entity(eid=1, role=EntityRole.WORKER, **props):
    return (V2EntityBuilder(eid).kind("worker").location(10.0, 10.0)
            .identity(role=role, properties=props).build())


def test_legacy_constants_are_the_medium_need_rates(catalog):
    assert need_rates(_entity(species_id="human")) == pytest.approx((0.1, 0.05))


def test_person_without_species_gets_the_ordinary_persons_needs(catalog):
    assert need_rates(_entity(role=EntityRole.CITIZEN)) == pytest.approx((0.1, 0.05))


@pytest.mark.parametrize("species", ["undead", "spirit", "elemental"])
def test_kinds_without_hunger_never_hunger(catalog, species):
    if catalog.get_species(species) is None:
        pytest.skip("species not in catalog")
    assert need_rates(_entity(role=EntityRole.MONSTER, species_id=species))[0] == 0.0


def test_kinds_with_different_profiles_build_needs_at_different_rates(catalog):
    wolf = need_rates(_entity(role=EntityRole.MONSTER, species_id="wolf"))
    human = need_rates(_entity(species_id="human"))
    assert wolf[0] > human[0]  # carnivore hunger is high
    assert wolf[1] == pytest.approx(0.05)  # carnivore_survival declares sleep: medium (content gap closed 2026-10-07)


def test_explicit_need_profile_overrides_species(catalog):
    assert need_rates(_entity(species_id="human", need_profile_id="undead_purpose"))[0] == 0.0


def test_undeclared_monster_is_a_reported_defect_with_unchanged_rates(catalog):
    monster = _entity(role=EntityRole.MONSTER)
    assert need_rates(monster) == pytest.approx((0.1, 0.05))
    state = AuthoritativeState(tick=0, seed=1, entities={1: monster})
    assert undeclared_need_kinds(state, catalog) == {(None, int(EntityRole.MONSTER)): 1}


def test_apply_path_accumulates_per_kind(catalog):
    from src.engine.apply import ApplyPath
    from src.engine.cadence import SystemCadence
    state = AuthoritativeState(tick=0, seed=1, entities={})
    out = {}
    for name, ent in (("human", _entity(1, species_id="human")),
                      ("undead", _entity(2, role=EntityRole.MONSTER, species_id="undead"))):
        changes = ApplyPath._compute_entity_changes(ent, None, 10, SystemCadence(), True, False, [], state)
        out[name] = changes["biological"].hunger
    assert out["human"] == pytest.approx(0.1) and out["undead"] == 0.0


def test_service_tile_prefers_own_tile_then_orthogonal_neighbour():
    state = AuthoritativeState(tick=0, seed=1, building_tiles={(5, 5): "inn"})
    assert service_tile(state, (5, 5)) == (5, 5)
    assert service_tile(state, (5, 6)) == (5, 5)
    assert service_tile(state, (4, 5)) == (5, 5)
    assert service_tile(state, (6, 6)) is None  # diagonal is not within reach (MOV-07)


def test_service_tile_filters_by_kind_when_two_buildings_are_in_reach():
    # Home to the north, inn to the east: the fixed offset order reaches the home first.
    state = AuthoritativeState(tick=0, seed=1, building_tiles={(5, 4): "home", (6, 5): "inn"})
    assert service_tile(state, (5, 5)) == (5, 4)
    assert service_tile(state, (5, 5), {"inn"}) == (6, 5)
    assert service_tile(state, (5, 5), {"inn", "home"}) == (5, 4)
    assert service_tile(state, (5, 5), {"blacksmith"}) is None


def test_eat_is_served_by_the_inn_when_a_home_is_nearer_in_reach():
    ent = (V2EntityBuilder(1).kind("worker").location(10.0, 10.0).biological(hunger=80.0)
           .inventory(gold=50).build())
    home = BuildingState(id=2, kind="home", position=(10, 9))
    inn = BuildingState(id=1, kind="inn", position=(11, 10))
    state = AuthoritativeState(
        tick=1, seed=1, entities={1: ent}, buildings={1: inn, 2: home},
        building_tiles={(11, 10): "inn", (10, 9): "home"}, town_tiles={(10, 10), (11, 10), (10, 9)},
    )
    task = TaskUpdate(work_kind_set="ENTITY_ACT", payload_set={"action": "EAT", "target_id": 1})
    update = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, task=task)})
    ent_upd = TownResolutionSystem.resolve(state, update).entity_updates[1]
    assert ent_upd.biological.hunger_delta == -20.0
    assert [t.transfer_kind for t in ent_upd.resource_transfers] == ["EAT"]


def test_rough_rest_recovers_sleep_debt_without_a_building():
    ent = _entity()
    upd = CoreActions.execute_survival(ent, "REST", 10)[ent.id]
    assert upd.biological.sleep_debt_delta == -ROUGH_REST_SLEEP_DEBT_RECOVERY


def test_inn_meal_is_served_to_a_subject_beside_the_inn():
    ent = (V2EntityBuilder(1).kind("worker").location(11.0, 10.0).biological(hunger=80.0)
           .inventory(gold=50).build())
    inn = BuildingState(id=1, kind="inn", position=(10, 10))
    state = AuthoritativeState(
        tick=1, seed=1, entities={1: ent}, buildings={1: inn},
        building_tiles={(10, 10): "inn"}, town_tiles={(11, 10), (10, 10)},
    )
    task = TaskUpdate(work_kind_set="ENTITY_ACT", payload_set={"action": "EAT", "target_id": 1})
    update = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, task=task)})
    out = TownResolutionSystem.resolve(state, update)
    ent_upd = out.entity_updates[1]
    assert ent_upd.biological.hunger_delta == -20.0
    assert [t.transfer_kind for t in ent_upd.resource_transfers] == ["EAT"]


def test_eat_scorer_targets_the_inn():
    from src.ai.goals.scorers import EatScorer
    from dataclasses import replace
    from src.engine.service_prices import EAT_PRICE_GOLD
    ent = (V2EntityBuilder(1).kind("worker").location(11.0, 10.0).biological(hunger=80.0).build())
    ent = replace(ent, inventory=replace(ent.inventory, gold=EAT_PRICE_GOLD))  # the inn is a way to eat only for a subject that can pay (SURV-06)
    inn = BuildingState(id=7, kind="inn", position=(10, 10))
    state = AuthoritativeState(tick=1, seed=1, entities={1: ent}, buildings={7: inn})
    assert EatScorer().score(ent, state).target_id == "7"


def test_need_path_report_flags_a_hungry_kind_in_a_world_with_no_inn(catalog):
    ent = _entity(species_id="human")
    state = AuthoritativeState(tick=0, seed=1, entities={1: ent})
    (row,) = need_path_report(state, catalog)
    assert row["kind"] == "human" and row["hunger_path"] is False
    assert row["advisory"] == "hungers but the world has no inn"


@pytest.mark.parametrize("species", ["undead", "spirit", "elemental"])
def test_hungerless_kinds_declare_sleep_none_explicitly(catalog, species):
    if catalog.get_species(species) is None:
        pytest.skip("species not in catalog")
    profile = catalog.get_need_profile(catalog.get_species(species).need_profile)
    assert profile.needs["sleep"] == "none" and need_rates(_entity(role=EntityRole.MONSTER, species_id=species)) == (0.0, 0.0)


def test_every_catalog_need_profile_declares_each_modelled_biological_need(catalog):
    from src.content.schema import MODELLED_BIOLOGICAL_NEEDS
    missing = [(pid, k) for pid, p in catalog.need_profiles.items() for k in MODELLED_BIOLOGICAL_NEEDS if k not in p.needs]
    assert missing == []


def test_validator_reports_an_absent_modelled_need_and_the_corpus_has_none(catalog):
    from src.content.schema import NeedProfileDefinition
    from src.content.validator import need_profile_gap_issues
    issues = need_profile_gap_issues(catalog)
    assert [i for i in issues if i.rule_id == "CAT-NEED-001"] == []
    catalog.need_profiles["gap_probe"] = NeedProfileDefinition(id="gap_probe", display_name="Gap", needs={"hunger": "low"})
    try:
        issues = need_profile_gap_issues(catalog)
    finally:
        del catalog.need_profiles["gap_probe"]
    assert [(i.rule_id, i.target_id) for i in issues] == [("CAT-NEED-001", "gap_probe")]


def test_absent_need_key_is_recorded_when_it_fires_and_never_on_the_corpus(catalog):
    from src.content.schema import NeedProfileDefinition
    from src.engine import biological_needs as bn
    bn.ABSENT_NEED_KEY_FIRINGS.clear()
    for species in ("human", "wolf", "goblin", "undead"):
        need_rates(_entity(role=EntityRole.MONSTER, species_id=species))
    assert bn.ABSENT_NEED_KEY_FIRINGS == []
    catalog.need_profiles["gap_probe"] = NeedProfileDefinition(id="gap_probe", display_name="Gap", needs={"hunger": "low"})
    try:
        rates = need_rates(_entity(role=EntityRole.MONSTER, need_profile_id="gap_probe"))
    finally:
        del catalog.need_profiles["gap_probe"]
    assert rates == pytest.approx((0.05, 0.0)) and bn.ABSENT_NEED_KEY_FIRINGS == [("gap_probe", "sleep")]
    bn.ABSENT_NEED_KEY_FIRINGS.clear()
