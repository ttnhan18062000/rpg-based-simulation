export const TILE_COLORS: Record<number, string> = {
  0: '#1a1d27', // FLOOR
  1: '#555b73', // WALL
  2: '#1e3a5f', // WATER
  3: '#2d4a3e', // TOWN
  4: '#4a2d2d', // CAMP
  5: '#2d3a4a', // SANCTUARY
  6: '#1b3a1b', // FOREST
  7: '#3a3420', // DESERT
  8: '#2a2a3a', // SWAMP
  9: '#3a3a3a', // MOUNTAIN
  10: '#5a5040', // ROAD
  11: '#4a6050', // BRIDGE
  12: '#4a4035', // RUINS
  13: '#6a3040', // DUNGEON_ENTRANCE
  14: '#8a3000', // LAVA
};

export const TILE_COLORS_DIM: Record<number, string> = {
  0: '#12141b',
  1: '#3a3e50',
  2: '#162a42',
  3: '#1f3329',
  4: '#331f1f',
  5: '#1f2833',
  6: '#132913',
  7: '#2a2517',
  8: '#1e1e2a',
  9: '#2a2a2a',
  10: '#3f3830',
  11: '#354538',
  12: '#352e25',
  13: '#4a2030',
  14: '#602000',
};

export const KIND_COLORS: Record<string, string> = {
  hero: '#4a9eff',
  goblin: '#f87171',
  goblin_scout: '#fb923c',
  goblin_warrior: '#dc2626',
  goblin_chief: '#fbbf24',
  wolf: '#a0a0a0',
  dire_wolf: '#808080',
  alpha_wolf: '#c0c0c0',
  bandit: '#e0a050',
  bandit_archer: '#d4943c',
  bandit_chief: '#f0c060',
  skeleton: '#b0b8c0',
  zombie: '#70a070',
  lich: '#c080ff',
  orc: '#60a060',
  orc_warrior: '#408040',
  orc_warlord: '#80c040',
};

export const STATE_COLORS: Record<string, string> = {
  IDLE: '#8b8fa8',
  WANDER: '#34d399',
  HUNT: '#fbbf24',
  COMBAT: '#f87171',
  FLEE: '#a78bfa',
  RETURN_TO_TOWN: '#60a5fa',
  RESTING_IN_TOWN: '#22d3ee',
  RETURN_TO_CAMP: '#f97316',
  GUARD_CAMP: '#ef4444',
  LOOTING: '#a3e635',
  ALERT: '#ff6b6b',
  VISIT_SHOP: '#38bdf8',
  VISIT_BLACKSMITH: '#f59e0b',
  VISIT_GUILD: '#818cf8',
  HARVESTING: '#7dd3a0',
  VISIT_CLASS_HALL: '#c084fc',
  VISIT_INN: '#fb923c',
};

export const TIER_NAMES = ['Basic', 'Scout', 'Warrior', 'Elite'];

export const ITEM_DISPLAY: Record<string, string> = {
  rusty_dagger: '\u2694 Rusty Dagger',
  iron_sword: '\u2694 Iron Sword',
  goblin_blade: '\u2694 Goblin Blade',
  chief_axe: '\u2694 Chief Axe',
  leather_vest: '\u{1F6E1} Leather Vest',
  chainmail: '\u{1F6E1} Chainmail',
  goblin_shield: '\u{1F6E1} Goblin Shield',
  chief_plate: '\u{1F6E1} Chief Plate',
  speed_ring: '\u{1F48D} Speed Ring',
  lucky_charm: '\u{1F48E} Lucky Charm',
  small_hp_potion: '\u2764 Small Potion',
  medium_hp_potion: '\u2764 Med Potion',
  large_hp_potion: '\u2764 Large Potion',
  wood: '\u{1FAB5} Wood',
  leather: '\u{1F9F6} Leather',
  iron_ore: '\u26CF Iron Ore',
  steel_bar: '\u2699 Steel Bar',
  enchanted_dust: '\u2728 Enchanted Dust',
  herb: '\u{1F33F} Herb',
  wild_berries: '\u{1F347} Wild Berries',
  raw_gem: '\u{1F48E} Raw Gem',
  fiber: '\u{1F9F5} Fiber',
  glowing_mushroom: '\u{1F344} Glowing Mushroom',
  dark_moss: '\u{1F343} Dark Moss',
  stone_block: '\u{1FAA8} Stone Block',
  wolf_pelt: '\u{1F43E} Wolf Pelt',
  wolf_fang: '\u{1F9B7} Wolf Fang',
  bandit_dagger: '\u{1F5E1} Bandit Dagger',
  bandit_bow: '\u{1F3F9} Bandit Bow',
  bone_shard: '\u{1F9B4} Bone Shard',
  ectoplasm: '\u{1F47B} Ectoplasm',
  orc_axe: '\u{1FA93} Orc Axe',
  orc_shield: '\u{1F6E1} Orc Shield',
};

