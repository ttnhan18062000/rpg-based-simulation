import { useState, useEffect, useRef, useCallback } from 'react';
import type { MapData, WorldState, SimulationStats, Entity, EntitySlim, GameEvent, GroundItem, Building, ResourceNode, Region, StaticData } from '@/types/api';

const API_BASE = '/api/v1';
const POLL_MS = 80;

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
  const pollingRef = useRef<ReturnType<typeof setTimeout> | null>(null);
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

  // Poll loop
  useEffect(() => {
    if (!mapLoadedRef.current && !mapData) return;

    let cancelled = false;

    const poll = async () => {
      if (cancelled) return;
      try {
        const selId = selectedIdRef.current;
        const selParam = selId != null ? `&selected=${selId}` : '';
        const [state, stats] = await Promise.all([
          fetchJSON<WorldState>(`/state?since_tick=${Math.max(0, lastTickRef.current - 5)}${selParam}`),
          fetchJSON<SimulationStats>('/stats'),
        ]);

        if (cancelled) return;

        // Always update simulation status (running/paused)
        setTotalSpawned(stats.total_spawned);
        setTotalDeaths(stats.total_deaths);
        if (!stats.running) {
          setStatus('STOPPED');
        } else if (stats.paused) {
          setStatus('PAUSED');
        } else {
          setStatus('RUNNING');
        }

        // Update selected entity when response content changes (avoids re-renders on same data)
        // Use response entity ID (not requested ID) to correctly handle in-flight poll transitions
        const responseSelId = state.selected_entity?.id ?? null;
        const selKey = `${responseSelId}_${state.tick}`;
        if (selKey !== lastSelKeyRef.current) {
          lastSelKeyRef.current = selKey;
          setSelectedEntity(state.selected_entity ?? null);
        }

        // Skip bulk entity/groundItem updates if tick hasn't advanced (avoids re-renders when paused)
        const tickChanged = state.tick !== lastTickRef.current;
        lastTickRef.current = state.tick;

        if (tickChanged) {
          setTick(state.tick);
          setAliveCount(state.alive_count);
          setEntities(state.entities);
          setGroundItems(state.ground_items || []);
        }

        if (state.events.length > 0) {
          setEvents(prev => {
            const existingKeys = new Set(prev.map(e => `${e.tick}:${e.message}`));
            const fresh = state.events.filter(e => !existingKeys.has(`${e.tick}:${e.message}`));
            return fresh.length > 0 ? [...prev, ...fresh] : prev;
          });
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
