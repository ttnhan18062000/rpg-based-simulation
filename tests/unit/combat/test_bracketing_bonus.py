from __future__ import annotations

from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole, Faction
from src.core.state import AuthoritativeState
from src.engine.combat import CombatResolutionSystem
from src.engine.legality import LegalityServiceV2


def create_mock_entity(
    eid: int,
    faction,
    pos: tuple[float, float] = (10.0, 10.0),
    hp: int = 100,
):
    """
    Build a minimal valid combat-capable entity for combat positioning tests.

    Important setup:
        - role/faction are set explicitly for hostility checks
        - hp/alive are kept consistent
        - readiness is set to 100 so combat is not rejected by readiness logic
        - attack range is set to 1 because all attackers are adjacent
        - lifecycle.active is set so spatial/flanking checks can treat the entity
          as a real participant

    Args:
        eid: Entity id.
        faction: Entity faction. Usually Faction.HERO_GUILD or
            Faction.MONSTER_HORDE.
        pos: Entity position.
        hp: Current hit points.

    Returns:
        EntityState suitable for direct combat and flanking tests.
    """
    role = (
        EntityRole.HERO
        if faction == Faction.HERO_GUILD or faction == 1
        else EntityRole.MONSTER
    )

    alive = hp > 0

    return (
        V2EntityBuilder(eid)
        .kind("hero" if role == EntityRole.HERO else "monster")
        .location(float(pos[0]), float(pos[1]))
        .identity(role=role, faction=faction)
        .combat(
            hp=hp,
            max_hp=max(100, hp),
            atk=10,
            def_stat=0,
            attack_range=1,
            alive=alive,
            readiness=100.0,
        )
        .lifecycle(active=alive)
        .build()
    )


def test_bracketing_bonus_requires_active_attackers():
    """
    LAW:
        Bracketing/flanking geometry requires hostile entities on opposite
        sides of the defender.

    Current latest-src behavior:
        - `LegalityServiceV2.check_flanking(defender_id, state)` detects the
          opposite-side geometry.
        - `CombatResolutionSystem.resolve_multi_attack(...)` validates active
          legal attackers and aggregates their damage.
        - There is no public `_route_combat_intent(...)` pipeline method in the
          latest source.

    Scenario:
        Monster stands at (10, 10).
        Hero A stands east at (11, 10).
        Hero B stands west at (9, 10).
        Both heroes are alive, active, adjacent, allied with each other, and
        hostile to the monster.

    Expected:
        - flanking geometry is detected
        - both attackers are accepted as simultaneous combat intents
        - total damage is greater than a single attack

    Fraud this catches:
        - test uses removed private pipeline method
        - passive/non-positioned entities accidentally count as attackers
        - opposite-side placement is broken
        - multi-attacker combat ignores one of the active attackers
    """
    target = create_mock_entity(
        1,
        Faction.MONSTER_HORDE,
        pos=(10.0, 10.0),
    )
    attacker_a = create_mock_entity(
        2,
        Faction.HERO_GUILD,
        pos=(11.0, 10.0),
    )
    attacker_b = create_mock_entity(
        3,
        Faction.HERO_GUILD,
        pos=(9.0, 10.0),
    )

    state = AuthoritativeState(
        tick=1,
        seed=42,
        entities={
            1: target,
            2: attacker_a,
            3: attacker_b,
        },
    )

    # Guard the test setup before checking combat behavior.
    assert target.navigation.position == (10.0, 10.0)
    assert attacker_a.navigation.position == (11.0, 10.0)
    assert attacker_b.navigation.position == (9.0, 10.0)
    assert attacker_a.identity.faction == attacker_b.identity.faction
    assert attacker_a.identity.faction != target.identity.faction
    assert attacker_a.lifecycle.active is True
    assert attacker_b.lifecycle.active is True
    assert target.combat.alive is True

    flanking_result = LegalityServiceV2.check_flanking(target.id, state)

    # Latest source may return either:
    #   bool
    # or:
    #   tuple[bool, bool] = (is_flanked, is_surrounded)
    # depending on the in-progress version.
    if isinstance(flanking_result, tuple):
        is_flanked = flanking_result[0]
    else:
        is_flanked = flanking_result

    assert is_flanked is True

    combat_upd = CombatResolutionSystem.resolve_multi_attack(
        attackers=[attacker_a, attacker_b],
        defender=target,
        state=state,
    )

    assert combat_upd.outcome_kind != "REJECTED", combat_upd.failure_reason
    assert combat_upd.damage_taken > 0
    assert combat_upd.simultaneous_intents is not None
    assert len(combat_upd.simultaneous_intents) == 2

    attacker_ids = {
        intent.attacker_id
        for intent in combat_upd.simultaneous_intents
    }

    assert attacker_ids == {2, 3}

    # With atk=10 and def=0, one attacker does 9 damage.
    # Two attackers with flanking (atk_mult=1.15) should do 10 damage each.
    # Formula: 11.5 * (11.5 / 12.5) = 10.58 -> 10.
    assert combat_upd.damage_taken == 20
    
    # Verify trace markers are present for both attackers in multi-attack
    assert combat_upd.trace.get("2_FLANKING") == 0.15
    assert combat_upd.trace.get("3_FLANKING") == 0.15


def test_bracketing_bonus_ignores_inactive_entities():
    """
    LAW: Bracketing bonus requires ACTIVE entities.
    Inactive or dead entities should not contribute to the geometry check.
    """
    target = create_mock_entity(1, Faction.MONSTER_HORDE, pos=(10.0, 10.0))
    attacker_a = create_mock_entity(2, Faction.HERO_GUILD, pos=(11.0, 10.0))
    # Attacker B is on the opposite side but INACTIVE/DEAD
    attacker_b = create_mock_entity(3, Faction.HERO_GUILD, pos=(9.0, 10.0), hp=0)

    state = AuthoritativeState(
        tick=2,
        seed=42,
        entities={
            1: target,
            2: attacker_a,
            3: attacker_b,
        },
    )

    # Legality check for flanking should fail because 3 is inactive
    is_flanked, _ = LegalityServiceV2.check_flanking(target.id, state)
    assert is_flanked is False

    # Multi-attack with both (one is inactive)
    combat_upd = CombatResolutionSystem.resolve_multi_attack(
        attackers=[attacker_a, attacker_b],
        defender=target,
        state=state,
    )

    # Only attacker_a should be valid
    assert len(combat_upd.simultaneous_intents) == 1
    assert combat_upd.simultaneous_intents[0].attacker_id == 2
    
    # Damage should be 9 (no flanking bonus)
    assert combat_upd.damage_taken == 9
    assert "2_FLANKING" not in combat_upd.trace