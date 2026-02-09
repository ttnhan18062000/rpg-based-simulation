import { X } from 'lucide-react';
import type { GroundItem } from '@/types/api';
import { itemName, ITEM_STATS, RARITY_COLORS } from '@/constants/colors';

interface LootPanelProps {
  loot: GroundItem;
  onClose: () => void;
}

export function LootPanel({ loot, onClose }: LootPanelProps) {
  return (
    <div className="flex-1 overflow-y-auto min-h-0">
      <div className="p-3 border-b border-border">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-bold text-accent-green">
            Loot Bag ({loot.x}, {loot.y})
          </span>
          <button onClick={onClose} className="text-text-secondary hover:text-text-primary p-0.5 cursor-pointer">
            <X className="w-4 h-4" />
          </button>
        </div>
        <span className="text-[11px] text-text-secondary">{loot.items.length} item{loot.items.length !== 1 ? 's' : ''}</span>
      </div>

      <div className="p-3">
        {loot.items.map((itemId, i) => {
          const stats = ITEM_STATS[itemId];
          const rarityColor = stats ? RARITY_COLORS[stats.rarity] || '#9ca3af' : '#9ca3af';

          return (
            <div key={`${itemId}-${i}`} className="mb-2 p-2 rounded border border-border bg-bg-primary">
              <div className="font-semibold text-xs" style={{ color: rarityColor }}>
                {itemName(itemId)}
              </div>
              {stats && (
                <div className="mt-1 text-[10px] leading-relaxed text-text-secondary">
                  <span className="capitalize">{stats.type} &middot; <span style={{ color: rarityColor }}>{stats.rarity}</span></span>
                  <div className="mt-0.5 flex flex-wrap gap-x-3">
                    {stats.atk ? <span className="text-accent-red">ATK +{stats.atk}</span> : null}
                    {stats.def ? <span className="text-accent-blue">DEF +{stats.def}</span> : null}
                    {stats.spd ? <span className="text-accent-green">SPD {stats.spd > 0 ? '+' : ''}{stats.spd}</span> : null}
                    {stats.maxHp ? <span className="text-accent-green">HP +{stats.maxHp}</span> : null}
                    {stats.crit ? <span className="text-accent-yellow">CRIT +{stats.crit}%</span> : null}
                    {stats.evasion ? <span className="text-accent-purple">EVA +{stats.evasion}%</span> : null}
                    {stats.luck ? <span className="text-accent-yellow">LUCK +{stats.luck}</span> : null}
                    {stats.heal ? <span className="text-accent-green">Heals {stats.heal} HP</span> : null}
                    {stats.gold ? <span className="text-accent-yellow">Worth {stats.gold}g</span> : null}
                  </div>
                </div>
              )}
              {!stats && (
                <div className="mt-1 text-[10px] text-text-secondary">Unknown item</div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
