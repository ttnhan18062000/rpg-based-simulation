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

import math as _math
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


def derive_crit_rate(base_crit: float, agi: int, luck: int = 0) -> float:
    """Crit rate = base + AGI*0.004 + Luck*0.01"""
    return base_crit + agi * 0.004 + luck * 0.01


def derive_evasion(base_evasion: float, agi: int) -> float:
    """Evasion = base + AGI*0.003"""
    return base_evasion + agi * 0.003


def derive_luck(base_luck: int, wis: int) -> int:
    """Luck = base + WIS*0.3"""
    return base_luck + int(wis * 0.3)


def derive_stamina(base_stamina: int, end: int) -> int:
    """Max stamina = base + END*2"""
    return base_stamina + end * 2


def derive_xp_multiplier(wis: int, int_: int) -> float:
    """XP gain multiplier based on Wisdom and Intelligence. Base 1.0 at 0/0."""
    return 1.0 + wis * 0.01 + int_ * 0.005


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


def derive_loot_modifier(luck: int) -> float:
    """Extra loot rarity modifier from Luck. Base 1.0 + Luck/100."""
    return 1.0 + luck * 0.01


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


def check_breakthroughs(attrs: Attributes, traits: list[str]) -> None:
    """Add breakthrough traits if attributes hit milestones (25, 50, 100)."""
    # 25 Milestone
    if attrs.str_ >= 25 and "str_25" not in traits: traits.append("str_25")
    if attrs.vit >= 25 and "vit_25" not in traits: traits.append("vit_25")
    if attrs.agi >= 25 and "agi_25" not in traits: traits.append("agi_25")
    if attrs.int_ >= 25 and "int_25" not in traits: traits.append("int_25")
    if attrs.per >= 25 and "per_25" not in traits: traits.append("per_25")
    
    # 50 Milestone (Advanced)
    if attrs.str_ >= 50 and "str_50" not in traits: traits.append("str_50") # Might
    if attrs.vit >= 50 and "vit_50" not in traits: traits.append("vit_50") # Juggernaut
    if attrs.agi >= 50 and "agi_50" not in traits: traits.append("agi_50") # Wind-dancer
    if attrs.int_ >= 50 and "int_50" not in traits: traits.append("int_50") # Savant

    # 100 Milestone (Legendary - Pillar Traits)
    if attrs.str_ >= 100 and "str_100" not in traits: traits.append("str_100") # Colossus
    if attrs.int_ >= 100 and "int_100" not in traits: traits.append("int_100") # Archmage


# ---------------------------------------------------------------------------
# Recalculate all derived stats from attributes
# ---------------------------------------------------------------------------

