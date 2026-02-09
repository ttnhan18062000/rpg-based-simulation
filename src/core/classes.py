"""Hero class system — classes, skills, breakthrough, and mastery.

Heroes choose a class which provides:
  - Attribute bonuses (base + cap)
  - Class-specific skills (learnable at class buildings for gold)
  - Breakthrough path (e.g. Warrior → Champion at Lv10+ with STR 30+)
  - Mastery progression (using skills increases mastery)

All entities also have race skills (innate, no cost to learn).

Skill types:
  - ACTIVE: Costs stamina, has cooldown, used in combat/exploration
  - PASSIVE: Always active, provides stat bonuses
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum, unique


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

@unique
class HeroClass(IntEnum):
    """Hero class identities."""
    NONE = 0
    WARRIOR = 1
    RANGER = 2
    MAGE = 3
    ROGUE = 4
    # Breakthroughs
    CHAMPION = 5
    SHARPSHOOTER = 6
    ARCHMAGE = 7
    ASSASSIN = 8


@unique
class SkillType(IntEnum):
    """Skill categories."""
    ACTIVE = 0
    PASSIVE = 1


@unique
class SkillTarget(IntEnum):
    """Who a skill targets."""
    SELF = 0
    SINGLE_ENEMY = 1
    AREA_ENEMIES = 2
    SINGLE_ALLY = 3
    AREA_ALLIES = 4


# ---------------------------------------------------------------------------
# Skill definition
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class SkillDef:
    """Immutable skill template/definition."""
    skill_id: str
    name: str
    description: str
    skill_type: SkillType
    target: SkillTarget
    class_req: HeroClass       # NONE = race skill (no class required)
    level_req: int = 1
    gold_cost: int = 0         # Cost to learn at building
    cooldown: int = 5          # Ticks between uses
    stamina_cost: int = 10     # Stamina to activate
    # Effects
    power: float = 1.0         # Damage multiplier or heal amount multiplier
    duration: int = 0          # Buff/debuff duration in ticks
    range: int = 1             # Effective range in tiles
    # Learning prerequisites
    mastery_req: str = ""       # Prerequisite skill_id that must have mastery >= mastery_threshold
    mastery_threshold: float = 25.0  # Min mastery on prerequisite skill
    # Stat modifiers (for passive skills)
    atk_mod: float = 0.0
    def_mod: float = 0.0
    spd_mod: float = 0.0
    crit_mod: float = 0.0
    evasion_mod: float = 0.0
    hp_mod: float = 0.0


@dataclass(slots=True)
class SkillInstance:
    """A learned skill on an entity, tracking cooldown and mastery."""
    skill_id: str
    cooldown_remaining: int = 0
    mastery: float = 0.0       # 0.0 to 100.0
    times_used: int = 0

    def is_ready(self) -> bool:
        return self.cooldown_remaining <= 0

    def use(self, base_cooldown: int) -> None:
        self.cooldown_remaining = base_cooldown
        self.times_used += 1
        # Mastery gain: diminishing returns
        gain = max(0.1, 1.0 - self.mastery * 0.008)
        self.mastery = min(100.0, self.mastery + gain)

    def tick(self) -> None:
        if self.cooldown_remaining > 0:
            self.cooldown_remaining -= 1

    @property
    def mastery_tier(self) -> int:
        """0=novice, 1=apprentice(25), 2=adept(50), 3=expert(75), 4=master(100)"""
        if self.mastery >= 100.0:
            return 4
        if self.mastery >= 75.0:
            return 3
        if self.mastery >= 50.0:
            return 2
        if self.mastery >= 25.0:
            return 1
        return 0

    def effective_power(self, base_power: float) -> float:
        """Power modified by mastery. +20% at mastery tier 2+."""
        mult = 1.0
        if self.mastery >= 50.0:
            mult += 0.20
        if self.mastery >= 100.0:
            mult += 0.15  # Total +35% at master
        return base_power * mult

    def effective_stamina_cost(self, base_cost: int) -> int:
        """Stamina cost reduced by mastery. -10% at tier 1+, -20% at tier 3+."""
        mult = 1.0
        if self.mastery >= 25.0:
            mult -= 0.10
        if self.mastery >= 75.0:
            mult -= 0.10  # Total -20%
        return max(1, int(base_cost * mult))

    def effective_cooldown(self, base_cd: int) -> int:
        """Cooldown reduced at mastery tier 3+."""
        if self.mastery >= 75.0:
            return max(1, base_cd - 1)
        return base_cd

    def copy(self) -> SkillInstance:
        return SkillInstance(
            skill_id=self.skill_id,
            cooldown_remaining=self.cooldown_remaining,
            mastery=self.mastery,
            times_used=self.times_used,
        )


# ---------------------------------------------------------------------------
# Class definition
# ---------------------------------------------------------------------------

# Attribute scaling grades — determines how effectively a class
# benefits from investing in each attribute.  Higher grades yield
# larger derived-stat bonuses from that attribute.
SCALING_GRADES = ('E', 'D', 'C', 'B', 'A', 'S', 'SS', 'SSS')

SCALING_MULTIPLIER: dict[str, float] = {
    'E': 0.60, 'D': 0.75, 'C': 0.90, 'B': 1.00,
    'A': 1.15, 'S': 1.30, 'SS': 1.50, 'SSS': 1.80,
}


@dataclass(frozen=True, slots=True)
class ClassDef:
    """Immutable class template."""
    class_id: HeroClass
    name: str
    description: str
    # Attribute bonuses applied when class is chosen
    str_bonus: int = 0
    agi_bonus: int = 0
    vit_bonus: int = 0
    int_bonus: int = 0
    spi_bonus: int = 0
    wis_bonus: int = 0
    end_bonus: int = 0
    per_bonus: int = 0
    cha_bonus: int = 0
    # Attribute cap bonuses
    str_cap_bonus: int = 0
    agi_cap_bonus: int = 0
    vit_cap_bonus: int = 0
    int_cap_bonus: int = 0
    spi_cap_bonus: int = 0
    wis_cap_bonus: int = 0
    end_cap_bonus: int = 0
    per_cap_bonus: int = 0
    cha_cap_bonus: int = 0
    # Breakthrough target
    breakthrough_class: HeroClass = HeroClass.NONE
    breakthrough_level: int = 10
    breakthrough_attr: str = ""      # e.g. "str" — which attribute must be >= threshold
    breakthrough_threshold: int = 30
    # Attribute scaling grades (E–SSS)
    str_scaling: str = 'E'
    agi_scaling: str = 'E'
    vit_scaling: str = 'E'
    int_scaling: str = 'E'
    spi_scaling: str = 'E'
    wis_scaling: str = 'E'
    end_scaling: str = 'E'
    per_scaling: str = 'E'
    cha_scaling: str = 'E'
    # Lore & identity
    tier: int = 1                    # 1 = base, 2 = breakthrough, 3 = transcendence
    lore: str = ''
    playstyle: str = ''
    role: str = ''                   # e.g. "DPS", "Tank", "Support"


@dataclass(frozen=True, slots=True)
class BreakthroughDef:
    """Breakthrough (promotion) definition."""
    from_class: HeroClass
    to_class: HeroClass
    level_req: int
    attr_req: str              # e.g. "str"
    attr_threshold: int
    # Bonuses on breakthrough
    str_bonus: int = 0
    agi_bonus: int = 0
    vit_bonus: int = 0
    int_bonus: int = 0
    spi_bonus: int = 0
    wis_bonus: int = 0
    end_bonus: int = 0
    per_bonus: int = 0
    cha_bonus: int = 0
    str_cap_bonus: int = 0
    agi_cap_bonus: int = 0
    vit_cap_bonus: int = 0
    int_cap_bonus: int = 0
    spi_cap_bonus: int = 0
    wis_cap_bonus: int = 0
    end_cap_bonus: int = 0
    per_cap_bonus: int = 0
    cha_cap_bonus: int = 0
    talent: str = ""           # Special passive ability name


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

# -- Class Definitions --

CLASS_DEFS: dict[HeroClass, ClassDef] = {
    # ---- Tier 1 — Base Classes ----
    HeroClass.WARRIOR: ClassDef(
        class_id=HeroClass.WARRIOR, name="Warrior",
        description="A frontline fighter specializing in strength and vitality.",
        str_bonus=3, vit_bonus=2, end_bonus=1,
        str_cap_bonus=10, vit_cap_bonus=5, end_cap_bonus=3,
        breakthrough_class=HeroClass.CHAMPION,
        breakthrough_level=10, breakthrough_attr="str", breakthrough_threshold=30,
        str_scaling='S', agi_scaling='D', vit_scaling='A', int_scaling='E', spi_scaling='E', wis_scaling='D', end_scaling='B', per_scaling='D', cha_scaling='C',
        tier=1, role='Tank / Melee DPS',
        lore=(
            'Warriors are forged in the crucible of battle. They stand where others fall, '
            'trading blows with monstrous foes through sheer grit and iron will. '
            'From humble militia training to legendary feats of arms, the Warrior\'s '
            'path is one of relentless perseverance. Ancient war-songs tell of warriors '
            'who held castle gates alone — their shields dented, their blades notched, '
            'yet their spirit unbroken.'
        ),
        playstyle=(
            'Warriors excel at sustained melee combat. High STR scaling makes every '
            'point of Strength hit harder, while strong VIT and END scaling provide '
            'the survivability to endure prolonged fights. Best paired with heavy '
            'armor and two-handed weapons. Ideal for players who like to lead the '
            'charge and control the front line.'
        ),
    ),
    HeroClass.RANGER: ClassDef(
        class_id=HeroClass.RANGER, name="Ranger",
        description="A swift scout with deadly precision and keen awareness.",
        agi_bonus=3, wis_bonus=2, end_bonus=1,
        agi_cap_bonus=10, wis_cap_bonus=5, end_cap_bonus=3,
        breakthrough_class=HeroClass.SHARPSHOOTER,
        breakthrough_level=10, breakthrough_attr="agi", breakthrough_threshold=30,
        per_bonus=1,
        per_cap_bonus=3,
        str_scaling='D', agi_scaling='S', vit_scaling='D', int_scaling='D', spi_scaling='E', wis_scaling='B', end_scaling='A', per_scaling='A', cha_scaling='D',
        tier=1, role='Ranged DPS / Scout',
        lore=(
            'Rangers are children of the wilds — trackers, hunters, and silent sentinels '
            'who read the land like an open book. They strike from afar with deadly '
            'accuracy, disappearing into brush before the enemy can react. '
            'The great Rangers of old could track a shadow across bare stone and pin '
            'a dragonfly\'s wing at a hundred paces. Their bond with nature grants '
            'them a preternatural awareness that few can match.'
        ),
        playstyle=(
            'Rangers dominate at range with high AGI scaling boosting speed, crit, and '
            'evasion. WIS scaling enhances luck and awareness, while END keeps stamina '
            'high for sustained kiting. Equip bows and light armor for maximum '
            'mobility. Perfect for hit-and-run tactics and exploration.'
        ),
    ),
    HeroClass.MAGE: ClassDef(
        class_id=HeroClass.MAGE, name="Mage",
        description="A scholar of arcane arts, wielding intelligence and wisdom.",
        int_bonus=2, spi_bonus=3, wis_bonus=2, vit_bonus=1,
        int_cap_bonus=5, spi_cap_bonus=10, wis_cap_bonus=5, vit_cap_bonus=3,
        breakthrough_class=HeroClass.ARCHMAGE,
        breakthrough_level=10, breakthrough_attr="spi", breakthrough_threshold=30,
        str_scaling='E', agi_scaling='D', vit_scaling='C', int_scaling='A', spi_scaling='S', wis_scaling='A', end_scaling='C', per_scaling='D', cha_scaling='D',
        tier=1, role='Ranged DPS / Support',
        lore=(
            'Mages bend the very fabric of reality through years of rigorous study '
            'and arcane experimentation. Where warriors trust steel, mages trust '
            'knowledge — and knowledge, properly applied, can shatter mountains. '
            'The great academies produce scholars who command fire, frost, and '
            'lightning, but the truly gifted transcend elemental boundaries to '
            'touch the raw weave of magic itself.'
        ),
        playstyle=(
            'Mages deliver devastating ranged damage through INT scaling that amplifies '
            'skill power and XP gain. WIS scaling reduces cooldowns and boosts luck. '
            'Fragile in melee — rely on crowd control, burst damage, and positioning. '
            'Enchanted robes and magical accessories complement their playstyle. '
            'Best suited for calculated, ability-focused combat.'
        ),
    ),
    HeroClass.ROGUE: ClassDef(
        class_id=HeroClass.ROGUE, name="Rogue",
        description="A cunning fighter blending agility and strength for lethal strikes.",
        agi_bonus=2, str_bonus=2, wis_bonus=1,
        agi_cap_bonus=8, str_cap_bonus=5, wis_cap_bonus=3,
        breakthrough_class=HeroClass.ASSASSIN,
        breakthrough_level=10, breakthrough_attr="agi", breakthrough_threshold=25,
        str_scaling='B', agi_scaling='S', vit_scaling='D', int_scaling='D', spi_scaling='E', wis_scaling='C', end_scaling='C', per_scaling='B', cha_scaling='D',
        tier=1, role='Melee DPS / Assassin',
        lore=(
            'Rogues thrive in the spaces between light and shadow. They are '
            'opportunists — striking when the moment is perfect, vanishing before '
            'retaliation arrives. Whether they hail from thieves\' guilds or '
            'noble spy networks, every Rogue shares an instinct for finding '
            'weakness. The legendary Rogues could pick a lock, slit a throat, '
            'and empty a vault before the guards changed shift.'
        ),
        playstyle=(
            'Rogues combine AGI and STR scaling for lethal burst damage. High crit '
            'rate and evasion from AGI make them slippery in combat, while B-rank '
            'STR scaling ensures their strikes hit hard. Short cooldowns and low '
            'stamina costs enable rapid skill chains. Glass cannon playstyle — '
            'dodge or die. Daggers and light armor recommended.'
        ),
    ),
    # ---- Tier 2 — Breakthrough Classes ----
    HeroClass.CHAMPION: ClassDef(
        class_id=HeroClass.CHAMPION, name="Champion",
        description="An elite warrior who has mastered the art of war.",
        str_bonus=6, vit_bonus=4, end_bonus=2,
        str_cap_bonus=20, vit_cap_bonus=10, end_cap_bonus=6,
        cha_bonus=1,
        cha_cap_bonus=3,
        str_scaling='SS', agi_scaling='C', vit_scaling='S', int_scaling='E', spi_scaling='E', wis_scaling='D', end_scaling='A', per_scaling='D', cha_scaling='B',
        tier=2, role='Tank / Melee DPS',
        lore=(
            'Champions are warriors who have transcended mere skill to embody the '
            'spirit of battle itself. Their blows carry the weight of a hundred '
            'campaigns, and their presence on the field inspires allies to fight '
            'beyond their limits. The title of Champion is earned only through '
            'trials of blood and iron — where the weak perish, the Champion endures. '
            'Tales speak of Champions who shattered siege engines with bare fists '
            'and held bridges against entire armies.'
        ),
        playstyle=(
            'Champions push Warrior strengths to the extreme. SS-rank STR scaling '
            'makes every Strength point devastatingly effective. S-rank VIT provides '
            'near-unbreakable durability. The Unyielding talent further cements '
            'their role as immovable front-liners. Can comfortably solo elite enemies '
            'that would overwhelm other classes.'
        ),
    ),
    HeroClass.SHARPSHOOTER: ClassDef(
        class_id=HeroClass.SHARPSHOOTER, name="Sharpshooter",
        description="A legendary marksman with unmatched precision.",
        agi_bonus=6, wis_bonus=4, end_bonus=2,
        agi_cap_bonus=20, wis_cap_bonus=10, end_cap_bonus=6,
        per_bonus=2,
        per_cap_bonus=6,
        str_scaling='D', agi_scaling='SS', vit_scaling='D', int_scaling='C', spi_scaling='E', wis_scaling='A', end_scaling='S', per_scaling='S', cha_scaling='D',
        tier=2, role='Ranged DPS / Scout',
        lore=(
            'Sharpshooters are Rangers who have achieved perfect unity between '
            'eye, hand, and bow. Every arrow they loose finds its mark with '
            'supernatural accuracy. They can read wind, distance, and a target\'s '
            'movement in the span of a heartbeat. The Precision talent grants them '
            'an almost prophetic ability to predict enemy movement — some say '
            'they can see the threads of fate themselves.'
        ),
        playstyle=(
            'Sharpshooters elevate the Ranger\'s ranged dominance with SS-rank AGI '
            'scaling for devastating crit rates and evasion. S-rank END scaling '
            'ensures they never run out of stamina for kiting. The Precision talent '
            'provides bonus crit damage. Excels at eliminating high-value targets '
            'from extreme range before they can close the distance.'
        ),
    ),
    HeroClass.ARCHMAGE: ClassDef(
        class_id=HeroClass.ARCHMAGE, name="Archmage",
        description="A supreme mage who commands arcane forces at will.",
        int_bonus=4, spi_bonus=6, wis_bonus=4, vit_bonus=2,
        int_cap_bonus=10, spi_cap_bonus=20, wis_cap_bonus=10, vit_cap_bonus=6,
        str_scaling='E', agi_scaling='D', vit_scaling='B', int_scaling='A', spi_scaling='SS', wis_scaling='S', end_scaling='B', per_scaling='C', cha_scaling='D',
        tier=2, role='Ranged DPS / Support',
        lore=(
            'Archmages have pierced the veil between study and mastery, touching '
            'the raw source of magical power. Where a Mage channels spells through '
            'formulas and incantations, an Archmage shapes reality through pure '
            'will. The Arcane Mastery talent allows them to weave multiple spell '
            'effects simultaneously — a feat that would shatter a lesser caster\'s '
            'mind. Court wizards and war-mages alike bow before an Archmage\'s authority.'
        ),
        playstyle=(
            'Archmages reach SS-rank INT scaling, making their skills devastatingly '
            'powerful. S-rank WIS dramatically boosts XP gain and luck. Improved VIT '
            'scaling (B-rank) gives more survivability than base Mages. The Arcane '
            'Mastery talent enhances all skill effects. The ultimate glass cannon — '
            'when positioned correctly, an Archmage can end battles before they begin.'
        ),
    ),
    HeroClass.ASSASSIN: ClassDef(
        class_id=HeroClass.ASSASSIN, name="Assassin",
        description="A lethal shadow, striking with perfect precision.",
        agi_bonus=5, str_bonus=4, wis_bonus=2,
        agi_cap_bonus=16, str_cap_bonus=10, wis_cap_bonus=6,
        per_bonus=1,
        per_cap_bonus=3,
        str_scaling='A', agi_scaling='SS', vit_scaling='D', int_scaling='D', spi_scaling='E', wis_scaling='B', end_scaling='B', per_scaling='A', cha_scaling='D',
        tier=2, role='Melee DPS / Assassin',
        lore=(
            'Assassins have perfected the Rogue\'s art of the unseen strike, '
            'elevating it from skill to something approaching dark poetry. '
            'They move through shadows as though the darkness itself is an ally, '
            'and their blades find gaps in the strongest armor. The Lethal talent '
            'grants them the ability to strike vital points with terrifying '
            'consistency. Kingdoms have fallen not to armies, but to a single '
            'Assassin\'s patience.'
        ),
        playstyle=(
            'Assassins combine SS-rank AGI with A-rank STR for the highest burst '
            'damage potential of any class. The Lethal talent provides guaranteed '
            'critical strikes under certain conditions. Extremely deadly in '
            'one-on-one combat but vulnerable when surrounded. Requires careful '
            'target selection and timing. The ultimate single-target killer.'
        ),
    ),
}

# -- Breakthrough Definitions --

BREAKTHROUGHS: dict[HeroClass, BreakthroughDef] = {
    HeroClass.WARRIOR: BreakthroughDef(
        from_class=HeroClass.WARRIOR, to_class=HeroClass.CHAMPION,
        level_req=10, attr_req="str", attr_threshold=30,
        str_bonus=3, vit_bonus=2, str_cap_bonus=10, vit_cap_bonus=5,
        talent="Unyielding",
    ),
    HeroClass.RANGER: BreakthroughDef(
        from_class=HeroClass.RANGER, to_class=HeroClass.SHARPSHOOTER,
        level_req=10, attr_req="agi", attr_threshold=30,
        agi_bonus=3, wis_bonus=2, agi_cap_bonus=10, wis_cap_bonus=5,
        talent="Precision",
    ),
    HeroClass.MAGE: BreakthroughDef(
        from_class=HeroClass.MAGE, to_class=HeroClass.ARCHMAGE,
        level_req=10, attr_req="spi", attr_threshold=30,
        spi_bonus=3, int_bonus=2, wis_bonus=2, spi_cap_bonus=10, int_cap_bonus=5, wis_cap_bonus=5,
        talent="Arcane Mastery",
    ),
    HeroClass.ROGUE: BreakthroughDef(
        from_class=HeroClass.ROGUE, to_class=HeroClass.ASSASSIN,
        level_req=10, attr_req="agi", attr_threshold=25,
        agi_bonus=3, str_bonus=2, agi_cap_bonus=8, str_cap_bonus=5,
        talent="Lethal",
    ),
}


# -- Skill Definitions --

SKILL_DEFS: dict[str, SkillDef] = {}


def _reg_skill(s: SkillDef) -> None:
    SKILL_DEFS[s.skill_id] = s


# ---- Warrior class skills ----
_reg_skill(SkillDef(
    "power_strike", "Power Strike",
    "A devastating blow dealing 1.8x damage.",
    SkillType.ACTIVE, SkillTarget.SINGLE_ENEMY, HeroClass.WARRIOR,
    level_req=1, gold_cost=50, cooldown=4, stamina_cost=12,
    power=1.8, range=1,
))
_reg_skill(SkillDef(
    "shield_wall", "Shield Wall",
    "Brace for impact, boosting DEF by 50% for 3 ticks.",
    SkillType.ACTIVE, SkillTarget.SELF, HeroClass.WARRIOR,
    level_req=3, gold_cost=100, cooldown=8, stamina_cost=15,
    mastery_req="power_strike", mastery_threshold=25.0,
    def_mod=0.5, duration=3,
))
_reg_skill(SkillDef(
    "battle_cry", "Battle Cry",
    "Boost ATK of nearby allies by 20% for 3 ticks.",
    SkillType.ACTIVE, SkillTarget.AREA_ALLIES, HeroClass.WARRIOR,
    level_req=5, gold_cost=200, cooldown=12, stamina_cost=20,
    mastery_req="shield_wall", mastery_threshold=25.0,
    atk_mod=0.2, duration=3, range=3,
))

# ---- Ranger class skills ----
_reg_skill(SkillDef(
    "quick_shot", "Quick Shot",
    "A fast ranged attack dealing 1.5x damage from up to 3 tiles away.",
    SkillType.ACTIVE, SkillTarget.SINGLE_ENEMY, HeroClass.RANGER,
    level_req=1, gold_cost=50, cooldown=3, stamina_cost=8,
    power=1.5, range=3,
))
_reg_skill(SkillDef(
    "evasive_step", "Evasive Step",
    "Boost evasion by 30% for 3 ticks.",
    SkillType.ACTIVE, SkillTarget.SELF, HeroClass.RANGER,
    level_req=3, gold_cost=100, cooldown=7, stamina_cost=10,
    mastery_req="quick_shot", mastery_threshold=25.0,
    evasion_mod=0.30, duration=3,
))
_reg_skill(SkillDef(
    "mark_prey", "Mark Prey",
    "Mark an enemy, increasing damage taken by 25% for 4 ticks.",
    SkillType.ACTIVE, SkillTarget.SINGLE_ENEMY, HeroClass.RANGER,
    level_req=5, gold_cost=200, cooldown=10, stamina_cost=15,
    mastery_req="evasive_step", mastery_threshold=25.0,
    def_mod=-0.25, duration=4, range=4,
))

# ---- Mage class skills ----
_reg_skill(SkillDef(
    "arcane_bolt", "Arcane Bolt",
    "Launch a magical bolt dealing 2.0x damage at range 4.",
    SkillType.ACTIVE, SkillTarget.SINGLE_ENEMY, HeroClass.MAGE,
    level_req=1, gold_cost=50, cooldown=4, stamina_cost=14,
    power=2.0, range=4,
))
_reg_skill(SkillDef(
    "frost_shield", "Frost Shield",
    "Create an ice barrier boosting DEF by 40% and slowing attackers for 3 ticks.",
    SkillType.ACTIVE, SkillTarget.SELF, HeroClass.MAGE,
    level_req=3, gold_cost=100, cooldown=8, stamina_cost=16,
    mastery_req="arcane_bolt", mastery_threshold=25.0,
    def_mod=0.4, duration=3,
))
_reg_skill(SkillDef(
    "mana_surge", "Mana Surge",
    "Channel arcane energy, boosting all skill power by 30% for 4 ticks.",
    SkillType.ACTIVE, SkillTarget.SELF, HeroClass.MAGE,
    level_req=5, gold_cost=200, cooldown=12, stamina_cost=22,
    mastery_req="frost_shield", mastery_threshold=25.0,
    atk_mod=0.3, duration=4,
))

# ---- Rogue class skills ----
_reg_skill(SkillDef(
    "backstab", "Backstab",
    "A precise strike dealing 2.2x damage with +15% crit chance.",
    SkillType.ACTIVE, SkillTarget.SINGLE_ENEMY, HeroClass.ROGUE,
    level_req=1, gold_cost=50, cooldown=4, stamina_cost=10,
    power=2.2, crit_mod=0.15, range=1,
))
_reg_skill(SkillDef(
    "shadowstep", "Shadowstep",
    "Vanish briefly, boosting evasion by 40% and SPD by 30% for 2 ticks.",
    SkillType.ACTIVE, SkillTarget.SELF, HeroClass.ROGUE,
    level_req=3, gold_cost=100, cooldown=7, stamina_cost=12,
    mastery_req="backstab", mastery_threshold=25.0,
    evasion_mod=0.40, spd_mod=0.3, duration=2,
))
_reg_skill(SkillDef(
    "poison_blade", "Poison Blade",
    "Coat weapon in poison, dealing damage over 4 ticks.",
    SkillType.ACTIVE, SkillTarget.SINGLE_ENEMY, HeroClass.ROGUE,
    level_req=5, gold_cost=200, cooldown=10, stamina_cost=15,
    mastery_req="shadowstep", mastery_threshold=25.0,
    power=0.5, duration=4, range=1,  # 0.5x ATK per tick for 4 ticks
))

# ---- Race skills (innate, no class required, no gold cost) ----

# Hero race skills
_reg_skill(SkillDef(
    "rally", "Rally",
    "Inspire nearby allies, boosting ATK and DEF by 10% for 3 ticks.",
    SkillType.ACTIVE, SkillTarget.AREA_ALLIES, HeroClass.NONE,
    level_req=1, gold_cost=0, cooldown=10, stamina_cost=15,
    atk_mod=0.1, def_mod=0.1, duration=3, range=3,
))
_reg_skill(SkillDef(
    "second_wind", "Second Wind",
    "When below 30% HP, recover 20% max HP instantly.",
    SkillType.ACTIVE, SkillTarget.SELF, HeroClass.NONE,
    level_req=3, gold_cost=0, cooldown=20, stamina_cost=20,
    hp_mod=0.2,
))

# Goblin race skills
_reg_skill(SkillDef(
    "ambush", "Ambush",
    "Surprise attack dealing 1.6x damage when attacking first.",
    SkillType.ACTIVE, SkillTarget.SINGLE_ENEMY, HeroClass.NONE,
    level_req=1, gold_cost=0, cooldown=5, stamina_cost=8,
    power=1.6, range=1,
))
_reg_skill(SkillDef(
    "scavenge", "Scavenge",
    "Passive: increased loot drop chance.",
    SkillType.PASSIVE, SkillTarget.SELF, HeroClass.NONE,
))

# Wolf race skills
_reg_skill(SkillDef(
    "pack_hunt", "Pack Hunt",
    "Passive: +15% ATK when allies are within 3 tiles.",
    SkillType.PASSIVE, SkillTarget.SELF, HeroClass.NONE,
    atk_mod=0.15, range=3,
))
_reg_skill(SkillDef(
    "feral_bite", "Feral Bite",
    "A vicious bite dealing 1.7x damage.",
    SkillType.ACTIVE, SkillTarget.SINGLE_ENEMY, HeroClass.NONE,
    level_req=1, gold_cost=0, cooldown=4, stamina_cost=10,
    power=1.7, range=1,
))

# Bandit race skills
_reg_skill(SkillDef(
    "quickdraw", "Quickdraw",
    "A fast first strike dealing 1.5x damage with +10% crit.",
    SkillType.ACTIVE, SkillTarget.SINGLE_ENEMY, HeroClass.NONE,
    level_req=1, gold_cost=0, cooldown=5, stamina_cost=8,
    power=1.5, crit_mod=0.10, range=1,
))

# Undead race skills
_reg_skill(SkillDef(
    "drain_life", "Drain Life",
    "Drain enemy HP, dealing 1.3x damage and healing self for 30% of damage dealt.",
    SkillType.ACTIVE, SkillTarget.SINGLE_ENEMY, HeroClass.NONE,
    level_req=1, gold_cost=0, cooldown=6, stamina_cost=12,
    power=1.3, hp_mod=0.3, range=1,
))

# Orc race skills
_reg_skill(SkillDef(
    "berserker_rage", "Berserker Rage",
    "When below 40% HP, boost ATK by 40% for 3 ticks.",
    SkillType.ACTIVE, SkillTarget.SELF, HeroClass.NONE,
    level_req=1, gold_cost=0, cooldown=8, stamina_cost=10,
    atk_mod=0.4, duration=3,
))
_reg_skill(SkillDef(
    "war_cry", "War Cry",
    "Intimidate nearby enemies, reducing their ATK by 15% for 3 ticks.",
    SkillType.ACTIVE, SkillTarget.AREA_ENEMIES, HeroClass.NONE,
    level_req=2, gold_cost=0, cooldown=10, stamina_cost=15,
    atk_mod=-0.15, duration=3, range=3,
))


# Race → default race skills mapping
RACE_SKILLS: dict[str, list[str]] = {
    "hero":           ["rally", "second_wind"],
    "goblin":         ["ambush", "scavenge"],
    "goblin_scout":   ["ambush", "scavenge"],
    "goblin_warrior": ["ambush"],
    "goblin_chief":   ["ambush", "scavenge"],
    "wolf":           ["pack_hunt", "feral_bite"],
    "dire_wolf":      ["pack_hunt", "feral_bite"],
    "alpha_wolf":     ["pack_hunt", "feral_bite"],
    "bandit":         ["quickdraw"],
    "bandit_archer":  ["quickdraw"],
    "bandit_chief":   ["quickdraw"],
    "skeleton":       ["drain_life"],
    "zombie":         ["drain_life"],
    "lich":           ["drain_life"],
    "orc":            ["berserker_rage", "war_cry"],
    "orc_warrior":    ["berserker_rage", "war_cry"],
    "orc_warlord":    ["berserker_rage", "war_cry"],
}


# Class → available class skills mapping
CLASS_SKILLS: dict[HeroClass, list[str]] = {
    HeroClass.WARRIOR: ["power_strike", "shield_wall", "battle_cry"],
    HeroClass.RANGER:  ["quick_shot", "evasive_step", "mark_prey"],
    HeroClass.MAGE:    ["arcane_bolt", "frost_shield", "mana_surge"],
    HeroClass.ROGUE:   ["backstab", "shadowstep", "poison_blade"],
    # Breakthroughs inherit parent class skills
    HeroClass.CHAMPION:    ["power_strike", "shield_wall", "battle_cry"],
    HeroClass.SHARPSHOOTER: ["quick_shot", "evasive_step", "mark_prey"],
    HeroClass.ARCHMAGE:    ["arcane_bolt", "frost_shield", "mana_surge"],
    HeroClass.ASSASSIN:    ["backstab", "shadowstep", "poison_blade"],
}


# Class building type → class mapping
CLASS_BUILDING_MAP: dict[str, HeroClass] = {
    "warrior_hall":  HeroClass.WARRIOR,
    "ranger_lodge":  HeroClass.RANGER,
    "mage_tower":    HeroClass.MAGE,
    "rogue_den":     HeroClass.ROGUE,
}


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def get_attr_value(attrs, attr_name: str) -> int:
    """Get attribute value by string name."""
    mapping = {"str": attrs.str_, "agi": attrs.agi, "vit": attrs.vit,
               "int": attrs.int_, "spi": attrs.spi, "wis": attrs.wis,
               "end": attrs.end, "per": attrs.per, "cha": attrs.cha}
    return mapping.get(attr_name, 0)


def can_breakthrough(hero_class: HeroClass, level: int, attrs) -> bool:
    """Check if an entity can breakthrough to the next class."""
    bt = BREAKTHROUGHS.get(hero_class)
    if bt is None:
        return False
    if level < bt.level_req:
        return False
    return get_attr_value(attrs, bt.attr_req) >= bt.attr_threshold


def available_class_skills(hero_class: HeroClass, level: int) -> list[str]:
    """Get skill IDs available for a class at a given level (ignores mastery)."""
    skill_ids = CLASS_SKILLS.get(hero_class, [])
    result = []
    for sid in skill_ids:
        sdef = SKILL_DEFS.get(sid)
        if sdef and level >= sdef.level_req:
            result.append(sid)
    return result


def can_learn_skill(
    sdef: SkillDef,
    level: int,
    known_skills: list[SkillInstance],
    class_mastery: float = 0.0,
) -> tuple[bool, str]:
    """Check whether a hero meets all requirements to learn a skill.

    Returns (can_learn, reason_if_not).
    """
    if level < sdef.level_req:
        return False, f"Requires level {sdef.level_req} (current: {level})"
    if sdef.mastery_req:
        prereq = None
        for si in known_skills:
            if si.skill_id == sdef.mastery_req:
                prereq = si
                break
        if prereq is None:
            prereq_def = SKILL_DEFS.get(sdef.mastery_req)
            prereq_name = prereq_def.name if prereq_def else sdef.mastery_req
            return False, f"Requires knowledge of {prereq_name}"
        if prereq.mastery < sdef.mastery_threshold:
            prereq_def = SKILL_DEFS.get(sdef.mastery_req)
            prereq_name = prereq_def.name if prereq_def else sdef.mastery_req
            return False, f"Requires {prereq_name} mastery {sdef.mastery_threshold:.0f}+ (current: {prereq.mastery:.0f})"
    return True, ""
