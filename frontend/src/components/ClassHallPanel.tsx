import { useState } from 'react';
import { X, ChevronDown, ChevronRight, Swords, Shield, Crosshair, Wand2, Sword, ArrowRight, Lock, Star } from 'lucide-react';
import type { Building } from '@/types/api';

/* ========================================================================= */
/* Static class data — mirrors backend src/core/classes.py                    */
/* ========================================================================= */

type ScalingGrade = 'E' | 'D' | 'C' | 'B' | 'A' | 'S' | 'SS' | 'SSS';

interface ClassSkill {
  skill_id: string;
  name: string;
  description: string;
  skill_type: 'active' | 'passive';
  target: string;
  level_req: number;
  gold_cost: number;
  cooldown: number;
  stamina_cost: number;
  power: number;
  duration: number;
  range: number;
  atk_mod: number;
  def_mod: number;
  spd_mod: number;
  crit_mod: number;
  evasion_mod: number;
  hp_mod: number;
}

interface BreakthroughInfo {
  from_class: string;
  to_class: string;
  level_req: number;
  attr_req: string;
  attr_threshold: number;
  talent: string;
  talent_desc: string;
  bonuses: { str: number; agi: number; vit: number; int: number; spi: number; wis: number; end: number; per: number; cha: number };
  cap_bonuses: { str: number; agi: number; vit: number; int: number; spi: number; wis: number; end: number; per: number; cha: number };
}

interface ClassData {
  id: string;
  name: string;
  description: string;
  tier: number;
  role: string;
  lore: string;
  playstyle: string;
  attr_bonuses: { str: number; agi: number; vit: number; int: number; spi: number; wis: number; end: number; per: number; cha: number };
  cap_bonuses: { str: number; agi: number; vit: number; int: number; spi: number; wis: number; end: number; per: number; cha: number };
  scaling: { str: ScalingGrade; agi: ScalingGrade; vit: ScalingGrade; int: ScalingGrade; spi: ScalingGrade; wis: ScalingGrade; end: ScalingGrade; per: ScalingGrade; cha: ScalingGrade };
  skills: ClassSkill[];
  breakthrough: BreakthroughInfo | null;
  breakthrough_class: ClassData | null;
}

const RACE_SKILLS: ClassSkill[] = [
  {
    skill_id: 'rally', name: 'Rally',
    description: 'Inspire nearby allies, boosting ATK and DEF by 10% for 3 ticks.',
    skill_type: 'active', target: 'area_allies', level_req: 1, gold_cost: 0,
    cooldown: 10, stamina_cost: 15, power: 1.0, duration: 3, range: 3,
    atk_mod: 0.1, def_mod: 0.1, spd_mod: 0, crit_mod: 0, evasion_mod: 0, hp_mod: 0,
  },
  {
    skill_id: 'second_wind', name: 'Second Wind',
    description: 'When below 30% HP, recover 20% max HP instantly.',
    skill_type: 'active', target: 'self', level_req: 3, gold_cost: 0,
    cooldown: 20, stamina_cost: 20, power: 1.0, duration: 0, range: 0,
    atk_mod: 0, def_mod: 0, spd_mod: 0, crit_mod: 0, evasion_mod: 0, hp_mod: 0.2,
  },
];

const WARRIOR_SKILLS: ClassSkill[] = [
  {
    skill_id: 'power_strike', name: 'Power Strike',
    description: 'A devastating blow dealing 1.8x damage. The Warrior channels raw strength into a single, crushing strike that can stagger even the hardiest foe.',
    skill_type: 'active', target: 'single_enemy', level_req: 1, gold_cost: 50,
    cooldown: 4, stamina_cost: 12, power: 1.8, duration: 0, range: 1,
    atk_mod: 0, def_mod: 0, spd_mod: 0, crit_mod: 0, evasion_mod: 0, hp_mod: 0,
  },
  {
    skill_id: 'shield_wall', name: 'Shield Wall',
    description: 'Brace for impact, boosting DEF by 50% for 3 ticks. The Warrior plants their feet and raises their guard, becoming a living fortress.',
    skill_type: 'active', target: 'self', level_req: 3, gold_cost: 100,
    cooldown: 8, stamina_cost: 15, power: 1.0, duration: 3, range: 0,
    atk_mod: 0, def_mod: 0.5, spd_mod: 0, crit_mod: 0, evasion_mod: 0, hp_mod: 0,
  },
  {
    skill_id: 'battle_cry', name: 'Battle Cry',
    description: 'Boost ATK of nearby allies by 20% for 3 ticks. A thunderous war shout that stirs the blood and emboldens companions within earshot.',
    skill_type: 'active', target: 'area_allies', level_req: 5, gold_cost: 200,
    cooldown: 12, stamina_cost: 20, power: 1.0, duration: 3, range: 3,
    atk_mod: 0.2, def_mod: 0, spd_mod: 0, crit_mod: 0, evasion_mod: 0, hp_mod: 0,
  },
];

const RANGER_SKILLS: ClassSkill[] = [
  {
    skill_id: 'quick_shot', name: 'Quick Shot',
    description: 'A fast ranged attack dealing 1.5x damage from up to 3 tiles away. The Ranger draws, aims, and releases in one fluid motion.',
    skill_type: 'active', target: 'single_enemy', level_req: 1, gold_cost: 50,
    cooldown: 3, stamina_cost: 8, power: 1.5, duration: 0, range: 3,
    atk_mod: 0, def_mod: 0, spd_mod: 0, crit_mod: 0, evasion_mod: 0, hp_mod: 0,
  },
  {
    skill_id: 'evasive_step', name: 'Evasive Step',
    description: 'Boost evasion by 30% for 3 ticks. A dancer\'s footwork honed by years of dodging wild beasts and enemy arrows.',
    skill_type: 'active', target: 'self', level_req: 3, gold_cost: 100,
    cooldown: 7, stamina_cost: 10, power: 1.0, duration: 3, range: 0,
    atk_mod: 0, def_mod: 0, spd_mod: 0, crit_mod: 0, evasion_mod: 0.30, hp_mod: 0,
  },
  {
    skill_id: 'mark_prey', name: 'Mark Prey',
    description: 'Mark an enemy, increasing damage taken by 25% for 4 ticks. The Ranger identifies weak points and telegraphs them to allies.',
    skill_type: 'active', target: 'single_enemy', level_req: 5, gold_cost: 200,
    cooldown: 10, stamina_cost: 15, power: 1.0, duration: 4, range: 4,
    atk_mod: 0, def_mod: -0.25, spd_mod: 0, crit_mod: 0, evasion_mod: 0, hp_mod: 0,
  },
];

