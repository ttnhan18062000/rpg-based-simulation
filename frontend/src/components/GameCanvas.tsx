import { useRef, useState, useCallback, useEffect, useMemo } from 'react';
import { ZoomIn, ZoomOut, Maximize2, ChevronDown, ChevronRight, MapPin } from 'lucide-react';
import type { MapData, Entity, GroundItem, Building, ResourceNode } from '@/types/api';
import { useCanvas } from '@/hooks/useCanvas';
import { CELL_SIZE, TILE_COLORS, TILE_COLORS_DIM, KIND_COLORS } from '@/constants/colors';

interface GameCanvasProps {
  mapData: MapData | null;
  entities: Entity[];
  groundItems: GroundItem[];
  buildings: Building[];
  resourceNodes: ResourceNode[];
  selectedEntityId: number | null;
  onEntityClick: (id: number | null) => void;
  onGroundItemClick?: (x: number, y: number) => void;
  onBuildingClick?: (building: Building) => void;
}

const MINIMAP_SCALE = 2;

const BUILDING_COLORS: Record<string, string> = {
  store: '#38bdf8',
  blacksmith: '#f59e0b',
  guild: '#818cf8',
  class_hall: '#c084fc',
  inn: '#fb923c',
  hero_house: '#34d399',
};

const MIN_ZOOM = 0.5;
const MAX_ZOOM = 3.0;
const ZOOM_STEP = 0.15;

const MM_DEFAULT_W = 180;
const MM_DEFAULT_H = 180;
const MM_MIN_SIZE = 80;
const MM_MAX_SIZE = 400;
const MM_MIN_ZOOM = 1.0;
const MM_MAX_ZOOM = 5.0;
const MM_ZOOM_STEP = 0.3;

const LOCATION_TILES: Record<number, { name: string; color: string }> = {
  4: { name: 'Enemy Camp', color: '#f87171' },
  5: { name: 'Sanctuary', color: '#818cf8' },
  12: { name: 'Ruins', color: '#a0906a' },
  13: { name: 'Dungeon', color: '#e06080' },
};

interface LocationEntry {
  name: string;
  color: string;
  x: number;
  y: number;
}

