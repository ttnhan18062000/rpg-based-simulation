import { X } from 'lucide-react';
import type { GroundItem } from '@/types/api';
import { RARITY_COLORS } from '@/constants/colors';
import { useMetadata } from '@/contexts/MetadataContext';

interface LootPanelProps {
  loot: GroundItem;
  onClose: () => void;
}

export function LootPanel({ loot, onClose }: LootPanelProps) {
  const { itemMap } = useMetadata();

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
          const item = itemMap[itemId];
          const rarityColor = item ? RARITY_COLORS[item.rarity] || '#9ca3af' : '#9ca3af';

          return (
            <div key={`${itemId}-${i}`} className="mb-2 p-2 rounded border border-border bg-bg-primary">
              <div className="font-semibold text-xs" style={{ color: rarityColor }}>
                {item?.name ?? itemId}
              </div>
              {item && (
                <div className="mt-1 text-[10px] leading-relaxed text-text-secondary">
                  <span className="capitalize">{item.item_type} &middot; <span style={{ color: rarityColor }}>{item.rarity}</span></span>
                  <div className="mt-0.5 flex flex-wrap gap-x-3">
                    {item.atk_bonus ? <span className="text-accent-red">ATK +{item.atk_bonus}</span> : null}
                    {item.def_bonus ? <span className="text-accent-blue">DEF +{item.def_bonus}</span> : null}
                    {item.spd_bonus ? <span className="text-accent-green">SPD {item.spd_bonus > 0 ? '+' : ''}{item.spd_bonus}</span> : null}
                    {item.max_hp_bonus ? <span className="text-accent-green">HP +{item.max_hp_bonus}</span> : null}
                    {item.crit_rate_bonus ? <span className="text-accent-yellow">CRIT +{(item.crit_rate_bonus * 100).toFixed(0)}%</span> : null}
                    {item.evasion_bonus ? <span className="text-accent-purple">EVA +{(item.evasion_bonus * 100).toFixed(0)}%</span> : null}
                    {item.luck_bonus ? <span className="text-accent-yellow">LUCK +{item.luck_bonus}</span> : null}
                    {item.heal_amount ? <span className="text-accent-green">Heals {item.heal_amount} HP</span> : null}
                    {item.gold_value ? <span className="text-accent-yellow">Worth {item.gold_value}g</span> : null}
                    {item.matk_bonus ? <span className="text-accent-purple">MATK +{item.matk_bonus}</span> : null}
                    {item.mdef_bonus ? <span className="text-accent-blue">MDEF +{item.mdef_bonus}</span> : null}
                  </div>
                </div>
              )}
              {!item && (
                <div className="mt-1 text-[10px] text-text-secondary">Unknown item</div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