const MAGE_SKILLS: ClassSkill[] = [
  {
    skill_id: 'arcane_bolt', name: 'Arcane Bolt',
    description: 'Launch a magical bolt dealing 2.0x damage at range 4. Pure arcane energy compressed into a searing projectile that bypasses physical armor.',
    skill_type: 'active', target: 'single_enemy', level_req: 1, gold_cost: 50,
    cooldown: 4, stamina_cost: 14, power: 2.0, duration: 0, range: 4,
    atk_mod: 0, def_mod: 0, spd_mod: 0, crit_mod: 0, evasion_mod: 0, hp_mod: 0,
  },
  {
    skill_id: 'frost_shield', name: 'Frost Shield',
    description: 'Create an ice barrier boosting DEF by 40% and slowing attackers for 3 ticks. Crystalline frost coalesces into a shimmering ward.',
    skill_type: 'active', target: 'self', level_req: 3, gold_cost: 100,
    cooldown: 8, stamina_cost: 16, power: 1.0, duration: 3, range: 0,
    atk_mod: 0, def_mod: 0.4, spd_mod: 0, crit_mod: 0, evasion_mod: 0, hp_mod: 0,
  },
  {
    skill_id: 'mana_surge', name: 'Mana Surge',
    description: 'Channel arcane energy, boosting all skill power by 30% for 4 ticks. The Mage opens the floodgates of their mana reserve.',
    skill_type: 'active', target: 'self', level_req: 5, gold_cost: 200,
    cooldown: 12, stamina_cost: 22, power: 1.0, duration: 4, range: 0,
    atk_mod: 0.3, def_mod: 0, spd_mod: 0, crit_mod: 0, evasion_mod: 0, hp_mod: 0,
  },
];

const ROGUE_SKILLS: ClassSkill[] = [
  {
    skill_id: 'backstab', name: 'Backstab',
    description: 'A precise strike dealing 2.2x damage with +15% crit chance. The Rogue exploits blind spots with surgical precision.',
    skill_type: 'active', target: 'single_enemy', level_req: 1, gold_cost: 50,
    cooldown: 4, stamina_cost: 10, power: 2.2, duration: 0, range: 1,
    atk_mod: 0, def_mod: 0, spd_mod: 0, crit_mod: 0.15, evasion_mod: 0, hp_mod: 0,
  },
  {
    skill_id: 'shadowstep', name: 'Shadowstep',
    description: 'Vanish briefly, boosting evasion by 40% and SPD by 30% for 2 ticks. The Rogue dissolves into shadow, reappearing behind their foe.',
    skill_type: 'active', target: 'self', level_req: 3, gold_cost: 100,
    cooldown: 7, stamina_cost: 12, power: 1.0, duration: 2, range: 0,
    atk_mod: 0, def_mod: 0, spd_mod: 0.3, crit_mod: 0, evasion_mod: 0.40, hp_mod: 0,
  },
  {
    skill_id: 'poison_blade', name: 'Poison Blade',
    description: 'Coat weapon in poison, dealing damage over 4 ticks. A venom brewed from swamp herbs that weakens even the toughest creatures.',
    skill_type: 'active', target: 'single_enemy', level_req: 5, gold_cost: 200,
    cooldown: 10, stamina_cost: 15, power: 0.5, duration: 4, range: 1,
    atk_mod: 0, def_mod: 0, spd_mod: 0, crit_mod: 0, evasion_mod: 0, hp_mod: 0,
  },
];

const TALENT_DESCRIPTIONS: Record<string, string> = {
  'Unyielding': 'When HP drops below 25%, gain +30% DEF and +20% ATK for 5 ticks. Cannot be staggered during this effect. A Champion does not fall — they dig in deeper.',
  'Precision': 'Critical strikes deal an additional 25% damage. Quick Shot range increases by 1 tile. Every arrow carries the weight of absolute certainty.',
  'Arcane Mastery': 'All skill durations extended by 1 tick. Skill cooldowns reduced by 1 tick. The weave of magic bends more readily to the Archmage\'s will.',
  'Lethal': 'Attacks against targets below 30% HP are guaranteed critical strikes. Backstab power increased to 2.8x. Death comes swiftly to those marked by an Assassin.',
};

