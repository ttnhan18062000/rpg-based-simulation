export interface EntityMemoryEntry {
  id: number;
  x: number;
  y: number;
  kind: string;
  hp: number;
  max_hp: number;
  atk: number;
  level: number;
  tick: number;
  visible: boolean;
}

export interface EntityAttributes {
  str: number;
  agi: number;
  vit: number;
  int: number;
  wis: number;
  end: number;
  // Training progression (0.0 to 1.0 fractional toward next point)
  str_frac: number;
  agi_frac: number;
  vit_frac: number;
  int_frac: number;
  wis_frac: number;
  end_frac: number;
}

export interface EntityAttributeCaps {
  str_cap: number;
  agi_cap: number;
  vit_cap: number;
  int_cap: number;
  wis_cap: number;
  end_cap: number;
}

export interface EntitySkill {
  skill_id: string;
  name: string;
  cooldown_remaining: number;
  mastery: number;
  times_used: number;
  skill_type: string;
  target: string;
  stamina_cost: number;
  cooldown: number;
  power: number;
  description: string;
}

export interface Entity {
  id: number;
  kind: string;
  x: number;
  y: number;
  hp: number;
  max_hp: number;
  atk: number;
  def: number;
  spd: number;
  luck: number;
  crit_rate: number;
  evasion: number;
  level: number;
  xp: number;
  xp_to_next: number;
  gold: number;
  tier: number;
  faction: string;
  state: string;
  weapon: string | null;
  armor: string | null;
  accessory: string | null;
  inventory_count: number;
  inventory_items: string[];
  vision_range: number;
  terrain_memory: Record<string, number>;
  entity_memory: EntityMemoryEntry[];
  goals: string[];
  loot_progress: number;
  loot_duration: number;
  known_recipes: string[];
  craft_target: string | null;
  // RPG fields
  stamina: number;
  max_stamina: number;
  hero_class: string;
  class_mastery: number;
  attributes: EntityAttributes | null;
  attribute_caps: EntityAttributeCaps | null;
  skills: EntitySkill[];
  active_effects: EntityEffect[];
  quests: EntityQuest[];
}

export interface EntityEffect {
  effect_type: string;
  source: string;
  remaining_ticks: number;
  atk_mult: number;
  def_mult: number;
  spd_mult: number;
}

export interface EntityQuest {
  quest_id: string;
  quest_type: string;
  title: string;
  description: string;
  target_kind: string;
  target_x: number | null;
  target_y: number | null;
  target_count: number;
  progress: number;
  completed: boolean;
  gold_reward: number;
  xp_reward: number;
}

export interface Building {
  building_id: string;
  name: string;
  x: number;
  y: number;
  building_type: string;
}

export interface GroundItem {
  x: number;
  y: number;
  items: string[];
}

export interface ResourceNode {
  node_id: number;
  resource_type: string;
  name: string;
  x: number;
  y: number;
  terrain: number;
  yields_item: string;
  remaining: number;
  max_harvests: number;
  is_available: boolean;
  harvest_ticks: number;
}

export interface GameEvent {
  tick: number;
  category: string;
  message: string;
}

export interface WorldState {
  tick: number;
  alive_count: number;
  entities: Entity[];
  events: GameEvent[];
  ground_items: GroundItem[];
  buildings: Building[];
  resource_nodes: ResourceNode[];
}

export interface SimulationStats {
  tick: number;
  alive_count: number;
  total_spawned: number;
  total_deaths: number;
  running: boolean;
  paused: boolean;
}

export interface MapData {
  width: number;
  height: number;
  grid: number[][];
}

export interface SimulationConfig {
  world_seed: number;
  grid_width: number;
  grid_height: number;
  max_ticks: number;
  num_workers: number;
  initial_entity_count: number;
  generator_spawn_interval: number;
  generator_max_entities: number;
  vision_range: number;
  flee_hp_threshold: number;
  tick_rate: number;
}
