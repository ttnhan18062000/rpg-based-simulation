"""
Contract tests for Genetics (Innate Talents) and Skill Scaling.

Covers:
- LEG-RPG-144: Innate Talents (Genetics)
- LEG-RPG-145: Skill Scaling (Types)
"""
import inspect
from pathlib import Path

import pytest
from src.systems.genetics import (
    GeneticsSystem, SkillScalingSystem,
    GeneticProfile, SkillDefinition, SkillType
)


class TestGeneticTalentMultipliers:
    """LEG-RPG-144: Talent multipliers from genetic profile."""

    def test_neutral_profile_no_change(self):
        base = {"strength": 20, "agility": 15, "intelligence": 12}
        profile = GeneticProfile()  # All 1.0
        effective = GeneticsSystem.apply_genetic_profile(base, profile)
        assert effective["strength"] == 20.0
        assert effective["agility"] == 15.0

    def test_high_strength_talent_boosts(self):
        base = {"strength": 20, "agility": 15}
        profile = GeneticProfile(strength_mult=1.3, agility_mult=0.9)
        effective = GeneticsSystem.apply_genetic_profile(base, profile)
        assert effective["strength"] == pytest.approx(26.0)
        assert effective["agility"] == pytest.approx(13.5)

    def test_deterministic_profile_from_seed(self):
        p1 = GeneticsSystem.generate_profile_from_seed(42)
        p2 = GeneticsSystem.generate_profile_from_seed(42)
        assert p1 == p2

    def test_different_seeds_different_profiles(self):
        p1 = GeneticsSystem.generate_profile_from_seed(42)
        p2 = GeneticsSystem.generate_profile_from_seed(99)
        # At least one multiplier should differ
        assert p1 != p2

    def test_profile_multipliers_in_range(self):
        profile = GeneticsSystem.generate_profile_from_seed(12345)
        for mult in [profile.strength_mult, profile.agility_mult,
                     profile.intelligence_mult, profile.wisdom_mult,
                     profile.constitution_mult, profile.charisma_mult]:
            assert 0.8 <= mult <= 1.3


class TestSkillScaling:
    """LEG-RPG-145: Physical/Magical/Elemental scaling."""

    def test_physical_scales_with_strength(self):
        skill = SkillDefinition(id="slash", name="Slash", skill_type=SkillType.PHYSICAL,
                                 base_power=20.0, primary_attribute="strength")
        stats = {"strength": 50.0}
        power = SkillScalingSystem.compute_skill_power(skill, stats)
        # 20 * (1 + 50/100) = 20 * 1.5 = 30
        assert power == pytest.approx(30.0)

    def test_magical_scales_with_int_and_wis(self):
        skill = SkillDefinition(id="fireball", name="Fireball", skill_type=SkillType.MAGICAL,
                                 base_power=25.0, primary_attribute="intelligence",
                                 secondary_attribute="wisdom")
        stats = {"intelligence": 40.0, "wisdom": 20.0}
        power = SkillScalingSystem.compute_skill_power(skill, stats)
        # 25 * (1 + 40/80 + 20/200) = 25 * (1 + 0.5 + 0.1) = 25 * 1.6 = 40
        assert power == pytest.approx(40.0)

    def test_elemental_has_bonus_multiplier(self):
        skill = SkillDefinition(id="lightning", name="Lightning Bolt",
                                 skill_type=SkillType.ELEMENTAL,
                                 base_power=30.0, primary_attribute="intelligence")
        stats = {"intelligence": 45.0}
        power = SkillScalingSystem.compute_skill_power(skill, stats)
        # 30 * (1 + 45/90) * 1.1 = 30 * 1.5 * 1.1 = 49.5
        assert power == pytest.approx(49.5)

    def test_hybrid_uses_combined_stats(self):
        skill = SkillDefinition(id="holy_strike", name="Holy Strike",
                                 skill_type=SkillType.HYBRID,
                                 base_power=20.0, primary_attribute="strength",
                                 secondary_attribute="wisdom")
        stats = {"strength": 30.0, "wisdom": 30.0}
        power = SkillScalingSystem.compute_skill_power(skill, stats)
        # 20 * (1 + 60/150) = 20 * 1.4 = 28
        assert power == pytest.approx(28.0)

    def test_type_scaling_differs(self):
        """Different skill types produce different power from same stats."""
        stats = {"strength": 30.0, "intelligence": 30.0}

        physical = SkillDefinition(id="a", name="A", skill_type=SkillType.PHYSICAL,
                                    base_power=20.0, primary_attribute="strength")
        magical = SkillDefinition(id="b", name="B", skill_type=SkillType.MAGICAL,
                                   base_power=20.0, primary_attribute="intelligence")

        p_phys = SkillScalingSystem.compute_skill_power(physical, stats)
        p_mag = SkillScalingSystem.compute_skill_power(magical, stats)
        # They should differ because formulas are different
        assert p_phys != p_mag

    def test_genetics_affects_skill_power(self):
        """End-to-end: genetics modify base stats, which affect skill scaling."""
        base = {"strength": 20, "intelligence": 20}
        profile = GeneticProfile(strength_mult=1.2, intelligence_mult=0.9)
        effective = GeneticsSystem.apply_genetic_profile(base, profile)

        skill = SkillDefinition(id="s", name="S", skill_type=SkillType.PHYSICAL,
                                 base_power=10.0, primary_attribute="strength")

        power_with_genetics = SkillScalingSystem.compute_skill_power(skill, effective)
        power_without = SkillScalingSystem.compute_skill_power(skill, {"strength": 20.0})

        assert power_with_genetics > power_without  # 1.2x strength


