"""RPG Attribute system — 9 primary attributes that derive combat & non-combat stats.

Refactored for AOA Stabilization:
- Removed legacy StatsProxy dependencies.
- recalc_derived_stats now works directly with Entity aspects.
- Standardized attribute training and decay logic.
"""

from __future__ import annotations
import math as _math
from typing import TYPE_CHECKING, Any
from src.core.models.base import SimulationModel
from pydantic import Field, PrivateAttr

if TYPE_CHECKING:
    from src.core.entities.entity import Entity
    from src.platform.rng import DeterministicRNG
from src.core.models.enums import TacticalRole, HeroClass

class Attributes(SimulationModel):
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

    # Fractional training accumulator (Private)
    _str_frac: float = PrivateAttr(default=0.0)
    _agi_frac: float = PrivateAttr(default=0.0)
    _vit_frac: float = PrivateAttr(default=0.0)
    _int_frac: float = PrivateAttr(default=0.0)
    _spi_frac: float = PrivateAttr(default=0.0)
    _wis_frac: float = PrivateAttr(default=0.0)
    _end_frac: float = PrivateAttr(default=0.0)
    _per_frac: float = PrivateAttr(default=0.0)
    _cha_frac: float = PrivateAttr(default=0.0)

    def copy(self) -> Attributes:
        """Absolute deep copy that preserves private fractional training progress."""
        new_obj = self.model_copy(deep=True)
        # Manually copy private progress attributes
        new_obj._str_frac = self._str_frac
        new_obj._agi_frac = self._agi_frac
        new_obj._vit_frac = self._vit_frac
        new_obj._int_frac = self._int_frac
        new_obj._spi_frac = self._spi_frac
        new_obj._wis_frac = self._wis_frac
        new_obj._end_frac = self._end_frac
        new_obj._per_frac = self._per_frac
        new_obj._cha_frac = self._cha_frac
        return new_obj

    def total(self) -> int:
        return (self.str_ + self.agi + self.vit + self.int_ + self.spi
                + self.wis + self.end + self.per + self.cha)

    def validate(self) -> None:
        """Ensure attributes stay within reasonable bounds."""
        self.str_ = max(1, self.str_)
        self.agi = max(1, self.agi)
        self.vit = max(1, self.vit)
        self.int_ = max(1, self.int_)
        self.spi = max(1, self.spi)
        self.wis = max(1, self.wis)
        self.end = max(1, self.end)
        self.per = max(1, self.per)
        self.cha = max(1, self.cha)

class AttributeCaps(SimulationModel):
    """Maximum trainable values for each attribute."""
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
        return self.model_copy(deep=True)

    def increase_all(self, amount: int) -> None:
        self.str_cap += amount
        self.agi_cap += amount
        self.vit_cap += amount
        self.int_cap += amount
        self.spi_cap += amount
        self.wis_cap += amount
        self.end_cap += amount
        self.per_cap += amount
        self.cha_cap += amount

    def validate(self) -> None:
        """Ensure caps stay positive."""
        self.str_cap = max(1, self.str_cap)
        self.agi_cap = max(1, self.agi_cap)
        self.vit_cap = max(1, self.vit_cap)
        self.int_cap = max(1, self.int_cap)
        self.spi_cap = max(1, self.spi_cap)
        self.wis_cap = max(1, self.wis_cap)
        self.end_cap = max(1, self.end_cap)
        self.per_cap = max(1, self.per_cap)
        self.cha_cap = max(1, self.cha_cap)

# ---------------------------------------------------------------------------
# Milestone 5: Role Profiling & Specialization
# ---------------------------------------------------------------------------

