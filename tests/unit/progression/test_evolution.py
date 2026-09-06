import pytest

from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState, EquipSlot
from src.core.enums import EntityRole, Faction
from src.core.updates import EntityUpdate, IdentityUpdate, StateUpdate
from src.engine.apply import ApplyPath
from src.engine.evolution import EvolutionSystem
from src.progression.leveling import LevelingService


def make_goblin_stage(
    entity_id: int,
    *,
    kind: str = "goblin_0",
    level: int = 1,
    points: int = 0,
):
    """
    Build a valid goblin evolution test entity using the new V2 builder.

    New builder rule:
        The old `.monster("goblin", tier)` shortcut is removed.
        Monster kind, faction, role, level, and combat validity must be
        expressed explicitly.

    Fraud this catches:
        - test accidentally creates an inactive entity and EvolutionSystem skips it
        - test uses generic "goblin" while asserting tiered "goblin_0 -> goblin_1"
        - monster role/faction are missing and evolution behavior becomes ambiguous
    """
    return (
        V2EntityBuilder(entity_id)
        .kind(kind)
        .location(0.0, 0.0)
        .identity(
            role=EntityRole.MONSTER,
            faction=Faction.MONSTER_HORDE,
            evolution_level=level,
            evolution_points=points,
        )
        .combat(
            hp=100,
            max_hp=100,
            atk=10,
            def_stat=5,
            attack_range=1,
            alive=True,
            readiness=100.0,
        )
        .lifecycle(active=True)
        .build()
    )


def test_goblin_evolution():
    """
    Verify goblin_0 evolves into goblin_1 when crossing level 10.

    Logic under test:
        EvolutionSystem evolves species only when a level-up crosses one of
        the evolution thresholds. For goblin_0 at level 9, gaining enough XP
        to reach level 10 should produce goblin_1 and refresh evolution gear.

    Fraud this catches:
        - evolution threshold is crossed but kind does not change
        - evolved goblin does not receive expected gear
        - old `.monster(...)` builder shortcut hides invalid setup
    """
    entity = make_goblin_stage(
        1,
        kind="goblin_0",
        level=9,
        points=0,
    )

    xp_needed = LevelingService.get_xp_required(9)

    state = AuthoritativeState(
        tick=0,
        seed=1,
        entities={1: entity},
    )

    state_upd = StateUpdate(
        entity_updates={
            1: EntityUpdate(
                entity_id=1,
                identity=IdentityUpdate(
                    evolution_points_delta=xp_needed,
                ),
            )
        }
    )

    refined = EvolutionSystem.evaluate(state, state_upd)
    new_state = ApplyPath.apply_generation(state, refined)
    new_entity = new_state.entities[1]

    assert new_entity.kind == "goblin_1"
    assert new_entity.identity.evolution_level == 10
    assert new_entity.equipment.slots[EquipSlot.MAIN_HAND] == "iron_sword"
    assert new_entity.equipment.slots[EquipSlot.TORSO] == "leather_armor"


def test_no_evolution_before_threshold():
    """
    Verify goblin_0 does not evolve before crossing level 10.

    Scenario:
        goblin_0 starts at level 8 and gains exactly enough XP to reach level 9.
        This is a normal level-up, but it does not cross the level-10 evolution
        threshold.

    Fraud this catches:
        - any level-up incorrectly triggers species evolution
        - test accidentally starts at level 9 and crosses the threshold
        - kind transition happens before the configured threshold
    """
    entity = make_goblin_stage(
        1,
        kind="goblin_0",
        level=8,
        points=0,
    )

    xp_needed = LevelingService.get_xp_required(8)

    state = AuthoritativeState(
        tick=0,
        seed=1,
        entities={1: entity},
    )

    state_upd = StateUpdate(
        entity_updates={
            1: EntityUpdate(
                entity_id=1,
                identity=IdentityUpdate(
                    evolution_points_delta=xp_needed,
                ),
            )
        }
    )

    refined = EvolutionSystem.evaluate(state, state_upd)
    new_state = ApplyPath.apply_generation(state, refined)
    new_entity = new_state.entities[1]

    assert new_entity.kind == "goblin_0"
    assert new_entity.identity.evolution_level == 9


def test_goblin_evolution_emits_entity_evolved_observability_event():
    """TCK-20260906-ENTITY-EVOLVED-EVENT-GAP: EvolutionSystem's real, production `kind_set` output
    must wire into the real ProgressionShaper observability layer, not just a hand-built mock
    update. Reuses the exact same real EvolutionSystem.evaluate() call as test_goblin_evolution()
    above -- this test's own value is proving the *observability* half of that same real
    transition, not re-proving the evolution mechanic itself.
    """
    from src.observability.event_shapers import ProgressionShaper

    entity = make_goblin_stage(1, kind="goblin_0", level=9, points=0)
    xp_needed = LevelingService.get_xp_required(9)
    state = AuthoritativeState(tick=0, seed=1, entities={1: entity})
    state_upd = StateUpdate(
        entity_updates={
            1: EntityUpdate(entity_id=1, identity=IdentityUpdate(evolution_points_delta=xp_needed)),
        }
    )

    refined = EvolutionSystem.evaluate(state, state_upd)

    events = ProgressionShaper().shape(state, refined, tick=0)
    ev = next(e for e in events if e.event_type == "entity_evolved")
    assert ev.payload == {"previous_kind": "goblin_0", "new_kind": "goblin_1"}