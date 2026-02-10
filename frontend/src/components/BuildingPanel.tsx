import { X, Store, Hammer, Shield, Bed, Home } from 'lucide-react';
import type { Building } from '@/types/api';
import { RARITY_COLORS } from '@/constants/colors';
import { useMetadata } from '@/contexts/MetadataContext';
import { ClassHallPanel } from './ClassHallPanel';

interface BuildingPanelProps {
  building: Building;
  onClose: () => void;
}

const BUILDING_ICONS: Record<string, React.ReactNode> = {
  store: <Store className="w-5 h-5 text-[#38bdf8]" />,
  blacksmith: <Hammer className="w-5 h-5 text-[#f59e0b]" />,
  guild: <Shield className="w-5 h-5 text-[#818cf8]" />,
  inn: <Bed className="w-5 h-5 text-[#fb923c]" />,
  hero_house: <Home className="w-5 h-5 text-[#34d399]" />,
};

const BUILDING_COLORS: Record<string, string> = {
  store: '#38bdf8',
  blacksmith: '#f59e0b',
  guild: '#818cf8',
  inn: '#fb923c',
  hero_house: '#34d399',
};

export function BuildingPanel({ building, onClose }: BuildingPanelProps) {
  // Class Hall gets its own dedicated panel
  if (building.building_type === 'class_hall') {
    return <ClassHallPanel building={building} onClose={onClose} />;
  }

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
      {building.building_type === 'inn' && <InnContent />}
      {building.building_type === 'hero_house' && <HeroHouseContent building={building} />}
    </div>
  );
}