ROLE_PROFILES: dict[TacticalRole, dict[str, float]] = {
    TacticalRole.MELEE_STRIKER:      {"str": 1.0, "vit": 0.8, "end": 0.6},
    TacticalRole.RANGED_SKIRMISHER:  {"agi": 1.0, "per": 0.8, "end": 0.6},
    TacticalRole.SUPPORT_HEALER:     {"spi": 1.0, "wis": 0.8, "int": 0.6},
    TacticalRole.AOE_PRESSURE:      {"int": 1.0, "spi": 0.8, "wis": 0.6},
    TacticalRole.RETREAT_BIASED:     {"vit": 0.5, "end": 1.0, "agi": 0.7}, # Defensive focus
}

def derive_tactical_role_from_class(hero_class: HeroClass) -> TacticalRole:
    """Map HeroClass to its natural intended tactical role."""
    melee_classes = {HeroClass.WARRIOR, HeroClass.CHAMPION, HeroClass.BRUTE, HeroClass.TANK}
    ranged_classes = {HeroClass.RANGER, HeroClass.SHARPSHOOTER, HeroClass.SCOUT}
    magic_classes = {HeroClass.MAGE, HeroClass.ARCHMAGE, HeroClass.CASTER}
    
    if hero_class in melee_classes: return TacticalRole.MELEE_STRIKER
    if hero_class in ranged_classes: return TacticalRole.RANGED_SKIRMISHER
    if hero_class in magic_classes: return TacticalRole.AOE_PRESSURE
    return TacticalRole.MELEE_STRIKER # Default fallback

def derive_tactical_role(entity: Any) -> TacticalRole:
    """Derive role from current effective stats and apply hysteresis stability."""
    prog = entity.progression
    attrs = prog.attributes
    if not attrs: return prog.tactical_role
    
    # Calculate scores for each role based on effective attributes
    scores: dict[TacticalRole, float] = {}
    for role, weights in ROLE_PROFILES.items():
        score = 0.0
        for attr_key, weight in weights.items():
            val = getattr(attrs, _TRAIN_MAP[attr_key][0])
            score += val * weight
        scores[role] = score
        
    # Find the highest scoring role (Ideal Role)
    ideal_role = max(scores, key=lambda k: scores[k])
    
    # Apply Hysteresis stability logic
    if ideal_role == prog.tactical_role:
        prog.role_stability = min(10, prog.role_stability + 1)
    else:
        prog.role_stability -= 1
        if prog.role_stability <= 0:
            prog.tactical_role = ideal_role
            prog.role_stability = 5 # Reset to mid-point stability
            
    return prog.tactical_role

def apply_soft_cap(value: float, cap: float) -> int:
    """Apply 3-stage piecewise linear diminishing returns. [Milestone 5]"""
    if value <= cap:
        return int(value)
    
    # Stage 1: 100% contribution (already handled)
    # Stage 2: 50% contribution until 2x cap
    if value <= cap * 2:
        overflow = value - cap
        return int(cap + overflow * 0.5)
        
    # Stage 3: 10% contribution thereafter
    base_cap = cap + cap * 0.5 # cap + (2*cap - cap)*0.5
    extreme_overflow = value - cap * 2
    return int(base_cap + extreme_overflow * 0.1)

# ---------------------------------------------------------------------------
# Attribute → derived stat formulas
# ---------------------------------------------------------------------------

def derive_max_hp(base_max_hp: int, vit: int, end: int) -> int:
    return base_max_hp + vit * 2 + int(end * 0.5)

def derive_atk(base_atk: int, str_: int) -> int:
    return base_atk + int(str_ * 0.5)

def derive_def(base_def: int, vit: int) -> int:
    return base_def + int(vit * 0.3)

def derive_spd(base_spd: int, agi: int) -> int:
    return base_spd + int(agi * 0.4)

def derive_crit_rate(base_crit: float, agi: int, luck: int = 0) -> float:
    return base_crit + agi * 0.004 + luck * 0.01

def derive_evasion(base_evasion: float, agi: int) -> float:
    return base_evasion + agi * 0.003

def derive_luck(base_luck: int, wis: int) -> int:
    return base_luck + int(wis * 0.3)

