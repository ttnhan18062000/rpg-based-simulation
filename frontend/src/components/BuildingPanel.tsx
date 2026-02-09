import { X, Store, Hammer, Shield } from 'lucide-react';
import type { Building } from '@/types/api';
import { itemName, ITEM_STATS, RARITY_COLORS } from '@/constants/colors';

interface BuildingPanelProps {
  building: Building;
  onClose: () => void;
}

// Shop inventory (mirrors backend SHOP_INVENTORY)
const SHOP_ITEMS: { item_id: string; buy_price: number }[] = [
  { item_id: 'small_hp_potion', buy_price: 15 },
  { item_id: 'medium_hp_potion', buy_price: 40 },
  { item_id: 'large_hp_potion', buy_price: 80 },
  { item_id: 'wooden_club', buy_price: 20 },
  { item_id: 'iron_sword', buy_price: 50 },
  { item_id: 'leather_vest', buy_price: 25 },
  { item_id: 'chainmail', buy_price: 60 },
  { item_id: 'lucky_charm', buy_price: 30 },
  { item_id: 'speed_ring', buy_price: 55 },
];

// Recipes (mirrors backend RECIPES)
const RECIPES: {
  recipe_id: string;
  output_item: string;
  gold_cost: number;
  materials: Record<string, number>;
  description: string;
}[] = [
  { recipe_id: 'craft_steel_sword', output_item: 'steel_sword', gold_cost: 60, materials: { iron_ore: 2, wood: 1 }, description: 'A well-forged steel blade with improved balance.' },
  { recipe_id: 'craft_battle_axe', output_item: 'battle_axe', gold_cost: 90, materials: { iron_ore: 3, steel_bar: 1 }, description: 'A heavy battle axe that hits hard but swings slow.' },
  { recipe_id: 'craft_enchanted_blade', output_item: 'enchanted_blade', gold_cost: 200, materials: { steel_bar: 2, enchanted_dust: 2 }, description: 'A blade infused with magical energy.' },
  { recipe_id: 'craft_iron_plate', output_item: 'iron_plate', gold_cost: 70, materials: { iron_ore: 3, leather: 1 }, description: 'Heavy iron plate armor.' },
  { recipe_id: 'craft_enchanted_robe', output_item: 'enchanted_robe', gold_cost: 150, materials: { leather: 2, enchanted_dust: 1 }, description: 'A light robe enchanted for agility.' },
  { recipe_id: 'craft_ring_of_power', output_item: 'ring_of_power', gold_cost: 120, materials: { iron_ore: 1, enchanted_dust: 1 }, description: 'A ring that amplifies attack and defense.' },
  { recipe_id: 'craft_evasion_amulet', output_item: 'evasion_amulet', gold_cost: 80, materials: { leather: 2, wood: 1 }, description: 'An amulet for enhanced agility.' },
];

// Material hints (mirrors backend MATERIAL_HINTS)
const MATERIAL_HINTS: Record<string, string> = {
  wood: 'Dropped by basic goblins in the wild.',
  leather: 'Skinned from goblins and goblin scouts.',
  iron_ore: 'Found on goblin warriors and in camp raids.',
  steel_bar: 'Rare drop from goblin warriors.',
  enchanted_dust: 'Harvested from elite goblins and chiefs. Very rare.',
};

const BUILDING_ICONS: Record<string, React.ReactNode> = {
  store: <Store className="w-5 h-5 text-[#38bdf8]" />,
  blacksmith: <Hammer className="w-5 h-5 text-[#f59e0b]" />,
  guild: <Shield className="w-5 h-5 text-[#818cf8]" />,
};

const BUILDING_COLORS: Record<string, string> = {
  store: '#38bdf8',
  blacksmith: '#f59e0b',
  guild: '#818cf8',
};

export function BuildingPanel({ building, onClose }: BuildingPanelProps) {
  return (
    <div className="flex-1 overflow-y-auto min-h-0">
      {/* Header */}
      <div className="p-3 border-b border-border">
        <div className="flex items-center justify-between mb-1">
          <div className="flex items-center gap-2">
            {BUILDING_ICONS[building.building_type]}
            <span className="text-sm font-bold" style={{ color: BUILDING_COLORS[building.building_type] }}>
              {building.name}
            </span>
          </div>
          <button onClick={onClose} className="text-text-secondary hover:text-text-primary p-0.5 cursor-pointer">
            <X className="w-4 h-4" />
          </button>
        </div>
        <span className="text-[11px] text-text-secondary">
          Position: ({building.x}, {building.y})
        </span>
      </div>

      {/* Content based on building type */}
      {building.building_type === 'store' && <StoreContent />}
      {building.building_type === 'blacksmith' && <BlacksmithContent />}
      {building.building_type === 'guild' && <GuildContent />}
    </div>
  );
}

