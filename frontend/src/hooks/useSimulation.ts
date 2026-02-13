import { useState, useEffect, useRef, useCallback } from 'react';
import type { MapData, WorldState, SimulationStats, Entity, GameEvent, GroundItem, Building, ResourceNode, Region } from '@/types/api';

const API_BASE = '/api/v1';
const POLL_MS = 80;

async function fetchJSON<T>(path: string): Promise<T> {
  const res = await fetch(API_BASE + path);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json() as Promise<T>;
}

export type SimStatus = 'CONNECTING' | 'RUNNING' | 'PAUSED' | 'STOPPED';

export interface SimulationState {
  mapData: MapData | null;
  entities: Entity[];
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

export function useSimulation(): SimulationState {
  const [mapData, setMapData] = useState<MapData | null>(null);
  const [entities, setEntities] = useState<Entity[]>([]);
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
  const pollingRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const mapLoadedRef = useRef(false);

  // Load map once
  useEffect(() => {
    let cancelled = false;
    const loadMap = async () => {
      try {
        const data = await fetchJSON<MapData>('/map');
        if (!cancelled) {
          setMapData(data);
          mapLoadedRef.current = true;
        }
      } catch {
        if (!cancelled) setTimeout(loadMap, 1000);
      }
    };
    loadMap();
    return () => { cancelled = true; };
  }, []);

  // Poll loop
  useEffect(() => {
    if (!mapLoadedRef.current && !mapData) return;

    let cancelled = false;

    const poll = async () => {
      if (cancelled) return;
      try {
        const [state, stats] = await Promise.all([
          fetchJSON<WorldState>(`/state?since_tick=${Math.max(0, lastTickRef.current - 5)}`),
          fetchJSON<SimulationStats>('/stats'),
        ]);

        if (cancelled) return;

        lastTickRef.current = state.tick;
        setTick(state.tick);
        setAliveCount(state.alive_count);
        setEntities(state.entities);
        setGroundItems(state.ground_items || []);
        setBuildings(state.buildings || []);
        setResourceNodes(state.resource_nodes || []);
        setRegions(state.regions || []);
        if (state.events.length > 0) {
          setEvents(prev => {
            // Merge: keep all previous events, append only genuinely new ones
            const existingKeys = new Set(prev.map(e => `${e.tick}:${e.message}`));
            const fresh = state.events.filter(e => !existingKeys.has(`${e.tick}:${e.message}`));
            return fresh.length > 0 ? [...prev, ...fresh] : prev;
          });
        }
        setTotalSpawned(stats.total_spawned);
        setTotalDeaths(stats.total_deaths);

        if (!stats.running) {
          setStatus('STOPPED');
        } else if (stats.paused) {
          setStatus('PAUSED');
        } else {
          setStatus('RUNNING');
        }
      } catch {
        // server gone — keep retrying
      }

      if (!cancelled) {
        pollingRef.current = setTimeout(poll, POLL_MS);
      }
    };

    poll();

    return () => {
      cancelled = true;
      if (pollingRef.current) clearTimeout(pollingRef.current);
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
