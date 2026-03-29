// TypeScript types matching backend /api/v1/metadata/* responses.
// This is the ONLY place metadata shapes are defined in the frontend.

// --- /metadata/enums ---

export interface EnumEntry {
  id: number;
  name: string;
  description: string;
}

export interface MaterialEntry {
  id: number;
  name: string;
  walkable: boolean;
}

export interface FactionEntry {
  id: number;
  name: string;
}

export interface FactionRelationEntry {
  faction_a: number;
  faction_b: number;
  relation: string;
}

export interface EntityKindEntry {
  kind: string;
  faction: string;
}

export interface EnumsData {
  materials: MaterialEntry[];
  ai_states: EnumEntry[];
  tiers: EnumEntry[];
  rarities: EnumEntry[];
  item_types: EnumEntry[];
  damage_types: EnumEntry[];
  elements: EnumEntry[];
  entity_roles: EnumEntry[];
  factions: FactionEntry[];
  faction_relations: FactionRelationEntry[];
  entity_kinds: EntityKindEntry[];
}

// --- /metadata/items ---

export interface ItemEntry {
  item_id: string;
  name: string;
  item_type: string;
  rarity: string;
  weight: number;
  atk_bonus: number;
  def_bonus: number;
  spd_bonus: number;
  max_hp_bonus: number;
  crit_rate_bonus: number;
  evasion_bonus: number;
  luck_bonus: number;
  matk_bonus: number;
  mdef_bonus: number;
  damage_type: string;
  element: string;
  heal_amount: number;
  mana_restore: number;
  gold_value: number;
  sell_value: number;
}

export interface ItemsData {
  items: ItemEntry[];
}

// --- /metadata/classes ---

export interface AttrBonuses {
  [key: string]: number;
  str: number;
  agi: number;
  vit: number;
  int: number;
  spi: number;
  wis: number;
  end: number;
  per: number;
  cha: number;
}

export interface AttrScaling {
  [key: string]: string;
  str: string;
  agi: string;
  vit: string;
  int: string;
  spi: string;
  wis: string;
  end: string;
  per: string;
  cha: string;
}

export interface SkillDefEntry {
  skill_id: string;
  name: string;
  description: string;
  skill_type: string;
  target: string;
  class_req: string;
  level_req: number;
  gold_cost: number;
  cooldown: number;
  stamina_cost: number;
  power: number;
  duration: number;
  range: number;
  mastery_req: string;
  mastery_threshold: number;
  atk_mod: number;
  def_mod: number;
  spd_mod: number;
  crit_mod: number;
  evasion_mod: number;
  hp_mod: number;
  damage_type: string;
}

export interface BreakthroughEntry {
  from_class: string;
  to_class: string;
  level_req: number;
  attr_req: string;
  attr_threshold: number;
  talent: string;
  bonuses: AttrBonuses;
  cap_bonuses: AttrBonuses;
}

export interface ClassEntry {
  id: string;
  name: string;
  description: string;
  tier: number;
  role: string;
  lore: string;
  playstyle: string;
  attr_bonuses: AttrBonuses;
  cap_bonuses: AttrBonuses;
  scaling: AttrScaling;
  skill_ids: string[];
  breakthrough: BreakthroughEntry | null;
}

export interface ScalingGradeEntry {
  grade: string;
  multiplier: number;
}

export interface MasteryTierEntry {
  name: string;
  min_mastery: number;
  power_bonus: string;
  stamina_reduction: string;
  cooldown_reduction: string;
}

export interface ClassesData {
  classes: ClassEntry[];
  skills: SkillDefEntry[];
  race_skills: Record<string, string[]>;
  scaling_grades: ScalingGradeEntry[];
  mastery_tiers: MasteryTierEntry[];
  skill_targets: EnumEntry[];
}

// --- /metadata/traits ---

export interface TraitEntry {
  trait_type: number;
  name: string;
  description: string;
}

export interface TraitsData {
  traits: TraitEntry[];
}

// --- /metadata/attributes ---

export interface AttributeDefEntry {
  key: string;
  label: string;
  description: string;
}

export interface AttributesData {
  attributes: AttributeDefEntry[];
}

// --- /metadata/buildings ---

export interface BuildingTypeEntry {
  building_type: string;
  name: string;
  description: string;
}

export interface BuildingsData {
  building_types: BuildingTypeEntry[];
}

// --- /metadata/resources ---

export interface ResourceTypeEntry {
  resource_type: string;
  name: string;
  terrain: string;
  yields_item: string;
  max_harvests: number;
  respawn_cooldown: number;
  harvest_ticks: number;
}

export interface ResourcesData {
  resource_types: ResourceTypeEntry[];
}

// --- /metadata/recipes ---

export interface RecipeEntry {
  recipe_id: string;
  output_item: string;
  output_name: string;
  gold_cost: number;
  materials: Record<string, number>;
}

export interface RecipesData {
  recipes: RecipeEntry[];
}

// --- Aggregated metadata ---

export interface GameMetadata {
  enums: EnumsData;
  items: ItemsData;
  classes: ClassesData;
  traits: TraitsData;
  attributes: AttributesData;
  buildings: BuildingsData;
  resources: ResourcesData;
  recipes: RecipesData;
  // Derived lookup maps (built on load)
  itemMap: Record<string, ItemEntry>;
  traitMap: Record<number, TraitEntry>;
  skillMap: Record<string, SkillDefEntry>;
  classMap: Record<string, ClassEntry>;
  aiStateMap: Record<string, EnumEntry>;
  buildingTypeMap: Record<string, BuildingTypeEntry>;
  attrKeys: string[];
  attrLabels: string[];
}
