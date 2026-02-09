# Minimap & Locations Panel

## Overview

The minimap is rendered in the top-left corner of the game canvas. It provides a bird's-eye view of the entire map, shows entity positions, buildings, resource nodes, and a viewport rectangle indicating the current camera position.

## Files

| File | Role |
|------|------|
| `frontend/src/components/GameCanvas.tsx` | Minimap container, resize, zoom, locations panel, click-to-jump |
| `frontend/src/hooks/useCanvas.ts` | Main world canvas rendering, click/hover with zoom-corrected coordinates |
| `frontend/src/constants/colors.ts` | `CELL_SIZE`, tile colors, dim tile colors, entity kind colors |

## Minimap Features

### Smaller Default Size

- `MINIMAP_SCALE = 2` pixels per tile (reduced from 3).
- Default container size: **180 × 180 px** (`MM_DEFAULT_W`, `MM_DEFAULT_H`).
- The canvas is CSS-scaled to fit inside the container using `mmFitScale`.

### Resizable (Drag Edges)

- A resize handle sits at the bottom-right corner of the minimap container.
- Drag it to resize between `MM_MIN_SIZE` (80 px) and `MM_MAX_SIZE` (400 px).
- The canvas resolution stays at full map size; only CSS scale changes.

### Separate Zoom

- Scrolling the mouse wheel **over the minimap** zooms the minimap (`mmZoom`, range 1×–5×).
- Scrolling **over the world canvas** zooms the world (`zoom`, range 0.5×–3×).
- Detection uses `mmContainerRef.contains(e.target)` inside the shared `onWheel` handler.
- When minimap is zoomed in (`mmZoom > 1`), it auto-centers on the current viewport position via `mmOffset`.

### Click to Jump

- Clicking anywhere on the minimap moves the world camera to that location.
- The click handler reverses the CSS `scale()` + `translate()` transform to recover tile coordinates accurately at any minimap zoom level.

## World Zoom – Hover & Click Fix

When the world canvas is CSS-scaled via `transform: scale(zoom)`, raw mouse coordinates must be divided by `zoom` to map back to tile coordinates. This is handled in `useCanvas.ts`:

```ts
const gx = Math.floor(e.nativeEvent.offsetX / (CELL_SIZE * zoom));
const gy = Math.floor(e.nativeEvent.offsetY / (CELL_SIZE * zoom));
```

The `zoom` parameter is passed from `GameCanvas` → `useCanvas` and applied in both `handleCanvasClick` and `handleCanvasHover`.

## Spectate Mode – Vision Filtering on Minimap

When spectating an entity (`selectedEntityId` is set):

1. A **visible set** is built from the entity's `vision_range` (Manhattan distance).
2. **Entities** outside the visible set (and not the spectated entity itself) are hidden on the minimap.
3. **Resource nodes** outside the visible set are hidden.
4. **Buildings** are always shown (they are permanent structures).
5. **Terrain** uses the same fog-of-war system: unexplored tiles are dark, explored tiles are dimmed, and tiles within current vision are bright.

This matches the world canvas behavior where ghosts and out-of-vision entities are not rendered.

## Locations Panel

A collapsible panel sits directly under the minimap.

### Content

- **Buildings**: General Store, Blacksmith, Adventurer Guild, Class Hall, Inn — each with position and color-coded name.
- **Tile clusters**: Enemy Camps (tile 4), Sanctuaries (tile 5), Ruins (tile 12), Dungeons (tile 13) — detected via flood-fill on the map grid, with the centroid used as the location coordinate.

### Interaction

- Click the **Locations** header to expand/collapse.
- Click any location entry to jump the world camera to that position.

## Constants

| Constant | Value | Description |
|----------|-------|-------------|
| `MINIMAP_SCALE` | 2 | Pixels per tile on minimap canvas |
| `MM_DEFAULT_W/H` | 180 | Default minimap container size (px) |
| `MM_MIN_SIZE` | 80 | Minimum resize dimension |
| `MM_MAX_SIZE` | 400 | Maximum resize dimension |
| `MM_MIN_ZOOM` | 1.0 | Minimap zoom lower bound |
| `MM_MAX_ZOOM` | 5.0 | Minimap zoom upper bound |
| `MM_ZOOM_STEP` | 0.3 | Minimap zoom increment per scroll tick |
| `MIN_ZOOM` | 0.5 | World zoom lower bound |
| `MAX_ZOOM` | 3.0 | World zoom upper bound |
| `ZOOM_STEP` | 0.15 | World zoom increment per scroll tick |