function StoreContent() {
  const { items } = useMetadata();
  // Show buyable items (non-material, non-zero gold_value)
  const shopItems = items.items.filter(it => it.gold_value > 0 && it.item_type !== 'material');

  return (
    <div className="p-3">
      <div className="text-[10px] font-bold uppercase tracking-wider text-text-secondary mb-2">
        Items for Sale
      </div>
      <div className="text-[11px] text-text-secondary mb-3">
        Heroes sell unused items here and buy upgrades when they have enough gold.
      </div>
      {shopItems.map((it) => {
        const rarityColor = RARITY_COLORS[it.rarity] || '#9ca3af';
        return (
          <div key={it.item_id} className="flex items-center justify-between py-1.5 border-b border-border/50 last:border-0">
            <div>
              <span className="text-xs font-semibold" style={{ color: rarityColor }}>
                {it.name}
              </span>
              <div className="text-[10px] text-text-secondary mt-0.5 flex gap-2">
                <span className="capitalize">{it.item_type}</span>
                {it.atk_bonus ? <span className="text-accent-red">+{it.atk_bonus} ATK</span> : null}
                {it.def_bonus ? <span className="text-accent-blue">+{it.def_bonus} DEF</span> : null}
                {it.heal_amount ? <span className="text-accent-green">Heals {it.heal_amount}</span> : null}
              </div>
            </div>
            <span className="text-xs font-bold text-accent-yellow">{it.gold_value}g</span>
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
  const { itemMap, recipes } = useMetadata();

  return (
    <div className="p-3">
      <div className="text-[10px] font-bold uppercase tracking-wider text-text-secondary mb-2">
        Crafting Recipes
      </div>
      <div className="text-[11px] text-text-secondary mb-3">
        Heroes visit to learn recipes, then gather materials and gold to craft powerful items.
      </div>
      {recipes.recipes.map((recipe) => {
        const outItem = itemMap[recipe.output_item];
        const rarityColor = outItem ? RARITY_COLORS[outItem.rarity] || '#9ca3af' : '#9ca3af';
        return (
          <div key={recipe.recipe_id} className="mb-3 p-2 rounded border border-border bg-bg-primary">
            <div className="font-semibold text-xs" style={{ color: rarityColor }}>
              {outItem?.name ?? recipe.output_item}
            </div>
            <div className="mt-1.5 flex flex-wrap gap-x-3 gap-y-0.5 text-[10px]">
              <span className="text-accent-yellow font-semibold">{recipe.gold_cost}g</span>
              {Object.entries(recipe.materials).map(([mat, qty]) => (
                <span key={mat} className="text-text-primary">
                  {qty}× {itemMap[mat]?.name ?? mat}
                </span>
              ))}
            </div>
            {outItem && (
              <div className="mt-1 flex gap-2 text-[10px]">
                {outItem.atk_bonus ? <span className="text-accent-red">+{outItem.atk_bonus} ATK</span> : null}
                {outItem.def_bonus ? <span className="text-accent-blue">+{outItem.def_bonus} DEF</span> : null}
                {outItem.spd_bonus ? <span className="text-accent-green">{outItem.spd_bonus > 0 ? '+' : ''}{outItem.spd_bonus} SPD</span> : null}
                {outItem.crit_rate_bonus ? <span className="text-accent-yellow">+{(outItem.crit_rate_bonus * 100).toFixed(0)}% CRIT</span> : null}
                {outItem.evasion_bonus ? <span className="text-accent-purple">+{(outItem.evasion_bonus * 100).toFixed(0)}% EVA</span> : null}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

function GuildContent() {
  const { items } = useMetadata();

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
      {items.items.filter(it => it.item_type === 'material').map((it) => {
        const rarityColor = RARITY_COLORS[it.rarity] || '#9ca3af';
        return (
          <div key={it.item_id} className="py-1 border-b border-border/50 last:border-0">
            <span className="text-xs font-semibold" style={{ color: rarityColor }}>
              {it.name}
            </span>
          </div>
        );
      })}
    </div>
  );
}

function InnContent() {
  return (
    <div className="p-3">
      <div className="text-[10px] font-bold uppercase tracking-wider text-text-secondary mb-2">
        Traveler's Inn
      </div>
      <div className="text-[11px] text-text-secondary mb-3">
        A warm hearth and a soft bed. Heroes rest here to rapidly recover HP and stamina before
        venturing back into the wilds.
      </div>

      <div className="text-[10px] font-bold uppercase tracking-wider text-text-secondary mb-2 mt-4">
        Services
      </div>
      <div className="space-y-1.5 text-[11px]">
        <div className="p-2 rounded border border-border bg-bg-primary">
          <div className="font-semibold text-[#fb923c] text-xs">Rest & Recovery</div>
          <div className="text-text-secondary text-[10px] mt-0.5">
            Heroes resting at the Inn regenerate <span className="text-accent-green font-semibold">4 stamina/tick</span> and
            recover HP faster than resting in the open.
          </div>
        </div>
        <div className="p-2 rounded border border-border bg-bg-primary">
          <div className="font-semibold text-[#fb923c] text-xs">Safe Haven</div>
          <div className="text-text-secondary text-[10px] mt-0.5">
            The Inn is located within town walls. Heroes are completely safe from enemy attacks
            while resting here.
          </div>
        </div>
      </div>

      <div className="text-[10px] font-bold uppercase tracking-wider text-text-secondary mb-2 mt-4">
        Stamina Regeneration Rates
      </div>
      <div className="space-y-1 text-[10px]">
        <div className="flex justify-between py-0.5 border-b border-border/30">
          <span className="text-text-secondary">Resting in Town / Idle</span>
          <span className="font-semibold text-accent-green">5 / tick</span>
        </div>
        <div className="flex justify-between py-0.5 border-b border-border/30">
          <span className="text-text-secondary font-semibold" style={{ color: '#fb923c' }}>Visiting Inn</span>
          <span className="font-semibold text-accent-green">4 / tick</span>
        </div>
        <div className="flex justify-between py-0.5 border-b border-border/30">
          <span className="text-text-secondary">Visiting Buildings</span>
          <span className="font-semibold text-accent-green">4 / tick</span>
        </div>
        <div className="flex justify-between py-0.5">
          <span className="text-text-secondary">Adventuring</span>
          <span className="font-semibold text-text-primary">1 / tick</span>
        </div>
      </div>
    </div>
  );
}

function HeroHouseContent({ building }: { building: Building }) {
  const { itemMap } = useMetadata();
  const storageItems = building.storage_items ?? [];
  const used = building.storage_used ?? 0;
  const max = building.storage_max ?? 0;
  const level = building.storage_level ?? 0;
  const pct = max > 0 ? Math.round((used / max) * 100) : 0;

  return (
    <div className="p-3">
      <div className="text-[11px] text-text-secondary mb-3">
        The hero's personal dwelling. Items stored here are safe from loss on death and persist
        between adventures.
      </div>

      <div className="text-[10px] font-bold uppercase tracking-wider text-text-secondary mb-2">
        Storage (Lv.{level})
      </div>
      <div className="mb-3">
        <div className="flex items-center justify-between text-[10px] mb-1">
          <span className="text-text-secondary">{used} / {max} slots</span>
          <span className="font-semibold" style={{ color: pct > 80 ? '#f87171' : '#34d399' }}>{pct}%</span>
        </div>
        <div className="w-full h-1.5 bg-bg-primary rounded-full overflow-hidden">
          <div
            className="h-full rounded-full transition-all"
            style={{ width: `${pct}%`, background: pct > 80 ? '#f87171' : '#34d399' }}
          />
        </div>
      </div>

      {storageItems.length > 0 ? (
        <div className="flex flex-wrap gap-1">
          {storageItems.map((iid, i) => {
            const item = itemMap[iid];
            const rarityColor = item ? RARITY_COLORS[item.rarity] || '#9ca3af' : '#9ca3af';
            return (
              <span
                key={i}
                className="inline-block text-[10px] border rounded px-1.5 py-0.5"
                style={{ borderColor: rarityColor + '40', color: rarityColor, background: rarityColor + '10' }}
              >
                {item?.name ?? iid}
              </span>
            );
          })}
        </div>
      ) : (
        <div className="text-[11px] text-text-secondary italic">Storage is empty.</div>
      )}

      <div className="text-[10px] font-bold uppercase tracking-wider text-text-secondary mb-2 mt-4">
        Features
      </div>
      <div className="space-y-1.5 text-[11px]">
        <div className="p-2 rounded border border-border bg-bg-primary">
          <div className="font-semibold text-[#34d399] text-xs">Safe Storage</div>
          <div className="text-text-secondary text-[10px] mt-0.5">
            Items stored here are never lost, even if the hero falls in battle.
          </div>
        </div>
        <div className="p-2 rounded border border-border bg-bg-primary">
          <div className="font-semibold text-[#34d399] text-xs">Rest & Recover</div>
          <div className="text-text-secondary text-[10px] mt-0.5">
            Heroes can visit home to rest, deposit loot, and retrieve stored items before heading out.
          </div>
        </div>
      </div>
    </div>
  );
}