def recalc_derived_stats(
    target: Any,
    new_attrs: "Attributes",
    old_attrs: "Attributes | None" = None,
) -> None:
    """Recompute all attribute-derived fields on a target (Entity, StatsProxy, or Aspect)."""
    combat = target.combat if hasattr(target, "combat") else target
    prog = target.progression if hasattr(target, "progression") else target
    has_combat = hasattr(combat, "hp")
    has_prog = hasattr(prog, "stamina")

    if old_attrs is not None:
        if has_combat:
            combat.max_hp -= derive_max_hp(0, old_attrs.vit, old_attrs.end)
            combat.atk -= derive_atk(0, old_attrs.str_)
            combat.def_ -= derive_def(0, old_attrs.vit)
            combat.spd -= derive_spd(0, old_attrs.agi)
            if hasattr(combat, "crit_rate"): combat.crit_rate -= derive_crit_rate(0.0, old_attrs.agi, old_attrs.wis)
            combat.evasion -= derive_evasion(0.0, old_attrs.agi)
            combat.luck -= derive_luck(0, old_attrs.wis)
            combat.matk -= derive_matk(0, old_attrs.spi, old_attrs.int_)
            combat.mdef -= derive_mdef(0, old_attrs.wis, old_attrs.spi)
        if has_prog:
            prog.max_stamina -= derive_stamina(0, old_attrs.end)

    if has_combat:
        combat.max_hp = derive_max_hp(combat.max_hp, new_attrs.vit, new_attrs.end)
        combat.atk = derive_atk(combat.atk, new_attrs.str_)
        combat.def_ = derive_def(combat.def_, new_attrs.vit)
        combat.spd = derive_spd(combat.spd, new_attrs.agi)
        if hasattr(combat, "crit_rate"): combat.crit_rate = derive_crit_rate(combat.crit_rate, new_attrs.agi, new_attrs.wis)
        combat.evasion = derive_evasion(combat.evasion, new_attrs.agi)
        combat.luck = derive_luck(combat.luck, new_attrs.wis)
        combat.matk = derive_matk(combat.matk, new_attrs.spi, new_attrs.int_)
        combat.mdef = derive_mdef(combat.mdef, new_attrs.wis, new_attrs.spi)
        combat.hp_regen = derive_hp_regen(new_attrs.end, new_attrs.vit)

    if has_prog:
        prog.max_stamina = derive_stamina(prog.max_stamina, new_attrs.end)

    if has_combat:
        if hasattr(combat, "vision_range"):
            combat.vision_range = derive_vision(6, new_attrs.per)
        if hasattr(combat, "cooldown_reduction"):
            combat.cooldown_reduction = derive_cooldown_reduction(new_attrs.int_, new_attrs.wis)
        if hasattr(combat, "loot_bonus"):
            combat.loot_bonus = derive_loot_bonus(new_attrs.per, new_attrs.wis)
        if hasattr(combat, "trade_bonus"):
            combat.trade_bonus = derive_trade_bonus(new_attrs.cha)
        if hasattr(combat, "interaction_speed"):
            combat.interaction_speed = derive_interaction_speed(new_attrs.cha, new_attrs.int_)
        if hasattr(combat, "rest_efficiency"):
            combat.rest_efficiency = derive_rest_efficiency(new_attrs.end, new_attrs.wis)

    # 3. Apply Breakthrough Passives
    traits = []
    id_source = None
    if hasattr(target, "identity") and target.identity:
        id_source = target.identity
    else:
        # Check for attached aspect parent
        _parent = getattr(target, "_entity", None)
        if _parent and hasattr(_parent, "identity"):
            id_source = _parent.identity
            
    if id_source and has_combat:
        traits = id_source.traits
        if "str_25" in traits: combat.atk = int(combat.atk * 1.1)
        if "vit_25" in traits: combat.max_hp = int(combat.max_hp * 1.1)
        if "agi_25" in traits: combat.spd = int(combat.spd * 1.1)
        if "str_50" in traits: combat.atk = int(combat.atk * 1.25)
        if "vit_50" in traits: combat.max_hp = int(combat.max_hp * 1.25)
        if "agi_50" in traits: combat.evasion += 0.05
        if "int_50" in traits: combat.matk = int(combat.matk * 1.3)
        if "str_100" in traits: combat.atk = int(combat.atk * 1.5)
        if "int_100" in traits: combat.matk = int(combat.matk * 1.5)


    if has_combat and hasattr(combat, "hp"):
        combat.hp = min(combat.hp, combat.max_hp)
    if has_prog and hasattr(prog, "stamina"):
        prog.stamina = min(prog.stamina, prog.max_stamina)
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
    race: str = "hero",
    talents: list[str] | None = None,
    weakness: str = "",
    aptitudes: dict[str, float] | None = None,
) -> None:
    """Apply fractional training gains from an action."""
    rates = TRAIN_RATES.get(action, {})
    if not rates:
        return
        
    from src.core.models.enums import RACE_PROFILES
    profile = RACE_PROFILES.get(race)
    if not profile:
        base_race = race.split('_')[0]
        profile = RACE_PROFILES.get(base_race)
        
    train_rate_mult = profile.train_rate if profile else 1.0
    if train_rate_mult == 0.0:
        return  # e.g., Undead don't train
        
    talents = talents or []
    old_snapshot = attrs.copy() if stats is not None else None
    changed = False
    
    aptitudes = aptitudes or {}
    
    # Pillar 3: Attribute Soft-Caps
    # Total trainable gain is limited by (Level * 5) + Base
    level = stats.level if stats else 1
    soft_cap_limit = level * 5 + 15 # +15 safe buffer for starter stats
    
    for attr_key, base_rate in rates.items():
        # Check Soft-Cap before training
        mapping = _TRAIN_MAP.get(attr_key)
        if mapping:
            current = getattr(attrs, mapping[0])
            if current >= soft_cap_limit:
                continue # Soft-Capped at this level

        # Apply multipliers
        rate = base_rate * train_rate_mult * aptitudes.get(attr_key, 1.0)
        if attr_key in talents:
            rate *= 2.0
        elif attr_key == weakness:
            rate *= 0.5
            
        if _apply_train(attrs, caps, attr_key, rate):
            changed = True
            
    if changed and stats is not None and old_snapshot is not None:
        # Increase region fatigue when performing actions (Anti-loop)
        rid = getattr(stats, "_entity", None).current_region_id if hasattr(stats, "_entity") else None
        if rid and action in ("attack", "harvest", "explore", "loot"):
            attrs.mind.region_fatigue[rid] = min(1.0, attrs.mind.region_fatigue.get(rid, 0.0) + 0.01)
            
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


