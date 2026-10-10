"""Sprite-facing high-level tools (shade, dither, stroke, outline, remap, lint, ascii).

Pure maths lives in `technique/`. Every writer emits an op batch through `api.apply_ops`, so it inherits
immutable revisions, the stale-base check, the sandbox and all bounds. Readers use the API's 32x32 region
readback, tiled, so they work on any sprite up to 128x128 (slower on large ones; the art targets are 16-32px).
"""

from __future__ import annotations

from visual_assets.drawing import api, config, palettes
from visual_assets.drawing.colors import hex_to_rgba, hue_toward, luma, norm_hex, rgba_to_hex
from visual_assets.drawing.errors import AdapterError
from visual_assets.drawing.technique.ascii import ascii_grid
from visual_assets.drawing.technique.dither import dither_cells
from visual_assets.drawing.technique.lint import lint_grid
from visual_assets.drawing.technique.masks import ellipse_cells, rect_cells
from visual_assets.drawing.technique.ramps import make_ramp
from visual_assets.drawing.technique.shading import LIGHTS, N4, shade_offsets
from visual_assets.drawing.technique.stroke import stroke_pixels

def read_grid(name: str, revision: str | None = None, frame: int = 1) -> tuple[list[list[str]], dict]:
    """Flattened frame as a grid of #rrggbbaa strings (row-major), plus the inspect summary."""
    first = api.inspect_sprite(
        name, revision, {"x": 0, "y": 0, "w": 1, "h": 1}, frame=frame
    )
    w, h = first["width"], first["height"]
    grid = [[""] * w for _ in range(h)]
    for ty in range(0, h, config.MAX_REGION):
        for tx in range(0, w, config.MAX_REGION):
            tw, th = min(config.MAX_REGION, w - tx), min(config.MAX_REGION, h - ty)
            tile = api.inspect_sprite(
                name, revision, {"x": tx, "y": ty, "w": tw, "h": th}, frame=frame
            )["region"]
            for j, row in enumerate(tile):
                grid[ty + j][tx : tx + tw] = row
    return grid, first


def _cells_where(grid, predicate) -> set:
    return {(x, y) for y, row in enumerate(grid) for x, c in enumerate(row) if predicate(c)}


def _pixel_ops(colors: dict, layer: str | None, frame: int, existing_layers: list[str]) -> list[dict]:
    """One or more `pixels` ops (<= 4096 each) for {(x, y): hex}, creating `layer` if absent."""
    if not colors:
        raise AdapterError("nothing to draw: the selected region is empty")
    if len(colors) > config.MAX_PIXELS_PER_CALL:
        raise AdapterError(
            f"{len(colors)} pixels exceeds the {config.MAX_PIXELS_PER_CALL} per-batch limit; "
            "use a smaller region"
        )
    ops: list[dict] = []
    if layer is not None and layer not in existing_layers:
        ops.append({"op": "add_layer", "name": layer})
    items = [{"x": x, "y": y, "color": c} for (x, y), c in sorted(colors.items(), key=lambda kv: (kv[0][1], kv[0][0]))]
    target = {"frame": frame, **({"layer": layer} if layer is not None else {})}
    for i in range(0, len(items), config.MAX_PIXELS_PER_OP):
        ops.append({"op": "pixels", "pixels": items[i : i + config.MAX_PIXELS_PER_OP], **target})
    return ops


def _layer_names(summary: dict) -> list[str]:
    return [layer["name"] for layer in summary["layers"]]


def _resolve_ramp(ramp, base, steps, bands) -> tuple[list[str], int]:
    if ramp is not None:
        if not isinstance(ramp, list) or len(ramp) < bands:
            raise AdapterError(f"ramp must be a list of at least {bands} colours")
        for c in ramp:
            hex_to_rgba(c)
        return ramp, len(ramp) // 2
    if base is None:
        raise AdapterError("give either ramp or base")
    steps = max(steps, bands)
    return make_ramp(base, steps), steps // 2


def ramp(base: str, steps: int = 5, hue_shift: float = 14.0) -> dict:
    colors = make_ramp(base, steps, hue_shift)
    return {
        "colors": colors,
        "base_index": steps // 2,
        "luma": [round(luma(hex_to_rgba(c))) for c in colors],
    }