const CLASSES: Record<string, ClassData> = {
  warrior: {
    id: 'warrior', name: 'Warrior', tier: 1, role: 'Tank / Melee DPS',
    description: 'A frontline fighter specializing in strength and vitality.',
    lore: 'Warriors are forged in the crucible of battle. They stand where others fall, trading blows with monstrous foes through sheer grit and iron will. From humble militia training to legendary feats of arms, the Warrior\'s path is one of relentless perseverance. Ancient war-songs tell of warriors who held castle gates alone \u2014 their shields dented, their blades notched, yet their spirit unbroken.',
    playstyle: 'Warriors excel at sustained melee combat. High STR scaling makes every point of Strength hit harder, while strong VIT and END scaling provide the survivability to endure prolonged fights. Best paired with heavy armor and two-handed weapons. Ideal for players who like to lead the charge and control the front line.',
    attr_bonuses: { str: 3, agi: 0, vit: 2, int: 0, spi: 0, wis: 0, end: 1, per: 0, cha: 0 },
    cap_bonuses: { str: 10, agi: 0, vit: 5, int: 0, spi: 0, wis: 0, end: 3, per: 0, cha: 0 },
    scaling: { str: 'S', agi: 'D', vit: 'A', int: 'E', spi: 'E', wis: 'D', end: 'B', per: 'D', cha: 'C' },
    skills: WARRIOR_SKILLS,
    breakthrough: {
      from_class: 'Warrior', to_class: 'Champion', level_req: 10,
      attr_req: 'STR', attr_threshold: 30, talent: 'Unyielding',
      talent_desc: TALENT_DESCRIPTIONS['Unyielding'],
      bonuses: { str: 3, agi: 0, vit: 2, int: 0, spi: 0, wis: 0, end: 0, per: 0, cha: 0 },
      cap_bonuses: { str: 10, agi: 0, vit: 5, int: 0, spi: 0, wis: 0, end: 0, per: 0, cha: 0 },
    },
    breakthrough_class: {
      id: 'champion', name: 'Champion', tier: 2, role: 'Tank / Melee DPS',
      description: 'An elite warrior who has mastered the art of war.',
      lore: 'Champions are warriors who have transcended mere skill to embody the spirit of battle itself. Their blows carry the weight of a hundred campaigns, and their presence on the field inspires allies to fight beyond their limits. The title of Champion is earned only through trials of blood and iron \u2014 where the weak perish, the Champion endures.',
      playstyle: 'Champions push Warrior strengths to the extreme. SS-rank STR scaling makes every Strength point devastatingly effective. S-rank VIT provides near-unbreakable durability. The Unyielding talent further cements their role as immovable front-liners.',
      attr_bonuses: { str: 6, agi: 0, vit: 4, int: 0, spi: 0, wis: 0, end: 2, per: 0, cha: 1 },
      cap_bonuses: { str: 20, agi: 0, vit: 10, int: 0, spi: 0, wis: 0, end: 6, per: 0, cha: 3 },
      scaling: { str: 'SS', agi: 'C', vit: 'S', int: 'E', spi: 'E', wis: 'D', end: 'A', per: 'D', cha: 'B' },
      skills: WARRIOR_SKILLS, breakthrough: null, breakthrough_class: null,
    },
  },
  ranger: {
    id: 'ranger', name: 'Ranger', tier: 1, role: 'Ranged DPS / Scout',
    description: 'A swift scout with deadly precision and keen awareness.',
    lore: 'Rangers are children of the wilds \u2014 trackers, hunters, and silent sentinels who read the land like an open book. They strike from afar with deadly accuracy, disappearing into brush before the enemy can react. The great Rangers of old could track a shadow across bare stone and pin a dragonfly\'s wing at a hundred paces.',
    playstyle: 'Rangers dominate at range with high AGI scaling boosting speed, crit, and evasion. WIS scaling enhances luck and awareness, while END keeps stamina high for sustained kiting. Equip bows and light armor for maximum mobility. Perfect for hit-and-run tactics and exploration.',
    attr_bonuses: { str: 0, agi: 3, vit: 0, int: 0, spi: 0, wis: 2, end: 1, per: 1, cha: 0 },
    cap_bonuses: { str: 0, agi: 10, vit: 0, int: 0, spi: 0, wis: 5, end: 3, per: 3, cha: 0 },
    scaling: { str: 'D', agi: 'S', vit: 'D', int: 'D', spi: 'E', wis: 'B', end: 'A', per: 'A', cha: 'D' },
    skills: RANGER_SKILLS,
    breakthrough: {
      from_class: 'Ranger', to_class: 'Sharpshooter', level_req: 10,
      attr_req: 'AGI', attr_threshold: 30, talent: 'Precision',
      talent_desc: TALENT_DESCRIPTIONS['Precision'],
      bonuses: { str: 0, agi: 3, vit: 0, int: 0, spi: 0, wis: 2, end: 0, per: 0, cha: 0 },
      cap_bonuses: { str: 0, agi: 10, vit: 0, int: 0, spi: 0, wis: 5, end: 0, per: 0, cha: 0 },
    },
    breakthrough_class: {
      id: 'sharpshooter', name: 'Sharpshooter', tier: 2, role: 'Ranged DPS / Scout',
      description: 'A legendary marksman with unmatched precision.',
      lore: 'Sharpshooters are Rangers who have achieved perfect unity between eye, hand, and bow. Every arrow they loose finds its mark with supernatural accuracy. The Precision talent grants them an almost prophetic ability to predict enemy movement.',
      playstyle: 'Sharpshooters elevate the Ranger\'s ranged dominance with SS-rank AGI scaling for devastating crit rates and evasion. S-rank END scaling ensures they never run out of stamina for kiting.',
      attr_bonuses: { str: 0, agi: 6, vit: 0, int: 0, spi: 0, wis: 4, end: 2, per: 2, cha: 0 },
      cap_bonuses: { str: 0, agi: 20, vit: 0, int: 0, spi: 0, wis: 10, end: 6, per: 6, cha: 0 },
      scaling: { str: 'D', agi: 'SS', vit: 'D', int: 'C', spi: 'E', wis: 'A', end: 'S', per: 'S', cha: 'D' },
      skills: RANGER_SKILLS, breakthrough: null, breakthrough_class: null,
    },
  },
  mage: {
    id: 'mage', name: 'Mage', tier: 1, role: 'Ranged DPS / Support',
    description: 'A scholar of arcane arts, wielding intelligence and wisdom.',
    lore: 'Mages bend the very fabric of reality through years of rigorous study and arcane experimentation. Where warriors trust steel, mages trust knowledge \u2014 and knowledge, properly applied, can shatter mountains. The great academies produce scholars who command fire, frost, and lightning.',
    playstyle: 'Mages deliver devastating ranged damage through INT scaling that amplifies skill power and XP gain. WIS scaling reduces cooldowns and boosts luck. Fragile in melee \u2014 rely on crowd control, burst damage, and positioning. Best suited for calculated, ability-focused combat.',
    attr_bonuses: { str: 0, agi: 0, vit: 1, int: 2, spi: 3, wis: 2, end: 0, per: 0, cha: 0 },
    cap_bonuses: { str: 0, agi: 0, vit: 3, int: 5, spi: 10, wis: 5, end: 0, per: 0, cha: 0 },
    scaling: { str: 'E', agi: 'D', vit: 'C', int: 'A', spi: 'S', wis: 'A', end: 'C', per: 'D', cha: 'D' },
    skills: MAGE_SKILLS,
    breakthrough: {
      from_class: 'Mage', to_class: 'Archmage', level_req: 10,
      attr_req: 'SPI', attr_threshold: 30, talent: 'Arcane Mastery',
      talent_desc: TALENT_DESCRIPTIONS['Arcane Mastery'],
      bonuses: { str: 0, agi: 0, vit: 0, int: 2, spi: 3, wis: 2, end: 0, per: 0, cha: 0 },
      cap_bonuses: { str: 0, agi: 0, vit: 0, int: 5, spi: 10, wis: 5, end: 0, per: 0, cha: 0 },
    },
    breakthrough_class: {
      id: 'archmage', name: 'Archmage', tier: 2, role: 'Ranged DPS / Support',
      description: 'A supreme mage who commands arcane forces at will.',
      lore: 'Archmages have pierced the veil between study and mastery, touching the raw source of magical power. The Arcane Mastery talent allows them to weave multiple spell effects simultaneously \u2014 a feat that would shatter a lesser caster\'s mind.',
      playstyle: 'Archmages reach SS-rank SPI scaling, making their magical attacks devastatingly powerful. S-rank WIS dramatically boosts luck and magic defense. The ultimate glass cannon \u2014 when positioned correctly, an Archmage can end battles before they begin.',
      attr_bonuses: { str: 0, agi: 0, vit: 2, int: 4, spi: 6, wis: 4, end: 0, per: 0, cha: 0 },
      cap_bonuses: { str: 0, agi: 0, vit: 6, int: 10, spi: 20, wis: 10, end: 0, per: 0, cha: 0 },
      scaling: { str: 'E', agi: 'D', vit: 'B', int: 'A', spi: 'SS', wis: 'S', end: 'B', per: 'C', cha: 'D' },
      skills: MAGE_SKILLS, breakthrough: null, breakthrough_class: null,
    },
  },
  rogue: {
    id: 'rogue', name: 'Rogue', tier: 1, role: 'Melee DPS / Assassin',
    description: 'A cunning fighter blending agility and strength for lethal strikes.',
    lore: 'Rogues thrive in the spaces between light and shadow. They are opportunists \u2014 striking when the moment is perfect, vanishing before retaliation arrives. Whether they hail from thieves\' guilds or noble spy networks, every Rogue shares an instinct for finding weakness.',
    playstyle: 'Rogues combine AGI and STR scaling for lethal burst damage. High crit rate and evasion from AGI make them slippery in combat, while B-rank STR scaling ensures their strikes hit hard. Short cooldowns and low stamina costs enable rapid skill chains. Glass cannon playstyle \u2014 dodge or die.',
    attr_bonuses: { str: 2, agi: 2, vit: 0, int: 0, spi: 0, wis: 1, end: 0, per: 0, cha: 0 },
    cap_bonuses: { str: 5, agi: 8, vit: 0, int: 0, spi: 0, wis: 3, end: 0, per: 0, cha: 0 },
    scaling: { str: 'B', agi: 'S', vit: 'D', int: 'D', spi: 'E', wis: 'C', end: 'C', per: 'B', cha: 'D' },
    skills: ROGUE_SKILLS,
    breakthrough: {
      from_class: 'Rogue', to_class: 'Assassin', level_req: 10,
      attr_req: 'AGI', attr_threshold: 25, talent: 'Lethal',
      talent_desc: TALENT_DESCRIPTIONS['Lethal'],
      bonuses: { str: 2, agi: 3, vit: 0, int: 0, spi: 0, wis: 0, end: 0, per: 0, cha: 0 },
      cap_bonuses: { str: 5, agi: 8, vit: 0, int: 0, spi: 0, wis: 0, end: 0, per: 0, cha: 0 },
    },
    breakthrough_class: {
      id: 'assassin', name: 'Assassin', tier: 2, role: 'Melee DPS / Assassin',
      description: 'A lethal shadow, striking with perfect precision.',
      lore: 'Assassins have perfected the Rogue\'s art of the unseen strike, elevating it from skill to something approaching dark poetry. They move through shadows as though the darkness itself is an ally. Kingdoms have fallen not to armies, but to a single Assassin\'s patience.',
      playstyle: 'Assassins combine SS-rank AGI with A-rank STR for the highest burst damage potential of any class. The Lethal talent provides guaranteed critical strikes under certain conditions. The ultimate single-target killer.',
      attr_bonuses: { str: 4, agi: 5, vit: 0, int: 0, spi: 0, wis: 2, end: 0, per: 1, cha: 0 },
      cap_bonuses: { str: 10, agi: 16, vit: 0, int: 0, spi: 0, wis: 6, end: 0, per: 3, cha: 0 },
      scaling: { str: 'A', agi: 'SS', vit: 'D', int: 'D', spi: 'E', wis: 'B', end: 'B', per: 'A', cha: 'D' },
      skills: ROGUE_SKILLS, breakthrough: null, breakthrough_class: null,
    },
  },
};

