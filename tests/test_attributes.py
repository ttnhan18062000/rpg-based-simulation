"""Tests for the RPG attribute system."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.core.attributes import (
    Attributes, AttributeCaps,
    derive_max_hp, derive_atk, derive_def, derive_spd,
    derive_crit_rate, derive_evasion, derive_luck, derive_stamina,
    derive_xp_multiplier, train_attributes, level_up_attributes,
)


class TestAttributeDerivation:
    """Test that derived stats are calculated correctly from attributes."""

    def test_derive_max_hp(self):
        # base 20, VIT=10, END=6 → 20 + 10*2 + 6*0.5 = 43
        assert derive_max_hp(20, 10, 6) == 43

    def test_derive_atk(self):
        # base 5, STR=10 → 5 + 10*0.5 = 10
        assert derive_atk(5, 10) == 10

    def test_derive_def(self):
        # base 2, VIT=10 → 2 + 10*0.3 = 5
        assert derive_def(2, 10) == 5

    def test_derive_spd(self):
        # base 8, AGI=10 → 8 + 10*0.4 = 12
        assert derive_spd(8, 10) == 12

    def test_derive_crit_rate(self):
        # base 0.05, AGI=10 → 0.05 + 10*0.004 = 0.09
        result = derive_crit_rate(0.05, 10)
        assert abs(result - 0.09) < 0.001

    def test_derive_evasion(self):
        # base 0.0, AGI=10 → 0.0 + 10*0.003 = 0.03
        result = derive_evasion(0.0, 10)
        assert abs(result - 0.03) < 0.001

    def test_derive_luck(self):
        # base 0, WIS=10 → 0 + 10*0.3 = 3
        assert derive_luck(0, 10) == 3

    def test_derive_stamina(self):
        # base 50, END=10 → 50 + 10*2 = 70
        assert derive_stamina(50, 10) == 70

    def test_derive_xp_multiplier(self):
        # INT=5, WIS=5 → 1.0 + 5*0.01 + 5*0.005 = 1.075
        result = derive_xp_multiplier(5, 5)
        assert abs(result - 1.075) < 0.001

    def test_derive_xp_multiplier_zero_attrs(self):
        result = derive_xp_multiplier(0, 0)
        assert result == 1.0


class TestAttributeCaps:
    """Test attribute cap management."""

    def test_default_caps(self):
        caps = AttributeCaps()
        assert caps.str_cap == 15
        assert caps.agi_cap == 15

    def test_increase_all(self):
        caps = AttributeCaps()
        caps.increase_all(5)
        assert caps.str_cap == 20
        assert caps.agi_cap == 20
        assert caps.vit_cap == 20
        assert caps.int_cap == 20
        assert caps.wis_cap == 20
        assert caps.end_cap == 20

    def test_copy(self):
        caps = AttributeCaps(str_cap=20, agi_cap=25)
        copy = caps.copy()
        assert copy.str_cap == 20
        assert copy.agi_cap == 25
        copy.str_cap = 99
        assert caps.str_cap == 20  # original unchanged


class TestAttributeTraining:
    """Test slow attribute training through actions."""

    def test_training_does_not_exceed_cap(self):
        attrs = Attributes(str_=15, agi=5, vit=5, int_=5, wis=5, end=5)
        caps = AttributeCaps(str_cap=15)  # STR already at cap
        # Lots of attack training should not push STR beyond cap
        for _ in range(200):
            train_attributes(attrs, caps, "attack")
        assert attrs.str_ <= caps.str_cap

    def test_training_accumulates_fractionally(self):
        attrs = Attributes(str_=5, agi=5, vit=5, int_=5, wis=5, end=5)
        caps = AttributeCaps(str_cap=50)
        # Attack trains STR at 0.015/action → need ~67 attacks to gain +1 STR
        for _ in range(70):
            train_attributes(attrs, caps, "attack")
        assert attrs.str_ >= 6  # Should have gained at least +1

    def test_move_trains_agi_and_end(self):
        attrs = Attributes(str_=5, agi=5, vit=5, int_=5, wis=5, end=5)
        caps = AttributeCaps(agi_cap=50, end_cap=50)
        for _ in range(200):
            train_attributes(attrs, caps, "move")
        assert attrs.agi >= 6  # AGI trains at 0.008/move
        assert attrs.end >= 6  # END trains at 0.005/move

    def test_unknown_action_does_nothing(self):
        attrs = Attributes(str_=5, agi=5, vit=5, int_=5, wis=5, end=5)
        caps = AttributeCaps()
        total_before = attrs.total()
        train_attributes(attrs, caps, "nonexistent")
        assert attrs.total() == total_before


class TestLevelUpAttributes:
    """Test attribute gains on level up."""

    def test_level_up_increases_base_and_caps(self):
        attrs = Attributes(str_=5, agi=5, vit=5, int_=5, wis=5, end=5)
        caps = AttributeCaps()
        level_up_attributes(attrs, caps)
        # Base: +2 each
        assert attrs.str_ == 7
        assert attrs.agi == 7
        assert attrs.vit == 7
        # Caps: +5 each
        assert caps.str_cap == 20
        assert caps.agi_cap == 20

    def test_level_up_respects_cap(self):
        attrs = Attributes(str_=14, agi=5, vit=5, int_=5, wis=5, end=5)
        caps = AttributeCaps(str_cap=15)
        level_up_attributes(attrs, caps)
        # Cap increases to 20, then STR goes from 14 → min(16, 20) = 16
        assert attrs.str_ == 16
        assert caps.str_cap == 20

    def test_attributes_copy(self):
        attrs = Attributes(str_=10, agi=8, _str_frac=0.5)
        copy = attrs.copy()
        assert copy.str_ == 10
        assert copy._str_frac == 0.5
        copy.str_ = 20
        assert attrs.str_ == 10  # original unchanged
