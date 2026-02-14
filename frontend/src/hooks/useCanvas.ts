import { useRef, useEffect, useCallback, useState, useMemo } from 'react';
import type { Entity, EntitySlim, GroundItem, Building, ResourceNode } from '@/types/api';
import type { DecodedMapData } from '@/hooks/useSimulation';
import {
  TILE_COLORS, KIND_COLORS, STATE_COLORS, CELL_SIZE, LOOT_COLOR, RESOURCE_COLORS, TILE_NAMES,
} from '@/constants/colors';

export interface HoverInfo {
  screenX: number;
  screenY: number;
  label: string;
}

export function useCanvas(
  mapData: DecodedMapData | null,
  entities: EntitySlim[],
  selectedEntity: Entity | null,
  groundItems: GroundItem[],
  buildings: Building[],
  resourceNodes: ResourceNode[],
  selectedEntityId: number | null,
  onEntityClick: (id: number | null) => void,
  onGroundItemClick?: (x: number, y: number) => void,
  onBuildingClick?: (building: Building) => void,
  zoom: number = 1.0,
  isDraggingRef?: React.RefObject<boolean>,
) {
  const gridRef = useRef<HTMLCanvasElement>(null);
  const entityRef = useRef<HTMLCanvasElement>(null);
  const overlayRef = useRef<HTMLCanvasElement>(null);
  const gridDrawnRef = useRef(false);
  const [hoverInfo, setHoverInfo] = useState<HoverInfo | null>(null);
  const hoveredEntityIdRef = useRef<number | null>(null);
  const lastOverlayKeyRef = useRef('');
  const selectedEntRef = useRef(selectedEntity);
  selectedEntRef.current = selectedEntity;

  // The full selected entity (with terrain_memory, entity_memory, vision_range)
  const selectedEnt = selectedEntity;

  // Draw grid once
  useEffect(() => {
    if (!mapData || gridDrawnRef.current) return;
    const gc = gridRef.current;
    if (!gc) return;
    const ctx = gc.getContext('2d');
    if (!ctx) return;

    const w = mapData.width * CELL_SIZE;
    const h = mapData.height * CELL_SIZE;

    gc.width = w;
    gc.height = h;

    if (entityRef.current) {
      entityRef.current.width = w;
      entityRef.current.height = h;
    }
    // Overlay canvas is tile-resolution (512×512), CSS-scaled to match grid
    if (overlayRef.current) {
      overlayRef.current.width = mapData.width;
      overlayRef.current.height = mapData.height;
    }

    ctx.clearRect(0, 0, w, h);

    for (let y = 0; y < mapData.height; y++) {
      for (let x = 0; x < mapData.width; x++) {
        const tile = mapData.grid[y][x];
        ctx.fillStyle = TILE_COLORS[tile] || TILE_COLORS[0];
        ctx.fillRect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE);
      }
    }

    // Grid lines
    ctx.strokeStyle = 'rgba(255,255,255,0.03)';
    ctx.lineWidth = 0.5;
    for (let x = 0; x <= mapData.width; x++) {
      ctx.beginPath();
      ctx.moveTo(x * CELL_SIZE, 0);
      ctx.lineTo(x * CELL_SIZE, h);
      ctx.stroke();
    }
    for (let y = 0; y <= mapData.height; y++) {
      ctx.beginPath();
      ctx.moveTo(0, y * CELL_SIZE);
      ctx.lineTo(w, y * CELL_SIZE);
      ctx.stroke();
    }

    gridDrawnRef.current = true;
  }, [mapData]);

  // Draw entities + ground items every update
  useEffect(() => {
    // Skip expensive redraw while user is dragging — next poll after drag ends will catch up
    if (isDraggingRef?.current) return;
    const ec = entityRef.current;
    if (!ec) return;
    const ctx = ec.getContext('2d');
    if (!ctx) return;

    const w = ec.width;
    const h = ec.height;
    ctx.clearRect(0, 0, w, h);

    // Build spectated entity's visible tile set
    let visibleSet: Set<string> | null = null;
    if (selectedEnt) {
      visibleSet = new Set<string>();
      const vr = selectedEnt.vision_range ?? 6;
      for (let dy = -vr; dy <= vr; dy++) {
        for (let dx = -vr; dx <= vr; dx++) {
          if (Math.abs(dx) + Math.abs(dy) > vr) continue;
          const tx = selectedEnt.x + dx;
          const ty = selectedEnt.y + dy;
          visibleSet.add(`${tx},${ty}`);
        }
      }
    } else if (selectedEntityId != null) {
      // Entity selected but full data not yet received — hide all (fog covers everything)
      visibleSet = new Set<string>();
    }

    // Draw ground items
    for (const gi of groundItems) {
      // If spectating, only show loots within vision
      if (visibleSet && !visibleSet.has(`${gi.x},${gi.y}`)) continue;

      const cx = gi.x * CELL_SIZE + CELL_SIZE / 2;
      const cy = gi.y * CELL_SIZE + CELL_SIZE / 2;
      const size = CELL_SIZE * 0.28;

      ctx.save();
      ctx.shadowColor = LOOT_COLOR;
      ctx.shadowBlur = 4;
      // Draw as a small diamond
      ctx.beginPath();
      ctx.moveTo(cx, cy - size);
      ctx.lineTo(cx + size, cy);
      ctx.lineTo(cx, cy + size);
      ctx.lineTo(cx - size, cy);
      ctx.closePath();
      ctx.fillStyle = LOOT_COLOR;
      ctx.fill();
      ctx.restore();

      // Item count badge
      if (gi.items.length > 1) {
        ctx.fillStyle = '#fff';
        ctx.font = 'bold 7px monospace';
        ctx.textAlign = 'center';
        ctx.fillText(`${gi.items.length}`, cx, cy + 3);
      }
    }

    // Draw building markers
    const bColors: Record<string, string> = { store: '#38bdf8', blacksmith: '#f59e0b', guild: '#818cf8', class_hall: '#c084fc', inn: '#fb923c' };
    const bLabels: Record<string, string> = { store: 'S', blacksmith: 'B', guild: 'G', class_hall: 'C', inn: 'I' };
    for (const b of buildings) {
      const bx = b.x * CELL_SIZE;
      const by = b.y * CELL_SIZE;
      const bc = bColors[b.building_type] || '#fff';
      ctx.fillStyle = bc;
      ctx.globalAlpha = 0.35;
      ctx.fillRect(bx, by, CELL_SIZE, CELL_SIZE);
      ctx.globalAlpha = 1.0;
      ctx.strokeStyle = bc;
      ctx.lineWidth = 1.5;
      ctx.strokeRect(bx + 1, by + 1, CELL_SIZE - 2, CELL_SIZE - 2);
      ctx.fillStyle = '#fff';
      ctx.font = 'bold 9px monospace';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(bLabels[b.building_type] || '?', bx + CELL_SIZE / 2, by + CELL_SIZE / 2);
    }
    ctx.textBaseline = 'alphabetic';

    // Draw resource nodes
    for (const rn of resourceNodes) {
      if (visibleSet && !visibleSet.has(`${rn.x},${rn.y}`)) continue;
      const rx = rn.x * CELL_SIZE;
      const ry = rn.y * CELL_SIZE;
      const rc = RESOURCE_COLORS[rn.resource_type] || '#7dd3a0';
      if (rn.is_available) {
        ctx.fillStyle = rc;
        ctx.globalAlpha = 0.5;
        ctx.fillRect(rx + 2, ry + 2, CELL_SIZE - 4, CELL_SIZE - 4);
        ctx.globalAlpha = 1.0;
        ctx.strokeStyle = rc;
        ctx.lineWidth = 1;
        ctx.strokeRect(rx + 2, ry + 2, CELL_SIZE - 4, CELL_SIZE - 4);
      } else {
        ctx.fillStyle = '#4a5568';
        ctx.globalAlpha = 0.3;
        ctx.fillRect(rx + 3, ry + 3, CELL_SIZE - 6, CELL_SIZE - 6);
        ctx.globalAlpha = 1.0;
      }
    }

    // Draw combat engagement lines (only for spectated or hovered entity)
    const entityMap = new Map<number, EntitySlim>(entities.map(e => [e.id, e]));
    const focusId = selectedEntityId ?? hoveredEntityIdRef.current;
    if (focusId != null) {
      // Collect lines: from focused entity to its target + from any entity targeting focused entity
      const linePairs: { from: EntitySlim; to: EntitySlim }[] = [];
      for (const ent of entities) {
        if (ent.combat_target_id == null) continue;
        const target = entityMap.get(ent.combat_target_id);
        if (!target) continue;
        // Show if this entity IS the focused entity, or targets the focused entity
        if (ent.id !== focusId && ent.combat_target_id !== focusId) continue;
        // Fog-of-war: both must be visible when spectating
        if (visibleSet) {
          const entVis = ent.id === selectedEntityId || visibleSet.has(`${ent.x},${ent.y}`);
          const tgtVis = target.id === selectedEntityId || visibleSet.has(`${target.x},${target.y}`);
          if (!entVis || !tgtVis) continue;
        }
        linePairs.push({ from: ent, to: target });
      }
      for (const { from: ent, to: target } of linePairs) {
        const ax = ent.x * CELL_SIZE + CELL_SIZE / 2;
        const ay = ent.y * CELL_SIZE + CELL_SIZE / 2;
        const tx = target.x * CELL_SIZE + CELL_SIZE / 2;
        const ty = target.y * CELL_SIZE + CELL_SIZE / 2;
        const angle = Math.atan2(ty - ay, tx - ax);
        const isRanged = (ent.weapon_range || 1) > 1;
        // Offset endpoints away from entity centers so melee lines are visible
        const inset = CELL_SIZE * 0.4;
        const sx = ax + inset * Math.cos(angle);
        const sy = ay + inset * Math.sin(angle);
        const ex = tx - inset * Math.cos(angle);
        const ey = ty - inset * Math.sin(angle);
        ctx.beginPath();
        ctx.moveTo(sx, sy);
        ctx.lineTo(ex, ey);
        ctx.strokeStyle = isRanged ? 'rgba(96, 165, 250, 0.6)' : 'rgba(248, 113, 113, 0.6)';
        ctx.lineWidth = isRanged ? 1.5 : 1;
        ctx.setLineDash(isRanged ? [4, 3] : []);
        ctx.stroke();
        ctx.setLineDash([]);
        // Arrowhead at target end
        const headLen = 5;
        ctx.beginPath();
        ctx.moveTo(ex, ey);
        ctx.lineTo(ex - headLen * Math.cos(angle - 0.4), ey - headLen * Math.sin(angle - 0.4));
        ctx.moveTo(ex, ey);
        ctx.lineTo(ex - headLen * Math.cos(angle + 0.4), ey - headLen * Math.sin(angle + 0.4));
        ctx.strokeStyle = isRanged ? 'rgba(96, 165, 250, 0.8)' : 'rgba(248, 113, 113, 0.8)';
        ctx.lineWidth = 1.5;
        ctx.stroke();
      }
    }

    // Draw entities
    for (const ent of entities) {
      // If spectating, only draw entities within the spectated entity's vision
      if (visibleSet && ent.id !== selectedEntityId) {
        if (!visibleSet.has(`${ent.x},${ent.y}`)) continue;
      }

      const cx = ent.x * CELL_SIZE + CELL_SIZE / 2;
      const cy = ent.y * CELL_SIZE + CELL_SIZE / 2;
      const isHero = ent.kind === 'hero';
      const isSelected = ent.id === selectedEntityId;
      const color = KIND_COLORS[ent.kind] || '#888';
      const stateColor = STATE_COLORS[ent.state] || '#888';

      if (isHero) {
        const size = CELL_SIZE * 0.45;
        ctx.save();
        ctx.shadowColor = '#fbbf24';
        ctx.shadowBlur = 6;
        ctx.beginPath();
        ctx.moveTo(cx, cy - size);
        ctx.lineTo(cx + size, cy);
        ctx.lineTo(cx, cy + size);
        ctx.lineTo(cx - size, cy);
        ctx.closePath();
        ctx.fillStyle = color;
        ctx.fill();
        ctx.restore();

        ctx.beginPath();
        ctx.moveTo(cx, cy - size - 1.5);
        ctx.lineTo(cx + size + 1.5, cy);
        ctx.lineTo(cx, cy + size + 1.5);
        ctx.lineTo(cx - size - 1.5, cy);
        ctx.closePath();
        ctx.strokeStyle = stateColor;
        ctx.lineWidth = 1.5;
        ctx.stroke();
      } else {
        const radius = CELL_SIZE * 0.35;
        ctx.beginPath();
        ctx.arc(cx, cy, radius, 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.fill();
        ctx.beginPath();
        ctx.arc(cx, cy, radius + 1.5, 0, Math.PI * 2);
        ctx.strokeStyle = stateColor;
        ctx.lineWidth = 1.5;
        ctx.stroke();
      }

      if (isSelected) {
        ctx.beginPath();
        ctx.arc(cx, cy, CELL_SIZE * 0.55, 0, Math.PI * 2);
        ctx.strokeStyle = '#fff';
        ctx.lineWidth = 2;
        ctx.setLineDash([3, 3]);
        ctx.stroke();
        ctx.setLineDash([]);
      }

      // HP bar
      const barW = CELL_SIZE - 2;
      const barH = 2;
      const barX = ent.x * CELL_SIZE + 1;
      const barY = ent.y * CELL_SIZE - 4;
      const hpRatio = Math.max(0, ent.hp / ent.max_hp);
      ctx.fillStyle = 'rgba(0,0,0,0.6)';
      ctx.fillRect(barX, barY, barW, barH);
      const hpCol = hpRatio > 0.5 ? '#34d399' : hpRatio > 0.25 ? '#fbbf24' : '#f87171';
      ctx.fillStyle = hpCol;
      ctx.fillRect(barX, barY, barW * hpRatio, barH);

      // ID label
      ctx.fillStyle = isHero ? '#fff' : 'rgba(255,255,255,0.7)';
      ctx.font = isHero ? 'bold 8px monospace' : '8px monospace';
      ctx.textAlign = 'center';
      ctx.fillText(`${ent.id}`, cx, cy + 3);

      // Loot progress bar (below HP bar, shown when entity is channeling loot)
      if (ent.state === 'LOOTING' && ent.loot_progress > 0 && ent.loot_duration > 0) {
        const lpRatio = ent.loot_progress / ent.loot_duration;
        const lpBarW = CELL_SIZE - 2;
        const lpBarH = 2;
        const lpBarX = ent.x * CELL_SIZE + 1;
        const lpBarY = ent.y * CELL_SIZE + CELL_SIZE + 1;
        ctx.fillStyle = 'rgba(0,0,0,0.6)';
        ctx.fillRect(lpBarX, lpBarY, lpBarW, lpBarH);
        ctx.fillStyle = '#a3e635';
        ctx.fillRect(lpBarX, lpBarY, lpBarW * lpRatio, lpBarH);
      }
    }

    // --- Vision border, weapon range ring, ghost markers (drawn on entity canvas) ---
    if (selectedEnt) {
      const vr2 = selectedEnt.vision_range || 6;
      const visSet2 = new Set<string>();
      for (let dy = -vr2; dy <= vr2; dy++) {
        for (let dx = -vr2; dx <= vr2; dx++) {
          if (Math.abs(dx) + Math.abs(dy) > vr2) continue;
          visSet2.add(`${selectedEnt.x + dx},${selectedEnt.y + dy}`);
        }
      }

      // Vision border
      ctx.strokeStyle = 'rgba(74, 158, 255, 0.3)';
      ctx.lineWidth = 1;
      for (const key of visSet2) {
        const [vx, vy] = key.split(',').map(Number);
        const px = vx * CELL_SIZE;
        const py = vy * CELL_SIZE;
        if (!visSet2.has(`${vx},${vy - 1}`)) { ctx.beginPath(); ctx.moveTo(px, py); ctx.lineTo(px + CELL_SIZE, py); ctx.stroke(); }
        if (!visSet2.has(`${vx},${vy + 1}`)) { ctx.beginPath(); ctx.moveTo(px, py + CELL_SIZE); ctx.lineTo(px + CELL_SIZE, py + CELL_SIZE); ctx.stroke(); }
        if (!visSet2.has(`${vx - 1},${vy}`)) { ctx.beginPath(); ctx.moveTo(px, py); ctx.lineTo(px, py + CELL_SIZE); ctx.stroke(); }
        if (!visSet2.has(`${vx + 1},${vy}`)) { ctx.beginPath(); ctx.moveTo(px + CELL_SIZE, py); ctx.lineTo(px + CELL_SIZE, py + CELL_SIZE); ctx.stroke(); }
      }

      // Weapon range ring
      const wRange = selectedEnt.weapon_range || 1;
      const rangeSet = new Set<string>();
      for (let dy = -wRange; dy <= wRange; dy++) {
        for (let dx = -wRange; dx <= wRange; dx++) {
          if (Math.abs(dx) + Math.abs(dy) <= wRange) {
            rangeSet.add(`${selectedEnt.x + dx},${selectedEnt.y + dy}`);
          }
        }
      }
      ctx.strokeStyle = wRange > 1 ? 'rgba(251, 146, 60, 0.45)' : 'rgba(248, 113, 113, 0.4)';
      ctx.lineWidth = 1.5;
      for (const key of rangeSet) {
        const [rx, ry] = key.split(',').map(Number);
        const px = rx * CELL_SIZE;
        const py = ry * CELL_SIZE;
        if (!rangeSet.has(`${rx},${ry - 1}`)) { ctx.beginPath(); ctx.moveTo(px, py); ctx.lineTo(px + CELL_SIZE, py); ctx.stroke(); }
        if (!rangeSet.has(`${rx},${ry + 1}`)) { ctx.beginPath(); ctx.moveTo(px, py + CELL_SIZE); ctx.lineTo(px + CELL_SIZE, py + CELL_SIZE); ctx.stroke(); }
        if (!rangeSet.has(`${rx - 1},${ry}`)) { ctx.beginPath(); ctx.moveTo(px, py); ctx.lineTo(px, py + CELL_SIZE); ctx.stroke(); }
        if (!rangeSet.has(`${rx + 1},${ry}`)) { ctx.beginPath(); ctx.moveTo(px + CELL_SIZE, py); ctx.lineTo(px + CELL_SIZE, py + CELL_SIZE); ctx.stroke(); }
      }

      // Ghost entity markers
      if (selectedEnt.entity_memory) {
        const memSet2 = new Set(Object.keys(selectedEnt.terrain_memory || {}));
        const visEntIds = new Set<number>();
        for (const e of entities) {
          if (e.id === selectedEntityId) continue;
          if (visSet2.has(`${e.x},${e.y}`)) visEntIds.add(e.id);
        }
        for (const em of selectedEnt.entity_memory) {
          if (visEntIds.has(em.id)) continue;
          if (visSet2.has(`${em.x},${em.y}`)) continue;
          if (!memSet2.has(`${em.x},${em.y}`)) continue;
          const ecx = em.x * CELL_SIZE + CELL_SIZE / 2;
          const ecy = em.y * CELL_SIZE + CELL_SIZE / 2;
          const emColor = KIND_COLORS[em.kind] || '#888';
          ctx.beginPath();
          ctx.arc(ecx, ecy, CELL_SIZE * 0.25, 0, Math.PI * 2);
          ctx.fillStyle = emColor + '55';
          ctx.fill();
          ctx.strokeStyle = emColor + '88';
          ctx.lineWidth = 1;
          ctx.setLineDash([2, 2]);
          ctx.stroke();
          ctx.setLineDash([]);
          ctx.fillStyle = emColor + 'aa';
          ctx.font = '7px monospace';
          ctx.textAlign = 'center';
          ctx.fillText('?', ecx, ecy + 2.5);
        }
      }
    }
  }, [entities, groundItems, buildings, resourceNodes, selectedEntityId, selectedEntity]);

  // Stable overlay key — memoized to avoid O(n) Object.keys on every render
  const overlayKey = useMemo(() => {
    if (selectedEnt) {
      const memSize = selectedEnt.terrain_memory ? Object.keys(selectedEnt.terrain_memory).length : 0;
      const emSize = selectedEnt.entity_memory ? selectedEnt.entity_memory.length : 0;
      return `${selectedEnt.id}_${selectedEnt.x}_${selectedEnt.y}_${memSize}_${emSize}`;
    }
    if (selectedEntityId != null) return `pending_${selectedEntityId}`;
    return '';
  }, [selectedEnt, selectedEntityId]);

  // Draw fog overlay (tile-resolution 512×512 canvas, CSS-scaled to match grid)
  useEffect(() => {
    if (isDraggingRef?.current) return; // Skip during drag — catches up on next poll after drag ends
    const oc = overlayRef.current;
    if (!oc || !mapData) return;
    const ctx = oc.getContext('2d');
    if (!ctx) return;

    const tw = mapData.width;
    const th = mapData.height;

    // Ensure overlay is tile-resolution
    if (oc.width !== tw) oc.width = tw;
    if (oc.height !== th) oc.height = th;

    // No entity selected — clear fog overlay
    if (!selectedEntityId) {
      if (lastOverlayKeyRef.current !== '') {
        ctx.clearRect(0, 0, tw, th);
        lastOverlayKeyRef.current = '';
      }
      return;
    }

    // Entity selected but full data not yet received — show full fog
    if (!selectedEnt) {
      if (lastOverlayKeyRef.current !== overlayKey) {
        ctx.clearRect(0, 0, tw, th);
        ctx.fillStyle = 'rgba(0, 0, 0, 1.0)'; // fully opaque until data arrives
        ctx.fillRect(0, 0, tw, th);
        lastOverlayKeyRef.current = overlayKey;
      }
      return;
    }

    // Skip redraw if position and memory haven't changed
    if (overlayKey === lastOverlayKeyRef.current) return;
    lastOverlayKeyRef.current = overlayKey;

    ctx.clearRect(0, 0, tw, th);

    const vr = selectedEnt.vision_range || 6;
    const mem = selectedEnt.terrain_memory || {};

    // Build visible set
    const visibleSet = new Set<string>();
    for (let dy = -vr; dy <= vr; dy++) {
      for (let dx = -vr; dx <= vr; dx++) {
        if (Math.abs(dx) + Math.abs(dy) > vr) continue;
        const tx = selectedEnt.x + dx;
        const ty = selectedEnt.y + dy;
        if (tx >= 0 && tx < tw && ty >= 0 && ty < th) {
          visibleSet.add(`${tx},${ty}`);
        }
      }
    }

    const memSet = new Set(Object.keys(mem));

    // Draw fog at 1px per tile (canvas is 512×512, CSS-scaled to 8192×8192)
    // Three fog levels: visible=clear, explored=50% dim, unseen=fully black
    for (let y = 0; y < th; y++) {
      for (let x = 0; x < tw; x++) {
        const key = `${x},${y}`;
        if (visibleSet.has(key)) {
          continue; // brightness 100%
        } else if (memSet.has(key)) {
          ctx.fillStyle = 'rgba(0, 0, 0, 0.5)'; // explored fog — 50% brightness
          ctx.fillRect(x, y, 1, 1);
        } else {
          ctx.fillStyle = 'rgba(0, 0, 0, 1.0)'; // unseen — completely dark
          ctx.fillRect(x, y, 1, 1);
        }
      }
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mapData, overlayKey, selectedEntityId]);

  // Helper: build visible set for spectated entity
  const buildVisibleSet = useCallback(() => {
    if (!selectedEnt) return null;
    const vs = new Set<string>();
    const vr = selectedEnt.vision_range ?? 6;
    for (let dy = -vr; dy <= vr; dy++) {
      for (let dx = -vr; dx <= vr; dx++) {
        if (Math.abs(dx) + Math.abs(dy) > vr) continue;
        vs.add(`${selectedEnt.x + dx},${selectedEnt.y + dy}`);
      }
    }
    return vs;
  }, [selectedEnt]);

  // Click handler — entities first, then buildings, then ground items
  const handleCanvasClick = useCallback((evt: React.MouseEvent) => {
    const ec = entityRef.current;
    if (!ec) return;
    const rect = ec.getBoundingClientRect();
    const mx = evt.clientX - rect.left;
    const my = evt.clientY - rect.top;
    // Account for CSS scale(zoom) — getBoundingClientRect returns visually scaled rect
    const gx = Math.floor(mx / (CELL_SIZE * zoom));
    const gy = Math.floor(my / (CELL_SIZE * zoom));
    // Fog-of-war gating: only allow clicks on visible tiles when spectating
    const visibleSet = buildVisibleSet();
    const tileVisible = !visibleSet || visibleSet.has(`${gx},${gy}`);
    const hit = entities.find(e => e.x === gx && e.y === gy);
    if (hit && tileVisible) {
      onEntityClick(hit.id);
      return;
    }
    // Check building click (priority over ground items)
    const bldg = buildings.find(b => b.x === gx && b.y === gy);
    if (bldg && onBuildingClick && tileVisible) {
      onBuildingClick(bldg);
      return;
    }
    // Check ground item click
    const gi = groundItems.find(g => g.x === gx && g.y === gy);
    if (gi && onGroundItemClick && tileVisible) {
      onGroundItemClick(gx, gy);
      return;
    }
    onEntityClick(null);
  }, [entities, groundItems, buildings, onEntityClick, onGroundItemClick, onBuildingClick, zoom, buildVisibleSet]);

  // Hover handler — collects ALL info on the hovered tile (terrain + entities + buildings + loot + resources)
  const handleCanvasHover = useCallback((evt: React.MouseEvent) => {
    const ec = entityRef.current;
    if (!ec) return;
    const rect = ec.getBoundingClientRect();
    const mx = evt.clientX - rect.left;
    const my = evt.clientY - rect.top;
    // Account for CSS scale(zoom)
    const gx = Math.floor(mx / (CELL_SIZE * zoom));
    const gy = Math.floor(my / (CELL_SIZE * zoom));

    // Build visible set for spectated entity
    const visibleSet = buildVisibleSet();
    const tileVisible = !visibleSet || visibleSet.has(`${gx},${gy}`);
    const memSet = selectedEnt?.terrain_memory ? new Set(Object.keys(selectedEnt.terrain_memory)) : null;
    const tileExplored = !memSet || memSet.has(`${gx},${gy}`);

    // Collect all tooltip lines for this tile
    const lines: string[] = [];

    // Unseen tiles — show nothing except coordinates
    if (!tileVisible && !tileExplored) {
      lines.push(`🗺 Unexplored (${gx}, ${gy})`);
      setHoverInfo({ screenX: evt.clientX, screenY: evt.clientY, label: lines.join('\n') });
      return;
    }

    // --- Terrain ---
    if (mapData && gx >= 0 && gx < mapData.width && gy >= 0 && gy < mapData.height) {
      const tile = mapData.grid[gy]?.[gx];
      if (tile != null) {
        const tileName = TILE_NAMES[tile] || `Tile ${tile}`;
        lines.push(`🗺 ${tileName} (${gx}, ${gy})`);
      }
    }

    // --- Entities (all on this tile) ---
    const tileEntities = entities.filter(e => e.x === gx && e.y === gy);
    hoveredEntityIdRef.current = tileEntities[0]?.id ?? null;
    for (const ent of tileEntities) {
      // Fog check: skip hidden entities (unless it's the spectated one)
      if (visibleSet && ent.id !== selectedEntityId && !tileVisible) continue;
      const parts = [`#${ent.id} ${ent.kind} Lv${ent.level}`];
      // Show class/stamina from full entity if this is the selected entity
      if (selectedEnt && ent.id === selectedEntityId) {
        if (selectedEnt.hero_class && selectedEnt.hero_class !== 'none') {
          parts[0] += ` (${selectedEnt.hero_class})`;
        }
        parts.push(`HP:${ent.hp}/${ent.max_hp}`);
        if (selectedEnt.max_stamina > 0) {
          parts.push(`STA:${selectedEnt.stamina}/${selectedEnt.max_stamina}`);
        }
      } else {
        parts.push(`HP:${ent.hp}/${ent.max_hp}`);
      }
      parts.push(ent.state);
      lines.push(`⚔ ${parts.join(' | ')}`);
    }

    // --- Ghost markers (remembered entities in fog) ---
    if (selectedEnt?.entity_memory && visibleSet && !tileVisible) {
      const memSet = new Set(Object.keys(selectedEnt.terrain_memory || {}));
      const ghosts = selectedEnt.entity_memory.filter(
        m => m.x === gx && m.y === gy && !visibleSet.has(`${m.x},${m.y}`) && memSet.has(`${gx},${gy}`)
      );
      for (const mem of ghosts) {
        lines.push(`👻 Ghost: #${mem.id} ${mem.kind} Lv${mem.level || '?'} (ATK:${mem.atk || '?'} HP:${mem.hp}/${mem.max_hp}) — tick ${mem.tick}`);
      }
    }

    // --- Buildings ---
    if (tileVisible) {
      const tileBuildings = buildings.filter(b => b.x === gx && b.y === gy);
      for (const bldg of tileBuildings) {
        lines.push(`🏛 ${bldg.name}`);
      }
    }

    // --- Ground items ---
    if (tileVisible) {
      const tileLoots = groundItems.filter(g => g.x === gx && g.y === gy);
      for (const gi of tileLoots) {
        const count = gi.items.length;
        if (count === 1) {
          lines.push(`💎 Loot: ${gi.items[0].replace(/_/g, ' ')}`);
        } else {
          lines.push(`💎 Loot bag (${count} items)`);
        }
      }
    }

    // --- Resource nodes ---
    if (tileVisible) {
      const tileNodes = resourceNodes.filter(r => r.x === gx && r.y === gy);
      for (const rn of tileNodes) {
        const status = rn.is_available ? `${rn.remaining}/${rn.max_harvests}` : 'depleted';
        lines.push(`🌿 ${rn.name} (${status}) → ${rn.yields_item.replace(/_/g, ' ')}`);
      }
    }

    if (lines.length > 0) {
      setHoverInfo({
        screenX: evt.clientX,
        screenY: evt.clientY,
        label: lines.join('\n'),
      });
    } else {
      setHoverInfo(null);
    }
  }, [entities, groundItems, resourceNodes, buildings, mapData, selectedEntityId, selectedEnt, buildVisibleSet, zoom]);

  const handleCanvasLeave = useCallback(() => {
    hoveredEntityIdRef.current = null;
    setHoverInfo(null);
  }, []);

  return {
    gridRef,
    entityRef,
    overlayRef,
    handleCanvasClick,
    handleCanvasHover,
    handleCanvasLeave,
    hoverInfo,
  };
}