def shade(
    name: str, base_revision: str, target: dict, ramp_colors: list[str] | None = None,
    base: str | None = None, steps: int = 5, light: str = "tl", bands: int = 3,
    form: str = "auto", contrast: float = 0.12, layer: str | None = None, frame: int = 1,
) -> dict:
    """Paint hard-banded shading over `target` (a flat-coloured area) in the given light direction.

    target: {"color": "#hex"} every pixel of that flat colour in the flattened frame, or
            {"opaque": true} all opaque pixels, or {"ellipse": {x,y,width,height}} /
            {"rect": {x,y,width,height}} a fresh shape.
    """
    if not isinstance(target, dict) or len(target) != 1:
        raise AdapterError("target must have exactly one of color/opaque/ellipse/rect")
    cols, bi = _resolve_ramp(ramp_colors, base, steps, bands)
    kind, spec = next(iter(target.items()))
    cur = api.inspect_sprite(name)
    if cur["revision"] != base_revision:
        raise AdapterError(f"stale base_revision {base_revision}; latest is {cur['revision']}. Re-inspect and retry.")
    if kind in ("ellipse", "rect"):
        for key in ("x", "y", "width", "height"):
            if not isinstance(spec.get(key), int):
                raise AdapterError(f"{kind}.{key} must be an integer")
        fn = ellipse_cells if kind == "ellipse" else rect_cells
        mask = fn(spec["x"], spec["y"], spec["width"], spec["height"])
        auto_form = "round" if kind == "ellipse" else "bevel"
    else:
        grid, _ = read_grid(name, base_revision, frame)
        if kind == "color":
            want = norm_hex(spec)
            mask = _cells_where(grid, lambda c: c == want)
        elif kind == "opaque" and spec is True:
            mask = _cells_where(grid, lambda c: not c.endswith("00"))
        else:
            raise AdapterError("target must be color, opaque:true, ellipse or rect")
        auto_form = "round"
    use_form = auto_form if form == "auto" else form
    if not mask:
        raise AdapterError("target selects no pixels")
    offsets = shade_offsets(mask, light, bands, use_form, 1, contrast)
    k = bands // 2
    colors = {p: norm_hex(cols[bi + max(-k, min(k, o))]) for p, o in offsets.items()}
    ops = _pixel_ops(colors, layer, frame, _layer_names(cur))
    out = api.apply_ops(name, base_revision, ops)
    out["shaded_pixels"] = len(colors)
    out["band_counts"] = {str(o): sum(1 for v in offsets.values() if v == o) for o in range(-k, k + 1)}
    return out


def dither(
    name: str, base_revision: str, color_dark: str, color_light: str, level: float,
    region: dict | None = None, target_color: str | None = None, level_to: float | None = None,
    axis: str = "x", matrix: int = 4, layer: str | None = None, frame: int = 1,
) -> dict:
    """Ordered-dither between two colours over a rect `region` {x,y,width,height} or over every
    pixel currently of `target_color`. Coverage `level` is the light colour's share."""
    cur = api.inspect_sprite(name)
    if cur["revision"] != base_revision:
        raise AdapterError(f"stale base_revision {base_revision}; latest is {cur['revision']}. Re-inspect and retry.")
    if (region is None) == (target_color is None):
        raise AdapterError("give exactly one of region or target_color")
    if region is not None:
        for key in ("x", "y", "width", "height"):
            if not isinstance(region.get(key), int):
                raise AdapterError(f"region.{key} must be an integer")
        cells = rect_cells(region["x"], region["y"], region["width"], region["height"])
    else:
        grid, _ = read_grid(name, base_revision, frame)
        want = norm_hex(target_color)
        cells = _cells_where(grid, lambda c: c == want)
    light_map = dither_cells(cells, level, level_to, axis, matrix)
    dark_c, light_c = norm_hex(color_dark), norm_hex(color_light)
    colors = {p: (light_c if is_light else dark_c) for p, is_light in light_map.items()}
    out = api.apply_ops(name, base_revision, _pixel_ops(colors, layer, frame, _layer_names(cur)))
    out["light_pixels"] = sum(light_map.values())
    out["dithered_pixels"] = len(light_map)
    return out


