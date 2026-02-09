"""RPG Attribute system — 9 primary attributes that derive combat & non-combat stats.

Primary Attributes:
  STR (Strength)     — ATK, carry weight
  AGI (Agility)      — SPD, evasion, crit rate
  VIT (Vitality)     — HP, physical DEF
  INT (Intelligence) — Skill power, XP gain, cooldown reduction
  SPI (Spirit)       — MATK (magic attack), mana-like resource scaling
  WIS (Wisdom)       — MDEF (magic defense), LUCK, cooldown reduction
  END (Endurance)    — Stamina, HP regen
  PER (Perception)   — Vision range, detection, loot quality, trap awareness
  CHA (Charisma)     — Trade prices, morale, social influence, recruitment

Each attribute has a base value (current) and a cap (max trainable).
Level ups increase both base (+2) and cap (+5).
Attributes can be slowly trained through actions.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class Attributes:
    """Primary RPG attributes for an entity (9 attributes)."""

    str_: int = 5      # Strength
    agi: int = 5        # Agility
    vit: int = 5        # Vitality
    int_: int = 5       # Intelligence
    spi: int = 5        # Spirit
    wis: int = 5        # Wisdom
    end: int = 5        # Endurance
    per: int = 5        # Perception
    cha: int = 5        # Charisma

    # Fractional training accumulator (not exposed to API, internal only)
    _str_frac: float = 0.0
    _agi_frac: float = 0.0
    _vit_frac: float = 0.0
    _int_frac: float = 0.0
    _spi_frac: float = 0.0
    _wis_frac: float = 0.0
    _end_frac: float = 0.0
    _per_frac: float = 0.0
    _cha_frac: float = 0.0

    def copy(self) -> Attributes:
        return Attributes(
            str_=self.str_, agi=self.agi, vit=self.vit,
            int_=self.int_, spi=self.spi, wis=self.wis,
            end=self.end, per=self.per, cha=self.cha,
            _str_frac=self._str_frac, _agi_frac=self._agi_frac,
            _vit_frac=self._vit_frac, _int_frac=self._int_frac,
            _spi_frac=self._spi_frac, _wis_frac=self._wis_frac,
            _end_frac=self._end_frac, _per_frac=self._per_frac,
            _cha_frac=self._cha_frac,
        )

    def total(self) -> int:
        """Sum of all primary attributes."""
        return (self.str_ + self.agi + self.vit + self.int_ + self.spi
                + self.wis + self.end + self.per + self.cha)


@dataclass(slots=True)
class AttributeCaps:
    """Maximum trainable values for each attribute.
    Caps increase on level up and can be boosted by class bonuses.
    """

    str_cap: int = 15
    agi_cap: int = 15
    vit_cap: int = 15
    int_cap: int = 15
    spi_cap: int = 15
    wis_cap: int = 15
    end_cap: int = 15
    per_cap: int = 15
    cha_cap: int = 15

    def copy(self) -> AttributeCaps:
        return AttributeCaps(
            str_cap=self.str_cap, agi_cap=self.agi_cap, vit_cap=self.vit_cap,
            int_cap=self.int_cap, spi_cap=self.spi_cap, wis_cap=self.wis_cap,
            end_cap=self.end_cap, per_cap=self.per_cap, cha_cap=self.cha_cap,
        )

    def increase_all(self, amount: int) -> None:
        """Increase all caps by a flat amount (called on level up)."""
        self.str_cap += amount
        self.agi_cap += amount
        self.vit_cap += amount
        self.int_cap += amount
        self.spi_cap += amount
        self.wis_cap += amount
        self.end_cap += amount
        self.per_cap += amount
        self.cha_cap += amount


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
# New derived stats for expanded attribute system
# ---------------------------------------------------------------------------

def derive_matk(base_matk: int, spi: int, int_: int) -> int:
    """Magic ATK = base + SPI*0.6 + INT*0.2"""
    return base_matk + int(spi * 0.6) + int(int_ * 0.2)


def derive_mdef(base_mdef: int, wis: int, spi: int) -> int:
    """Magic DEF = base + WIS*0.4 + SPI*0.15"""
    return base_mdef + int(wis * 0.4) + int(spi * 0.15)


def derive_vision(base_vision: int, per: int) -> int:
    """Vision range = base + PER*0.3  (integer tiles)"""
    return base_vision + int(per * 0.3)


def derive_loot_bonus(per: int, wis: int) -> float:
    """Loot quality / drop chance multiplier. Base 1.0."""
    return 1.0 + per * 0.008 + wis * 0.003


def derive_trade_bonus(cha: int) -> float:
    """Trade price modifier (buy discount / sell bonus). Base 1.0."""
    return 1.0 + cha * 0.01


def derive_interaction_speed(cha: int, int_: int) -> float:
    """Interaction speed multiplier (harvest, craft, etc.). Base 1.0."""
    return 1.0 + cha * 0.005 + int_ * 0.005


def derive_rest_efficiency(end: int, wis: int) -> float:
    """Rest / regen efficiency multiplier. Base 1.0."""
    return 1.0 + end * 0.008 + wis * 0.004


def derive_hp_regen(end: int, vit: int) -> float:
    """HP regen per rest tick. Base 1.0."""
    return 1.0 + end * 0.15 + vit * 0.05


def derive_cooldown_reduction(int_: int, wis: int) -> float:
    """Cooldown reduction multiplier for skills. Base 1.0 (lower=faster)."""
    return max(0.5, 1.0 - int_ * 0.005 - wis * 0.003)


# ---------------------------------------------------------------------------
# Recalculate all derived stats from attributes
# ---------------------------------------------------------------------------

def recalc_derived_stats(
    stats: 'Stats',
    new_attrs: 'Attributes',
    old_attrs: 'Attributes | None' = None,
) -> None:
    """Recompute all attribute-derived fields on a Stats object.

    Two modes:
    - **Creation mode** (old_attrs=None): stats contain raw base values,
      attribute bonuses are added on top.
    - **Delta mode** (old_attrs provided): strips old attribute contributions
      then re-applies with new_attrs. Use after level-up or training.
    """
    if old_attrs is not None:
        # Strip old attribute contributions from combat stats
        stats.max_hp -= derive_max_hp(0, old_attrs.vit, old_attrs.end)
        stats.atk -= derive_atk(0, old_attrs.str_)
        stats.def_ -= derive_def(0, old_attrs.vit)
        stats.spd -= derive_spd(0, old_attrs.agi)
        stats.crit_rate -= derive_crit_rate(0.0, old_attrs.agi)
        stats.evasion -= derive_evasion(0.0, old_attrs.agi)
        stats.luck -= derive_luck(0, old_attrs.wis)
        stats.max_stamina -= derive_stamina(0, old_attrs.end)
        stats.matk -= derive_matk(0, old_attrs.spi, old_attrs.int_)
        stats.mdef -= derive_mdef(0, old_attrs.wis, old_attrs.spi)

    # Add new attribute contributions to combat stats
    stats.max_hp = derive_max_hp(stats.max_hp, new_attrs.vit, new_attrs.end)
    stats.atk = derive_atk(stats.atk, new_attrs.str_)
    stats.def_ = derive_def(stats.def_, new_attrs.vit)
    stats.spd = derive_spd(stats.spd, new_attrs.agi)
    stats.crit_rate = derive_crit_rate(stats.crit_rate, new_attrs.agi)
    stats.evasion = derive_evasion(stats.evasion, new_attrs.agi)
    stats.luck = derive_luck(stats.luck, new_attrs.wis)
    stats.max_stamina = derive_stamina(stats.max_stamina, new_attrs.end)
    stats.matk = derive_matk(stats.matk, new_attrs.spi, new_attrs.int_)
    stats.mdef = derive_mdef(stats.mdef, new_attrs.wis, new_attrs.spi)

    # Non-combat stats — always derived purely from attributes (fixed base)
    stats.vision_range = derive_vision(6, new_attrs.per)
    stats.hp_regen = derive_hp_regen(new_attrs.end, new_attrs.vit)
    stats.cooldown_reduction = derive_cooldown_reduction(new_attrs.int_, new_attrs.wis)
    stats.loot_bonus = derive_loot_bonus(new_attrs.per, new_attrs.wis)
    stats.trade_bonus = derive_trade_bonus(new_attrs.cha)
    stats.interaction_speed = derive_interaction_speed(new_attrs.cha, new_attrs.int_)
    stats.rest_efficiency = derive_rest_efficiency(new_attrs.end, new_attrs.wis)

    # Ensure HP/stamina don't exceed new max
    if stats.hp > stats.max_hp:
        stats.hp = stats.max_hp
    if stats.stamina > stats.max_stamina:
        stats.stamina = stats.max_stamina


# ---------------------------------------------------------------------------
# Training: attribute gain from actions
# ---------------------------------------------------------------------------

# Training rates per action type (very slow)
TRAIN_RATES: dict[str, dict[str, float]] = {
    "move":     {"agi": 0.008, "end": 0.005, "per": 0.003},
    "attack":   {"str": 0.015, "agi": 0.008},
    "defend":   {"vit": 0.010, "end": 0.008},
    "rest":     {"wis": 0.006, "end": 0.003},
    "harvest":  {"end": 0.010, "wis": 0.005, "per": 0.004},
    "loot":     {"wis": 0.005, "per": 0.006},
    "skill":    {"int": 0.010, "wis": 0.005, "spi": 0.008},
    "magic_attack": {"spi": 0.015, "int": 0.008},
    "trade":    {"cha": 0.012, "wis": 0.003},
    "explore":  {"per": 0.010, "agi": 0.005},
    "interact": {"cha": 0.008, "int": 0.004},
}


def train_attributes(
    attrs: Attributes,
    caps: AttributeCaps,
    action: str,
    stats: 'Stats | None' = None,
) -> None:
    """Apply fractional training gains from an action.

    When fractional accumulator reaches >= 1.0, the integer attribute
    increases by 1 (up to cap). This makes training very slow.

    If *stats* is provided, derived stats are updated when any attribute
    actually increments (using the delta-mode of recalc_derived_stats).
    """
    rates = TRAIN_RATES.get(action, {})
    if not rates:
        return
    old_snapshot = attrs.copy() if stats is not None else None
    changed = False
    for attr_key, rate in rates.items():
        if _apply_train(attrs, caps, attr_key, rate):
            changed = True
    if changed and stats is not None and old_snapshot is not None:
        recalc_derived_stats(stats, attrs, old_attrs=old_snapshot)


# Map from train key → (attr_field, frac_field, cap_field)
_TRAIN_MAP: dict[str, tuple[str, str, str]] = {
    "str": ("str_",  "_str_frac", "str_cap"),
    "agi": ("agi",   "_agi_frac", "agi_cap"),
    "vit": ("vit",   "_vit_frac", "vit_cap"),
    "int": ("int_",  "_int_frac", "int_cap"),
    "spi": ("spi",   "_spi_frac", "spi_cap"),
    "wis": ("wis",   "_wis_frac", "wis_cap"),
    "end": ("end",   "_end_frac", "end_cap"),
    "per": ("per",   "_per_frac", "per_cap"),
    "cha": ("cha",   "_cha_frac", "cha_cap"),
}


def _apply_train(attrs: Attributes, caps: AttributeCaps, key: str, rate: float) -> bool:
    """Add fractional training to one attribute. Returns True if attribute incremented."""
    mapping = _TRAIN_MAP.get(key)
    if mapping is None:
        return False
    attr_field, frac_field, cap_field = mapping
    cap = getattr(caps, cap_field)
    current = getattr(attrs, attr_field)
    frac = getattr(attrs, frac_field) + rate
    incremented = False
    if frac >= 1.0 and current < cap:
        gain = int(frac)
        setattr(attrs, attr_field, min(current + gain, cap))
        frac -= gain
        incremented = True
    setattr(attrs, frac_field, frac)
    return incremented


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
    attrs.spi = min(attrs.spi + 2, caps.spi_cap)
    attrs.wis = min(attrs.wis + 2, caps.wis_cap)
    attrs.end = min(attrs.end + 2, caps.end_cap)
    attrs.per = min(attrs.per + 2, caps.per_cap)
    attrs.cha = min(attrs.cha + 2, caps.cha_cap)