def derive_stamina(base_stamina: int, end: int) -> int:
    # Bonus is absolute addition to base
    return base_stamina + end * 2

def derive_xp_multiplier(wis: int, int_: int) -> float:
    return 1.0 + wis * 0.01 + int_ * 0.005

def derive_matk(base_matk: int, spi: int, int_: int) -> int:
    return base_matk + int(spi * 0.6) + int(int_ * 0.2)

def derive_mdef(base_mdef: int, wis: int, spi: int) -> int:
    return base_mdef + int(wis * 0.4) + int(spi * 0.15)

def derive_vision(base_vision: int, per: int) -> int:
    return base_vision + int(per * 0.3)

def derive_loot_bonus(per: int, wis: int) -> float:
    return 1.0 + per * 0.008 + wis * 0.003

def derive_trade_bonus(cha: int) -> float:
    return 1.0 + cha * 0.01

def derive_interaction_speed(cha: int, int_: int) -> float:
    return 1.0 + cha * 0.005 + int_ * 0.005

def derive_rest_efficiency(end: int, wis: int) -> float:
    return 1.0 + end * 0.008 + wis * 0.004

def derive_hp_regen(end: int, vit: int) -> float:
    return 1.0 + end * 0.15 + vit * 0.05

def derive_cooldown_reduction(int_: int, wis: int) -> float:
    return max(0.5, 1.0 - int_ * 0.005 - wis * 0.003)

# ---------------------------------------------------------------------------
# Recalculate derived stats
# ---------------------------------------------------------------------------

def recalc_derived_stats(entity: "Entity", new_attrs: Attributes, old_attrs: Attributes | None = None) -> None:
    """Recompute all attribute-derived fields for the given Entity. [AOA STABILIZATION]"""
    combat = entity.combat
    prog = entity.progression
    
    # Milestone 5: Dynamic Role Update
    derive_tactical_role(entity)
    
    # Reset old contributions if necessary
    if old_attrs is not None:
        # Revert old attribute contributions before applying new ones
        prog.max_stamina -= derive_stamina(0, old_attrs.end)
        combat.max_hp -= derive_max_hp(0, old_attrs.vit, old_attrs.end)
        combat.atk_base -= derive_atk(0, old_attrs.str_)
        combat.def_base -= derive_def(0, old_attrs.vit)
        combat.spd_base -= derive_spd(0, old_attrs.agi)
        combat.crit_rate -= derive_crit_rate(0.0, old_attrs.agi, old_attrs.wis)
        combat.evasion -= derive_evasion(0.0, old_attrs.agi)
        combat.luck -= derive_luck(0, old_attrs.wis)
        combat.matk -= derive_matk(0, old_attrs.spi, old_attrs.int_)
        combat.mdef -= derive_mdef(0, old_attrs.wis, old_attrs.spi)

    # Apply new contributions
    raw_max_hp = derive_max_hp(combat.max_hp, new_attrs.vit, new_attrs.end)
    combat.max_hp = apply_soft_cap(raw_max_hp, 200.0) # Milestone 5 Ceiling
    
    raw_atk = derive_atk(combat.atk_base, new_attrs.str_)
    combat.atk_base = apply_soft_cap(raw_atk, 40.0) 
    
    raw_def = derive_def(combat.def_base, new_attrs.vit)
    combat.def_base = apply_soft_cap(raw_def, 20.0)
    
    raw_spd = derive_spd(combat.spd_base, new_attrs.agi)
    combat.spd_base = apply_soft_cap(raw_spd, 25.0)
    
    combat.crit_rate = derive_crit_rate(combat.crit_rate, new_attrs.agi, new_attrs.wis)
    combat.evasion = derive_evasion(combat.evasion, new_attrs.agi)
    combat.luck = derive_luck(combat.luck, new_attrs.wis)
    
    raw_matk = derive_matk(combat.matk, new_attrs.spi, new_attrs.int_)
    combat.matk = apply_soft_cap(raw_matk, 40.0)
    
    combat.mdef = derive_mdef(combat.mdef, new_attrs.wis, new_attrs.spi)
    combat.hp_regen = derive_hp_regen(new_attrs.end, new_attrs.vit)
    
    raw_stamina = derive_stamina(prog.max_stamina, new_attrs.end)
    prog.max_stamina = apply_soft_cap(raw_stamina, 200.0)
    
    entity.spatial.vision_range = derive_vision(6, new_attrs.per)
    combat.cooldown_reduction = derive_cooldown_reduction(new_attrs.int_, new_attrs.wis)
    
    # Interaction Aspect stabilization
    entity.interaction.loot_bonus = derive_loot_bonus(new_attrs.per, new_attrs.wis)
    entity.interaction.trade_bonus = derive_trade_bonus(new_attrs.cha)
    entity.interaction.interaction_speed = derive_interaction_speed(new_attrs.cha, new_attrs.int_)
    entity.interaction.rest_efficiency = derive_rest_efficiency(new_attrs.end, new_attrs.wis)

    # Breakthrough Milestones
    traits = entity.identity.traits
    # Support both string and enum checks during transition
    if "str_25" in traits: combat.atk_base = int(combat.atk_base * 1.1)
    if "vit_25" in traits: combat.max_hp = int(combat.max_hp * 1.1)
    if "agi_25" in traits: combat.spd_base = int(combat.spd_base * 1.1)
    
    # Check for new breakthroughs
    if prog.attributes:
        attrs = prog.attributes
        if attrs.str_ >= 25 and "str_25" not in traits:
            traits.append("str_25")
        if attrs.vit >= 25 and "vit_25" not in traits:
            traits.append("vit_25")
        # agi breakthrough
        if attrs.agi >= 25 and "agi_25" not in traits:
            traits.append("agi_25")
    
    combat.hp = min(combat.hp, combat.max_hp)
    prog.stamina = min(prog.stamina, prog.max_stamina)