def stroke(
    name: str, base_revision: str, points: list, color: str, closed: bool = False,
    pixel_perfect: bool = True, layer: str | None = None, frame: int = 1,
) -> dict:
    cur = api.inspect_sprite(name)
    if cur["revision"] != base_revision:
        raise AdapterError(f"stale base_revision {base_revision}; latest is {cur['revision']}. Re-inspect and retry.")
    if not isinstance(points, list) or not points:
        raise AdapterError("points must be a non-empty list of [x, y]")
    pts = []
    for p in points:
        if not (isinstance(p, (list, tuple)) and len(p) == 2 and all(isinstance(v, int) for v in p)):
            raise AdapterError("each point must be [x, y] integers")
        pts.append((p[0], p[1]))
    pixels = stroke_pixels(pts, closed, pixel_perfect)
    c = norm_hex(color)
    out = api.apply_ops(
        name, base_revision, _pixel_ops({p: c for p in pixels}, layer, frame, _layer_names(cur))
    )
    out["stroke_pixels"] = len(set(pixels))  # a closed stroke repeats its start point
    return out


def auto_outline(
    name: str, base_revision: str, mode: str = "full", color: str = "#000000",
    darken: float = 0.45, light: str = "tl", lit_edges: str = "outline",
    layer: str | None = "outline", frame: int = 1,
) -> dict:
    """Outline the flattened silhouette on its own layer (default 'outline').

    mode 'full'  : one colour on every edge.
    mode 'selout': each outline pixel takes a colour ALREADY in the sprite that is clearly darker
                   than the neighbouring fill (nearest to a darkened, blue-shifted version of it);
                   only if none exists does it introduce that darkened colour.
    lit_edges 'skip' leaves the edges facing the light unoutlined (classic selective outline).
    Pixels that would fall off the canvas are clipped and reported in `outline_clipped`.
    """
    if mode not in ("full", "selout"):
        raise AdapterError("mode must be 'full' or 'selout'")
    if lit_edges not in ("outline", "skip"):
        raise AdapterError("lit_edges must be 'outline' or 'skip'")
    if light not in LIGHTS:
        raise AdapterError(f"light must be one of {sorted(LIGHTS)}")
    if not 0.1 <= darken <= 0.9:
        raise AdapterError("darken must be in [0.1, 0.9]")
    cur = api.inspect_sprite(name)
    if cur["revision"] != base_revision:
        raise AdapterError(f"stale base_revision {base_revision}; latest is {cur['revision']}. Re-inspect and retry.")
    grid, _ = read_grid(name, base_revision, frame)
    h, w = len(grid), len(grid[0])
    opaque = _cells_where(grid, lambda c: not c.endswith("00"))
    ldx, ldy = LIGHTS[light]
    full_c = norm_hex(color)
    existing = sorted({c for row in grid for c in row if not c.endswith("00")})
    colors: dict = {}
    clipped = 0
    for (x, y) in opaque:
        for dx, dy in N4:
            ox, oy = x + dx, y + dy
            if (ox, oy) in opaque:
                continue
            if not (0 <= ox < w and 0 <= oy < h):
                clipped += 1
                continue
            if lit_edges == "skip" and (dx * ldx + dy * ldy) > 0:
                continue
            if mode == "full":
                colors[(ox, oy)] = full_c
            else:
                nbrs = [grid[oy + ey][ox + ex] for ex, ey in N4
                        if (ox + ex, oy + ey) in opaque]
                base_c = min(nbrs, key=lambda c: luma(hex_to_rgba(c)))
                colors[(ox, oy)] = _selout_color(base_c, darken, existing)
    if not colors:
        raise AdapterError("no outline pixels to draw (empty frame, or every edge skipped/clipped)")
    out = api.apply_ops(name, base_revision, _pixel_ops(colors, layer, frame, _layer_names(cur)))
    out["outline_pixels"] = len(colors)
    out["outline_clipped"] = clipped
    return out


