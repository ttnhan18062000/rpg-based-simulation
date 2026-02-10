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

export function hpColor(ratio: number): string {
  if (ratio > 0.5) return '#34d399';
  if (ratio > 0.25) return '#fbbf24';
  return '#f87171';
}

export const CELL_SIZE = 16;

export const LOOT_COLOR = '#a3e635';

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