export function GameCanvas({ mapData, entities, groundItems, buildings, resourceNodes, selectedEntityId, onEntityClick, onGroundItemClick, onBuildingClick }: GameCanvasProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const minimapRef = useRef<HTMLCanvasElement>(null);
  const mmContainerRef = useRef<HTMLDivElement>(null);

  // State — zoom declared before useCanvas so it can be passed
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [zoom, setZoom] = useState(1.0);
  const [mmZoom, setMmZoom] = useState(1.0);
  const [mmSize, setMmSize] = useState({ w: MM_DEFAULT_W, h: MM_DEFAULT_H });
  const [locationsOpen, setLocationsOpen] = useState(false);

  const {
    gridRef, entityRef, overlayRef,
    handleCanvasClick, handleCanvasHover, handleCanvasLeave,
    hoverInfo,
  } = useCanvas(mapData, entities, groundItems, buildings, resourceNodes, selectedEntityId, onEntityClick, onGroundItemClick, onBuildingClick, zoom);

  const dragRef = useRef<{ startX: number; startY: number; panX: number; panY: number } | null>(null);
  const isDraggingRef = useRef(false);
  const mmResizeRef = useRef<{ startX: number; startY: number; startW: number; startH: number } | null>(null);

  const width = mapData ? mapData.width * CELL_SIZE : 0;
  const height = mapData ? mapData.height * CELL_SIZE : 0;
  const mmW = mapData ? mapData.width * MINIMAP_SCALE : 0;
  const mmH = mapData ? mapData.height * MINIMAP_SCALE : 0;

  // Find selected entity for minimap fog
  const selectedEnt = entities.find(e => e.id === selectedEntityId) ?? null;

  // Fit scale: CSS-scale minimap canvas to fit in the container
  const mmFitScale = mmW > 0 && mmH > 0 ? Math.min(mmSize.w / mmW, mmSize.h / mmH) : 1;
  const mmTotalScale = mmFitScale * mmZoom;

  // Minimap pan offset — center on viewport when zoomed
  const mmOffset = useMemo(() => {
    if (!mapData || mmZoom <= 1) return { x: 0, y: 0 };
    const outer = containerRef.current;
    const vCenterTX = outer ? (-pan.x + outer.clientWidth / 2) / (CELL_SIZE * zoom) : mapData.width / 2;
    const vCenterTY = outer ? (-pan.y + outer.clientHeight / 2) / (CELL_SIZE * zoom) : mapData.height / 2;
    const vcCX = vCenterTX * MINIMAP_SCALE;
    const vcCY = vCenterTY * MINIMAP_SCALE;
    let tx = mmSize.w / (2 * mmTotalScale) - vcCX;
    let ty = mmSize.h / (2 * mmTotalScale) - vcCY;
    tx = Math.min(0, Math.max(mmSize.w / mmTotalScale - mmW, tx));
    ty = Math.min(0, Math.max(mmSize.h / mmTotalScale - mmH, ty));
    return { x: tx, y: ty };
  }, [mapData, pan, zoom, mmZoom, mmSize, mmW, mmH, mmTotalScale]);

  // Compute locations from map data + buildings
  const locations = useMemo<LocationEntry[]>(() => {
    if (!mapData) return [];
    const result: LocationEntry[] = [];
    const bNames: Record<string, string> = {
      store: 'General Store', blacksmith: 'Blacksmith', guild: 'Adventurer Guild',
      class_hall: 'Class Hall', inn: 'Inn', hero_house: "Hero's House",
    };
    const bColors: Record<string, string> = {
      store: '#38bdf8', blacksmith: '#f59e0b', guild: '#818cf8',
      class_hall: '#c084fc', inn: '#fb923c', hero_house: '#34d399',
    };
    for (const b of buildings) {
      result.push({ name: bNames[b.building_type] || b.name, color: bColors[b.building_type] || '#fff', x: b.x, y: b.y });
    }
    const visited = new Set<string>();
    for (let y = 0; y < mapData.height; y++) {
      for (let x = 0; x < mapData.width; x++) {
        const tile = mapData.grid[y][x];
        const locInfo = LOCATION_TILES[tile];
        if (!locInfo) continue;
        const key = `${x},${y}`;
        if (visited.has(key)) continue;
        const queue = [{ x, y }];
        visited.add(key);
        let sumX = 0, sumY = 0, count = 0;
        while (queue.length > 0) {
          const p = queue.shift()!;
          sumX += p.x; sumY += p.y; count++;
          for (const [dx, dy] of [[0,1],[0,-1],[1,0],[-1,0]]) {
            const nx = p.x + dx, ny = p.y + dy;
            if (nx < 0 || ny < 0 || nx >= mapData.width || ny >= mapData.height) continue;
            const nk = `${nx},${ny}`;
            if (visited.has(nk)) continue;
            if (mapData.grid[ny][nx] !== tile) continue;
            visited.add(nk);
            queue.push({ x: nx, y: ny });
          }
        }
        result.push({ name: locInfo.name, color: locInfo.color, x: Math.round(sumX / count), y: Math.round(sumY / count) });
      }
    }
    return result;
  }, [mapData, buildings]);

  // Scroll wheel — route to minimap zoom or world zoom
  const handleWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault();
    const mmEl = mmContainerRef.current;
    if (mmEl && mmEl.contains(e.target as Node)) {
      setMmZoom(prev => Math.min(MM_MAX_ZOOM, Math.max(MM_MIN_ZOOM, prev + (e.deltaY < 0 ? MM_ZOOM_STEP : -MM_ZOOM_STEP))));
    } else {
      setZoom(prev => Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, prev + (e.deltaY < 0 ? ZOOM_STEP : -ZOOM_STEP))));
    }
  }, []);

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if (e.button !== 0) return;
    dragRef.current = { startX: e.clientX, startY: e.clientY, panX: pan.x, panY: pan.y };
    isDraggingRef.current = false;
  }, [pan]);

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (!dragRef.current) {
      handleCanvasHover(e);
      return;
    }
    const dx = e.clientX - dragRef.current.startX;
    const dy = e.clientY - dragRef.current.startY;
    if (Math.abs(dx) > 3 || Math.abs(dy) > 3) isDraggingRef.current = true;
    if (isDraggingRef.current) {
      setPan({ x: dragRef.current.panX + dx, y: dragRef.current.panY + dy });
    }
  }, [handleCanvasHover]);

  const handleMouseUp = useCallback((e: React.MouseEvent) => {
    if (!isDraggingRef.current) {
      handleCanvasClick(e);
    }
    dragRef.current = null;
    isDraggingRef.current = false;
  }, [handleCanvasClick]);

  const handleMouseLeaveOuter = useCallback(() => {
    dragRef.current = null;
    isDraggingRef.current = false;
    handleCanvasLeave();
  }, [handleCanvasLeave]);

  // Minimap resize via drag handle
  const handleResizeMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    mmResizeRef.current = { startX: e.clientX, startY: e.clientY, startW: mmSize.w, startH: mmSize.h };
  }, [mmSize]);

  useEffect(() => {
    const onMove = (e: MouseEvent) => {
      if (!mmResizeRef.current) return;
      const dx = e.clientX - mmResizeRef.current.startX;
      const dy = e.clientY - mmResizeRef.current.startY;
      setMmSize({
        w: Math.min(MM_MAX_SIZE, Math.max(MM_MIN_SIZE, mmResizeRef.current.startW + dx)),
        h: Math.min(MM_MAX_SIZE, Math.max(MM_MIN_SIZE, mmResizeRef.current.startH + dy)),
      });
    };
    const onUp = () => { mmResizeRef.current = null; };
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
    return () => {
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('mouseup', onUp);
    };
  }, []);

  // Draw minimap
  useEffect(() => {
    const mc = minimapRef.current;
    if (!mc || !mapData) return;
    const ctx = mc.getContext('2d');
    if (!ctx) return;
    mc.width = mmW;
    mc.height = mmH;
    ctx.clearRect(0, 0, mmW, mmH);

    // Build explored set from selected entity's terrain memory
    const exploredSet = selectedEnt?.terrain_memory ? new Set(Object.keys(selectedEnt.terrain_memory)) : null;

    // Build visible set for entity filtering on minimap
    let visibleSet: Set<string> | null = null;
    if (selectedEnt) {
      visibleSet = new Set<string>();
      const vr = selectedEnt.vision_range || 6;
      for (let dy = -vr; dy <= vr; dy++) {
        for (let dx = -vr; dx <= vr; dx++) {
          if (Math.abs(dx) + Math.abs(dy) > vr) continue;
          visibleSet.add(`${selectedEnt.x + dx},${selectedEnt.y + dy}`);
        }
      }
    }

    // Tiles with fog-of-war
    for (let y = 0; y < mapData.height; y++) {
      for (let x = 0; x < mapData.width; x++) {
        const tile = mapData.grid[y][x];
        if (exploredSet && !exploredSet.has(`${x},${y}`)) {
          ctx.fillStyle = '#0a0b10';
        } else if (exploredSet) {
          ctx.fillStyle = TILE_COLORS_DIM[tile] || TILE_COLORS_DIM[0];
        } else {
          ctx.fillStyle = TILE_COLORS[tile] || TILE_COLORS[0];
        }
        ctx.fillRect(x * MINIMAP_SCALE, y * MINIMAP_SCALE, MINIMAP_SCALE, MINIMAP_SCALE);
      }
    }

    // Bright overlay for currently visible area
    if (selectedEnt && visibleSet) {
      for (const key of visibleSet) {
        const [vx, vy] = key.split(',').map(Number);
        if (vx >= 0 && vx < mapData.width && vy >= 0 && vy < mapData.height) {
          const tile = mapData.grid[vy][vx];
          ctx.fillStyle = TILE_COLORS[tile] || TILE_COLORS[0];
          ctx.fillRect(vx * MINIMAP_SCALE, vy * MINIMAP_SCALE, MINIMAP_SCALE, MINIMAP_SCALE);
        }
      }
    }

    // Entities as dots — filter by vision when spectating
    for (const ent of entities) {
      if (visibleSet && ent.id !== selectedEntityId && !visibleSet.has(`${ent.x},${ent.y}`)) continue;
      const color = KIND_COLORS[ent.kind] || '#888';
      ctx.fillStyle = color;
      const s = ent.kind === 'hero' ? MINIMAP_SCALE : Math.max(1, MINIMAP_SCALE - 1);
      ctx.fillRect(
        ent.x * MINIMAP_SCALE + (MINIMAP_SCALE - s) / 2,
        ent.y * MINIMAP_SCALE + (MINIMAP_SCALE - s) / 2,
        s, s,
      );
    }

    // Resource node markers — filter by vision when spectating
    for (const rn of resourceNodes) {
      if (visibleSet && !visibleSet.has(`${rn.x},${rn.y}`)) continue;
      ctx.fillStyle = rn.is_available ? '#7dd3a0' : '#4a5568';
      ctx.fillRect(rn.x * MINIMAP_SCALE, rn.y * MINIMAP_SCALE, MINIMAP_SCALE - 1, MINIMAP_SCALE - 1);
    }

    // Building markers on minimap
    for (const b of buildings) {
      ctx.fillStyle = BUILDING_COLORS[b.building_type] || '#fff';
      ctx.fillRect(b.x * MINIMAP_SCALE, b.y * MINIMAP_SCALE, MINIMAP_SCALE, MINIMAP_SCALE);
    }

    // Viewport rectangle
    const outer = containerRef.current;
    if (outer) {
      const vw = outer.clientWidth;
      const vh = outer.clientHeight;
      const vx = (-pan.x) / (CELL_SIZE * zoom) * MINIMAP_SCALE;
      const vy = (-pan.y) / (CELL_SIZE * zoom) * MINIMAP_SCALE;
      const vWidth = vw / (CELL_SIZE * zoom) * MINIMAP_SCALE;
      const vHeight = vh / (CELL_SIZE * zoom) * MINIMAP_SCALE;
      ctx.strokeStyle = 'rgba(255,255,255,0.6)';
      ctx.lineWidth = 1;
      ctx.strokeRect(vx, vy, vWidth, vHeight);
    }
  }, [mapData, entities, buildings, resourceNodes, selectedEnt, selectedEntityId, pan, zoom, mmW, mmH]);

  // Minimap click → jump to location (accounts for minimap zoom + pan offset)
  const handleMinimapClick = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    const outer = containerRef.current;
    const mmCont = mmContainerRef.current;
    if (!outer || !mmCont || !mapData) return;
    const rect = mmCont.getBoundingClientRect();
    const cx = e.clientX - rect.left;
    const cy = e.clientY - rect.top;
    // Reverse CSS transform: screen → canvas → tile
    const canvasX = cx / mmTotalScale - mmOffset.x;
    const canvasY = cy / mmTotalScale - mmOffset.y;
    const tileX = canvasX / MINIMAP_SCALE;
    const tileY = canvasY / MINIMAP_SCALE;
    setPan({
      x: -(tileX * CELL_SIZE * zoom - outer.clientWidth / 2),
      y: -(tileY * CELL_SIZE * zoom - outer.clientHeight / 2),
    });
  }, [mapData, zoom, mmTotalScale, mmOffset]);

  // Jump camera to a location (used by locations panel)
  const jumpToLocation = useCallback((x: number, y: number) => {
    const outer = containerRef.current;
    if (!outer) return;
    setPan({
      x: -(x * CELL_SIZE * zoom - outer.clientWidth / 2),
      y: -(y * CELL_SIZE * zoom - outer.clientHeight / 2),
    });
  }, [zoom]);

  return (
    <div
      ref={containerRef}
      className="relative flex-1 overflow-hidden bg-bg-primary"
      style={{ cursor: isDraggingRef.current ? 'grabbing' : 'crosshair' }}
      onWheel={handleWheel}
    >
      {!mapData ? (
        <div className="flex items-center justify-center h-full text-text-secondary text-sm animate-pulse">
          Loading map...
        </div>
      ) : (
        <div
          className="absolute"
          style={{ width: width * zoom, height: height * zoom, transform: `translate(${pan.x}px, ${pan.y}px)` }}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseLeaveOuter}
        >
          <canvas ref={gridRef} className="absolute top-0 left-0" style={{ zIndex: 1, transform: `scale(${zoom})`, transformOrigin: 'top left' }} />
          <canvas ref={entityRef} className="absolute top-0 left-0" style={{ zIndex: 2, transform: `scale(${zoom})`, transformOrigin: 'top left' }} />
          <canvas ref={overlayRef} className="absolute top-0 left-0" style={{ zIndex: 3, pointerEvents: 'none', transform: `scale(${zoom})`, transformOrigin: 'top left' }} />
        </div>
      )}

      {/* Minimap + Locations panel */}
      {mapData && (
        <div className="absolute top-2 left-2 z-40 flex flex-col">
          {/* Minimap container — resizable, zoomable */}
          <div
            ref={mmContainerRef}
            className="relative border border-border/50 rounded shadow-lg overflow-hidden bg-[#0a0b10]"
            style={{ width: mmSize.w, height: mmSize.h }}
          >
            <canvas
              ref={minimapRef}
              className="absolute top-0 left-0"
              style={{
                imageRendering: 'pixelated',
                cursor: 'pointer',
                transform: `scale(${mmTotalScale}) translate(${mmOffset.x}px, ${mmOffset.y}px)`,
                transformOrigin: 'top left',
              }}
              onClick={handleMinimapClick}
            />
            {/* Resize handle — bottom-right corner */}
            <div
              className="absolute bottom-0 right-0 w-2.5 h-2.5 cursor-se-resize opacity-40 hover:opacity-80 transition-opacity"
              style={{ background: 'linear-gradient(135deg, transparent 50%, rgba(255,255,255,0.5) 50%)' }}
              onMouseDown={handleResizeMouseDown}
            />
            {/* Minimap zoom indicator */}
            {mmZoom > 1.01 && (
              <div className="absolute top-0.5 right-0.5 px-1 py-px rounded text-[8px] font-bold text-white/60 bg-black/50 pointer-events-none">
                {Math.round(mmZoom * 100)}%
              </div>
            )}
          </div>

          {/* Locations panel */}
          <div className="mt-1 rounded border border-border/40 bg-bg-tertiary/90 shadow-lg" style={{ width: mmSize.w }}>
            <button
              onClick={() => setLocationsOpen(prev => !prev)}
              className="w-full flex items-center gap-1 px-2 py-1 text-[9px] font-bold uppercase tracking-wider
                         text-text-secondary hover:text-text-primary transition-colors cursor-pointer"
            >
              {locationsOpen ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
              <MapPin className="w-3 h-3" />
              Locations ({locations.length})
            </button>
            {locationsOpen && (
              <div className="max-h-40 overflow-y-auto border-t border-border/30">
                {locations.map((loc, i) => (
                  <button
                    key={i}
                    onClick={() => jumpToLocation(loc.x, loc.y)}
                    className="w-full flex items-center justify-between px-2 py-0.5 text-[9px] text-left
                               hover:bg-white/[0.04] transition-colors cursor-pointer"
                  >
                    <span className="font-semibold" style={{ color: loc.color }}>{loc.name}</span>
                    <span className="text-text-secondary">({loc.x}, {loc.y})</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Zoom controls */}
      <div className="absolute bottom-2 left-2 flex flex-col gap-1 z-40">
        <button
          onClick={() => setZoom(prev => Math.min(MAX_ZOOM, prev + ZOOM_STEP))}
          className="w-7 h-7 flex items-center justify-center bg-bg-tertiary border border-border rounded
                     text-text-secondary hover:text-text-primary hover:bg-bg-secondary transition-colors cursor-pointer"
          title="Zoom In"
        >
          <ZoomIn className="w-4 h-4" />
        </button>
        <button
          onClick={() => setZoom(1.0)}
          className="w-7 h-7 flex items-center justify-center bg-bg-tertiary border border-border rounded
                     text-text-secondary hover:text-text-primary hover:bg-bg-secondary transition-colors cursor-pointer
                     text-[9px] font-bold"
          title="Reset Zoom"
        >
          <Maximize2 className="w-3.5 h-3.5" />
        </button>
        <button
          onClick={() => setZoom(prev => Math.max(MIN_ZOOM, prev - ZOOM_STEP))}
          className="w-7 h-7 flex items-center justify-center bg-bg-tertiary border border-border rounded
                     text-text-secondary hover:text-text-primary hover:bg-bg-secondary transition-colors cursor-pointer"
          title="Zoom Out"
        >
          <ZoomOut className="w-4 h-4" />
        </button>
        <div className="text-center text-[9px] text-text-secondary font-mono">
          {Math.round(zoom * 100)}%
        </div>
      </div>

      {/* Hover tooltip */}
      {hoverInfo && (
        <div
          className="fixed z-50 pointer-events-none px-2 py-1 rounded text-[11px] font-semibold
                     bg-bg-tertiary border border-border text-text-primary shadow-lg whitespace-nowrap"
          style={{ left: hoverInfo.screenX + 12, top: hoverInfo.screenY - 8 }}
        >
          {hoverInfo.label}
        </div>
      )}
    </div>
  );
}
