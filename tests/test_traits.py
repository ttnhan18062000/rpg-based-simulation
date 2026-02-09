"""Tests for the trait system — typed aggregation, assignment, and compatibility."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.core.enums import TraitType
from src.core.traits import (
    TraitDef, UtilityBonus, TraitStatModifiers,
    TRAIT_DEFS, INCOMPATIBLE_PAIRS,
    aggregate_trait_utility, aggregate_trait_stats,
    are_compatible, assign_traits,
)


# ---------------------------------------------------------------------------
# UtilityBonus dataclass tests
# ---------------------------------------------------------------------------

class TestUtilityBonus:
    """Test the typed UtilityBonus dataclass."""

    def test_default_values_all_zero(self):
        bonus = UtilityBonus()
        assert bonus.combat == 0.0
        assert bonus.flee == 0.0
        assert bonus.explore == 0.0
        assert bonus.loot == 0.0
        assert bonus.trade == 0.0
        assert bonus.rest == 0.0
        assert bonus.craft == 0.0
        assert bonus.social == 0.0

    def test_fields_are_settable(self):
        bonus = UtilityBonus(combat=0.3, flee=-0.1, explore=0.2)
        assert bonus.combat == 0.3
        assert bonus.flee == -0.1
        assert bonus.explore == 0.2

    def test_attribute_access_not_dict(self):
        """UtilityBonus uses attribute access, not dict .get()."""
        bonus = UtilityBonus(combat=0.5)
        assert hasattr(bonus, "combat")
        assert not hasattr(bonus, "get")  # not a dict


# ---------------------------------------------------------------------------
# TraitStatModifiers dataclass tests
# ---------------------------------------------------------------------------

class TestTraitStatModifiers:
    """Test the typed TraitStatModifiers dataclass."""

    def test_default_multiplicative_values_are_1(self):
        mods = TraitStatModifiers()
        assert mods.atk_mult == 1.0
        assert mods.def_mult == 1.0
        assert mods.matk_mult == 1.0
        assert mods.mdef_mult == 1.0
        assert mods.hp_regen_mult == 1.0
        assert mods.interaction_speed_mult == 1.0

    def test_default_additive_values_are_0(self):
        mods = TraitStatModifiers()
        assert mods.crit_bonus == 0.0
        assert mods.evasion_bonus == 0.0
        assert mods.vision_bonus == 0
        assert mods.flee_threshold_mod == 0.0

    def test_fields_are_settable(self):
        mods = TraitStatModifiers(atk_mult=1.2, crit_bonus=0.05, vision_bonus=2)
        assert mods.atk_mult == 1.2
        assert mods.crit_bonus == 0.05
        assert mods.vision_bonus == 2


# ---------------------------------------------------------------------------
# aggregate_trait_utility() tests
# ---------------------------------------------------------------------------

class TestAggregateTraitUtility:
    """Test trait utility aggregation returns typed UtilityBonus."""

    def test_empty_traits_returns_zero_bonus(self):
        bonus = aggregate_trait_utility([])
        assert isinstance(bonus, UtilityBonus)
        assert bonus.combat == 0.0
        assert bonus.flee == 0.0

    def test_single_known_trait(self):
        # AGGRESSIVE should boost combat utility
        bonus = aggregate_trait_utility([TraitType.AGGRESSIVE])
        assert isinstance(bonus, UtilityBonus)
        tdef = TRAIT_DEFS[TraitType.AGGRESSIVE]
        assert bonus.combat == tdef.combat_utility
        assert bonus.flee == tdef.flee_utility

    def test_multiple_traits_sum(self):
        traits = [TraitType.AGGRESSIVE, TraitType.BRAVE]
        bonus = aggregate_trait_utility(traits)
        expected_combat = (
            TRAIT_DEFS[TraitType.AGGRESSIVE].combat_utility
            + TRAIT_DEFS[TraitType.BRAVE].combat_utility
        )
        assert abs(bonus.combat - expected_combat) < 0.001

    def test_unknown_trait_id_ignored(self):
        bonus = aggregate_trait_utility([9999])
        assert bonus.combat == 0.0
        assert bonus.flee == 0.0


# ---------------------------------------------------------------------------
# aggregate_trait_stats() tests
# ---------------------------------------------------------------------------

class TestAggregateTraitStats:
    """Test trait stat aggregation returns typed TraitStatModifiers."""

    def test_empty_traits_returns_defaults(self):
        mods = aggregate_trait_stats([])
        assert isinstance(mods, TraitStatModifiers)
        assert mods.atk_mult == 1.0
        assert mods.def_mult == 1.0

    def test_single_trait_applies_multipliers(self):
        mods = aggregate_trait_stats([TraitType.AGGRESSIVE])
        tdef = TRAIT_DEFS[TraitType.AGGRESSIVE]
        assert abs(mods.atk_mult - tdef.atk_mult) < 0.001
        assert abs(mods.crit_bonus - tdef.crit_bonus) < 0.001

    def test_multiplicative_stacking(self):
        """Multiple traits with atk_mult should multiply, not add."""
        # Get two traits that both modify atk_mult
        traits_with_atk = [
            tid for tid, tdef in TRAIT_DEFS.items()
            if tdef.atk_mult != 1.0
        ]
        if len(traits_with_atk) >= 2:
            t1, t2 = traits_with_atk[0], traits_with_atk[1]
            mods = aggregate_trait_stats([t1, t2])
            expected = TRAIT_DEFS[t1].atk_mult * TRAIT_DEFS[t2].atk_mult
            assert abs(mods.atk_mult - expected) < 0.001

    def test_additive_stacking(self):
        """Additive fields (crit_bonus, evasion_bonus) should sum."""
        traits_with_crit = [
            tid for tid, tdef in TRAIT_DEFS.items()
            if tdef.crit_bonus != 0.0
        ]
        if len(traits_with_crit) >= 2:
            t1, t2 = traits_with_crit[0], traits_with_crit[1]
            mods = aggregate_trait_stats([t1, t2])
            expected = TRAIT_DEFS[t1].crit_bonus + TRAIT_DEFS[t2].crit_bonus
            assert abs(mods.crit_bonus - expected) < 0.001

    def test_unknown_trait_id_ignored(self):
        mods = aggregate_trait_stats([9999])
        assert mods.atk_mult == 1.0


# ---------------------------------------------------------------------------
# Compatibility tests
# ---------------------------------------------------------------------------

class TestTraitCompatibility:
    """Test incompatible trait pair enforcement."""

    def test_same_trait_compatible(self):
        assert are_compatible(TraitType.AGGRESSIVE, TraitType.AGGRESSIVE) is True

    def test_incompatible_pair(self):
        # AGGRESSIVE and CAUTIOUS should be incompatible
        assert are_compatible(TraitType.AGGRESSIVE, TraitType.CAUTIOUS) is False
        assert are_compatible(TraitType.CAUTIOUS, TraitType.AGGRESSIVE) is False

    def test_compatible_pair(self):
        # AGGRESSIVE and CURIOUS should be compatible
        assert are_compatible(TraitType.AGGRESSIVE, TraitType.CURIOUS) is True

    def test_incompatible_pairs_are_symmetric(self):
        for a, b in INCOMPATIBLE_PAIRS:
            assert are_compatible(a, b) is False
            assert are_compatible(b, a) is False


# ---------------------------------------------------------------------------
# Trait assignment tests
# ---------------------------------------------------------------------------

class _FakeRNG:
    """Minimal fake RNG for trait assignment testing."""
    def __init__(self):
        self._counter = 0

    def next_int(self, domain, eid, tick, lo, hi):
        self._counter += 1
        # Return values cycling through [lo, hi]
        return lo + (self._counter % (hi - lo + 1)) if hi > lo else lo

    def next_float(self, domain, eid, tick):
        self._counter += 1
        return (self._counter % 100) / 100.0

    def next_bool(self, domain, eid, tick, probability):
        self._counter += 1
        return (self._counter % 100) / 100.0 < probability


class TestTraitAssignment:
    """Test trait assignment logic."""

    def test_assigns_between_2_and_4_traits(self):
        rng = _FakeRNG()
        from src.core.enums import Domain
        traits = assign_traits(rng, Domain.SPAWN, 1, 0)
        assert 2 <= len(traits) <= 4

    def test_no_incompatible_pairs_in_result(self):
        rng = _FakeRNG()
        from src.core.enums import Domain
        for eid in range(20):  # test multiple spawns
            traits = assign_traits(rng, Domain.SPAWN, eid, 0)
            for i, a in enumerate(traits):
                for b in traits[i + 1:]:
                    assert are_compatible(a, b), (
                        f"Incompatible pair found: {a}, {b} in traits {traits}"
                    )

    def test_all_assigned_traits_are_valid(self):
        rng = _FakeRNG()
        from src.core.enums import Domain
        traits = assign_traits(rng, Domain.SPAWN, 1, 0)
        for t in traits:
            assert t in TRAIT_DEFS, f"Unknown trait {t} assigned"

    def test_race_prefix_accepted(self):
        rng = _FakeRNG()
        from src.core.enums import Domain
        hero_traits = assign_traits(rng, Domain.SPAWN, 1, 0, race_prefix="hero")
        assert 2 <= len(hero_traits) <= 4
        goblin_traits = assign_traits(rng, Domain.SPAWN, 2, 0, race_prefix="goblin")
        assert 2 <= len(goblin_traits) <= 4


# ---------------------------------------------------------------------------
# TraitDef registry tests
# ---------------------------------------------------------------------------

class TestTraitDefRegistry:
    """Test trait definition registry."""

    def test_registry_not_empty(self):
        assert len(TRAIT_DEFS) > 0

    def test_all_trait_types_have_definitions(self):
        # Every TraitType enum value that's in TRAIT_DEFS should be valid
        for trait_id, tdef in TRAIT_DEFS.items():
            assert isinstance(tdef, TraitDef)
            assert tdef.name != ""

    def test_trait_defs_have_all_utility_fields(self):
        for trait_id, tdef in TRAIT_DEFS.items():
            assert hasattr(tdef, "combat_utility")
            assert hasattr(tdef, "flee_utility")
            assert hasattr(tdef, "explore_utility")
            assert hasattr(tdef, "loot_utility")
            assert hasattr(tdef, "trade_utility")
            assert hasattr(tdef, "rest_utility")
            assert hasattr(tdef, "craft_utility")
            assert hasattr(tdef, "social_utility")

    def test_trait_defs_have_all_stat_fields(self):
        for trait_id, tdef in TRAIT_DEFS.items():
            assert hasattr(tdef, "atk_mult")
            assert hasattr(tdef, "def_mult")
            assert hasattr(tdef, "matk_mult")
            assert hasattr(tdef, "mdef_mult")
            assert hasattr(tdef, "crit_bonus")
            assert hasattr(tdef, "evasion_bonus")
            assert hasattr(tdef, "vision_bonus")
            assert hasattr(tdef, "hp_regen_mult")
            assert hasattr(tdef, "flee_threshold_mod")
