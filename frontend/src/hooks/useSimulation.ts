import { useState, useEffect, useRef, useCallback } from 'react';
import type { MapData, WorldState, SimulationStats, Entity, EntitySlim, GameEvent, GroundItem, Building, ResourceNode, Region, StaticData } from '@/types/api';

const API_BASE = '/api/v1';

async function fetchJSON<T>(path: string): Promise<T> {
  const res = await fetch(API_BASE + path);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json() as Promise<T>;
}

export type SimStatus = 'CONNECTING' | 'RUNNING' | 'PAUSED' | 'STOPPED';

// Decoded map data with 2D grid (decoded from RLE on load)
export interface DecodedMapData {
  width: number;
  height: number;
  grid: number[][];
}

export interface SimulationState {
  mapData: DecodedMapData | null;
  entities: EntitySlim[];
  selectedEntity: Entity | null;
  events: GameEvent[];
  groundItems: GroundItem[];
  buildings: Building[];
  resourceNodes: ResourceNode[];
  regions: Region[];
  tick: number;
  aliveCount: number;
  totalSpawned: number;
  totalDeaths: number;
  status: SimStatus;
  selectedEntityId: number | null;
  selectEntity: (id: number | null) => void;
  sendControl: (action: string) => Promise<void>;
  setSpeed: (tps: number) => Promise<void>;
  clearEvents: () => Promise<void>;
}

function decodeRLE(rle: number[], width: number, height: number): number[][] {
  const grid: number[][] = [];
  const flat: number[] = [];
  for (let i = 0; i < rle.length; i += 2) {
    const value = rle[i];
    const count = rle[i + 1];
    for (let j = 0; j < count; j++) flat.push(value);
  }
  for (let y = 0; y < height; y++) {
    grid.push(flat.slice(y * width, (y + 1) * width));
  }
  return grid;
}

