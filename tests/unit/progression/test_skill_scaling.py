import pytest
from src.core.gameplay.classes import SKILL_DEFS, SkillDef, SkillType, SkillTarget, HeroClass
from src.core.models.enums import DamageType, Faction
from src.actions.damage import get_damage_calculator, DamageContext
from src.core.entities.entity import Entity
from src.core.models.vectors import Vector2
from src.core.gameplay.attributes import Attributes
from src.core.aspects.identity import IdentityAspect
from src.core.aspects.spatial import SpatialAspect
from src.core.aspects.combat import CombatAspect
from src.core.aspects.progression import ProgressionAspect
from src.core.aspects.mind import MindAspect
from src.core.registry.registry_loader import load_all_registries

@pytest.fixture(scope="module", autouse=True)
def setup_registries():
    # Load from the project root data directory
    import os
    from src.core.gameplay.classes import SKILL_DEFS
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    data_dir = os.path.join(project_root, "data")
    load_all_registries(data_dir)

class TestSkillDefDamageType:
    """SkillDef has a damage_type field routing to correct stat pair."""

    def test_default_is_physical(self):
        sdef = SkillDef(
            "test_skill", "Test", "desc",
            SkillType.ACTIVE, SkillTarget.SINGLE_ENEMY, HeroClass.NONE,
        )
        assert sdef.damage_type == DamageType.PHYSICAL

    def test_arcane_bolt_is_magical(self):
        sdef = SKILL_DEFS["arcane_bolt"]
        assert sdef.damage_type == DamageType.MAGICAL

    def test_drain_life_is_magical(self):
        sdef = SKILL_DEFS["drain_life"]
        assert sdef.damage_type == DamageType.MAGICAL

    def test_power_strike_is_physical(self):
        sdef = SKILL_DEFS["power_strike"]
        assert sdef.damage_type == DamageType.PHYSICAL

    def test_backstab_is_physical(self):
        sdef = SKILL_DEFS["backstab"]
        assert sdef.damage_type == DamageType.PHYSICAL

    def test_quick_shot_is_physical(self):
        sdef = SKILL_DEFS["quick_shot"]
        assert sdef.damage_type == DamageType.PHYSICAL

    def test_ambush_is_physical(self):
        sdef = SKILL_DEFS["ambush"]
        assert sdef.damage_type == DamageType.PHYSICAL

    def test_buff_skills_default_physical(self):
        """Buff/debuff skills without power don't deal damage, but default to PHYSICAL."""
        for sid in ("shield_wall", "evasive_step", "frost_shield",
                    "shadowstep", "rally", "berserker_rage", "war_cry"):
            sdef = SKILL_DEFS[sid]
            assert sdef.damage_type == DamageType.PHYSICAL, f"{sid} should default to PHYSICAL"