# ---------------------------------------------------------------------------
# Training: attribute gain from actions
# ---------------------------------------------------------------------------

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
}

def train_attributes(entity: Any, action: str, bucket: Any = None, aptitudes: dict[str, float] | None = None) -> None:
    """Apply fractional training gains from an action.
    
    Legacy Support: Supports both (entity, action) and (attrs, caps, action).
    """
    if isinstance(entity, Attributes) and isinstance(action, AttributeCaps):
        # Legacy call: train_attributes(attrs, caps, action_str)
        _train_attributes_legacy(entity, action, bucket, aptitudes=aptitudes)
        return

    # Modern AOA call: train_attributes(entity, action_str)
    ent: Entity = entity
    rates = TRAIN_RATES.get(action, {})
    if not rates: return
    
    prog = ent.progression
    attrs = prog.attributes
    caps = prog.attribute_caps
    
    if attrs is None or caps is None:
        return
        
    old_snapshot = attrs.copy()
    changed = False
    
    soft_cap_limit = prog.level * 5 + 15 # Legacy base
    aptitudes = aptitudes or prog.aptitudes
    role_weights = ROLE_PROFILES.get(prog.tactical_role, {})
    
    for attr_key, base_rate in rates.items():
        rate = base_rate * aptitudes.get(attr_key, 1.0)
        
        # Pillar 3: Specialized Soft Cap Diminishing Returns [Milestone 5]
        weight = role_weights.get(attr_key, 0.0)
        if weight >= 1.0: # Primary
            soft_limit = prog.level * 10 + 20
        elif weight >= 0.5: # Secondary
            soft_limit = prog.level * 5 + 15
        else: # Off-role
            soft_limit = prog.level * 2 + 10

        current_val = getattr(attrs, _TRAIN_MAP[attr_key][0])
        if current_val >= soft_limit:
            rate *= 0.5 # 50% slow beyond first soft cap
            if current_val >= soft_limit * 2:
                rate *= 0.2 # 90% total slow for extreme specialization
            
        if _apply_train(attrs, caps, attr_key, rate):
            changed = True
            
    if changed:
        recalc_derived_stats(ent, attrs, old_attrs=old_snapshot)