export function itemName(id: string): string {
  return ITEM_DISPLAY[id] || id;
}

export function hpColor(ratio: number): string {
  if (ratio > 0.5) return '#34d399';
  if (ratio > 0.25) return '#fbbf24';
  return '#f87171';
}

export const CELL_SIZE = 16;

export const LOOT_COLOR = '#a3e635';

export interface ItemStats {
  name: string;
  type: 'weapon' | 'armor' | 'accessory' | 'consumable' | 'material';
  rarity: 'common' | 'uncommon' | 'rare';
  atk?: number;
  def?: number;
  spd?: number;
  maxHp?: number;
  crit?: number;
  evasion?: number;
  luck?: number;
  heal?: number;
  gold?: number;
}

export const ITEM_STATS: Record<string, ItemStats> = {
  wooden_club:       { name: 'Wooden Club',         type: 'weapon',     rarity: 'common',   atk: 2 },
  iron_sword:        { name: 'Iron Sword',          type: 'weapon',     rarity: 'common',   atk: 4 },
  steel_sword:       { name: 'Steel Sword',         type: 'weapon',     rarity: 'uncommon', atk: 6, spd: 1 },
  battle_axe:        { name: 'Battle Axe',          type: 'weapon',     rarity: 'uncommon', atk: 8, spd: -1 },
  enchanted_blade:   { name: 'Enchanted Blade',     type: 'weapon',     rarity: 'rare',     atk: 10, spd: 2, crit: 5 },
  goblin_cleaver:    { name: 'Goblin Chief Cleaver', type: 'weapon',     rarity: 'rare',     atk: 12, crit: 10 },
  leather_vest:      { name: 'Leather Vest',        type: 'armor',      rarity: 'common',   def: 2 },
  chainmail:         { name: 'Chainmail',           type: 'armor',      rarity: 'uncommon', def: 4, spd: -1 },
  iron_plate:        { name: 'Iron Plate',          type: 'armor',      rarity: 'uncommon', def: 6, spd: -2 },
  enchanted_robe:    { name: 'Enchanted Robe',      type: 'armor',      rarity: 'rare',     def: 4, spd: 2, evasion: 5 },
  goblin_guard:      { name: 'Goblin Chief Guard',  type: 'armor',      rarity: 'rare',     def: 8, evasion: 5 },
  lucky_charm:       { name: 'Lucky Charm',         type: 'accessory',  rarity: 'common',   crit: 3, luck: 3 },
  speed_ring:        { name: 'Speed Ring',          type: 'accessory',  rarity: 'uncommon', spd: 3 },
  evasion_amulet:    { name: 'Amulet of Evasion',   type: 'accessory',  rarity: 'uncommon', evasion: 8 },
  ring_of_power:     { name: 'Ring of Power',       type: 'accessory',  rarity: 'rare',     atk: 3, def: 3 },
  small_hp_potion:   { name: 'Small Health Potion', type: 'consumable', rarity: 'common',   heal: 15 },
  medium_hp_potion:  { name: 'Medium Health Potion',type: 'consumable', rarity: 'uncommon', heal: 30 },
  large_hp_potion:   { name: 'Large Health Potion', type: 'consumable', rarity: 'rare',     heal: 50 },
  gold_pouch_s:      { name: 'Small Gold Pouch',    type: 'consumable', rarity: 'common',   gold: 10 },
  gold_pouch_m:      { name: 'Gold Pouch',          type: 'consumable', rarity: 'uncommon', gold: 25 },
  gold_pouch_l:      { name: 'Large Gold Pouch',    type: 'consumable', rarity: 'rare',     gold: 50 },
  camp_treasure:     { name: 'Camp Treasure Chest', type: 'consumable', rarity: 'rare',     gold: 100 },
  wood:              { name: 'Wood',                type: 'material',   rarity: 'common' },
  leather:           { name: 'Leather',             type: 'material',   rarity: 'common' },
  iron_ore:          { name: 'Iron Ore',            type: 'material',   rarity: 'uncommon' },
  steel_bar:         { name: 'Steel Bar',           type: 'material',   rarity: 'uncommon' },
  enchanted_dust:    { name: 'Enchanted Dust',      type: 'material',   rarity: 'rare' },
  herb:              { name: 'Herb',                type: 'material',   rarity: 'common' },
  wild_berries:      { name: 'Wild Berries',        type: 'consumable', rarity: 'common',   heal: 8 },
  raw_gem:           { name: 'Raw Gem',             type: 'material',   rarity: 'uncommon' },
  fiber:             { name: 'Fiber',               type: 'material',   rarity: 'common' },
  glowing_mushroom:  { name: 'Glowing Mushroom',    type: 'material',   rarity: 'uncommon' },
  dark_moss:         { name: 'Dark Moss',           type: 'material',   rarity: 'common' },
  stone_block:       { name: 'Stone Block',         type: 'material',   rarity: 'common' },
  wolf_pelt:         { name: 'Wolf Pelt',           type: 'material',   rarity: 'common' },
  wolf_fang:         { name: 'Wolf Fang',           type: 'material',   rarity: 'uncommon' },
  bandit_dagger:     { name: 'Bandit Dagger',       type: 'weapon',     rarity: 'common',   atk: 3, spd: 2 },
  bandit_bow:        { name: 'Bandit Bow',          type: 'weapon',     rarity: 'uncommon', atk: 5, crit: 5 },
  bone_shard:        { name: 'Bone Shard',          type: 'material',   rarity: 'common' },
  ectoplasm:         { name: 'Ectoplasm',           type: 'material',   rarity: 'uncommon' },
  orc_axe:           { name: 'Orc Axe',             type: 'weapon',     rarity: 'uncommon', atk: 7, spd: -1 },
  orc_shield:        { name: 'Orc Shield',          type: 'armor',      rarity: 'uncommon', def: 5, spd: -1 },
};