def _selout_color(neighbour: str, factor: float, existing: list[str]) -> str:
    """Selective-outline colour for one pixel. Reuse a colour already in the sprite when one is
    clearly darker than the neighbouring fill (keeps the palette small: a per-neighbour invented
    colour multiplied a 16px knight to 19 colours); otherwise fall back to a darkened neighbour."""
    want = _darken(neighbour, factor)
    wr, wg, wb, _ = hex_to_rgba(want)
    limit = luma(hex_to_rgba(neighbour)) * 0.7
    darker = [c for c in existing if luma(hex_to_rgba(c)) <= limit]
    if not darker:
        return want

    def dist(c):
        r, g, b, _ = hex_to_rgba(c)
        return ((r - wr) ** 2 + (g - wg) ** 2 + (b - wb) ** 2, c)

    return min(darker, key=dist)


def _darken(value: str, factor: float) -> str:
    import colorsys
    r, g, b, a = hex_to_rgba(value)
    hh, ss, vv = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    hh = hue_toward(hh * 360.0, 250.0, 15.0) / 360.0
    rr, gg, bb = colorsys.hsv_to_rgb(hh, min(1.0, ss * 1.05), vv * factor)
    return rgba_to_hex(round(rr * 255), round(gg * 255), round(bb * 255), 255).ljust(9, "f")


def remap_palette(
    name: str, base_revision: str, palette: list[str], frame: int = 1
) -> dict:
    """Snap every opaque pixel to the nearest colour in `palette` (perceptually weighted RGB).
    Reads the flattened frame, so it refuses sprites whose pixels live on more than one layer."""
    if not isinstance(palette, list) or not 1 <= len(palette) <= config.MAX_PALETTE:
        raise AdapterError(f"palette must hold 1..{config.MAX_PALETTE} colours")
    pal = [(norm_hex(c), hex_to_rgba(c)) for c in palette]
    cur = api.inspect_sprite(name)
    if cur["revision"] != base_revision:
        raise AdapterError(f"stale base_revision {base_revision}; latest is {cur['revision']}. Re-inspect and retry.")
    active = [l["name"] for l in cur["layers"] if l["nonempty_by_frame"][frame - 1] > 0]
    if len(active) != 1:
        raise AdapterError(
            f"remap_palette needs exactly one layer with pixels in frame {frame} (found {active}); "
            "it reads the flattened frame"
        )
    grid, _ = read_grid(name, base_revision, frame)

    def dist(a, b) -> float:
        rm = (a[0] + b[0]) / 2
        dr, dg, db = a[0] - b[0], a[1] - b[1], a[2] - b[2]
        return (2 + rm / 256) * dr * dr + 4 * dg * dg + (2 + (255 - rm) / 256) * db * db

    colors, changed = {}, 0
    for y, row in enumerate(grid):
        for x, c in enumerate(row):
            if c.endswith("00"):
                continue
            rgba = hex_to_rgba(c)
            best = min(pal, key=lambda p: (dist(rgba, p[1]), p[0]))
            new = best[0][:7] + c[7:]  # keep the pixel's own alpha
            if new != c:
                changed += 1
            colors[(x, y)] = new
    if not colors:
        raise AdapterError("no opaque pixels to remap")
    ops = _pixel_ops(colors, active[0], frame, _layer_names(cur))
    ops.append({"op": "set_palette", "colors": [c for c, _ in pal]})
    out = api.apply_ops(name, base_revision, ops)
    out["remapped_pixels"] = changed
    return out


def lint(name: str, revision: str | None = None, frame: int = 1, palette: list[str] | None = None, palette_id: str | None = None) -> dict:
    """Advisory lint of one frame; `palette` (a list of colours) or `palette_id` (a committed palette such as `icons-v1`) adds the off-palette report. Giving both is an error."""
    if palette is not None and palette_id is not None:
        raise AdapterError("give palette or palette_id, not both")
    if palette_id is not None:
        palette = palettes.load_palette(palette_id)
    elif palette is not None:
        palette = [norm_hex(c)[:7] for c in palette]
    grid, _ = read_grid(name, revision, frame)
    return lint_grid(grid, palette=palette)


def ascii_view(name: str, revision: str | None = None, frame: int = 1) -> dict:
    grid, info = read_grid(name, revision, frame)
    rows, legend = ascii_grid(grid)
    return {"revision": info["revision"], "width": info["width"], "height": info["height"],
            "rows": rows, "legend": legend}
