"""RPG Attribute system — primary attributes that derive combat stats.

Primary Attributes:
  STR (Strength)  — Increases ATK, carry weight
  AGI (Agility)   — Increases SPD, evasion, crit rate
  VIT (Vitality)  — Increases HP, DEF
  INT (Intelligence) — Increases skill power, XP gain bonus
  WIS (Wisdom)    — Increases LUCK, mana/skill cooldown reduction
  END (Endurance) — Increases stamina, HP regen

Each attribute has a base value (current) and a cap (max trainable).
Level ups increase both base (+2) and cap (+5).
Attributes can be slowly trained through actions.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class Attributes:
    """Primary RPG attributes for an entity."""

    str_: int = 5      # Strength
    agi: int = 5        # Agility
    vit: int = 5        # Vitality
    int_: int = 5       # Intelligence
    wis: int = 5        # Wisdom
    end: int = 5        # Endurance

    # Fractional training accumulator (not exposed to API, internal only)
    _str_frac: float = 0.0
    _agi_frac: float = 0.0
    _vit_frac: float = 0.0
    _int_frac: float = 0.0
    _wis_frac: float = 0.0
    _end_frac: float = 0.0

    def copy(self) -> Attributes:
        return Attributes(
            str_=self.str_, agi=self.agi, vit=self.vit,
            int_=self.int_, wis=self.wis, end=self.end,
            _str_frac=self._str_frac, _agi_frac=self._agi_frac,
            _vit_frac=self._vit_frac, _int_frac=self._int_frac,
            _wis_frac=self._wis_frac, _end_frac=self._end_frac,
        )

    def total(self) -> int:
        """Sum of all primary attributes."""
        return self.str_ + self.agi + self.vit + self.int_ + self.wis + self.end


@dataclass(slots=True)
class AttributeCaps:
    """Maximum trainable values for each attribute.
    Caps increase on level up and can be boosted by class bonuses.
    """

    str_cap: int = 15
    agi_cap: int = 15
    vit_cap: int = 15
    int_cap: int = 15
    wis_cap: int = 15
    end_cap: int = 15

    def copy(self) -> AttributeCaps:
        return AttributeCaps(
            str_cap=self.str_cap, agi_cap=self.agi_cap, vit_cap=self.vit_cap,
            int_cap=self.int_cap, wis_cap=self.wis_cap, end_cap=self.end_cap,
        )

    def increase_all(self, amount: int) -> None:
        """Increase all caps by a flat amount (called on level up)."""
        self.str_cap += amount
        self.agi_cap += amount
        self.vit_cap += amount
        self.int_cap += amount
        self.wis_cap += amount
        self.end_cap += amount


# ---------------------------------------------------------------------------
# Attribute → derived stat formulas
# ---------------------------------------------------------------------------

def derive_max_hp(base_max_hp: int, vit: int, end: int) -> int:
    """Max HP = base + VIT*2 + END*0.5"""
    return base_max_hp + vit * 2 + int(end * 0.5)


def derive_atk(base_atk: int, str_: int) -> int:
    """ATK = base + STR*0.5"""
    return base_atk + int(str_ * 0.5)


def derive_def(base_def: int, vit: int) -> int:
    """DEF = base + VIT*0.3"""
    return base_def + int(vit * 0.3)


def derive_spd(base_spd: int, agi: int) -> int:
    """SPD = base + AGI*0.4"""
    return base_spd + int(agi * 0.4)


def derive_crit_rate(base_crit: float, agi: int) -> float:
    """Crit rate = base + AGI*0.004"""
    return base_crit + agi * 0.004


def derive_evasion(base_evasion: float, agi: int) -> float:
    """Evasion = base + AGI*0.003"""
    return base_evasion + agi * 0.003


def derive_luck(base_luck: int, wis: int) -> int:
    """Luck = base + WIS*0.3"""
    return base_luck + int(wis * 0.3)


def derive_stamina(base_stamina: int, end: int) -> int:
    """Max stamina = base + END*2"""
    return base_stamina + end * 2


def derive_xp_multiplier(int_: int, wis: int) -> float:
    """XP gain multiplier from INT and WIS. Base 1.0."""
    return 1.0 + int_ * 0.01 + wis * 0.005


# ---------------------------------------------------------------------------
# Training: attribute gain from actions
# ---------------------------------------------------------------------------

# Training rates per action type (very slow)
TRAIN_RATES: dict[str, dict[str, float]] = {
    "move":     {"agi": 0.008, "end": 0.005},
    "attack":   {"str": 0.015, "agi": 0.008},
    "defend":   {"vit": 0.010, "end": 0.008},
    "rest":     {"wis": 0.006, "end": 0.003},
    "harvest":  {"end": 0.010, "wis": 0.005},
    "loot":     {"wis": 0.005},
    "skill":    {"int": 0.010, "wis": 0.005},
}


def train_attributes(
    attrs: Attributes,
    caps: AttributeCaps,
    action: str,
) -> None:
    """Apply fractional training gains from an action.

    When fractional accumulator reaches >= 1.0, the integer attribute
    increases by 1 (up to cap). This makes training very slow.
    """
    rates = TRAIN_RATES.get(action, {})
    for attr_key, rate in rates.items():
        _apply_train(attrs, caps, attr_key, rate)


def _apply_train(attrs: Attributes, caps: AttributeCaps, key: str, rate: float) -> None:
    """Add fractional training to one attribute."""
    frac_field = f"_{key}_frac"
    if key == "str":
        cap = caps.str_cap
        current = attrs.str_
        frac = attrs._str_frac + rate
        if frac >= 1.0 and current < cap:
            attrs.str_ = min(current + int(frac), cap)
            frac -= int(frac)
        attrs._str_frac = frac
    elif key == "agi":
        cap = caps.agi_cap
        current = attrs.agi
        frac = attrs._agi_frac + rate
        if frac >= 1.0 and current < cap:
            attrs.agi = min(current + int(frac), cap)
            frac -= int(frac)
        attrs._agi_frac = frac
    elif key == "vit":
        cap = caps.vit_cap
        current = attrs.vit
        frac = attrs._vit_frac + rate
        if frac >= 1.0 and current < cap:
            attrs.vit = min(current + int(frac), cap)
            frac -= int(frac)
        attrs._vit_frac = frac
    elif key == "int":
        cap = caps.int_cap
        current = attrs.int_
        frac = attrs._int_frac + rate
        if frac >= 1.0 and current < cap:
            attrs.int_ = min(current + int(frac), cap)
            frac -= int(frac)
        attrs._int_frac = frac
    elif key == "wis":
        cap = caps.wis_cap
        current = attrs.wis
        frac = attrs._wis_frac + rate
        if frac >= 1.0 and current < cap:
            attrs.wis = min(current + int(frac), cap)
            frac -= int(frac)
        attrs._wis_frac = frac
    elif key == "end":
        cap = caps.end_cap
        current = attrs.end
        frac = attrs._end_frac + rate
        if frac >= 1.0 and current < cap:
            attrs.end = min(current + int(frac), cap)
            frac -= int(frac)
        attrs._end_frac = frac


# ---------------------------------------------------------------------------
# Level-up attribute gains
# ---------------------------------------------------------------------------

def level_up_attributes(attrs: Attributes, caps: AttributeCaps) -> None:
    """Apply attribute gains on level up.

    - Base attributes: +2 to each (up to cap)
    - Caps: +5 to each
    """
    caps.increase_all(5)

    attrs.str_ = min(attrs.str_ + 2, caps.str_cap)
    attrs.agi = min(attrs.agi + 2, caps.agi_cap)
    attrs.vit = min(attrs.vit + 2, caps.vit_cap)
    attrs.int_ = min(attrs.int_ + 2, caps.int_cap)
    attrs.wis = min(attrs.wis + 2, caps.wis_cap)
    attrs.end = min(attrs.end + 2, caps.end_cap)
