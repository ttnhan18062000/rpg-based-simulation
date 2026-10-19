"""D79 step 3: a level-up raises levels and stats and never renames the entity kind."""
import pytest

from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole, Faction
from src.core.state import AuthoritativeState
from src.core.updates import EntityUpdate, IdentityUpdate, StateUpdate
from src.engine.evolution import EvolutionSystem
from src.progression.leveling import LevelingService


def _entity(kind, role, level):
    return (
        V2EntityBuilder(1).kind(kind).location(0.0, 0.0)
        .identity(role=role, faction=Faction.MONSTER_HORDE, evolution_level=level, evolution_points=0)
        .combat(hp=100, max_hp=100, atk=10, def_stat=5, attack_range=1, alive=True, readiness=100.0)
        .lifecycle(active=True).build()
    )


def _evaluate(entity, levels_to_gain):
    start = entity.identity.evolution_level
    xp = sum(LevelingService.get_xp_required(lv) for lv in range(start, start + levels_to_gain))
    state = AuthoritativeState(tick=1, seed=1, entities={1: entity})
    update = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, identity=IdentityUpdate(evolution_points_delta=xp))})
    return EvolutionSystem.evaluate(state, update).entity_updates[1]


@pytest.mark.parametrize("threshold", [10, 25, 50])
@pytest.mark.parametrize("kind,role", [("hero", EntityRole.HERO), ("goblin", EntityRole.MONSTER), ("wolf", EntityRole.MONSTER)])
def test_crossing_a_threshold_leaves_the_kind_alone(kind, role, threshold):
    upd = _evaluate(_entity(kind, role, threshold - 1), 1)
    assert upd.kind_set is None
    assert upd.identity.evolution_level_set == threshold


def test_levels_stats_and_hp_still_rise_on_a_crossing():
    upd = _evaluate(_entity("goblin", EntityRole.MONSTER, 9), 1)
    assert upd.identity.evolution_level_set == 10
    assert upd.combat.hp_delta == 20
    assert upd.attributes.strength_delta > 0 or upd.attributes.vitality_delta > 0


def test_a_hero_still_gains_ability_points_on_a_crossing():
    upd = _evaluate(_entity("hero", EntityRole.HERO, 9), 1)
    assert upd.kind_set is None and upd.identity.unspent_ap_delta > 0
