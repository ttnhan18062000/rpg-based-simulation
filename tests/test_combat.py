"""Tests for the attribute-enhanced combat system."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.core.attributes import Attributes, AttributeCaps
from src.core.models import Entity, Stats, Vector2
from src.core.enums import AIState, EnemyTier
from src.core.faction import Faction
from src.core.items import Inventory


def _make_entity(
    eid: int, kind: str = "hero", pos: tuple = (0, 0),
    hp: int = 50, atk: int = 10, def_: int = 5, spd: int = 10,
    str_: int = 5, agi: int = 5, vit: int = 5,
    faction: Faction = Faction.HERO_GUILD,
    stamina: int = 50,
) -> Entity:
    """Helper to create a test entity with attributes."""
    stats = Stats(
        hp=hp, max_hp=hp, atk=atk, def_=def_, spd=spd,
        stamina=stamina, max_stamina=stamina,
    )
    attrs = Attributes(str_=str_, agi=agi, vit=vit, int_=5, wis=5, end=5)
    caps = AttributeCaps()
    inv = Inventory(items=[], max_slots=12, max_weight=30.0)
    return Entity(
        id=eid, kind=kind, pos=Vector2(*pos),
        stats=stats, faction=faction,
        inventory=inv, attributes=attrs, attribute_caps=caps,
    )


class TestEntityWithAttributes:
    """Test entity creation with the new attribute fields."""

    def test_entity_has_attributes(self):
        e = _make_entity(1)
        assert e.attributes is not None
        assert e.attributes.str_ == 5
        assert e.attribute_caps is not None

    def test_entity_has_stamina(self):
        e = _make_entity(1, stamina=60)
        assert e.stats.stamina == 60
        assert e.stats.max_stamina == 60
        assert e.stats.stamina_ratio == 1.0

    def test_stamina_ratio_partial(self):
        e = _make_entity(1, stamina=50)
        e.stats.stamina = 25
        assert abs(e.stats.stamina_ratio - 0.5) < 0.01

    def test_entity_copy_preserves_attributes(self):
        e = _make_entity(1, str_=15, agi=12)
        e.hero_class = 1  # WARRIOR
        e.class_mastery = 25.0
        copy = e.copy()
        assert copy.attributes.str_ == 15
        assert copy.attributes.agi == 12
        assert copy.attribute_caps is not None
        assert copy.hero_class == 1
        assert copy.class_mastery == 25.0
        # Ensure deep copy
        copy.attributes.str_ = 99
        assert e.attributes.str_ == 15

    def test_entity_copy_preserves_skills(self):
        from src.core.classes import SkillInstance
        e = _make_entity(1)
        e.skills = [SkillInstance(skill_id="power_strike", mastery=50.0)]
        copy = e.copy()
        assert len(copy.skills) == 1
        assert copy.skills[0].mastery == 50.0
        copy.skills[0].mastery = 0.0
        assert e.skills[0].mastery == 50.0


class TestDamageFormula:
    """Test that the attribute-enhanced damage formula produces sensible results."""

    def test_higher_str_more_damage(self):
        """Entity with higher STR should deal more raw damage."""
        # We test the formula directly rather than the full combat action
        # raw_damage = int(atk_power * str_mult) - int(def_power * vit_mult) // 2

        # Attacker with STR=5 vs STR=20
        atk_power = 10
        def_power = 5

        str_mult_low = 1.0 + 5 * 0.02   # 1.10
        str_mult_high = 1.0 + 20 * 0.02  # 1.40
        vit_mult = 1.0 + 5 * 0.01        # 1.05

        raw_low = int(atk_power * str_mult_low) - int(def_power * vit_mult) // 2
        raw_high = int(atk_power * str_mult_high) - int(def_power * vit_mult) // 2

        assert raw_high > raw_low

    def test_higher_vit_less_damage_taken(self):
        """Defender with higher VIT should take less damage."""
        atk_power = 10
        def_power = 5
        str_mult = 1.0 + 10 * 0.02  # 1.20

        vit_mult_low = 1.0 + 5 * 0.01   # 1.05
        vit_mult_high = 1.0 + 20 * 0.01  # 1.20

        raw_low_vit = int(atk_power * str_mult) - int(def_power * vit_mult_low) // 2
        raw_high_vit = int(atk_power * str_mult) - int(def_power * vit_mult_high) // 2

        assert raw_high_vit <= raw_low_vit

    def test_minimum_damage_is_one(self):
        """Even with 0 ATK, minimum raw damage should be 1."""
        atk_power = 0
        def_power = 50
        str_mult = 1.0
        vit_mult = 1.2

        raw = int(atk_power * str_mult) - int(def_power * vit_mult) // 2
        raw = max(raw, 1)
        assert raw == 1


class TestStaminaMechanics:
    """Test stamina cost and regeneration."""

    def test_stamina_decreases_on_attack(self):
        e = _make_entity(1, stamina=50)
        # Simulate attack stamina cost
        e.stats.stamina = max(0, e.stats.stamina - 3)
        assert e.stats.stamina == 47

    def test_stamina_decreases_on_move(self):
        e = _make_entity(1, stamina=50)
        e.stats.stamina = max(0, e.stats.stamina - 1)
        assert e.stats.stamina == 49

    def test_stamina_decreases_on_harvest(self):
        e = _make_entity(1, stamina=50)
        e.stats.stamina = max(0, e.stats.stamina - 2)
        assert e.stats.stamina == 48

    def test_stamina_cannot_go_below_zero(self):
        e = _make_entity(1, stamina=1)
        e.stats.stamina = max(0, e.stats.stamina - 5)
        assert e.stats.stamina == 0

    def test_stamina_regen_resting(self):
        e = _make_entity(1, stamina=50)
        e.stats.stamina = 20
        # Resting regen: +5 per tick
        regen = 5
        e.stats.stamina = min(e.stats.stamina + regen, e.stats.max_stamina)
        assert e.stats.stamina == 25

    def test_stamina_regen_active(self):
        e = _make_entity(1, stamina=50)
        e.stats.stamina = 20
        # Active regen: +1 per tick
        regen = 1
        e.stats.stamina = min(e.stats.stamina + regen, e.stats.max_stamina)
        assert e.stats.stamina == 21

    def test_stamina_regen_capped(self):
        e = _make_entity(1, stamina=50)
        e.stats.stamina = 49
        regen = 5
        e.stats.stamina = min(e.stats.stamina + regen, e.stats.max_stamina)
        assert e.stats.stamina == 50


class TestSkillUsage:
    """Test skill usage in combat (best_ready_skill helper + USE_SKILL processing)."""

    def test_best_ready_skill_returns_highest_power(self):
        from src.core.classes import SkillInstance
        from src.ai.states import best_ready_skill
        e = _make_entity(1, stamina=50)
        e.skills = [
            SkillInstance(skill_id="power_strike"),   # power=1.8
            SkillInstance(skill_id="ambush"),          # power=1.6
        ]
        result = best_ready_skill(e)
        assert result == "power_strike"

    def test_best_ready_skill_skips_on_cooldown(self):
        from src.core.classes import SkillInstance
        from src.ai.states import best_ready_skill
        e = _make_entity(1, stamina=50)
        si = SkillInstance(skill_id="power_strike")
        si.cooldown_remaining = 3  # on cooldown
        e.skills = [si, SkillInstance(skill_id="ambush")]
        result = best_ready_skill(e)
        assert result == "ambush"

    def test_best_ready_skill_skips_insufficient_stamina(self):
        from src.core.classes import SkillInstance
        from src.ai.states import best_ready_skill
        e = _make_entity(1, stamina=5)
        e.stats.stamina = 5
        # power_strike costs 12 stamina, ambush costs 8 — both too expensive
        e.skills = [
            SkillInstance(skill_id="power_strike"),
            SkillInstance(skill_id="ambush"),
        ]
        result = best_ready_skill(e)
        assert result is None

    def test_best_ready_skill_none_when_no_skills(self):
        from src.ai.states import best_ready_skill
        e = _make_entity(1, stamina=50)
        e.skills = []
        assert best_ready_skill(e) is None

    def test_best_ready_skill_ignores_passive(self):
        from src.core.classes import SkillInstance
        from src.ai.states import best_ready_skill
        e = _make_entity(1, stamina=50)
        e.skills = [SkillInstance(skill_id="scavenge")]  # passive skill
        assert best_ready_skill(e) is None

    def test_skill_use_costs_stamina(self):
        from src.core.classes import SkillInstance, SKILL_DEFS
        e = _make_entity(1, stamina=50)
        si = SkillInstance(skill_id="power_strike")
        sdef = SKILL_DEFS["power_strike"]
        cost = si.effective_stamina_cost(sdef.stamina_cost)
        e.stats.stamina -= cost
        assert e.stats.stamina == 50 - cost
        assert e.stats.stamina < 50

    def test_skill_use_sets_cooldown(self):
        from src.core.classes import SkillInstance, SKILL_DEFS
        si = SkillInstance(skill_id="power_strike")
        sdef = SKILL_DEFS["power_strike"]
        assert si.is_ready()
        cd = si.effective_cooldown(sdef.cooldown)
        si.use(base_cooldown=cd)
        assert not si.is_ready()
        assert si.cooldown_remaining == cd

    def test_skill_use_increases_mastery(self):
        from src.core.classes import SkillInstance, SKILL_DEFS
        si = SkillInstance(skill_id="power_strike")
        assert si.mastery == 0.0
        sdef = SKILL_DEFS["power_strike"]
        si.use(base_cooldown=si.effective_cooldown(sdef.cooldown))
        assert si.mastery > 0.0
        assert si.times_used == 1

    def test_self_skill_heals(self):
        from src.core.classes import SkillInstance, SKILL_DEFS
        e = _make_entity(1, hp=100, stamina=50)
        e.stats.hp = 50  # half HP
        sdef = SKILL_DEFS.get("second_wind")
        assert sdef is not None
        hp_mod = getattr(sdef, 'hp_mod', 0.0) or 0.0
        heal = int(e.stats.max_hp * hp_mod) if hp_mod > 0 else 0
        e.stats.hp = min(e.stats.hp + heal, e.stats.max_hp)
        assert e.stats.hp > 50  # healed some

    def test_skill_damage_formula(self):
        from src.core.classes import SkillInstance, SKILL_DEFS
        attacker = _make_entity(1, atk=20, str_=10, stamina=50)
        defender = _make_entity(2, hp=100, def_=5, vit=5, faction=Faction.GOBLIN_HORDE)
        si = SkillInstance(skill_id="power_strike")
        sdef = SKILL_DEFS["power_strike"]
        power = si.effective_power(sdef.power)
        raw_dmg = int(attacker.effective_atk() * power)
        dmg = max(raw_dmg - defender.effective_def() // 2, 1)
        defender.stats.hp -= dmg
        assert defender.stats.hp < 100
        assert dmg > 0


class TestSkillEffects:
    """Test skill buff/debuff StatusEffect application."""

    def test_self_buff_applies_effect(self):
        from src.core.effects import skill_effect, EffectType
        e = _make_entity(1)
        eff = skill_effect(atk_mod=0.2, def_mod=0.5, duration=3, source="Shield Wall")
        e.effects.append(eff)
        assert len(e.effects) == 1
        assert e.effects[0].effect_type == EffectType.SKILL_BUFF
        assert e.effects[0].atk_mult == 1.2
        assert e.effects[0].def_mult == 1.5
        assert e.effects[0].remaining_ticks == 3

    def test_buff_modifies_effective_stats(self):
        from src.core.effects import skill_effect
        e = _make_entity(1, atk=10, def_=10)
        base_atk = e.effective_atk()
        base_def = e.effective_def()
        e.effects.append(skill_effect(atk_mod=0.3, def_mod=0.4, duration=3))
        assert e.effective_atk() > base_atk
        assert e.effective_def() > base_def

    def test_debuff_reduces_effective_stats(self):
        from src.core.effects import skill_effect
        e = _make_entity(1, atk=20, def_=10)
        base_atk = e.effective_atk()
        e.effects.append(skill_effect(atk_mod=-0.15, duration=3, is_debuff=True))
        assert e.effective_atk() < base_atk

    def test_effect_expires_after_ticks(self):
        from src.core.effects import skill_effect
        e = _make_entity(1)
        eff = skill_effect(atk_mod=0.2, duration=2, source="test")
        e.effects.append(eff)
        assert len(e.effects) == 1
        assert eff.remaining_ticks == 2
        eff.tick()  # 2 -> 1
        assert eff.remaining_ticks == 1
        assert not eff.expired
        eff.tick()  # 1 -> 0
        assert eff.remaining_ticks == 0
        assert eff.expired
        e.effects = [ef for ef in e.effects if not ef.expired]
        assert len(e.effects) == 0

    def test_hp_per_tick_dot(self):
        from src.core.effects import skill_effect
        e = _make_entity(1, hp=50)
        eff = skill_effect(hp_per_tick=-5, duration=3, is_debuff=True, source="poison")
        e.effects.append(eff)
        # Simulate tick: apply hp_per_tick then tick
        e.stats.hp = max(0, e.stats.hp + eff.hp_per_tick)
        assert e.stats.hp == 45

    def test_hp_per_tick_regen(self):
        from src.core.effects import skill_effect
        e = _make_entity(1, hp=50)
        e.stats.hp = 30
        eff = skill_effect(hp_per_tick=10, duration=3, source="regen")
        e.effects.append(eff)
        e.stats.hp = min(e.stats.hp + eff.hp_per_tick, e.stats.max_hp)
        assert e.stats.hp == 40

    def test_multiple_effects_stack(self):
        from src.core.effects import skill_effect
        e = _make_entity(1, atk=10)
        e.effects.append(skill_effect(atk_mod=0.2, duration=3))
        e.effects.append(skill_effect(atk_mod=0.3, duration=3))
        # Multiplicative: 10 * 1.2 * 1.3 = 15.6 -> 15
        assert e.effective_atk() == int(10 * 1.2 * 1.3)

    def test_skill_effect_factory_debuff_type(self):
        from src.core.effects import skill_effect, EffectType
        eff = skill_effect(atk_mod=-0.15, duration=3, is_debuff=True, source="War Cry")
        assert eff.effect_type == EffectType.SKILL_DEBUFF
        assert eff.atk_mult == 0.85
        assert eff.source == "War Cry"
