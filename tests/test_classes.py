"""Tests for the class, skill, breakthrough, and mastery systems."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.core.classes import (
    HeroClass, SkillType, SkillTarget, SkillDef, SkillInstance,
    ClassDef, BreakthroughDef, CLASS_DEFS, BREAKTHROUGHS, SKILL_DEFS,
    RACE_SKILLS, CLASS_SKILLS, can_breakthrough, available_class_skills,
    get_attr_value,
)
from src.core.attributes import Attributes


class TestSkillDef:
    """Test skill definitions and registry."""

    def test_skill_registry_not_empty(self):
        assert len(SKILL_DEFS) > 0

    def test_warrior_skills_exist(self):
        assert "power_strike" in SKILL_DEFS
        assert "shield_wall" in SKILL_DEFS
        assert "battle_cry" in SKILL_DEFS

    def test_ranger_skills_exist(self):
        assert "quick_shot" in SKILL_DEFS
        assert "evasive_step" in SKILL_DEFS
        assert "mark_prey" in SKILL_DEFS

    def test_mage_skills_exist(self):
        assert "arcane_bolt" in SKILL_DEFS
        assert "frost_shield" in SKILL_DEFS
        assert "mana_surge" in SKILL_DEFS

    def test_rogue_skills_exist(self):
        assert "backstab" in SKILL_DEFS
        assert "shadowstep" in SKILL_DEFS
        assert "poison_blade" in SKILL_DEFS

    def test_race_skills_exist(self):
        assert "rally" in SKILL_DEFS
        assert "second_wind" in SKILL_DEFS
        assert "ambush" in SKILL_DEFS
        assert "pack_hunt" in SKILL_DEFS
        assert "feral_bite" in SKILL_DEFS
        assert "quickdraw" in SKILL_DEFS
        assert "drain_life" in SKILL_DEFS
        assert "berserker_rage" in SKILL_DEFS
        assert "war_cry" in SKILL_DEFS

    def test_power_strike_stats(self):
        ps = SKILL_DEFS["power_strike"]
        assert ps.skill_type == SkillType.ACTIVE
        assert ps.target == SkillTarget.SINGLE_ENEMY
        assert ps.class_req == HeroClass.WARRIOR
        assert ps.power == 1.8
        assert ps.stamina_cost == 12
        assert ps.cooldown == 4

    def test_race_skill_no_class_req(self):
        rally = SKILL_DEFS["rally"]
        assert rally.class_req == HeroClass.NONE
        assert rally.gold_cost == 0


class TestSkillInstance:
    """Test skill instance mechanics."""

    def test_initial_state(self):
        si = SkillInstance(skill_id="power_strike")
        assert si.is_ready()
        assert si.mastery == 0.0
        assert si.times_used == 0
        assert si.mastery_tier == 0

    def test_use_sets_cooldown(self):
        si = SkillInstance(skill_id="power_strike")
        si.use(base_cooldown=4)
        assert si.cooldown_remaining == 4
        assert not si.is_ready()
        assert si.times_used == 1

    def test_tick_reduces_cooldown(self):
        si = SkillInstance(skill_id="power_strike")
        si.use(base_cooldown=3)
        si.tick()
        assert si.cooldown_remaining == 2
        si.tick()
        assert si.cooldown_remaining == 1
        si.tick()
        assert si.cooldown_remaining == 0
        assert si.is_ready()

    def test_mastery_gain(self):
        si = SkillInstance(skill_id="power_strike")
        si.use(base_cooldown=4)
        assert si.mastery > 0.0

    def test_mastery_tiers(self):
        si = SkillInstance(skill_id="power_strike", mastery=0.0)
        assert si.mastery_tier == 0
        si.mastery = 25.0
        assert si.mastery_tier == 1
        si.mastery = 50.0
        assert si.mastery_tier == 2
        si.mastery = 75.0
        assert si.mastery_tier == 3
        si.mastery = 100.0
        assert si.mastery_tier == 4

    def test_effective_power_scales_with_mastery(self):
        si = SkillInstance(skill_id="power_strike", mastery=0.0)
        base_power = 1.8
        assert si.effective_power(base_power) == base_power

        si.mastery = 50.0
        assert si.effective_power(base_power) > base_power  # +20%

        si.mastery = 100.0
        assert si.effective_power(base_power) > base_power * 1.2  # +35%

    def test_effective_stamina_cost_reduces_with_mastery(self):
        si = SkillInstance(skill_id="power_strike", mastery=0.0)
        base_cost = 12
        assert si.effective_stamina_cost(base_cost) == 12

        si.mastery = 25.0
        assert si.effective_stamina_cost(base_cost) < 12  # -10%

        si.mastery = 75.0
        assert si.effective_stamina_cost(base_cost) < si.effective_stamina_cost.__func__(
            SkillInstance(skill_id="x", mastery=25.0), base_cost)  # -20% total

    def test_effective_cooldown_reduces_at_mastery_3(self):
        si = SkillInstance(skill_id="power_strike", mastery=0.0)
        assert si.effective_cooldown(4) == 4
        si.mastery = 75.0
        assert si.effective_cooldown(4) == 3
        # Minimum cooldown is 1
        assert si.effective_cooldown(1) == 1

    def test_copy(self):
        si = SkillInstance(skill_id="power_strike", cooldown_remaining=3, mastery=50.0, times_used=10)
        copy = si.copy()
        assert copy.skill_id == "power_strike"
        assert copy.mastery == 50.0
        assert copy.times_used == 10
        copy.mastery = 0.0
        assert si.mastery == 50.0  # original unchanged


class TestClassDefs:
    """Test class definitions and breakthroughs."""

    def test_all_base_classes_defined(self):
        assert HeroClass.WARRIOR in CLASS_DEFS
        assert HeroClass.RANGER in CLASS_DEFS
        assert HeroClass.MAGE in CLASS_DEFS
        assert HeroClass.ROGUE in CLASS_DEFS

    def test_warrior_class(self):
        w = CLASS_DEFS[HeroClass.WARRIOR]
        assert w.name == "Warrior"
        assert w.str_bonus == 3
        assert w.vit_bonus == 2
        assert w.str_cap_bonus == 10
        assert w.breakthrough_class == HeroClass.CHAMPION

    def test_breakthroughs_defined(self):
        assert HeroClass.WARRIOR in BREAKTHROUGHS
        assert HeroClass.RANGER in BREAKTHROUGHS
        assert HeroClass.MAGE in BREAKTHROUGHS
        assert HeroClass.ROGUE in BREAKTHROUGHS

    def test_warrior_breakthrough(self):
        bt = BREAKTHROUGHS[HeroClass.WARRIOR]
        assert bt.to_class == HeroClass.CHAMPION
        assert bt.level_req == 10
        assert bt.attr_req == "str"
        assert bt.attr_threshold == 30
        assert bt.talent == "Unyielding"


class TestBreakthroughLogic:
    """Test breakthrough eligibility checks."""

    def test_can_breakthrough_warrior(self):
        attrs = Attributes(str_=30, agi=5, vit=5, int_=5, wis=5, end=5)
        assert can_breakthrough(HeroClass.WARRIOR, 10, attrs) is True

    def test_cannot_breakthrough_low_level(self):
        attrs = Attributes(str_=30, agi=5, vit=5, int_=5, wis=5, end=5)
        assert can_breakthrough(HeroClass.WARRIOR, 9, attrs) is False

    def test_cannot_breakthrough_low_attr(self):
        attrs = Attributes(str_=29, agi=5, vit=5, int_=5, wis=5, end=5)
        assert can_breakthrough(HeroClass.WARRIOR, 10, attrs) is False

    def test_cannot_breakthrough_no_class(self):
        attrs = Attributes(str_=30, agi=5, vit=5, int_=5, wis=5, end=5)
        assert can_breakthrough(HeroClass.NONE, 10, attrs) is False

    def test_cannot_breakthrough_already_advanced(self):
        attrs = Attributes(str_=30, agi=5, vit=5, int_=5, wis=5, end=5)
        # CHAMPION has no breakthrough defined
        assert can_breakthrough(HeroClass.CHAMPION, 10, attrs) is False


class TestAvailableClassSkills:
    """Test skill availability based on class and level."""

    def test_warrior_level_1(self):
        skills = available_class_skills(HeroClass.WARRIOR, 1)
        assert "power_strike" in skills
        assert "shield_wall" not in skills  # Requires level 3

    def test_warrior_level_5(self):
        skills = available_class_skills(HeroClass.WARRIOR, 5)
        assert "power_strike" in skills
        assert "shield_wall" in skills
        assert "battle_cry" in skills

    def test_no_class(self):
        skills = available_class_skills(HeroClass.NONE, 10)
        assert skills == []


class TestRaceSkills:
    """Test race skill mappings."""

    def test_hero_race_skills(self):
        assert "rally" in RACE_SKILLS["hero"]
        assert "second_wind" in RACE_SKILLS["hero"]

    def test_wolf_race_skills(self):
        assert "pack_hunt" in RACE_SKILLS["wolf"]
        assert "feral_bite" in RACE_SKILLS["wolf"]

    def test_orc_race_skills(self):
        assert "berserker_rage" in RACE_SKILLS["orc"]
        assert "war_cry" in RACE_SKILLS["orc"]

    def test_all_race_skill_ids_valid(self):
        for kind, skill_ids in RACE_SKILLS.items():
            for sid in skill_ids:
                assert sid in SKILL_DEFS, f"Race skill '{sid}' for '{kind}' not in SKILL_DEFS"

    def test_all_class_skill_ids_valid(self):
        for cls, skill_ids in CLASS_SKILLS.items():
            for sid in skill_ids:
                assert sid in SKILL_DEFS, f"Class skill '{sid}' for {cls} not in SKILL_DEFS"


class TestGetAttrValue:
    """Test attribute value getter by string name."""

    def test_get_str(self):
        attrs = Attributes(str_=10)
        assert get_attr_value(attrs, "str") == 10

    def test_get_agi(self):
        attrs = Attributes(agi=15)
        assert get_attr_value(attrs, "agi") == 15

    def test_get_unknown(self):
        attrs = Attributes()
        assert get_attr_value(attrs, "unknown") == 0
