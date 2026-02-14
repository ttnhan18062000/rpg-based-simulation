import { useState, useEffect } from 'react';
import { Info, Search, ScrollText } from 'lucide-react';
import type { Entity, EntitySlim, GameEvent, GroundItem, Building } from '@/types/api';
import type { DecodedMapData } from '@/hooks/useSimulation';
import { ControlPanel } from './ControlPanel';
import { Legend } from './Legend';
import { EntityList } from './EntityList';
import { InspectPanel } from './InspectPanel';
import { EventLog } from './EventLog';
import { LootPanel } from './LootPanel';
import { BuildingPanel } from './BuildingPanel';

type TabId = 'info' | 'inspect' | 'events';

interface SidebarProps {
  entities: EntitySlim[];
  selectedEntity: Entity | null;
  events: GameEvent[];
  mapData: DecodedMapData | null;
  selectedEntityId: number | null;
  onSelectEntity: (id: number | null) => void;
  sendControl: (action: string) => Promise<void>;
  setSpeed: (tps: number) => Promise<void>;
  inspectedLoot: GroundItem | null;
  onClearLoot: () => void;
  selectedBuilding: Building | null;
  onClearBuilding: () => void;
  clearEvents: () => Promise<void>;
}

export function Sidebar({
  entities, selectedEntity, events, mapData, selectedEntityId, onSelectEntity, sendControl, setSpeed,
  inspectedLoot, onClearLoot, selectedBuilding, onClearBuilding, clearEvents,
}: SidebarProps) {
  // Determine mode: building, spectate, or default
  const isSpectating = selectedEntityId !== null;
  const isBuildingView = selectedBuilding !== null;
  const isLootView = inspectedLoot !== null;

  // Auto-select appropriate tab when context changes
  const [activeTab, setActiveTab] = useState<TabId>('info');

  useEffect(() => {
    if (isBuildingView || isLootView) {
      setActiveTab('inspect');
    } else if (isSpectating) {
      setActiveTab('inspect');
    }
  }, [isBuildingView, isLootView, isSpectating]);

  const handleSelectEntity = (id: number) => {
    onSelectEntity(id);
  };

  // selectedEntity is passed directly from parent (full Entity from API)

  // Filter events related to the spectated entity (use entity_ids array)
  const entityEvents = selectedEntityId
    ? events.filter(ev =>
        ev.entity_ids?.includes(selectedEntityId) ?? false
      )
    : [];

  // Tab layout depends on mode:
  // - Building/Loot view: INSPECT only (shows building/loot panel)
  // - Spectating entity: INSPECT only (shows entity panel with events sub-section)
  // - Default: INFO + EVENTS
  const tabs: { id: TabId; label: string; icon: React.ReactNode }[] =
    (isBuildingView || isLootView || isSpectating)
      ? [{ id: 'inspect', label: isBuildingView ? selectedBuilding!.name : (isLootView ? 'Loot' : 'Inspect'), icon: <Search className="w-4 h-4" /> }]
      : [
          { id: 'info', label: 'Info', icon: <Info className="w-4 h-4" /> },
          { id: 'events', label: 'Events', icon: <ScrollText className="w-4 h-4" /> },
        ];

  return (
    <div className="bg-bg-secondary border-l border-border flex flex-col overflow-hidden w-[360px]">
      {/* Controls */}
      <ControlPanel sendControl={sendControl} setSpeed={setSpeed} />

      {/* Tab Bar */}
      <div className="flex bg-bg-tertiary border-b border-border px-1 gap-1 py-1">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex-1 flex items-center justify-center gap-2 py-2.5 text-xs font-semibold uppercase tracking-wider
                        rounded-md transition-colors cursor-pointer
                        ${activeTab === tab.id
                          ? 'text-accent-blue bg-bg-secondary shadow-sm'
                          : 'text-text-secondary hover:text-text-primary hover:bg-white/[0.03]'
                        }`}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="flex-1 flex flex-col min-h-0 overflow-hidden">
        {activeTab === 'info' && (
          <div className="flex flex-col flex-1 min-h-0">
            <Legend />
            <EntityList
              entities={entities}
              selectedEntityId={selectedEntityId}
              onSelect={handleSelectEntity}
            />
          </div>
        )}
        {activeTab === 'inspect' && (
          isBuildingView ? (
            <BuildingPanel building={selectedBuilding!} onClose={onClearBuilding} />
          ) : isLootView ? (
            <LootPanel loot={inspectedLoot!} onClose={onClearLoot} />
          ) : (
            <InspectPanel
              entity={selectedEntity ?? undefined}
              mapData={mapData}
              events={entityEvents}
              onClose={() => onSelectEntity(null)}
            />
          )
        )}
        {activeTab === 'events' && (
          <EventLog events={events} onClear={clearEvents} />
        )}
      </div>
    </div>
  );
}
