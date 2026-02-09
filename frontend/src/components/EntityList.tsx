import type { Entity } from '@/types/api';
import { KIND_COLORS, hpColor } from '@/constants/colors';

interface EntityListProps {
  entities: Entity[];
  selectedEntityId: number | null;
  onSelect: (id: number) => void;
}

export function EntityList({ entities, selectedEntityId, onSelect }: EntityListProps) {
  const sorted = [...entities].sort((a, b) => {
    if (a.kind === 'hero' && b.kind !== 'hero') return -1;
    if (a.kind !== 'hero' && b.kind === 'hero') return 1;
    return a.id - b.id;
  });

  return (
    <div className="flex flex-col min-h-0 flex-1">
      <div className="px-4 py-2.5 text-[11px] font-bold uppercase tracking-widest text-text-secondary bg-bg-tertiary">
        Entities ({entities.length})
      </div>
      <div className="flex-1 overflow-y-auto min-h-0">
        {sorted.map((e) => {
          const color = KIND_COLORS[e.kind] || '#888';
          const ratio = Math.max(0, e.hp / e.max_hp);
          const hpCol = hpColor(ratio);
          const isSelected = e.id === selectedEntityId;

          return (
            <div
              key={e.id}
              onClick={() => onSelect(e.id)}
              className={`grid grid-cols-[10px_1fr_auto] items-center gap-2 px-4 py-1.5 text-xs
                         border-b border-bg-primary cursor-pointer transition-colors
                         hover:bg-bg-tertiary
                         ${isSelected ? 'bg-bg-tertiary border-l-2 border-l-accent-blue' : ''}`}
            >
              <div
                className="w-2.5 h-2.5 rounded-full"
                style={{ background: color }}
              />
              <div className="flex flex-col gap-px">
                <div className="font-semibold text-xs">
                  #{e.id} {e.kind}{' '}
                  <span className="text-text-secondary text-[10px]">Lv{e.level}</span>
                </div>
                <div className="text-[10px] text-text-secondary">
                  ({e.x},{e.y}) {e.state}
                </div>
              </div>
              <div className="flex flex-col items-end gap-0.5 w-[60px]">
                <span className="text-[11px] tabular-nums">{e.hp}/{e.max_hp}</span>
                <div className="w-full h-1 bg-bg-primary rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-[width] duration-200"
                    style={{ width: `${ratio * 100}%`, background: hpCol }}
                  />
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
