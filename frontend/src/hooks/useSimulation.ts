import { useState, useEffect, useRef, useCallback } from 'react';
import type { MapData, WorldState, SimulationStats, Entity, EntitySlim, WireEntitySlim, GameEvent, GroundItem, Building, ResourceNode, TreasureChest, Region, StaticData, Manifest } from '@/types/api';

const API_BASE = '/api/v1';

function wsBase(): string {
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${proto}//${window.location.host}${API_BASE}`;
}

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
  treasureChests: TreasureChest[];
  regions: Region[];
  manifest: Manifest | null;
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
  const [treasureChests, setTreasureChests] = useState<TreasureChest[]>([]);
  const [regions, setRegions] = useState<Region[]>([]);
  const [manifest, setManifest] = useState<Manifest | null>(null);
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
        const [rawMap, staticData, manifestData] = await Promise.all([
          fetchJSON<MapData>('/map'),
          fetchJSON<StaticData>('/static'),
          fetchJSON<Manifest>('/manifest'),
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
          setTreasureChests(staticData.treasure_chests || []);
          setRegions(staticData.regions || []);
          setManifest(manifestData);
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

  // WebSocket stream loop
  useEffect(() => {
    if (!mapLoadedRef.current && !mapData) return;

    let ws: WebSocket | null = null;
    let pollInterval: ReturnType<typeof setInterval> | null = null;
    let pollingStatus = false;
    let reconnectTimeout: ReturnType<typeof setTimeout> | null = null;

    const scheduleReconnect = () => {
      if (reconnectTimeout) return;
      reconnectTimeout = setTimeout(() => {
        reconnectTimeout = null;
        connectWS();
      }, 2000);
    };

    const connectWS = () => {
      ws = new WebSocket(`${wsBase()}/ws`);

      ws.onopen = () => {
        ws!.send(JSON.stringify({ type: 'handshake', format: 'json' }));
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          if (data.error) {
            console.error('Stream error:', data.error);
            return;
          }

          const isDelta = Array.isArray(data.changed) && Array.isArray(data.removed);
          if (!isDelta) {
            // Initial post-handshake message: manager.get_state() minimal-summary shape
            // ({tick, world_time, entities_count, maturity, seed}), not a delta. No entity/event
            // state to reduce here.
            return;
          }

          setTick(data.tick);

          setEntities((prev: EntitySlim[]) => {
            // Convert array to map for fast updates
            const entMap = new Map(prev.map(e => [e.id, e]));

            // Remove dead
            for (const id of data.removed) {
              entMap.delete(id);
            }

            // Upsert changed
            for (const upd of data.changed as WireEntitySlim[]) {
              // present_entity_slim never sends state/loot_progress/loot_duration — '' never
              // matches 'LOOTING', so this default stays inert, not a fabricated value.
              const full: EntitySlim = {
                ...upd,
                state: upd.state ?? '',
                tier: upd.tier ?? 0,
                combat_target_id: upd.combat_target_id ?? null,
                loot_progress: upd.loot_progress ?? 0,
                loot_duration: upd.loot_duration ?? 0,
              };
              entMap.set(full.id, full);
            }

            const next = Array.from(entMap.values());
            setAliveCount(next.length);
            return next;
          });

          if (data.events && data.events.length > 0) {
            setEvents((prev: GameEvent[]) => {
              const existingKeys = new Set(prev.map(e => `${e.tick}:${e.message}`));
              const fresh = data.events.filter((e: GameEvent) => !existingKeys.has(`${e.tick}:${e.message}`));
              return fresh.length > 0 ? [...prev, ...fresh] : prev;
            });
          }
        } catch (err) {
          console.error('Failed to parse WS payload:', err);
        }
      };

      ws.onclose = () => {
        scheduleReconnect();
      };

      ws.onerror = () => {
        ws?.close();
        scheduleReconnect();
      };
    };

    connectWS();

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
             
             // Merge dynamic world object states (Audit Point 3)
             if (state.resource_nodes) {
                 setResourceNodes((prev: ResourceNode[]) => {
                     const nodeMap = new Map(state.resource_nodes!.map(n => [n.node_id, n]));
                     return prev.map(node => {
                         const dyn = nodeMap.get(node.node_id);
                         if (dyn) return { ...node, remaining: dyn.remaining, is_available: dyn.is_available };
                         return node;
                     });
                 });
             }
             if (state.treasure_chests) {
                 setTreasureChests((prev: TreasureChest[]) => {
                     const chestMap = new Map(state.treasure_chests!.map(c => [c.chest_id, c]));
                     return prev.map(chest => {
                         const dyn = chestMap.get(chest.chest_id);
                         if (dyn) return { ...chest, looted: dyn.looted, guard_entity_id: dyn.guard_entity_id };
                         return chest;
                     });
                 });
             }
             if (state.buildings) {
                 setBuildings((prev: Building[]) => {
                     const bldMap = new Map(state.buildings!.map(b => [b.building_id, b]));
                     return prev.map(bld => {
                        const dyn = bldMap.get(bld.building_id);
                        if (dyn) return { 
                            ...bld, 
                            storage_items: dyn.storage_items,
                            storage_used: dyn.storage_used,
                            storage_max: dyn.storage_max,
                            storage_level: dyn.storage_level
                        };
                        return bld;
                     });
                 });
             }
         }
      } catch (err) {
        // quiet fail
      } finally {
        pollingStatus = false;
      }
    };
    
    pollInterval = setInterval(fallbackPoll, 500);

    return () => {
      if (ws) ws.close();
      if (pollInterval) clearInterval(pollInterval);
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
    };
  }, [mapData]);

  const sendControl = useCallback(async (action: string) => {
    try {
      if (action === 'pause') {
        await fetch(`${API_BASE}/control/pause`, { method: 'POST' });
      } else if (action === 'resume') {
        await fetch(`${API_BASE}/control/resume`, { method: 'POST' });
      } else {
        console.error(`Unsupported control action: ${action}`);
      }
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
    treasureChests,
    regions,
    manifest,
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