function StoreContent() {
  return (
    <div className="p-3">
      <div className="text-[10px] font-bold uppercase tracking-wider text-text-secondary mb-2">
        Items for Sale
      </div>
      <div className="text-[11px] text-text-secondary mb-3">
        Heroes sell unused items here and buy upgrades when they have enough gold.
      </div>
      {SHOP_ITEMS.map((si) => {
        const stats = ITEM_STATS[si.item_id];
        const rarityColor = stats ? RARITY_COLORS[stats.rarity] || '#9ca3af' : '#9ca3af';
        return (
          <div key={si.item_id} className="flex items-center justify-between py-1.5 border-b border-border/50 last:border-0">
            <div>
              <span className="text-xs font-semibold" style={{ color: rarityColor }}>
                {itemName(si.item_id)}
              </span>
              {stats && (
                <div className="text-[10px] text-text-secondary mt-0.5 flex gap-2">
                  <span className="capitalize">{stats.type}</span>
                  {stats.atk ? <span className="text-accent-red">+{stats.atk} ATK</span> : null}
                  {stats.def ? <span className="text-accent-blue">+{stats.def} DEF</span> : null}
                  {stats.heal ? <span className="text-accent-green">Heals {stats.heal}</span> : null}
                </div>
              )}
            </div>
            <span className="text-xs font-bold text-accent-yellow">{si.buy_price}g</span>
          </div>
        );
      })}
      <div className="mt-3 text-[10px] font-bold uppercase tracking-wider text-text-secondary mb-1">
        Sell Prices
      </div>
      <div className="text-[11px] text-text-secondary space-y-0.5">
        <div><span style={{ color: RARITY_COLORS.common }}>Common</span>: 5g</div>
        <div><span style={{ color: RARITY_COLORS.uncommon }}>Uncommon</span>: 15g</div>
        <div><span style={{ color: RARITY_COLORS.rare }}>Rare</span>: 40g</div>
      </div>
    </div>
  );
}

function BlacksmithContent() {
  return (
    <div className="p-3">
      <div className="text-[10px] font-bold uppercase tracking-wider text-text-secondary mb-2">
        Crafting Recipes
      </div>
      <div className="text-[11px] text-text-secondary mb-3">
        Heroes visit to learn recipes, then gather materials and gold to craft powerful items.
      </div>
      {RECIPES.map((recipe) => {
        const stats = ITEM_STATS[recipe.output_item];
        const rarityColor = stats ? RARITY_COLORS[stats.rarity] || '#9ca3af' : '#9ca3af';
        return (
          <div key={recipe.recipe_id} className="mb-3 p-2 rounded border border-border bg-bg-primary">
            <div className="font-semibold text-xs" style={{ color: rarityColor }}>
              {itemName(recipe.output_item)}
            </div>
            <div className="text-[10px] text-text-secondary mt-0.5">{recipe.description}</div>
            <div className="mt-1.5 flex flex-wrap gap-x-3 gap-y-0.5 text-[10px]">
              <span className="text-accent-yellow font-semibold">{recipe.gold_cost}g</span>
              {Object.entries(recipe.materials).map(([mat, qty]) => (
                <span key={mat} className="text-text-primary">
                  {qty}× {itemName(mat)}
                </span>
              ))}
            </div>
            {stats && (
              <div className="mt-1 flex gap-2 text-[10px]">
                {stats.atk ? <span className="text-accent-red">+{stats.atk} ATK</span> : null}
                {stats.def ? <span className="text-accent-blue">+{stats.def} DEF</span> : null}
                {stats.spd ? <span className="text-accent-green">{stats.spd > 0 ? '+' : ''}{stats.spd} SPD</span> : null}
                {stats.crit ? <span className="text-accent-yellow">+{stats.crit}% CRIT</span> : null}
                {stats.evasion ? <span className="text-accent-purple">+{stats.evasion}% EVA</span> : null}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

function GuildContent() {
  return (
    <div className="p-3">
      <div className="text-[10px] font-bold uppercase tracking-wider text-text-secondary mb-2">
        Adventurer's Guild
      </div>
      <div className="text-[11px] text-text-secondary mb-3">
        Heroes visit the guild to learn about enemy camp locations and where to find crafting materials.
      </div>

      <div className="text-[10px] font-bold uppercase tracking-wider text-text-secondary mb-2 mt-4">
        Services
      </div>
      <div className="space-y-1.5 text-[11px]">
        <div className="p-2 rounded border border-border bg-bg-primary">
          <div className="font-semibold text-accent-red text-xs">Camp Intel</div>
          <div className="text-text-secondary text-[10px] mt-0.5">
            Reveals all goblin camp locations on the hero's terrain memory map.
          </div>
        </div>
        <div className="p-2 rounded border border-border bg-bg-primary">
          <div className="font-semibold text-accent-yellow text-xs">Material Hints</div>
          <div className="text-text-secondary text-[10px] mt-0.5">
            Provides tips on where to find crafting materials for the hero's current craft target.
          </div>
        </div>
      </div>

      <div className="text-[10px] font-bold uppercase tracking-wider text-text-secondary mb-2 mt-4">
        Material Sources
      </div>
      {Object.entries(MATERIAL_HINTS).map(([mat, hint]) => {
        const stats = ITEM_STATS[mat];
        const rarityColor = stats ? RARITY_COLORS[stats.rarity] || '#9ca3af' : '#9ca3af';
        return (
          <div key={mat} className="py-1 border-b border-border/50 last:border-0">
            <span className="text-xs font-semibold" style={{ color: rarityColor }}>
              {itemName(mat)}
            </span>
            <div className="text-[10px] text-text-secondary">{hint}</div>
          </div>
        );
      })}
    </div>
  );
}