export function useSimulation(): SimulationState {
  const [mapData, setMapData] = useState<DecodedMapData | null>(null);
  const [entities, setEntities] = useState<EntitySlim[]>([]);
  const [selectedEntity, setSelectedEntity] = useState<Entity | null>(null);
  const [events, setEvents] = useState<GameEvent[]>([]);
  const [groundItems, setGroundItems] = useState<GroundItem[]>([]);
  const [buildings, setBuildings] = useState<Building[]>([]);
  const [resourceNodes, setResourceNodes] = useState<ResourceNode[]>([]);
  const [regions, setRegions] = useState<Region[]>([]);
  const [tick, setTick] = useState(0);
  const [aliveCount, setAliveCount] = useState(0);
  const [totalSpawned, setTotalSpawned] = useState(0);
  const [totalDeaths, setTotalDeaths] = useState(0);
  const [status, setStatus] = useState<SimStatus>('CONNECTING');
  const [selectedEntityId, setSelectedEntityId] = useState<number | null>(null);

  const lastTickRef = useRef(0);
  const mapLoadedRef = useRef(false);
  const staticLoadedRef = useRef(false);
  const selectedIdRef = useRef<number | null>(null);
  const lastSelKeyRef = useRef('');

  // Ref is synced immediately in selectEntity callback (not via useEffect)
  // to ensure the very next poll includes the ?selected= param

  // Load map + static data once
  useEffect(() => {
    let cancelled = false;
    const loadInitial = async () => {
      try {
        const [rawMap, staticData] = await Promise.all([
          fetchJSON<MapData>('/map'),
          fetchJSON<StaticData>('/static'),
        ]);
        if (!cancelled) {
          const decoded: DecodedMapData = {
            width: rawMap.width,
            height: rawMap.height,
            grid: decodeRLE(rawMap.grid, rawMap.width, rawMap.height),
          };
          setMapData(decoded);
          setBuildings(staticData.buildings || []);
          setResourceNodes(staticData.resource_nodes || []);
          setRegions(staticData.regions || []);
          mapLoadedRef.current = true;
          staticLoadedRef.current = true;
        }
      } catch {
        if (!cancelled) setTimeout(loadInitial, 1000);
      }
    };
    loadInitial();
    return () => { cancelled = true; };
  }, []);

  // EventSource stream loop
  useEffect(() => {
    if (!mapLoadedRef.current && !mapData) return;

    let evtSource: EventSource | null = null;
    let pollInterval: ReturnType<typeof setInterval> | null = null;
    let pollingStatus = false;

    const connectStream = () => {
      evtSource = new EventSource(`${API_BASE}/stream`);
      
      evtSource.onmessage = (event) => {
        try {
          const delta = JSON.parse(event.data);
          
          if (delta.error) {
            console.error('Stream error:', delta.error);
            return;
          }

          setTick(delta.tick);

          setEntities((prev) => {
            // Convert array to map for fast updates
            const entMap = new Map(prev.map(e => [e.id, e]));

            // Remove dead
            for (const id of delta.removed) {
              entMap.delete(id);
            }

            // Upsert changed
            for (const upd of delta.changed) {
              entMap.set(upd.id, upd);
            }

            const next = Array.from(entMap.values());
            setAliveCount(next.length);
            return next;
          });

          if (delta.events && delta.events.length > 0) {
            setEvents(prev => {
              const existingKeys = new Set(prev.map(e => `${e.tick}:${e.message}`));
              const fresh = delta.events.filter((e: GameEvent) => !existingKeys.has(`${e.tick}:${e.message}`));
              return fresh.length > 0 ? [...prev, ...fresh] : prev;
            });
          }
        } catch (err) {
          console.error('Failed to parse SSE payload:', err);
        }
      };

      evtSource.onerror = () => {
        evtSource?.close();
        setTimeout(connectStream, 2000); // Reconnect on failure
      };
    };

    connectStream();

    // Secondary slow-poll: 1) fetches full selected_entity data, 2) fetches stats (total spawns, status)
    // Runs every 500ms instead of 80ms
    const fallbackPoll = async () => {
      if (pollingStatus) return;
      pollingStatus = true;
      try {
        const [stats] = await Promise.all([
          fetchJSON<SimulationStats>('/stats'),
        ]);

        setTotalSpawned(stats.total_spawned);
        setTotalDeaths(stats.total_deaths);
        if (!stats.running) {
          setStatus('STOPPED');
        } else if (stats.paused) {
          setStatus('PAUSED');
        } else {
          setStatus('RUNNING');
        }

        const selId = selectedIdRef.current;
        if (selId !== null) {
            const state = await fetchJSON<WorldState>(`/state?since_tick=${Math.max(0, lastTickRef.current - 5)}&selected=${selId}`);
            const responseSelId = state.selected_entity?.id ?? null;
            const selKey = `${responseSelId}_${state.tick}`;
            if (selKey !== lastSelKeyRef.current) {
                lastSelKeyRef.current = selKey;
                setSelectedEntity(state.selected_entity ?? null);
            }
            // Ground items only come from the massive dump currently
            setGroundItems(state.ground_items || []);
        } else {
            setSelectedEntity(null);
            
            // Still need to get ground items periodically if no selection
             const state = await fetchJSON<WorldState>(`/state?since_tick=${Math.max(0, lastTickRef.current - 5)}`);
             setGroundItems(state.ground_items || []);
        }
      } catch (err) {
        // quiet fail
      } finally {
        pollingStatus = false;
      }
    };
    
    pollInterval = setInterval(fallbackPoll, 500);

    return () => {
      if (evtSource) evtSource.close();
      if (pollInterval) clearInterval(pollInterval);
    };
  }, [mapData]);

  const sendControl = useCallback(async (action: string) => {
    try {
      await fetch(`${API_BASE}/control/${action}`, { method: 'POST' });
    } catch (e) {
      console.error('Control error:', e);
    }
  }, []);

  const setSpeed = useCallback(async (tps: number) => {
    try {
      await fetch(`${API_BASE}/speed?tps=${tps}`, { method: 'POST' });
    } catch {
      // ignore
    }
  }, []);

  const selectEntity = useCallback((id: number | null) => {
    selectedIdRef.current = id; // Sync ref immediately so next poll includes ?selected=
    setSelectedEntityId(id);
  }, []);

  const clearEvents = useCallback(async () => {
    try {
      await fetch(`${API_BASE}/clear_events`, { method: 'POST' });
      setEvents([]);
    } catch (e) {
      console.error('Clear events error:', e);
    }
  }, []);

  return {
    mapData,
    entities,
    selectedEntity,
    events,
    groundItems,
    buildings,
    resourceNodes,
    regions,
    tick,
    aliveCount,
    totalSpawned,
    totalDeaths,
    status,
    selectedEntityId,
    selectEntity,
    sendControl,
    setSpeed,
    clearEvents,
  };
}
