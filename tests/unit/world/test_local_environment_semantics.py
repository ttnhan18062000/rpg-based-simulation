from __future__ import annotations

from dataclasses import replace

from src.core.enums import ReasonCode
from src.core.state import AuthoritativeState, BuildingState
from src.engine.combat import CombatResolutionSystem
from src.engine.legality import LegalityServiceV2


def _reason_value(reason):
    """
    Normalize a legality reason for assertions.

    Some in-progress source paths may return ReasonCode enums, while other
    paths may return raw strings. This helper keeps the tests focused on the
    semantic reason instead of the exact representation.
    """
    return reason.value if hasattr(reason, "value") else reason


def create_mock_entity(
    eid: int,
    faction,
    pos: tuple[float, float] = (10.0, 10.0),
    hp: int = 100,
):
    """
    Build a minimal valid combat-capable entity for local environment tests.

    The helper intentionally sets:
        - navigation position via `.location(...)`
        - faction for hostility checks
        - combat hp/max_hp/alive/readiness for attack legality
        - lifecycle.active for modern entity activity checks

    Args:
        eid: Entity id.
        faction: Faction value used by hostility checks.
        pos: Entity position.
        hp: Current HP. If hp <= 0, the entity is marked dead.

    Returns:
        EntityState: A valid entity suitable for terrain, movement, and combat
        legality tests.
    """
    from src.core.builder import V2EntityBuilder

    alive = hp > 0

    return (
        V2EntityBuilder(eid)
        .kind("hero")
        .location(float(pos[0]), float(pos[1]))
        .identity(faction=faction)
        .combat(
            hp=hp,
            max_hp=max(100, hp),
            alive=alive,
            readiness=100.0,
        )
        .lifecycle(active=alive)
        .build()
    )


def test_terrain_movement_blockage():
    """
    LAW:
        A WALL terrain tile must not be occupiable.

    Scenario:
        The target tile is marked as WALL. The occupancy verifier should reject
        movement into that tile with PATH_NOT_FOUND.

    Fraud this catches:
        - terrain collision is ignored
        - WALL tiles are treated as walkable
        - movement legality silently accepts blocked terrain
    """
    state = AuthoritativeState(
        tick=1,
        seed=42,
        terrain={(10, 11): "WALL"},
    )

    is_legal, reason = LegalityServiceV2.verify_occupancy(
        (10, 11),
        state,
    )

    assert is_legal is False
    assert _reason_value(reason) == _reason_value(ReasonCode.PATH_NOT_FOUND)


def test_building_movement_blockage():
    """
    LAW:
        A building tile must not be occupiable by normal movement.

    Scenario:
        A shop exists at the target tile. The occupancy verifier should reject
        movement into that tile with BUILDING_OBSTRUCTION.

    Fraud this catches:
        - building collision is ignored
        - entities can move into occupied building tiles
        - movement legality only checks terrain but not buildings
    """
    building = BuildingState(
        id=1,
        kind="shop",
        position=(10, 11),
    )

    state = AuthoritativeState(
        tick=1,
        seed=42,
        buildings={1: building},
        building_tiles={(10, 11): "shop"}
    )

    is_legal, reason = LegalityServiceV2.verify_occupancy(
        (10, 11),
        state,
    )

    assert is_legal is False
    assert _reason_value(reason) == _reason_value(ReasonCode.BUILDING_OBSTRUCTION)


def test_combat_line_of_sight():
    """
    LAW:
        Ranged/melee attack legality must respect line-of-sight obstruction.

    Scenario:
        Attacker and target are two tiles apart.
        First, there is no obstruction, so the attack is legal.
        Then, a WALL is placed between them, so the attack is rejected with
        LOS_OBSTRUCTED.

    Fraud this catches:
        - attack legality checks range but ignores line of sight
        - WALL terrain blocks movement but not attacks
        - attack legality gives a generic failure instead of LOS_OBSTRUCTED
    """
    attacker = create_mock_entity(1, 1, pos=(10.0, 10.0))
    attacker = replace(
        attacker,
        combat=replace(
            attacker.combat,
            range=2,
            alive=True,
            readiness=100.0,
        ),
    )

    target = create_mock_entity(2, 2, pos=(10.0, 12.0))

    # Case 1: clear line of sight.
    clear_state = AuthoritativeState(
        tick=1,
        seed=42,
        entities={1: attacker, 2: target},
    )

    is_legal, reason = LegalityServiceV2.verify_attack_legality(
        attacker,
        target,
        clear_state,
    )

    assert is_legal is True

    # Case 2: WALL blocks the line between attacker and target.
    blocked_state = AuthoritativeState(
        tick=1,
        seed=42,
        entities={1: attacker, 2: target},
        terrain={(10, 11): "WALL"},
    )

    is_legal, reason = LegalityServiceV2.verify_attack_legality(
        attacker,
        target,
        blocked_state,
    )

    assert is_legal is False
    assert _reason_value(reason) == _reason_value(ReasonCode.LOS_OBSTRUCTED)


def test_high_ground_bonus():
    """
    LAW:
        An attacker standing on high ground must receive the high-ground combat
        modifier.

    Current source behavior:
        High ground is not a flat +5 damage bonus. The latest combat system uses
        a tactical attack multiplier:

            CombatResolutionSystem.HIGH_GROUND_BONUS == 0.20

        Damage is then calculated through the fractional armor mitigation
        formula.

    Scenario:
        Attacker has atk=10 and defender has def=0.
        Without high ground, damage would be:

            int(10 * (10 / (10 + 0 * 2 + 1))) == 9

        With high ground, atk multiplier becomes 1.20, so damage should be
        greater than 9.

    Fraud this catches:
        - high-ground terrain is ignored
        - combat trace does not record HIGH_GROUND
        - old pipeline-private `_route_combat_intent` is used even though the
          latest pipeline routes combat through action/domain logic
    """
    attacker = create_mock_entity(1, 1, pos=(10.0, 10.0))
    attacker = replace(
        attacker,
        combat=replace(
            attacker.combat,
            atk=10,
            range=1,
            alive=True,
            readiness=100.0,
        ),
    )

    target = create_mock_entity(2, 2, pos=(10.0, 11.0))
    target = replace(
        target,
        combat=replace(
            target.combat,
            hp=100,
            max_hp=100,
            def_stat=0,
            alive=True,
        ),
    )

    state = AuthoritativeState(
        tick=1,
        seed=42,
        entities={1: attacker, 2: target},
        terrain={
            (10, 10): "HILL",
            (10, 11): "PLAIN",
        },
    )

    combat_upd = CombatResolutionSystem.resolve_attack(
        attacker,
        target,
        state,
    )

    assert combat_upd.outcome_kind != "REJECTED", combat_upd.failure_reason

    # Strong semantic proof: the combat system detected and recorded high ground.
    assert "HIGH_GROUND" in combat_upd.trace
    assert combat_upd.trace["HIGH_GROUND"] == CombatResolutionSystem.HIGH_GROUND_BONUS

    # Final attack multiplier should include the high-ground bonus.
    assert combat_upd.trace["FINAL_ATK_MULT"] > 1.0

    # Baseline damage at atk=10/def=0 without high ground is 9.
    assert combat_upd.damage_taken > 9