def _train_attributes_legacy(attrs: Attributes, caps: AttributeCaps, action: str, aptitudes: dict[str, float] | None = None) -> None:
    rates = TRAIN_RATES.get(action, {})
    aptitudes = aptitudes or {}
    for attr_key, rate in rates.items():
        final_rate = rate * aptitudes.get(attr_key, 1.0)
        _apply_train(attrs, caps, attr_key, final_rate)

def level_up_attributes(attrs: Attributes, caps: AttributeCaps) -> None:
    """Standard level-up gain: increase all attributes and caps."""
    caps.increase_all(5)
    attrs.str_ += 2
    attrs.agi += 2
    attrs.vit += 2
    attrs.int_ += 2
    attrs.spi += 2
    attrs.wis += 2
    attrs.end += 2
    attrs.per += 2
    attrs.cha += 2

def check_breakthroughs(entity: Entity) -> list[str]:
    """Check for new attribute breakthroughs (Milestone 25/50/75/100)."""
    attrs = entity.progression.attributes
    traits = entity.identity.traits
    new_breakthroughs = []
    
    if attrs.str_ >= 25 and "str_25" not in traits:
        traits.append("str_25")
        new_breakthroughs.append("str_25")
    if attrs.vit >= 25 and "vit_25" not in traits:
        traits.append("vit_25")
        new_breakthroughs.append("vit_25")
    # ... add others as needed
    return new_breakthroughs

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
    mapping = _TRAIN_MAP.get(key)
    if mapping is None: return False
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
# Speed → action delay
# ---------------------------------------------------------------------------

_ACTION_DELAY_MULT: dict[str, float] = {
    "move": 2.0, "attack": 1.5, "skill": 2.5, "loot": 1.2,
    "harvest": 1.2, "use_item": 1.0, "rest": 1.5, "building": 2.0,
}

def speed_delay(spd: int, action: str = "move", interaction_speed: float = 1.0) -> float:
    """Calculate the delay (in ticks) before the next action. [AOA STABILIZATION]
    
    Milestone 5: Rebalanced for Tempo.
    Uses a softer logarithmic curve to ensure diminishing returns at high agility.
    """
    s = max(spd, 1)
    # base = 1.0 / (1.0 + math.log(s)) -> Replaced with more controlled curve
    base = 1.2 / (1.0 + _math.log1p(s * 0.5))
    
    delay = base * _ACTION_DELAY_MULT.get(action, 1.0)
    if action in ("loot", "harvest", "use_item", "rest"):
        delay /= max(interaction_speed, 0.5)
        
    # Pillar 3: Tempo Limit (Minimum 0.4s recovery window)
    return max(0.4, min(4.0, delay))

def decay_attributes(
    entity: Entity,
    rng: DeterministicRNG,
    decay_amount: float = 0.1,
) -> bool:
    """Fractionally reduce a random primary attribute of the entity.
    
    If fractional reaches negative and integer attribute is > 5,
    reduce the integer attribute. Returns True if attribute was reduced.
    """
    from src.core.models.enums import Domain
    prog = entity.progression
    attrs = prog.attributes
    if not attrs:
        return False
        
    # Pick a random attribute to decay
    attr_keys = list(_TRAIN_MAP.keys())
    # Deterministic choice based on entity identity and world tick
    idx = rng.next_int(Domain.AI_DECISION, entity.id, 9999, 0, len(attr_keys) - 1)
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
            frac = 0.9 # Reset fractional to near-full to avoid immediate double decay
            changed = True
        else:
            frac = 0.0 # Clamp at 0 and don't reduce attribute
            
    setattr(attrs, frac_field, frac)
    
    if changed:
        recalc_derived_stats(entity, attrs, old_attrs=old_snapshot)
        
    return changed