const CLASS_ORDER = ['warrior', 'ranger', 'mage', 'rogue'] as const;

const CLASS_COLORS: Record<string, string> = {
  warrior: '#f87171', ranger: '#34d399', mage: '#818cf8', rogue: '#fbbf24',
  champion: '#ff4444', sharpshooter: '#22c55e', archmage: '#a78bfa', assassin: '#f59e0b',
};

const CLASS_ICONS: Record<string, React.ReactNode> = {
  warrior: <Shield className="w-4 h-4" />,
  ranger: <Crosshair className="w-4 h-4" />,
  mage: <Wand2 className="w-4 h-4" />,
  rogue: <Sword className="w-4 h-4" />,
};

const GRADE_COLORS: Record<string, string> = {
  'E': '#6b7280', 'D': '#94a3b8', 'C': '#34d399', 'B': '#60a5fa',
  'A': '#fb923c', 'S': '#f87171', 'SS': '#f59e0b', 'SSS': '#ffd700',
};

const GRADE_BG: Record<string, string> = {
  'E': 'rgba(107,114,128,0.15)', 'D': 'rgba(148,163,184,0.15)', 'C': 'rgba(52,211,153,0.15)', 'B': 'rgba(96,165,250,0.15)',
  'A': 'rgba(251,146,60,0.15)', 'S': 'rgba(248,113,113,0.2)', 'SS': 'rgba(245,158,11,0.2)', 'SSS': 'rgba(255,215,0,0.25)',
};

