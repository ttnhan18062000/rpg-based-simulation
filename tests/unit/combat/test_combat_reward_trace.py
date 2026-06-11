"""
Tests asserting REWARD_CATEGORY and REWARD_SOURCE are present in combat update traces.
"""
from __future__ import annotations

from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole, Faction
from src.core.state import AuthoritativeState
from src.engine.combat import CombatResolutionSystem
from src.engine.combat_rewards import RewardCategory


def _hero(eid: int, atk: int = 1000, hp: int = 100) -> object:
    return (V2EntityBuilder(eid)
        .kind("hero")
        .location(0.0, 0.0)
        .identity(role=EntityRole.HERO, faction=Faction.HERO_GUILD)
        .attributes(strength=0, vitality=0)
        .combat(hp=hp, max_hp=hp, atk=atk, def_stat=1, readiness=100.0)
        .build())


def _monster(eid: int, hp: int = 10, evolution_level: int = 1) -> object:
    b = (V2EntityBuilder(eid)
        .kind("hero")
        .location(0.0, 0.0)
        .identity(role=EntityRole.MONSTER, faction=Faction.MONSTER_HORDE)
        .attributes(strength=0, vitality=0)
        .combat(hp=hp, max_hp=hp, atk=5, def_stat=1, readiness=100.0))
    entity = b.build()
    if evolution_level != 1:
        from dataclasses import replace
        entity = replace(entity, identity=replace(entity.identity, evolution_level=evolution_level))
    return entity


def _state(*entities) -> AuthoritativeState:
    return AuthoritativeState(tick=1, seed=42, entities={e.id: e for e in entities})


# ── resolve_attack trace ──────────────────────────────────────────────────────

def test_resolve_attack_monster_kill_has_reward_category():
    """Monster kill via resolve_attack includes REWARD_CATEGORY in trace."""
    attacker = _hero(1)
    defender = _monster(2)
    result = CombatResolutionSystem.resolve_attack(attacker, defender, _state(attacker, defender))
    assert result.outcome_kind == "KILL"
    assert "REWARD_CATEGORY" in result.trace, "REWARD_CATEGORY missing from resolve_attack kill trace"
    assert result.trace["REWARD_CATEGORY"] == RewardCategory.HOSTILE_CREATURE.value


def test_resolve_attack_monster_kill_reward_source_is_hostile_relation():
    """REWARD_SOURCE on monster kill is 'hostile_relation'."""
    attacker = _hero(1)
    defender = _monster(2)
    result = CombatResolutionSystem.resolve_attack(attacker, defender, _state(attacker, defender))
    assert result.trace["REWARD_SOURCE"] == "hostile_relation"


def test_resolve_attack_hero_defeat_has_hero_kill_category():
    """Hero defender killed → REWARD_CATEGORY = hero_kill."""
    attacker = (V2EntityBuilder(1)
        .kind("hero").location(0.0, 0.0)
        .identity(role=EntityRole.MONSTER, faction=Faction.MONSTER_HORDE)
        .attributes(strength=0, vitality=0)
        .combat(hp=100, max_hp=100, atk=1000, def_stat=1, readiness=100.0)
        .build())
    defender = _hero(2, atk=5, hp=10)
    result = CombatResolutionSystem.resolve_attack(attacker, defender, _state(attacker, defender))
    assert "REWARD_CATEGORY" in result.trace
    assert result.trace["REWARD_CATEGORY"] == RewardCategory.HERO_KILL.value


def test_resolve_attack_survive_has_no_reward_trace_keys():
    """Surviving combat must NOT include REWARD_CATEGORY or REWARD_SOURCE in trace."""
    attacker = _hero(1, atk=5)       # low ATK — won't kill high-HP defender
    defender = _monster(2, hp=1000)
    result = CombatResolutionSystem.resolve_attack(attacker, defender, _state(attacker, defender))
    assert result.outcome_kind == "SURVIVE"
    assert "REWARD_CATEGORY" not in result.trace
    assert "REWARD_SOURCE" not in result.trace


# ── resolve_skill_usage trace ─────────────────────────────────────────────────

def test_resolve_skill_usage_kill_has_reward_category():
    """Skill-based kill includes REWARD_CATEGORY and REWARD_SOURCE in trace."""
    attacker = _hero(1)
    defender = _monster(2)
    result = CombatResolutionSystem.resolve_skill_usage(
        attacker, defender, _state(attacker, defender), damage=999
    )
    assert result.outcome_kind == "KILL"
    assert "REWARD_CATEGORY" in result.trace, "REWARD_CATEGORY missing from resolve_skill_usage trace"
    assert "REWARD_SOURCE" in result.trace, "REWARD_SOURCE missing from resolve_skill_usage trace"


def test_resolve_skill_usage_kill_reward_source_value():
    """REWARD_SOURCE from skill kill matches classification source."""
    attacker = _hero(1)
    defender = _monster(2)
    result = CombatResolutionSystem.resolve_skill_usage(
        attacker, defender, _state(attacker, defender), damage=999
    )
    assert result.trace["REWARD_SOURCE"] == "hostile_relation"


def test_resolve_skill_usage_survive_has_no_reward_trace_keys():
    """Surviving skill attack must NOT include reward trace keys."""
    attacker = _hero(1)
    defender = _monster(2, hp=1000)
    result = CombatResolutionSystem.resolve_skill_usage(
        attacker, defender, _state(attacker, defender), damage=1
    )
    assert result.outcome_kind == "SURVIVE"
    assert "REWARD_CATEGORY" not in result.trace
    assert "REWARD_SOURCE" not in result.trace


# ── reward values unchanged ───────────────────────────────────────────────────

def test_reward_xp_calculation_unchanged():
    """XP = evolution_level * xp_multiplier — unchanged by adding trace keys."""
    attacker = _hero(1)
    defender = _monster(2, evolution_level=3)
    result = CombatResolutionSystem.resolve_attack(attacker, defender, _state(attacker, defender))
    xp_transfers = [t for t in result.resource_transfers if t.xp_reward > 0]
    assert xp_transfers, "Expected at least one XP resource transfer"
    assert xp_transfers[0].xp_reward == 3 * 10  # evolution_level=3, xp_multiplier=10
