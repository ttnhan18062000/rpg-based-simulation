import pytest
"""
- [RPG-COMBAT-001] Damage calculation follows the Fractional Armor Mitigation (FAM) law.
- [RPG-COMBAT-002] Combat outcomes (SURVIVE, DEFEAT, KILL) are mutually exclusive.
"""
from src.core.state import AuthoritativeState
from src.engine.combat import CombatResolutionSystem
from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole, Faction

def create_mock_entity(eid, faction=Faction.HERO_GUILD, atk=10, dfn=5, hp=100, role=EntityRole.HERO):
    return (V2EntityBuilder(eid)
        .kind("hero")
        .location(0.0, 0.0)
        .combat(readiness=100.0)
        .identity(role=role, faction=faction)
        .attributes(strength=0, vitality=0)
        .combat(hp=hp, max_hp=hp, atk=atk, def_stat=dfn)
        .build())

def test_combat_damage_calculation():
    """
    [RPG-COMBAT-001] Damage calculation follows the Fractional Armor Mitigation (FAM) law.
    Formula: damage = atk * (atk / (atk + def * 2.0 + 1.0))
    atk=10, def=5 => 10 * (10 / (10 + 10 + 1)) = 10 * (10/21) = 10 * 0.476 = 4.76 => 4
    """
    attacker = create_mock_entity(1, atk=10)
    defender = create_mock_entity(2, dfn=5)
    
    damage = CombatResolutionSystem.calculate_damage(attacker, defender)
    assert damage == 4

def test_survival_outcome():
    attacker = create_mock_entity(1, faction=1, atk=10)
    defender = create_mock_entity(2, faction=2, hp=100) # Different faction
    
    state = AuthoritativeState(tick=1, seed=42, entities={1: attacker, 2: defender})
    update = CombatResolutionSystem.resolve_attack(attacker, defender, state=state)
    assert update.damage_taken > 0
    assert update.outcome_kind == "SURVIVE"
    assert update.alive_set is True

def test_defeat_outcome():
    # Non-lethal attack
    attacker = create_mock_entity(1, faction=1, atk=1000)
    defender = create_mock_entity(2, faction=2, hp=10, role=EntityRole.MONSTER)
    
    state = AuthoritativeState(tick=1, seed=42, entities={1: attacker, 2: defender})
    update = CombatResolutionSystem.resolve_attack(attacker, defender, state=state, is_lethal=False)
    assert update.outcome_kind == "DEFEAT"
    assert update.alive_set is False

def test_kill_outcome():
    # Lethal attack
    attacker = create_mock_entity(1, faction=1, atk=1000)
    defender = create_mock_entity(2, faction=2, hp=10, role=EntityRole.MONSTER)
    
    state = AuthoritativeState(tick=1, seed=42, entities={1: attacker, 2: defender})
    update = CombatResolutionSystem.resolve_attack(attacker, defender, state=state, is_lethal=True)
    assert update.outcome_kind == "KILL"
    assert update.alive_set is False

def test_opportunity_attack_outcome():
    attacker = create_mock_entity(1, faction=1)
    defender = create_mock_entity(2, faction=2)

    state = AuthoritativeState(tick=1, seed=42, entities={1: attacker, 2: defender})
    update = CombatResolutionSystem.resolve_opportunity_attack(attacker, defender, state=state)
    assert update.is_opportunity_attack is True
    assert update.is_lethal is False # OAs are usually non-lethal in this engine's tactical rules
    assert update.outcome_kind in ["SURVIVE", "DEFEAT"]