def decay_attributes(
    attrs: Attributes,
    stats: 'Stats',
    rng: 'DeterministicRNG',
    entity_id: int,
    tick: int,
    decay_amount: float = 0.1,
) -> bool:
    """Fractionally reduce a random primary attribute.
    
    If fractional reaches negative and integer attribute is > 5,
    reduce the integer attribute. Returns True if attribute was reduced.
    """
    from src.core.models.enums import Domain
    # Pick a random attribute to decay
    attr_keys = list(_TRAIN_MAP.keys())
    # Deterministic choice
    idx = rng.next_int(Domain.AI_DECISION, entity_id, tick + 99, 0, len(attr_keys) - 1)
    key = attr_keys[idx]
    
    mapping = _TRAIN_MAP.get(key)
    if mapping is None:
        return False
        
    attr_field, frac_field, _ = mapping
    old_snapshot = attrs.copy()
    
    current = getattr(attrs, attr_field)
    frac = getattr(attrs, frac_field) - decay_amount
    
    changed = False
    if frac < 0.0:
        if current > 5: # Don't decay below base starting value
            setattr(attrs, attr_field, current - 1)
            frac += 1.0
            changed = True
        else:
            frac = 0.0 # Clamp at 0.0 if we can't reduce integer
            
    setattr(attrs, frac_field, frac)
    
    if changed:
        recalc_derived_stats(stats, attrs, old_attrs=old_snapshot)
        
    return changed


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

def level_up_attributes(attrs: Attributes, caps: AttributeCaps, aptitudes: dict[str, float] | None = None) -> None:
    """Apply attribute gains on level up.

    - Base attributes: +2 (modified by aptitude) to each (up to cap)
    - Caps: +5 to each
    """
    caps.increase_all(5)
    
    aptitudes = aptitudes or {}

    attrs.str_ = min(attrs.str_ + int(2 * aptitudes.get("str", 1.0)), caps.str_cap)
    attrs.agi = min(attrs.agi + int(2 * aptitudes.get("agi", 1.0)), caps.agi_cap)
    attrs.vit = min(attrs.vit + int(2 * aptitudes.get("vit", 1.0)), caps.vit_cap)
    attrs.int_ = min(attrs.int_ + int(2 * aptitudes.get("int", 1.0)), caps.int_cap)
    attrs.spi = min(attrs.spi + int(2 * aptitudes.get("spi", 1.0)), caps.spi_cap)
    attrs.wis = min(attrs.wis + int(2 * aptitudes.get("wis", 1.0)), caps.wis_cap)
    attrs.end = min(attrs.end + int(2 * aptitudes.get("end", 1.0)), caps.end_cap)
    attrs.per = min(attrs.per + int(2 * aptitudes.get("per", 1.0)), caps.per_cap)
    attrs.cha = min(attrs.cha + int(2 * aptitudes.get("cha", 1.0)), caps.cha_cap)


# ---------------------------------------------------------------------------
# Speed → action delay (Option D: logarithmic + action-type multipliers)
# ---------------------------------------------------------------------------

# Action-type delay multipliers (lower = faster for that action type)
_ACTION_DELAY_MULT: dict[str, float] = {
    "move": 2.0,
    "attack": 1.5,
    "skill": 2.5,
    "loot": 1.2,
    "harvest": 1.2,
    "use_item": 1.0,
    "rest": 1.5,
    "building": 2.0,     # Building visit interactions (shop, blacksmith, guild, etc.)
}

# Minimum delay floor (prevents infinitely fast actions)
_MIN_DELAY = 0.3
# Maximum delay ceiling
_MAX_DELAY = 4.0


def speed_delay(spd: int, action: str = "move", interaction_speed: float = 1.0) -> float:
    """Compute action delay from speed stat using logarithmic diminishing returns.

    Formula: delay = action_mult / (1.0 + ln(max(spd, 1)))
    Then scaled by interaction_speed for loot/harvest/use_item.

    SPD →  delay (move, mult=2.0):
      1  → 2.00
      5  → 0.76
     10  → 0.60
     15  → 0.54
     20  → 0.50
     30  → 0.45
     50  → 0.40

    Returns a float clamped to [_MIN_DELAY, _MAX_DELAY].
    """
    s = max(spd, 1)
    base = 1.0 / (1.0 + _math.log(s))
    mult = _ACTION_DELAY_MULT.get(action, 1.0)
    delay = base * mult

    # Apply interaction_speed stat for non-combat actions
    if action in ("loot", "harvest", "use_item", "rest"):
        delay /= max(interaction_speed, 0.5)

    return max(_MIN_DELAY, min(_MAX_DELAY, delay))
