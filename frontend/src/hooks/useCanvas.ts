import { useRef, useEffect, useCallback, useState } from 'react';
import type { MapData, Entity, GroundItem, Building, ResourceNode } from '@/types/api';
import {
  TILE_COLORS, TILE_COLORS_DIM, KIND_COLORS, STATE_COLORS, CELL_SIZE, LOOT_COLOR, RESOURCE_COLORS,
} from '@/constants/colors';

export interface HoverInfo {
  screenX: number;
  screenY: number;
  label: string;
}

export function useCanvas(
  mapData: MapData | null,
  entities: Entity[],
  groundItems: GroundItem[],
  buildings: Building[],
  resourceNodes: ResourceNode[],
  selectedEntityId: number | null,
  onEntityClick: (id: number | null) => void,
  onGroundItemClick?: (x: number, y: number) => void,
  onBuildingClick?: (building: Building) => void,
  zoom: number = 1.0,
) {
  const gridRef = useRef<HTMLCanvasElement>(null);
  const entityRef = useRef<HTMLCanvasElement>(null);
  const overlayRef = useRef<HTMLCanvasElement>(null);
  const gridDrawnRef = useRef(false);
  const [hoverInfo, setHoverInfo] = useState<HoverInfo | null>(null);

  // Build selected entity's visible set (reused across effects)
  const selectedEnt = entities.find(e => e.id === selectedEntityId) ?? null;

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
    if (overlayRef.current) {
      overlayRef.current.width = w;
      overlayRef.current.height = h;
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
      const vr = selectedEnt.vision_range || 6;
      for (let dy = -vr; dy <= vr; dy++) {
        for (let dx = -vr; dx <= vr; dx++) {
          if (Math.abs(dx) + Math.abs(dy) > vr) continue;
          const tx = selectedEnt.x + dx;
          const ty = selectedEnt.y + dy;
          visibleSet.add(`${tx},${ty}`);
        }
      }
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
  }, [entities, groundItems, buildings, resourceNodes, selectedEntityId, selectedEnt]);

  // Draw overlay (fog of war + ghost markers)
  useEffect(() => {
    const oc = overlayRef.current;
    if (!oc || !mapData) return;
    const ctx = oc.getContext('2d');
    if (!ctx) return;

    const w = oc.width;
    const h = oc.height;
    ctx.clearRect(0, 0, w, h);

    if (!selectedEnt) return;

    const vr = selectedEnt.vision_range || 6;
    const mem = selectedEnt.terrain_memory || {};

    // Build visible set
    const visibleSet = new Set<string>();
    for (let dy = -vr; dy <= vr; dy++) {
      for (let dx = -vr; dx <= vr; dx++) {
        if (Math.abs(dx) + Math.abs(dy) > vr) continue;
        const tx = selectedEnt.x + dx;
        const ty = selectedEnt.y + dy;
        if (tx >= 0 && tx < mapData.width && ty >= 0 && ty < mapData.height) {
          visibleSet.add(`${tx},${ty}`);
        }
      }
    }

    const memSet = new Set(Object.keys(mem));

    for (let y = 0; y < mapData.height; y++) {
      for (let x = 0; x < mapData.width; x++) {
        const key = `${x},${y}`;
        if (visibleSet.has(key)) {
          continue;
        } else if (memSet.has(key)) {
          ctx.fillStyle = 'rgba(0, 0, 0, 0.55)';
          ctx.fillRect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE);
          const tile = mem[key];
          const dimColor = TILE_COLORS_DIM[tile] || TILE_COLORS_DIM[0];
          ctx.fillStyle = dimColor + '40';
          ctx.fillRect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE);
        } else {
          ctx.fillStyle = 'rgba(0, 0, 0, 0.82)';
          ctx.fillRect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE);
        }
      }
    }

    // Vision border
    ctx.strokeStyle = 'rgba(74, 158, 255, 0.3)';
    ctx.lineWidth = 1;
    for (const key of visibleSet) {
      const [vx, vy] = key.split(',').map(Number);
      const px = vx * CELL_SIZE;
      const py = vy * CELL_SIZE;
      if (!visibleSet.has(`${vx},${vy - 1}`)) { ctx.beginPath(); ctx.moveTo(px, py); ctx.lineTo(px + CELL_SIZE, py); ctx.stroke(); }
      if (!visibleSet.has(`${vx},${vy + 1}`)) { ctx.beginPath(); ctx.moveTo(px, py + CELL_SIZE); ctx.lineTo(px + CELL_SIZE, py + CELL_SIZE); ctx.stroke(); }
      if (!visibleSet.has(`${vx - 1},${vy}`)) { ctx.beginPath(); ctx.moveTo(px, py); ctx.lineTo(px, py + CELL_SIZE); ctx.stroke(); }
      if (!visibleSet.has(`${vx + 1},${vy}`)) { ctx.beginPath(); ctx.moveTo(px + CELL_SIZE, py); ctx.lineTo(px + CELL_SIZE, py + CELL_SIZE); ctx.stroke(); }
    }

    // Ghost entity markers — only from entity_memory, not visible ones
    if (selectedEnt.entity_memory) {
      // Build a set of entity IDs that are currently visible on the entity layer
      const visibleEntityIds = new Set<number>();
      for (const e of entities) {
        if (e.id === selectedEntityId) continue;
        if (visibleSet.has(`${e.x},${e.y}`)) {
          visibleEntityIds.add(e.id);
        }
      }

      for (const em of selectedEnt.entity_memory) {
        // Skip if this entity is currently visible in vision
        if (visibleEntityIds.has(em.id)) continue;
        // Skip if the remembered position is within vision (entity moved away)
        if (visibleSet.has(`${em.x},${em.y}`)) continue;
        // Only show ghost in remembered (explored) tiles
        const memKey = `${em.x},${em.y}`;
        if (!memSet.has(memKey)) continue;

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
  }, [mapData, entities, selectedEntityId, selectedEnt]);

  // Helper: build visible set for spectated entity
  const buildVisibleSet = useCallback(() => {
    if (!selectedEnt) return null;
    const vs = new Set<string>();
    const vr = selectedEnt.vision_range || 6;
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
    const hit = entities.find(e => e.x === gx && e.y === gy);
    if (hit) {
      onEntityClick(hit.id);
      return;
    }
    // Check building click (priority over ground items)
    const bldg = buildings.find(b => b.x === gx && b.y === gy);
    if (bldg && onBuildingClick) {
      onBuildingClick(bldg);
      return;
    }
    // Check ground item click
    const gi = groundItems.find(g => g.x === gx && g.y === gy);
    if (gi && onGroundItemClick) {
      onGroundItemClick(gx, gy);
      return;
    }
    onEntityClick(null);
  }, [entities, groundItems, buildings, onEntityClick, onGroundItemClick, onBuildingClick, zoom]);

  // Hover handler — respects fog of war when spectating
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

    // Check entities — skip if hidden by fog of war
    const ent = entities.find(e => e.x === gx && e.y === gy);
    if (ent) {
      // If spectating, only show hover for the spectated entity or those within vision
      if (visibleSet && ent.id !== selectedEntityId && !visibleSet.has(`${gx},${gy}`)) {
        // Entity is in fog — check if it's a ghost in memory
        if (selectedEnt?.entity_memory) {
          const mem = selectedEnt.entity_memory.find(m => m.x === gx && m.y === gy && !m.visible);
          if (mem) {
            setHoverInfo({
              screenX: evt.clientX,
              screenY: evt.clientY,
              label: `Ghost: #${mem.id} ${mem.kind} Lv${mem.level || '?'} (ATK:${mem.atk || '?'}) — last seen tick ${mem.tick}`,
            });
            return;
          }
        }
        setHoverInfo(null);
        return;
      }
      const parts = [`#${ent.id} ${ent.kind} Lv${ent.level}`];
      if (ent.hero_class && ent.hero_class !== 'none') {
        parts[0] += ` (${ent.hero_class})`;
      }
      parts.push(`HP:${ent.hp}/${ent.max_hp}`);
      if (ent.max_stamina > 0) {
        parts.push(`STA:${ent.stamina}/${ent.max_stamina}`);
      }
      parts.push(ent.state);
      setHoverInfo({
        screenX: evt.clientX,
        screenY: evt.clientY,
        label: parts.join(' | '),
      });
      return;
    }

    // Check ghost markers on overlay (remembered entities in fog)
    if (selectedEnt?.entity_memory && visibleSet) {
      const mem = selectedEnt.entity_memory.find(
        m => m.x === gx && m.y === gy && !visibleSet.has(`${m.x},${m.y}`)
      );
      if (mem) {
        const memSet = new Set(Object.keys(selectedEnt.terrain_memory || {}));
        if (memSet.has(`${gx},${gy}`)) {
          setHoverInfo({
            screenX: evt.clientX,
            screenY: evt.clientY,
            label: `Ghost: #${mem.id} ${mem.kind} Lv${mem.level || '?'} (ATK:${mem.atk || '?'} HP:${mem.hp}/${mem.max_hp}) — tick ${mem.tick}`,
          });
          return;
        }
      }
    }

    // Check buildings
    const bldg = buildings.find(b => b.x === gx && b.y === gy);
    if (bldg) {
      setHoverInfo({
        screenX: evt.clientX,
        screenY: evt.clientY,
        label: `${bldg.name}`,
      });
      return;
    }

    // Check ground items — also respect fog
    const gi = groundItems.find(g => g.x === gx && g.y === gy);
    if (gi && (!visibleSet || visibleSet.has(`${gx},${gy}`))) {
      const count = gi.items.length;
      setHoverInfo({
        screenX: evt.clientX,
        screenY: evt.clientY,
        label: count === 1 ? `Loot: ${gi.items[0].replace(/_/g, ' ')}` : `Loot bag (${count} items)`,
      });
      return;
    }

    // Check resource nodes
    const rn = resourceNodes.find(r => r.x === gx && r.y === gy);
    if (rn && (!visibleSet || visibleSet.has(`${gx},${gy}`))) {
      const status = rn.is_available ? `${rn.remaining}/${rn.max_harvests}` : 'depleted';
      setHoverInfo({
        screenX: evt.clientX,
        screenY: evt.clientY,
        label: `${rn.name} (${status}) → ${rn.yields_item.replace(/_/g, ' ')}`,
      });
      return;
    }

    setHoverInfo(null);
  }, [entities, groundItems, resourceNodes, selectedEntityId, selectedEnt, buildVisibleSet, zoom]);

  const handleCanvasLeave = useCallback(() => {
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