export const RARITY_COLORS: Record<string, string> = {
  common: '#9ca3af',
  uncommon: '#34d399',
  rare: '#a78bfa',
};

export const RESOURCE_COLORS: Record<string, string> = {
  herb_patch: '#6ee7b7',
  timber: '#a0845c',
  berry_bush: '#e879a0',
  gem_deposit: '#c084fc',
  cactus_fiber: '#a3d977',
  sand_iron: '#d4a053',
  mushroom_grove: '#a78bfa',
  bog_iron: '#7a8070',
  dark_moss: '#5a7060',
  ore_vein: '#9ca3af',
  crystal_node: '#93c5fd',
  granite_quarry: '#78716c',
};

export const LEGEND_ITEMS = [
  { label: 'Hero', color: '#4a9eff' },
  { label: 'Goblin', color: '#f87171' },
  { label: 'Wolf', color: '#a0a0a0' },
  { label: 'Bandit', color: '#e0a050' },
  { label: 'Undead', color: '#b0b8c0' },
  { label: 'Orc', color: '#60a060' },
  { label: 'Town', color: '#2d4a3e' },
  { label: 'Forest', color: '#1b3a1b' },
  { label: 'Desert', color: '#3a3420' },
  { label: 'Swamp', color: '#2a2a3a' },
  { label: 'Mountain', color: '#3a3a3a' },
  { label: 'Camp', color: '#4a2d2d' },
  { label: 'Resource', color: '#7dd3a0' },
  { label: 'Loot', color: '#a3e635' },
  { label: 'Store', color: '#38bdf8' },
  { label: 'Blacksmith', color: '#f59e0b' },
  { label: 'Guild', color: '#818cf8' },
  { label: 'Class Hall', color: '#c084fc' },
  { label: 'Inn', color: '#fb923c' },
  { label: 'Road', color: '#5a5040' },
  { label: 'Ruins', color: '#4a4035' },
  { label: 'Dungeon', color: '#6a3040' },
];
