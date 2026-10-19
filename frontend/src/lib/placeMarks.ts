// Places on the Live Map (D69): each place the API presents (`Region.locations`, from `StatePresenter.present_place`) is outlined over its tiles and labelled
// with its name. Pure helpers and one draw function, so the geometry is testable without a canvas.
import { CELL_SIZE } from '@/constants/colors';
import type { Location } from '@/types/api';

export const PLACE_TYPE_COLORS: Record<string, string> = {
  city: '#fbbf24',
  camp: '#f87171',
  nest: '#fb7185',
  lair: '#f43f5e',
  ruin: '#a0906a',
  dungeon: '#e06080',
  landmark: '#60a5fa',
};
export const PLACE_DEFAULT_COLOR = '#e5e7eb';

export function placeColor(place: Pick<Location, 'location_type'>): string {
  return PLACE_TYPE_COLORS[place.location_type] ?? PLACE_DEFAULT_COLOR;
}

/** The place's outline in canvas pixels: its tiles (a footprint, or the one tile it stands on). */
export function placeRect(place: Pick<Location, 'x' | 'y' | 'tiles'>): { x: number; y: number; w: number; h: number } {
  const tiles = place.tiles ?? { x: place.x, y: place.y, width: 1, height: 1 };
  return { x: tiles.x * CELL_SIZE, y: tiles.y * CELL_SIZE, w: tiles.width * CELL_SIZE, h: tiles.height * CELL_SIZE };
}

type Ctx = Pick<CanvasRenderingContext2D, 'strokeRect' | 'fillText' | 'save' | 'restore' | 'strokeStyle' | 'fillStyle' | 'lineWidth' | 'font' | 'textAlign' | 'textBaseline'>;

/** Draws every place's outline and name label. The label sits above the outline, centred on it. */
export function drawPlaces(ctx: Ctx, places: ReadonlyArray<Location>): void {
  ctx.save();
  ctx.lineWidth = 1.5;
  ctx.font = 'bold 10px sans-serif';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'bottom';
  for (const place of places) {
    const { x, y, w, h } = placeRect(place);
    const color = placeColor(place);
    ctx.strokeStyle = color;
    ctx.strokeRect(x + 0.75, y + 0.75, w - 1.5, h - 1.5);
    ctx.fillStyle = color;
    ctx.fillText(place.name, x + w / 2, Math.max(10, y - 2));
  }
  ctx.restore();
}
