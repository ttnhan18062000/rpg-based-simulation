import { Trash2 } from 'lucide-react';
import type { GameEvent } from '@/types/api';

interface EventLogProps {
  events: GameEvent[];
  onClear: () => void;
}

const CATEGORY_COLORS: Record<string, string> = {
  combat: 'text-accent-red',
  movement: 'text-text-secondary',
  rest: 'text-accent-green',
  spawn: 'text-accent-blue',
  death: 'text-accent-red',
  level_up: 'text-accent-purple',
  loot: 'text-accent-yellow',
  item: 'text-accent-green',
  skill: 'text-accent-purple',
  harvest: 'text-accent-green',
};

const NOTABLE = new Set(['combat', 'death', 'level_up', 'loot', 'item', 'skill', 'harvest']);

export function EventLog({ events, onClear }: EventLogProps) {
  const notable = events.filter(ev => NOTABLE.has(ev.category) || ev.metadata);
  const recent = [...notable].reverse();

  return (
    <div className="flex-1 flex flex-col min-h-0 overflow-hidden">
      {/* Header with count + clear button */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-border bg-bg-tertiary">
        <span className="text-[10px] font-bold uppercase tracking-wider text-text-secondary">
          Events ({notable.length})
        </span>
        <button
          onClick={onClear}
          className="flex items-center gap-1 text-[10px] text-text-secondary hover:text-accent-red transition-colors cursor-pointer px-1.5 py-0.5 rounded hover:bg-white/[0.05]"
          title="Clear all events"
        >
          <Trash2 className="w-3 h-3" />
          Clear
        </button>
      </div>
      <div className="flex-1 overflow-y-auto min-h-0">
        {recent.length === 0 ? (
          <div className="text-text-secondary text-xs text-center py-8">No events yet</div>
        ) : (
          recent.map((ev, i) => (
            <div
              key={`${ev.tick}-${i}`}
              className={`px-4 py-1 text-[11px] font-mono border-b border-bg-primary leading-relaxed
                         ${CATEGORY_COLORS[ev.category] || 'text-text-secondary'}`}
            >
              <span className="text-accent-blue font-semibold">[{ev.tick}]</span>{' '}
              {ev.message}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
