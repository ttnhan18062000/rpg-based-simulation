import { useRef, useState, useCallback, useEffect } from 'react';
import { ZoomIn, ZoomOut, Maximize2 } from 'lucide-react';
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

const MINIMAP_SCALE = 3; // pixels per tile on minimap

const BUILDING_COLORS: Record<string, string> = {
  store: '#38bdf8',
  blacksmith: '#f59e0b',
  guild: '#818cf8',
  class_hall: '#c084fc',
  inn: '#fb923c',
};

const MIN_ZOOM = 0.5;
const MAX_ZOOM = 3.0;
const ZOOM_STEP = 0.15;

export function GameCanvas({ mapData, entities, groundItems, buildings, resourceNodes, selectedEntityId, onEntityClick, onGroundItemClick, onBuildingClick }: GameCanvasProps) {
  const {
    gridRef, entityRef, overlayRef,
    handleCanvasClick, handleCanvasHover, handleCanvasLeave,
    hoverInfo,
  } = useCanvas(mapData, entities, groundItems, buildings, resourceNodes, selectedEntityId, onEntityClick, onGroundItemClick, onBuildingClick);

  const containerRef = useRef<HTMLDivElement>(null);
  const minimapRef = useRef<HTMLCanvasElement>(null);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [zoom, setZoom] = useState(1.0);
  const dragRef = useRef<{ startX: number; startY: number; panX: number; panY: number } | null>(null);
  const isDraggingRef = useRef(false);

  const width = mapData ? mapData.width * CELL_SIZE : 0;
  const height = mapData ? mapData.height * CELL_SIZE : 0;
  const mmW = mapData ? mapData.width * MINIMAP_SCALE : 0;
  const mmH = mapData ? mapData.height * MINIMAP_SCALE : 0;

  // Find selected entity for minimap fog
  const selectedEnt = entities.find(e => e.id === selectedEntityId) ?? null;

  // Drag to pan
  // Scroll wheel zoom
  const handleWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault();
    setZoom(prev => Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, prev + (e.deltaY < 0 ? ZOOM_STEP : -ZOOM_STEP))));
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

    // Tiles with fog-of-war
    for (let y = 0; y < mapData.height; y++) {
      for (let x = 0; x < mapData.width; x++) {
        const tile = mapData.grid[y][x];
        if (exploredSet && !exploredSet.has(`${x},${y}`)) {
          // Unexplored: very dark
          ctx.fillStyle = '#0a0b10';
        } else if (exploredSet) {
          // Explored but use dim colors
          ctx.fillStyle = TILE_COLORS_DIM[tile] || TILE_COLORS_DIM[0];
        } else {
          ctx.fillStyle = TILE_COLORS[tile] || TILE_COLORS[0];
        }
        ctx.fillRect(x * MINIMAP_SCALE, y * MINIMAP_SCALE, MINIMAP_SCALE, MINIMAP_SCALE);
      }
    }

    // Bright overlay for currently visible area
    if (selectedEnt) {
      const vr = selectedEnt.vision_range || 6;
      for (let dy = -vr; dy <= vr; dy++) {
        for (let dx = -vr; dx <= vr; dx++) {
          if (Math.abs(dx) + Math.abs(dy) > vr) continue;
          const vx = selectedEnt.x + dx;
          const vy = selectedEnt.y + dy;
          if (vx >= 0 && vx < mapData.width && vy >= 0 && vy < mapData.height) {
            const tile = mapData.grid[vy][vx];
            ctx.fillStyle = TILE_COLORS[tile] || TILE_COLORS[0];
            ctx.fillRect(vx * MINIMAP_SCALE, vy * MINIMAP_SCALE, MINIMAP_SCALE, MINIMAP_SCALE);
          }
        }
      }
    }

    // Entities as dots
    for (const ent of entities) {
      const color = KIND_COLORS[ent.kind] || '#888';
      ctx.fillStyle = color;
      const s = ent.kind === 'hero' ? MINIMAP_SCALE : Math.max(1, MINIMAP_SCALE - 1);
      ctx.fillRect(
        ent.x * MINIMAP_SCALE + (MINIMAP_SCALE - s) / 2,
        ent.y * MINIMAP_SCALE + (MINIMAP_SCALE - s) / 2,
        s, s,
      );
    }

    // Resource node markers on minimap
    for (const rn of resourceNodes) {
      ctx.fillStyle = rn.is_available ? '#7dd3a0' : '#4a5568';
      ctx.fillRect(rn.x * MINIMAP_SCALE, rn.y * MINIMAP_SCALE, MINIMAP_SCALE - 1, MINIMAP_SCALE - 1);
    }

    // Building markers on minimap
    for (const b of buildings) {
      ctx.fillStyle = BUILDING_COLORS[b.building_type] || '#fff';
      ctx.fillRect(b.x * MINIMAP_SCALE, b.y * MINIMAP_SCALE, MINIMAP_SCALE, MINIMAP_SCALE);
    }

    // Viewport rectangle (accounting for zoom)
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
  }, [mapData, entities, buildings, resourceNodes, selectedEnt, pan, zoom, mmW, mmH]);

  // Minimap click → jump to location
  const handleMinimapClick = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    const mc = minimapRef.current;
    const outer = containerRef.current;
    if (!mc || !outer || !mapData) return;
    const rect = mc.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;
    const tileX = mx / MINIMAP_SCALE;
    const tileY = my / MINIMAP_SCALE;
    const newPanX = -(tileX * CELL_SIZE * zoom - outer.clientWidth / 2);
    const newPanY = -(tileY * CELL_SIZE * zoom - outer.clientHeight / 2);
    setPan({ x: newPanX, y: newPanY });
  }, [mapData, zoom]);

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

      {/* Minimap */}
      {mapData && (
        <canvas
          ref={minimapRef}
          className="absolute top-2 left-2 border border-border/50 rounded shadow-lg z-40"
          style={{ width: mmW, height: mmH, cursor: 'pointer', imageRendering: 'pixelated' }}
          onClick={handleMinimapClick}
        />
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