class TestCombineGeneticProfiles:
    """Inheritance combination: two parent GeneticProfiles + occupation-bias -> a child
    GeneticProfile, per TCK-20260902-REPRODUCTION-GENETICS-INHERITANCE."""

    def test_combine_genetic_profiles_stays_within_multiplier_range(self):
        floor = GeneticProfile(strength_mult=0.8, agility_mult=0.8, intelligence_mult=0.8,
                                wisdom_mult=0.8, constitution_mult=0.8, charisma_mult=0.8)
        ceiling = GeneticProfile(strength_mult=1.3, agility_mult=1.3, intelligence_mult=1.3,
                                  wisdom_mult=1.3, constitution_mult=1.3, charisma_mult=1.3)

        for combat_lean in (True, False):
            for seed in (0, 1, 42, 999999):
                combined = GeneticsSystem.combine_profiles(
                    floor, ceiling, combat_lean=combat_lean, seed=seed
                )
                for attr in ("strength_mult", "agility_mult", "intelligence_mult",
                             "wisdom_mult", "constitution_mult", "charisma_mult"):
                    mult = getattr(combined, attr)
                    assert 0.8 <= mult <= 1.3

    def test_combine_genetic_profiles_is_deterministic(self):
        parent_a = GeneticsSystem.generate_profile_from_seed(11)
        parent_b = GeneticsSystem.generate_profile_from_seed(22)

        combined_1 = GeneticsSystem.combine_profiles(parent_a, parent_b, combat_lean=True, seed=100)
        combined_2 = GeneticsSystem.combine_profiles(parent_a, parent_b, combat_lean=True, seed=100)
        assert combined_1 == combined_2

        combined_different_seed = GeneticsSystem.combine_profiles(
            parent_a, parent_b, combat_lean=True, seed=200
        )
        assert combined_1 != combined_different_seed

    def test_adventurer_parents_bias_toward_combat_attributes(self):
        """Two-HERO-parent pairs pull combat-relevant attributes (strength/agility/
        constitution) measurably higher than the same parent pair without the bias."""
        parent_a = GeneticsSystem.generate_profile_from_seed(1)
        parent_b = GeneticsSystem.generate_profile_from_seed(2)
        combat_attrs = ("strength_mult", "agility_mult", "constitution_mult")

        combat_lean_means = []
        neutral_means = []
        for seed in range(30):
            combat_lean = GeneticsSystem.combine_profiles(
                parent_a, parent_b, combat_lean=True, seed=seed
            )
            neutral = GeneticsSystem.combine_profiles(
                parent_a, parent_b, combat_lean=False, seed=seed
            )
            combat_lean_means.append(sum(getattr(combat_lean, a) for a in combat_attrs) / 3)
            neutral_means.append(sum(getattr(neutral, a) for a in combat_attrs) / 3)

        avg_combat_lean = sum(combat_lean_means) / len(combat_lean_means)
        avg_neutral = sum(neutral_means) / len(neutral_means)
        assert avg_combat_lean > avg_neutral

    def test_civilian_parents_produce_flatter_neutral_spread(self):
        """Any non-double-HERO pairing (civilian, worker/guard, or a mismatch) falls
        through to the same neutral spread -- non-combat attributes are unaffected by
        combat_lean either way."""
        parent_a = GeneticsSystem.generate_profile_from_seed(3)
        parent_b = GeneticsSystem.generate_profile_from_seed(4)
        non_combat_attrs = ("intelligence_mult", "wisdom_mult", "charisma_mult")

        for seed in range(10):
            combat_lean = GeneticsSystem.combine_profiles(
                parent_a, parent_b, combat_lean=True, seed=seed
            )
            neutral = GeneticsSystem.combine_profiles(
                parent_a, parent_b, combat_lean=False, seed=seed
            )
            for attr in non_combat_attrs:
                assert getattr(combat_lean, attr) == getattr(neutral, attr)


def test_genetics_system_has_real_non_test_non_shim_caller():
    """AC1 regression guard: GeneticsSystem/GeneticProfile must have at least one real,
    live, non-test, non-shim call site in src/ -- so a future refactor cannot silently
    remove the only caller and revert to the pre-TCK-20260902-REPRODUCTION-GENETICS-INHERITANCE
    orphaned-system state."""
    src_root = Path(__file__).resolve().parents[3] / "src"
    excluded = {
        src_root / "systems" / "lifecycle_systems" / "genetics.py",
        src_root / "systems" / "genetics.py",
    }

    real_callers = []
    for path in src_root.rglob("*.py"):
        if path in excluded:
            continue
        text = path.read_text()
        if "GeneticsSystem" in text or "GeneticProfile" in text:
            real_callers.append(path)

    assert real_callers, "expected at least one real, non-shim caller of GeneticsSystem/GeneticProfile in src/"

    import src.core.builder as builder_module
    birth_record_source = inspect.getsource(builder_module.V2EntityBuilder.birth_record)
    assert "GeneticsSystem.combine_profiles" in birth_record_source