const SCALING_MULTIPLIER: Record<string, number> = {
  'E': 0.60, 'D': 0.75, 'C': 0.90, 'B': 1.00,
  'A': 1.15, 'S': 1.30, 'SS': 1.50, 'SSS': 1.80,
};

const ATTR_LABELS = ['STR', 'AGI', 'VIT', 'INT', 'SPI', 'WIS', 'END', 'PER', 'CHA'] as const;
const ATTR_KEYS = ['str', 'agi', 'vit', 'int', 'spi', 'wis', 'end', 'per', 'cha'] as const;
const ATTR_COLORS: Record<string, string> = {
  str: '#f87171', agi: '#34d399', vit: '#fb923c', int: '#818cf8',
  spi: '#c084fc', wis: '#a78bfa', end: '#fbbf24', per: '#2dd4bf', cha: '#f472b6',
};
const ATTR_EFFECTS: Record<string, string> = {
  str: 'ATK +0.5/pt, carry weight',
  agi: 'SPD +0.4, Crit +0.4%, Eva +0.3%',
  vit: 'HP +2, DEF +0.3/pt',
  int: 'Skill power, XP gain +1%/pt, CD reduction',
  spi: 'MATK +0.5/pt, mana scaling',
  wis: 'MDEF +0.3/pt, Luck +0.3, CD reduction',
  end: 'Stamina +2, HP regen',
  per: 'Vision range, detection, loot quality',
  cha: 'Trade prices, morale, recruitment',
};

const TARGET_LABELS: Record<string, string> = {
  self: 'Self', single_enemy: 'Single Enemy', area_enemies: 'AoE Enemies',
  single_ally: 'Single Ally', area_allies: 'AoE Allies',
};

const MASTERY_TIERS = [
  { name: 'Novice', range: '0\u201324%', power: '\u2014', stamina: '\u2014', cooldown: '\u2014' },
  { name: 'Apprentice', range: '25\u201349%', power: '\u2014', stamina: '\u221210%', cooldown: '\u2014' },
  { name: 'Adept', range: '50\u201374%', power: '+20%', stamina: '\u221210%', cooldown: '\u2014' },
  { name: 'Expert', range: '75\u201399%', power: '+20%', stamina: '\u221220%', cooldown: '\u22121 tick' },
  { name: 'Master', range: '100%', power: '+35%', stamina: '\u221225%', cooldown: '\u22121 tick' },
];

/* ========================================================================= */
/* Component                                                                  */
/* ========================================================================= */

interface ClassHallPanelProps {
  building: Building;
  onClose: () => void;
}