def test_wound_penalties_scale_with_severity_through_live_combat_path():
    """
    [TCK-20260824-WOUND-PENALTY-FORMULA-WIRING] _get_wound_infliction must construct
    WoundState via WoundService.create_wound() (severity-scaled), not the old hardcoded
    flat penalty=5.0. Two wounds of different severity, produced by the real combat
    resolution entry point (resolve_attack -> _get_wound_infliction), must carry
    measurably different penalties -- not a pinned constant.
    """
    # Mild wound: damage=40 against max_hp=100 -> severity=0.4
    mild_attacker = create_mock_entity(1, faction=Faction.HERO_GUILD, atk=50, dfn=5)
    mild_defender = create_mock_entity(2, faction=Faction.MONSTER_HORDE, atk=5, dfn=5, hp=100)
    mild_state = AuthoritativeState(tick=1, seed=42, entities={1: mild_attacker, 2: mild_defender})
    mild_update = CombatResolutionSystem.resolve_attack(mild_attacker, mild_defender, state=mild_state)

    # Severe wound: damage=99 against max_hp=100 -> severity=0.99
    severe_attacker = create_mock_entity(3, faction=Faction.HERO_GUILD, atk=100, dfn=5)
    severe_defender = create_mock_entity(4, faction=Faction.MONSTER_HORDE, atk=5, dfn=0, hp=100)
    severe_state = AuthoritativeState(tick=1, seed=42, entities={3: severe_attacker, 4: severe_defender})
    severe_update = CombatResolutionSystem.resolve_attack(severe_attacker, severe_defender, state=severe_state)

    assert mild_update.wound_update is not None
    assert severe_update.wound_update is not None
    mild_wound = mild_update.wound_update.wounds_add[0]
    severe_wound = severe_update.wound_update.wounds_add[0]

    # Not the old flat penalty=5.0 bug (which also never set speed/max_hp penalties at all)
    assert mild_wound.atk_penalty != 5.0
    assert mild_wound.def_penalty != 5.0

    # Severity-scaled per WoundService.create_wound's contract, and measurably different
    # between the two wounds -- this is the live-path behavior under test, not a re-test
    # of WoundService.create_wound() in isolation.
    assert mild_wound.severity < severe_wound.severity
    assert mild_wound.atk_penalty < severe_wound.atk_penalty
    assert mild_wound.def_penalty < severe_wound.def_penalty
    assert mild_wound.speed_penalty < severe_wound.speed_penalty
    assert mild_wound.max_hp_penalty < severe_wound.max_hp_penalty
    assert mild_wound.atk_penalty == int(mild_wound.severity * 3)
    assert mild_wound.def_penalty == int(mild_wound.severity * 2)
    assert mild_wound.speed_penalty == int(mild_wound.severity * 2)
    assert mild_wound.max_hp_penalty == int(mild_wound.severity * 10)
    assert severe_wound.atk_penalty == int(severe_wound.severity * 3)
    assert severe_wound.def_penalty == int(severe_wound.severity * 2)
    assert severe_wound.speed_penalty == int(severe_wound.severity * 2)
    assert severe_wound.max_hp_penalty == int(severe_wound.severity * 10)


def test_severe_wound_max_hp_penalty_reduces_effective_max_hp_through_apply_path():
    """
    [TCK-20260824-WOUND-PENALTY-FORMULA-WIRING] wound.max_hp_penalty must be non-zero for
    a severe wound inflicted through the live combat path, and must actually reduce
    effective max_hp once run through the authoritative apply path -- not just be
    non-zero on the WoundState object in isolation.
    """
    from src.engine.apply import ApplyPath
    from src.core.updates import EntityUpdate

    attacker = create_mock_entity(1, faction=Faction.HERO_GUILD, atk=100, dfn=5)
    defender = create_mock_entity(2, faction=Faction.MONSTER_HORDE, atk=5, dfn=0, hp=100)
    state = AuthoritativeState(tick=1, seed=42, entities={1: attacker, 2: defender})
    update = CombatResolutionSystem.resolve_attack(attacker, defender, state=state)

    assert update.wound_update is not None
    wound = update.wound_update.wounds_add[0]
    assert wound.max_hp_penalty > 0

    before_max_hp = defender.combat.max_hp
    result = ApplyPath._apply_entity_update(
        defender, EntityUpdate(entity_id=defender.id, wound_update=update.wound_update)
    )
    # get_effective_stats recomputes max_hp from attributes/equipment/traits (not a bare
    # subtraction from the pre-recompute combat.max_hp), so only assert the direction and
    # magnitude of the wound's own effect, not an exact post-recompute value.
    assert result.combat.max_hp < before_max_hp


def test_wound_infliction_below_live_threshold_produces_no_wound():
    """
    [TCK-20260824-WOUND-THRESHOLD-DECISION] Negative-boundary companion to
    test_wound_penalties_scale_with_severity_through_live_combat_path: damage at or below
    max_hp * 0.25 (the live strict `>` gate in _get_wound_infliction) must not produce a
    wound, through the real resolve_attack() entry point.
    """
    attacker = create_mock_entity(1, faction=Faction.HERO_GUILD, atk=10, dfn=5)
    defender = create_mock_entity(2, faction=Faction.MONSTER_HORDE, atk=5, dfn=5, hp=100)
    state = AuthoritativeState(tick=1, seed=42, entities={1: attacker, 2: defender})
    update = CombatResolutionSystem.resolve_attack(attacker, defender, state=state)

    assert update.damage_taken <= defender.combat.max_hp * 0.25
    assert update.wound_update is None
