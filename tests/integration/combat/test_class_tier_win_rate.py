from src.core.builder import V2EntityBuilder
from src.core.classes import CLASS_REGISTRY
from src.core.enums import EntityRole, Faction
from src.core.state import AttributeComponent
from src.engine.combat import CombatResolutionSystem
from src.engine.rpg_depth import SkillScalingService


def _build_attacker(entity_id: int, class_id):
    """
    A WARRIOR-classed attacker at CLASS_REGISTRY['WARRIOR'] base stats, with
    default (unbonused) attributes, optionally branched into a class tier.
    """
    class_def = CLASS_REGISTRY["WARRIOR"]
    attributes = AttributeComponent()
    derived = SkillScalingService.get_effective_stats(
        attributes,
        base_hp=class_def.base_hp,
        base_atk=class_def.base_atk,
        base_def=class_def.base_def,
        class_id=class_id,
    )
    return (
        V2EntityBuilder(entity_id)
        .kind("hero")
        .location(0.0, 0.0)
        .identity(role=EntityRole.HERO, faction=Faction.HERO_GUILD, class_id=class_id or "WARRIOR")
        .combat(
            hp=derived["max_hp"],
            max_hp=derived["max_hp"],
            atk=derived["atk"],
            def_stat=derived["def_stat"],
            alive=True,
            readiness=100.0,
        )
        .lifecycle(active=True)
        .build()
    )


def _build_opponent(entity_id: int, atk: int, def_stat: int, hp: int):
    return (
        V2EntityBuilder(entity_id)
        .kind("mob")
        .location(1.0, 0.0)
        .identity(role=EntityRole.MONSTER, faction=Faction.MONSTER_HORDE)
        .combat(hp=hp, max_hp=hp, atk=atk, def_stat=def_stat, alive=True, readiness=100.0)
        .lifecycle(active=True)
        .build()
    )


def _attacker_wins(attacker, opponent, max_rounds: int = 50) -> bool:
    """
    Deterministic alternating-turn damage exchange. CombatResolutionSystem.
    calculate_damage() is a pure, RNG-free function (int(atk*(atk/(atk+dfn*2+1)))),
    so this is a fixed sweep across opponent profiles, not a statistical sample.
    """
    attacker_hp = attacker.combat.hp
    opponent_hp = opponent.combat.hp
    for _ in range(max_rounds):
        opponent_hp -= CombatResolutionSystem.calculate_damage(attacker, opponent)
        if opponent_hp <= 0:
            return True
        attacker_hp -= CombatResolutionSystem.calculate_damage(opponent, attacker)
        if attacker_hp <= 0:
            return False
    return opponent_hp <= attacker_hp


def test_tier_bonus_does_not_decrease_win_rate():
    """
    Verify WARRIOR_CHAMPION's tier attribute bonuses (AC #4) do not decrease
    average combat win-rate versus a fixed roster of varied opponents.

    Fraud this catches:
        - a tier bonus that looks additive on the registry but nets a worse
          win-rate once fed through the real deterministic damage formula
          against a spread of opponent atk/def profiles
    """
    pre_tier_attacker = _build_attacker(1, class_id=None)
    post_tier_attacker = _build_attacker(2, class_id="WARRIOR_CHAMPION")

    roster = [
        _build_opponent(100 + i, atk=atk, def_stat=max(1, atk // 2), hp=80 + atk * 2)
        for i, atk in enumerate(range(8, 28, 2))
    ]

    pre_wins = sum(1 for opp in roster if _attacker_wins(pre_tier_attacker, opp))
    post_wins = sum(1 for opp in roster if _attacker_wins(post_tier_attacker, opp))

    assert post_wins >= pre_wins