export function ClassHallPanel({ building, onClose }: ClassHallPanelProps) {
  const [selectedClass, setSelectedClass] = useState<string>('warrior');
  const [expandedSkills, setExpandedSkills] = useState<Record<string, boolean>>({});
  const [showBreakthroughClass, setShowBreakthroughClass] = useState(false);

  const cls = CLASSES[selectedClass];
  const displayCls = showBreakthroughClass && cls.breakthrough_class ? cls.breakthrough_class : cls;
  const color = CLASS_COLORS[displayCls.id] || '#888';

  const toggleSkill = (id: string) => setExpandedSkills(prev => ({ ...prev, [id]: !prev[id] }));

  return (
    <div className="flex-1 flex flex-col overflow-hidden min-h-0">
      {/* Header */}
      <div className="p-3 border-b border-border shrink-0">
        <div className="flex items-center justify-between mb-1">
          <div className="flex items-center gap-2">
            <Swords className="w-5 h-5 text-[#c084fc]" />
            <span className="text-sm font-bold text-[#c084fc]">{building.name}</span>
          </div>
          <button onClick={onClose} className="text-text-secondary hover:text-text-primary p-0.5 cursor-pointer">
            <X className="w-4 h-4" />
          </button>
        </div>
        <p className="text-[10px] text-text-secondary leading-relaxed">
          The hall of heroes. Study the path of each class, learn their skills, and pursue mastery through breakthrough.
        </p>
      </div>

      {/* Class Tab Bar */}
      <div className="flex bg-bg-tertiary border-b border-border px-1 gap-0.5 py-1 shrink-0">
        {CLASS_ORDER.map((cid) => {
          const c = CLASSES[cid];
          const cColor = CLASS_COLORS[cid];
          return (
            <button
              key={cid}
              onClick={() => { setSelectedClass(cid); setShowBreakthroughClass(false); }}
              className={`flex-1 flex items-center justify-center gap-1 py-1.5 text-[9px] font-semibold uppercase tracking-wider
                          rounded transition-colors cursor-pointer
                          ${selectedClass === cid
                            ? 'bg-bg-secondary shadow-sm'
                            : 'text-text-secondary hover:text-text-primary hover:bg-white/[0.03]'
                          }`}
              style={selectedClass === cid ? { color: cColor } : undefined}
            >
              {CLASS_ICONS[cid]}
              {c.name}
            </button>
          );
        })}
      </div>

      {/* Scrollable Content */}
      <div className="flex-1 overflow-y-auto min-h-0">
        {/* Class Progression Tree */}
        <ProgressionTree cls={cls} showBreakthrough={showBreakthroughClass} onToggle={setShowBreakthroughClass} />

        {/* Class Overview */}
        <div className="p-3 border-b border-border">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-sm font-bold" style={{ color }}>{displayCls.name}</span>
            <span className="text-[8px] px-1.5 py-0.5 rounded-full font-bold uppercase border" style={{ color, borderColor: `${color}40` }}>
              Tier {displayCls.tier}
            </span>
            <span className="text-[9px] text-text-secondary">{displayCls.role}</span>
          </div>
          <p className="text-[10px] text-text-secondary leading-relaxed mb-2">{displayCls.description}</p>
          <p className="text-[10px] text-text-primary leading-relaxed italic">{displayCls.lore}</p>
        </div>

        {/* Playstyle */}
        <div className="p-3 border-b border-border">
          <div className="text-[10px] font-bold uppercase tracking-wider text-text-secondary mb-1.5">Playstyle</div>
          <p className="text-[10px] text-text-primary leading-relaxed">{displayCls.playstyle}</p>
        </div>

        {/* Attribute Scaling */}
        <div className="p-3 border-b border-border">
          <div className="text-[10px] font-bold uppercase tracking-wider text-text-secondary mb-2">Attribute Scaling</div>
          <div className="grid grid-cols-9 gap-1">
            {ATTR_KEYS.map((key, i) => {
              const grade = displayCls.scaling[key];
              const gradeColor = GRADE_COLORS[grade];
              const gradeBg = GRADE_BG[grade];
              const mult = SCALING_MULTIPLIER[grade];
              return (
                <div key={key} className="flex flex-col items-center gap-0.5">
                  <span className="text-[9px] font-bold uppercase" style={{ color: ATTR_COLORS[key] }}>{ATTR_LABELS[i]}</span>
                  <div
                    className="w-full py-1.5 rounded text-center text-xs font-black tracking-wide"
                    style={{ color: gradeColor, background: gradeBg }}
                  >
                    {grade}
                  </div>
                  <span className="text-[8px] text-text-secondary">{Math.round(mult * 100)}%</span>
                </div>
              );
            })}
          </div>
          <div className="mt-2 text-[9px] text-text-secondary leading-relaxed">
            Scaling determines how effectively this class benefits from each attribute.
            <span className="font-semibold" style={{ color: GRADE_COLORS['S'] }}> S</span>=130%,
            <span className="font-semibold" style={{ color: GRADE_COLORS['SS'] }}> SS</span>=150%,
            <span className="font-semibold" style={{ color: GRADE_COLORS['A'] }}> A</span>=115%,
            <span className="font-semibold" style={{ color: GRADE_COLORS['B'] }}> B</span>=100% (baseline).
          </div>
        </div>

        {/* Attribute Bonuses */}
        <div className="p-3 border-b border-border">
          <div className="text-[10px] font-bold uppercase tracking-wider text-text-secondary mb-2">Base Attribute Bonuses</div>
          <div className="grid grid-cols-2 gap-x-4 gap-y-1">
            {ATTR_KEYS.map((key, i) => {
              const bonus = displayCls.attr_bonuses[key];
              const capBonus = displayCls.cap_bonuses[key];
              if (bonus === 0 && capBonus === 0) return null;
              return (
                <div key={key} className="flex items-center justify-between text-[10px]">
                  <span className="font-semibold" style={{ color: ATTR_COLORS[key] }}>{ATTR_LABELS[i]}</span>
                  <span className="text-text-primary">
                    {bonus > 0 && <span className="text-accent-green">+{bonus}</span>}
                    {capBonus > 0 && <span className="text-text-secondary ml-1">(cap +{capBonus})</span>}
                  </span>
                </div>
              );
            })}
          </div>
          <div className="mt-1.5 text-[9px] text-text-secondary">
            Bonuses applied when this class is chosen or upon breakthrough.
          </div>
        </div>

        {/* Attribute Effect Reference */}
        <div className="p-3 border-b border-border">
          <div className="text-[10px] font-bold uppercase tracking-wider text-text-secondary mb-2">Attribute Effects</div>
          <div className="space-y-0.5">
            {ATTR_KEYS.map((key, i) => (
              <div key={key} className="flex items-center gap-2 text-[10px]">
                <span className="w-7 font-bold" style={{ color: ATTR_COLORS[key] }}>{ATTR_LABELS[i]}</span>
                <span className="text-text-secondary">{ATTR_EFFECTS[key]}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Class Skills */}
        <div className="p-3 border-b border-border">
          <div className="text-[10px] font-bold uppercase tracking-wider text-text-secondary mb-2">
            Class Skills ({displayCls.skills.length})
          </div>
          {displayCls.skills.map((sk) => (
            <SkillCard key={sk.skill_id} skill={sk} expanded={!!expandedSkills[sk.skill_id]} onToggle={() => toggleSkill(sk.skill_id)} color={color} />
          ))}
        </div>

        {/* Race Skills */}
        <div className="p-3 border-b border-border">
          <div className="text-[10px] font-bold uppercase tracking-wider text-text-secondary mb-2">
            Race Skills (Hero \u2014 Innate)
          </div>
          <div className="text-[9px] text-text-secondary mb-1.5">
            All heroes learn these skills automatically. No gold cost required.
          </div>
          {RACE_SKILLS.map((sk) => (
            <SkillCard key={sk.skill_id} skill={sk} expanded={!!expandedSkills[sk.skill_id]} onToggle={() => toggleSkill(sk.skill_id)} color="#888" />
          ))}
        </div>

        {/* Breakthrough Details */}
        {cls.breakthrough && (
          <div className="p-3 border-b border-border">
            <div className="text-[10px] font-bold uppercase tracking-wider text-text-secondary mb-2">
              Breakthrough: {cls.breakthrough.from_class} \u2192 {cls.breakthrough.to_class}
            </div>
            <div className="rounded-md border border-border/50 p-2.5 bg-bg-primary">
              <div className="flex items-center gap-2 mb-2">
                <Star className="w-4 h-4" style={{ color: CLASS_COLORS[cls.breakthrough_class?.id || ''] || color }} />
                <span className="text-xs font-bold" style={{ color: CLASS_COLORS[cls.breakthrough_class?.id || ''] || color }}>
                  {cls.breakthrough.to_class}
                </span>
              </div>

              <div className="text-[10px] font-bold text-text-secondary uppercase tracking-wider mb-1">Requirements</div>
              <div className="flex gap-3 mb-2 text-[10px]">
                <span className="text-text-primary">Level <span className="font-bold text-accent-yellow">{cls.breakthrough.level_req}+</span></span>
                <span className="text-text-primary">{cls.breakthrough.attr_req} <span className="font-bold text-accent-yellow">{'\u2265'} {cls.breakthrough.attr_threshold}</span></span>
              </div>

              <div className="text-[10px] font-bold text-text-secondary uppercase tracking-wider mb-1">Breakthrough Bonuses</div>
              <div className="flex flex-wrap gap-x-3 gap-y-0.5 mb-2">
                {ATTR_KEYS.map((key, i) => {
                  const b = cls.breakthrough!.bonuses[key];
                  const cb = cls.breakthrough!.cap_bonuses[key];
                  if (b === 0 && cb === 0) return null;
                  return (
                    <span key={key} className="text-[10px]">
                      <span className="font-semibold" style={{ color: ATTR_COLORS[key] }}>{ATTR_LABELS[i]}</span>
                      {b > 0 && <span className="text-accent-green"> +{b}</span>}
                      {cb > 0 && <span className="text-text-secondary"> (cap +{cb})</span>}
                    </span>
                  );
                })}
              </div>

              <div className="text-[10px] font-bold text-text-secondary uppercase tracking-wider mb-1">Special Talent</div>
              <div className="rounded border border-border/40 p-2 bg-bg-tertiary">
                <div className="font-bold text-[11px] mb-0.5" style={{ color: CLASS_COLORS[cls.breakthrough_class?.id || ''] || color }}>
                  {cls.breakthrough.talent}
                </div>
                <div className="text-[10px] text-text-primary leading-relaxed">{cls.breakthrough.talent_desc}</div>
              </div>
            </div>
          </div>
        )}

        {/* Mastery Tier Reference */}
        <div className="p-3 border-b border-border">
          <div className="text-[10px] font-bold uppercase tracking-wider text-text-secondary mb-2">Skill Mastery Tiers</div>
          <div className="text-[9px] text-text-secondary mb-2">
            Using skills builds mastery. Higher mastery tiers unlock power bonuses, stamina reductions, and cooldown improvements.
          </div>
          <table className="w-full text-[9px]">
            <thead>
              <tr className="text-text-secondary uppercase">
                <th className="text-left py-0.5 font-bold">Tier</th>
                <th className="text-left py-0.5 font-bold">Mastery</th>
                <th className="text-center py-0.5 font-bold">Power</th>
                <th className="text-center py-0.5 font-bold">Stamina</th>
                <th className="text-center py-0.5 font-bold">CD</th>
              </tr>
            </thead>
            <tbody>
              {MASTERY_TIERS.map((t, i) => {
                const tierColors = ['#6b7280', '#60a5fa', '#34d399', '#fbbf24', '#f87171'];
                return (
                  <tr key={i} className="border-t border-border/30">
                    <td className="py-1 font-semibold" style={{ color: tierColors[i] }}>{t.name}</td>
                    <td className="py-1 text-text-secondary">{t.range}</td>
                    <td className="py-1 text-center text-text-primary">{t.power}</td>
                    <td className="py-1 text-center text-text-primary">{t.stamina}</td>
                    <td className="py-1 text-center text-text-primary">{t.cooldown}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Footer */}
        <div className="p-3 text-[9px] text-text-secondary leading-relaxed">
          Heroes visit the Class Hall to learn new class skills (costs gold) and attempt breakthroughs when they meet the level and attribute requirements.
          Breakthrough classes inherit all skills from the base class and gain improved attribute scaling.
        </div>
      </div>
    </div>
  );
}

/* ========================================================================= */
/* Progression Tree                                                           */
/* ========================================================================= */

function ProgressionTree({ cls, showBreakthrough, onToggle }: {
  cls: ClassData;
  showBreakthrough: boolean;
  onToggle: (v: boolean) => void;
}) {
  const bt = cls.breakthrough_class;
  const baseColor = CLASS_COLORS[cls.id];
  const btColor = bt ? CLASS_COLORS[bt.id] || '#888' : '#888';

  return (
    <div className="p-3 border-b border-border">
      <div className="text-[10px] font-bold uppercase tracking-wider text-text-secondary mb-2">Class Progression</div>
      <div className="flex items-center gap-1.5">
        {/* Base class node */}
        <button
          onClick={() => onToggle(false)}
          className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-md border text-[10px] font-bold transition-all cursor-pointer
                      ${!showBreakthrough ? 'shadow-md' : 'opacity-70 hover:opacity-100'}`}
          style={{
            color: baseColor,
            borderColor: !showBreakthrough ? baseColor : `${baseColor}40`,
            background: !showBreakthrough ? `${baseColor}15` : 'transparent',
          }}
        >
          {CLASS_ICONS[cls.id]}
          {cls.name}
          <span className="text-[8px] text-text-secondary font-normal">Lv1</span>
        </button>

        {/* Arrow */}
        <ArrowRight className="w-3.5 h-3.5 text-text-secondary shrink-0" />

        {/* Breakthrough class node */}
        {bt ? (
          <button
            onClick={() => onToggle(true)}
            className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-md border text-[10px] font-bold transition-all cursor-pointer
                        ${showBreakthrough ? 'shadow-md' : 'opacity-70 hover:opacity-100'}`}
            style={{
              color: btColor,
              borderColor: showBreakthrough ? btColor : `${btColor}40`,
              background: showBreakthrough ? `${btColor}15` : 'transparent',
            }}
          >
            <Star className="w-3.5 h-3.5" />
            {bt.name}
            <span className="text-[8px] text-text-secondary font-normal">Lv{cls.breakthrough?.level_req || 10}+</span>
          </button>
        ) : (
          <span className="flex items-center gap-1 px-2.5 py-1.5 rounded-md border border-border/30 text-[10px] text-text-secondary">
            <Lock className="w-3 h-3" /> ???
          </span>
        )}

        {/* Future tier 3 (locked) */}
        <ArrowRight className="w-3.5 h-3.5 text-text-secondary/40 shrink-0" />
        <span className="flex items-center gap-1 px-2.5 py-1.5 rounded-md border border-border/20 text-[10px] text-text-secondary/40">
          <Lock className="w-3 h-3" /> Transcendence
        </span>
      </div>
    </div>
  );
}

/* ========================================================================= */
/* Skill Card                                                                 */
/* ========================================================================= */

function SkillCard({ skill: sk, expanded, onToggle, color }: {
  skill: ClassSkill; expanded: boolean; onToggle: () => void; color: string;
}) {
  const isPassive = sk.skill_type === 'passive';

  return (
    <div className="rounded-md border border-border/40 mb-1.5 overflow-hidden">
      {/* Skill header (always visible) */}
      <button
        onClick={onToggle}
        className="w-full flex items-center gap-2 p-2 text-left cursor-pointer hover:bg-white/[0.02] transition-colors"
      >
        {expanded
          ? <ChevronDown className="w-3 h-3 text-text-secondary shrink-0" />
          : <ChevronRight className="w-3 h-3 text-text-secondary shrink-0" />
        }
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5">
            <span className="text-[11px] font-bold text-text-primary">{sk.name}</span>
            {isPassive && <span className="text-[7px] px-1 py-px rounded bg-bg-tertiary text-text-secondary uppercase font-bold">passive</span>}
            {!isPassive && <span className="text-[7px] px-1 py-px rounded uppercase font-bold" style={{ color, background: `${color}15` }}>{TARGET_LABELS[sk.target] || sk.target}</span>}
          </div>
          <div className="text-[9px] text-text-secondary mt-0.5 flex gap-2">
            <span>Lv {sk.level_req}</span>
            {sk.gold_cost > 0 && <span className="text-accent-yellow">{sk.gold_cost}g</span>}
            {!isPassive && <span>CD {sk.cooldown}</span>}
            {!isPassive && <span>{sk.stamina_cost} sta</span>}
            {!isPassive && sk.power !== 1.0 && <span className="text-accent-red">{sk.power}x</span>}
          </div>
        </div>
      </button>

      {/* Expanded details */}
      {expanded && (
        <div className="px-3 pb-2.5 border-t border-border/30">
          <p className="text-[10px] text-text-primary leading-relaxed mt-2 mb-2">{sk.description}</p>

          <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-[9px]">
            <DetailRow label="Type" value={isPassive ? 'Passive' : 'Active'} />
            <DetailRow label="Target" value={TARGET_LABELS[sk.target] || sk.target} />
            <DetailRow label="Level Req" value={`${sk.level_req}`} />
            <DetailRow label="Gold Cost" value={sk.gold_cost > 0 ? `${sk.gold_cost}g` : 'Free'} valueColor={sk.gold_cost > 0 ? '#fbbf24' : '#34d399'} />
            {!isPassive && <DetailRow label="Cooldown" value={`${sk.cooldown} ticks`} />}
            {!isPassive && <DetailRow label="Stamina" value={`${sk.stamina_cost}`} />}
            {!isPassive && sk.power !== 1.0 && <DetailRow label="Power" value={`${sk.power}x`} valueColor="#f87171" />}
            {sk.range > 0 && <DetailRow label="Range" value={`${sk.range} tiles`} />}
            {sk.duration > 0 && <DetailRow label="Duration" value={`${sk.duration} ticks`} />}
          </div>

          {/* Modifiers */}
          {(sk.atk_mod !== 0 || sk.def_mod !== 0 || sk.spd_mod !== 0 || sk.crit_mod !== 0 || sk.evasion_mod !== 0 || sk.hp_mod !== 0) && (
            <div className="mt-2">
              <div className="text-[9px] font-bold text-text-secondary uppercase mb-0.5">Modifiers</div>
              <div className="flex flex-wrap gap-1.5 text-[9px]">
                {sk.atk_mod !== 0 && <ModBadge label="ATK" value={sk.atk_mod} />}
                {sk.def_mod !== 0 && <ModBadge label="DEF" value={sk.def_mod} />}
                {sk.spd_mod !== 0 && <ModBadge label="SPD" value={sk.spd_mod} />}
                {sk.crit_mod !== 0 && <ModBadge label="CRIT" value={sk.crit_mod} />}
                {sk.evasion_mod !== 0 && <ModBadge label="EVA" value={sk.evasion_mod} />}
                {sk.hp_mod !== 0 && <ModBadge label="HP" value={sk.hp_mod} />}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function DetailRow({ label, value, valueColor }: { label: string; value: string; valueColor?: string }) {
  return (
    <div className="flex justify-between">
      <span className="text-text-secondary">{label}</span>
      <span className="font-semibold" style={valueColor ? { color: valueColor } : undefined}>{value}</span>
    </div>
  );
}

function ModBadge({ label, value }: { label: string; value: number }) {
  const isPositive = value > 0;
  const pct = Math.round(value * 100);
  return (
    <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${isPositive ? 'text-accent-green bg-accent-green/10' : 'text-accent-red bg-accent-red/10'}`}>
      {label} {isPositive ? '+' : ''}{pct}%
    </span>
  );
}