class TestDamageCalculatorRouting:
    """DamageCalculator uses correct stat pair based on damage_type."""

    def _make_entity(self, atk=20, def_=10, matk=30, mdef=15, str_=10, spi=12, vit=8, wis=6):
        return Entity(
            id=1, kind="hero",
            identity=IdentityAspect(name="TestHero", faction=Faction.HERO_GUILD),
            spatial=SpatialAspect(pos=Vector2(5, 5)),
            combat=CombatAspect(hp=100, max_hp=100, atk_base=atk, def_base=def_, spd_base=10, matk=matk, mdef=mdef),
            progression=ProgressionAspect(
                attributes=Attributes(str_=str_, spi=spi, vit=vit, wis=wis)
            ),
            mind=MindAspect()
        )

    def test_physical_uses_atk_def(self):
        attacker = self._make_entity(atk=20, def_=5, matk=50, mdef=50)
        defender = self._make_entity(atk=5, def_=15, matk=5, mdef=5)
        calc = get_damage_calculator(DamageType.PHYSICAL)
        ctx = calc.resolve(attacker, defender)
        # Physical should use combatAspect atk and def_
        assert ctx.atk_power == attacker.combat.atk
        assert ctx.def_power == defender.combat.def_

    def test_magical_uses_matk_mdef(self):
        attacker = self._make_entity(atk=5, def_=5, matk=30, mdef=5)
        defender = self._make_entity(atk=5, def_=5, matk=5, mdef=20)
        calc = get_damage_calculator(DamageType.MAGICAL)
        ctx = calc.resolve(attacker, defender)
        assert ctx.atk_power == attacker.combat.matk
        assert ctx.def_power == defender.combat.mdef

    def test_physical_atk_mult_scales_with_str(self):
        attacker = self._make_entity(str_=20)
        defender = self._make_entity()
        calc = get_damage_calculator(DamageType.PHYSICAL)
        ctx = calc.resolve(attacker, defender)
        expected_mult = 1.0 + 20 * 0.02  # 1.4
        assert abs(ctx.atk_mult - expected_mult) < 0.01

    def test_magical_atk_mult_scales_with_spi(self):
        attacker = self._make_entity(spi=25)
        defender = self._make_entity()
        calc = get_damage_calculator(DamageType.MAGICAL)
        ctx = calc.resolve(attacker, defender)
        expected_mult = 1.0 + 25 * 0.02  # 1.5
        assert abs(ctx.atk_mult - expected_mult) < 0.01

    def test_physical_def_mult_scales_with_vit(self):
        attacker = self._make_entity()
        defender = self._make_entity(vit=30)
        calc = get_damage_calculator(DamageType.PHYSICAL)
        ctx = calc.resolve(attacker, defender)
        expected_mult = 1.0 + 30 * 0.01  # 1.3
        assert abs(ctx.def_mult - expected_mult) < 0.01

    def test_magical_def_mult_scales_with_wis(self):
        attacker = self._make_entity()
        defender = self._make_entity(wis=20)
        calc = get_damage_calculator(DamageType.MAGICAL)
        ctx = calc.resolve(attacker, defender)
        expected_mult = 1.0 + 20 * 0.01  # 1.2
        assert abs(ctx.def_mult - expected_mult) < 0.01


class TestSkillDamageTypeIntegration:
    """Verify that skill damage_type routes to the correct calculator."""

    def test_magical_skill_higher_dmg_with_high_matk(self):
        """A magical skill should do more damage when MATK is high and ATK is low."""
        calc_phys = get_damage_calculator(DamageType.PHYSICAL)
        calc_mag = get_damage_calculator(DamageType.MAGICAL)

        attacker = Entity(
            id=1, kind="mage",
            identity=IdentityAspect(faction=Faction.HERO_GUILD),
            spatial=SpatialAspect(pos=Vector2(0, 0)),
            combat=CombatAspect(hp=100, max_hp=100, atk_base=5, def_base=10, spd_base=10, matk=30, mdef=5),
            progression=ProgressionAspect(level=1)
        )

        defender = Entity(
            id=2, kind="goblin",
            identity=IdentityAspect(faction=Faction.GOBLIN_HORDE),
            spatial=SpatialAspect(pos=Vector2(1, 0)),
            combat=CombatAspect(hp=100, max_hp=100, atk_base=10, def_base=10, spd_base=10, matk=5, mdef=10),
            progression=ProgressionAspect(level=1)
        )

        phys_ctx = calc_phys.resolve(attacker, defender)
        mag_ctx = calc_mag.resolve(attacker, defender)

        # Magical should have higher atk_power because MATK=30 >> ATK=5
        assert mag_ctx.atk_power > phys_ctx.atk_power

    def test_all_damage_skills_have_valid_damage_type(self):
        """Every skill with power > 0 should have a valid DamageType."""
        for sid, sdef in SKILL_DEFS.items():
            if sdef.power > 0 and sdef.target in (SkillTarget.SINGLE_ENEMY, SkillTarget.AREA_ENEMIES):
                assert sdef.damage_type in (DamageType.PHYSICAL, DamageType.MAGICAL), \
                    f"Skill {sid} has power={sdef.power} but invalid damage_type={sdef.damage_type}"
