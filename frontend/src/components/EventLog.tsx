import type { GameEvent } from '@/types/api';

interface EventLogProps {
  events: GameEvent[];
}

const CATEGORY_COLORS: Record<string, string> = {
  ATTACK: 'text-accent-red',
  MOVE: 'text-text-secondary',
  REST: 'text-accent-green',
  SPAWN: 'text-accent-blue',
  DEATH: 'text-accent-red',
  LEVEL_UP: 'text-accent-purple',
  LOOT: 'text-accent-yellow',
  USE_ITEM: 'text-accent-green',
};

export function EventLog({ events }: EventLogProps) {
  const recent = events.slice(-100).reverse();

  return (
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
  );
}
