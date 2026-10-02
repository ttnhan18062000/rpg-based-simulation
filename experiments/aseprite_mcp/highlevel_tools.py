"""Sprite-facing high-level tools (spike). Pure maths lives in highlevel.py.

Every writer emits an op batch through `adapter.apply_ops`, so it inherits immutable revisions, the
stale-base check, the sandbox and all bounds. Readers use the adapter's 32x32 region readback,
tiled, so they work on any sprite up to 128x128 (slower on large ones; the art targets are 16-32px).
"""

from __future__ import annotations

import adapter
import highlevel as hl

AdapterError = adapter.AdapterError
_MAX_TILE = adapter.MAX_REGION


# --------------------------------------------------------------------------- readback


def read_grid(name: str, revision: str | None = None, frame: int = 1) -> tuple[list[list[str]], dict]:
    """Flattened frame as a grid of #rrggbbaa strings (row-major), plus the inspect summary."""
    first = adapter.inspect_sprite(
        name, revision, {"x": 0, "y": 0, "w": 1, "h": 1}, frame=frame
    )
    w, h = first["width"], first["height"]
    grid = [[""] * w for _ in range(h)]
    for ty in range(0, h, _MAX_TILE):
        for tx in range(0, w, _MAX_TILE):
            tw, th = min(_MAX_TILE, w - tx), min(_MAX_TILE, h - ty)
            tile = adapter.inspect_sprite(
                name, revision, {"x": tx, "y": ty, "w": tw, "h": th}, frame=frame
            )["region"]
            for j, row in enumerate(tile):
                grid[ty + j][tx : tx + tw] = row
    return grid, first


def _cells_where(grid, predicate) -> set:
    return {(x, y) for y, row in enumerate(grid) for x, c in enumerate(row) if predicate(c)}


# --------------------------------------------------------------------------- op emission


def _pixel_ops(colors: dict, layer: str | None, frame: int, existing_layers: list[str]) -> list[dict]:
    """One or more `pixels` ops (<= 4096 each) for {(x, y): hex}, creating `layer` if absent."""
    if not colors:
        raise AdapterError("nothing to draw: the selected region is empty")
    if len(colors) > adapter.MAX_PIXELS_PER_CALL:
        raise AdapterError(
            f"{len(colors)} pixels exceeds the {adapter.MAX_PIXELS_PER_CALL} per-batch limit; "
            "use a smaller region"
        )
    ops: list[dict] = []
    if layer is not None and layer not in existing_layers:
        ops.append({"op": "add_layer", "name": layer})
    items = [{"x": x, "y": y, "color": c} for (x, y), c in sorted(colors.items(), key=lambda kv: (kv[0][1], kv[0][0]))]
    target = {"frame": frame, **({"layer": layer} if layer is not None else {})}
    for i in range(0, len(items), adapter.MAX_PIXELS_PER_OP):
        ops.append({"op": "pixels", "pixels": items[i : i + adapter.MAX_PIXELS_PER_OP], **target})
    return ops


def _layer_names(summary: dict) -> list[str]:
    return [layer["name"] for layer in summary["layers"]]


def _resolve_ramp(ramp, base, steps, bands) -> tuple[list[str], int]:
    if ramp is not None:
        if not isinstance(ramp, list) or len(ramp) < bands:
            raise AdapterError(f"ramp must be a list of at least {bands} colours")
        for c in ramp:
            hl.hex_to_rgba(c)
        return ramp, len(ramp) // 2
    if base is None:
        raise AdapterError("give either ramp or base")
    steps = max(steps, bands)
    return hl.make_ramp(base, steps), steps // 2


# --------------------------------------------------------------------------- tools


def ramp(base: str, steps: int = 5, hue_shift: float = 14.0) -> dict:
    colors = hl.make_ramp(base, steps, hue_shift)
    return {
        "colors": colors,
        "base_index": steps // 2,
        "luma": [round(hl.luma(hl.hex_to_rgba(c))) for c in colors],
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
    cur = adapter.inspect_sprite(name)
    if cur["revision"] != base_revision:
        raise AdapterError(f"stale base_revision {base_revision}; latest is {cur['revision']}. Re-inspect and retry.")
    if kind in ("ellipse", "rect"):
        for key in ("x", "y", "width", "height"):
            if not isinstance(spec.get(key), int):
                raise AdapterError(f"{kind}.{key} must be an integer")
        fn = hl.ellipse_cells if kind == "ellipse" else hl.rect_cells
        mask = fn(spec["x"], spec["y"], spec["width"], spec["height"])
        auto_form = "round" if kind == "ellipse" else "bevel"
    else:
        grid, _ = read_grid(name, base_revision, frame)
        if kind == "color":
            want = hl.norm_hex(spec)
            mask = _cells_where(grid, lambda c: c == want)
        elif kind == "opaque" and spec is True:
            mask = _cells_where(grid, lambda c: not c.endswith("00"))
        else:
            raise AdapterError("target must be color, opaque:true, ellipse or rect")
        auto_form = "round"
    use_form = auto_form if form == "auto" else form
    if not mask:
        raise AdapterError("target selects no pixels")
    offsets = hl.shade_offsets(mask, light, bands, use_form, 1, contrast)
    k = bands // 2
    colors = {p: hl.norm_hex(cols[bi + max(-k, min(k, o))]) for p, o in offsets.items()}
    ops = _pixel_ops(colors, layer, frame, _layer_names(cur))
    out = adapter.apply_ops(name, base_revision, ops)
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
    cur = adapter.inspect_sprite(name)
    if cur["revision"] != base_revision:
        raise AdapterError(f"stale base_revision {base_revision}; latest is {cur['revision']}. Re-inspect and retry.")
    if (region is None) == (target_color is None):
        raise AdapterError("give exactly one of region or target_color")
    if region is not None:
        for key in ("x", "y", "width", "height"):
            if not isinstance(region.get(key), int):
                raise AdapterError(f"region.{key} must be an integer")
        cells = hl.rect_cells(region["x"], region["y"], region["width"], region["height"])
    else:
        grid, _ = read_grid(name, base_revision, frame)
        want = hl.norm_hex(target_color)
        cells = _cells_where(grid, lambda c: c == want)
    light_map = hl.dither_cells(cells, level, level_to, axis, matrix)
    dark_c, light_c = hl.norm_hex(color_dark), hl.norm_hex(color_light)
    colors = {p: (light_c if is_light else dark_c) for p, is_light in light_map.items()}
    out = adapter.apply_ops(name, base_revision, _pixel_ops(colors, layer, frame, _layer_names(cur)))
    out["light_pixels"] = sum(light_map.values())
    out["dithered_pixels"] = len(light_map)
    return out


def stroke(
    name: str, base_revision: str, points: list, color: str, closed: bool = False,
    pixel_perfect: bool = True, layer: str | None = None, frame: int = 1,
) -> dict:
    cur = adapter.inspect_sprite(name)
    if cur["revision"] != base_revision:
        raise AdapterError(f"stale base_revision {base_revision}; latest is {cur['revision']}. Re-inspect and retry.")
    if not isinstance(points, list) or not points:
        raise AdapterError("points must be a non-empty list of [x, y]")
    pts = []
    for p in points:
        if not (isinstance(p, (list, tuple)) and len(p) == 2 and all(isinstance(v, int) for v in p)):
            raise AdapterError("each point must be [x, y] integers")
        pts.append((p[0], p[1]))
    pixels = hl.stroke_pixels(pts, closed, pixel_perfect)
    c = hl.norm_hex(color)
    out = adapter.apply_ops(
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
    if light not in hl.LIGHTS:
        raise AdapterError(f"light must be one of {sorted(hl.LIGHTS)}")
    if not 0.1 <= darken <= 0.9:
        raise AdapterError("darken must be in [0.1, 0.9]")
    cur = adapter.inspect_sprite(name)
    if cur["revision"] != base_revision:
        raise AdapterError(f"stale base_revision {base_revision}; latest is {cur['revision']}. Re-inspect and retry.")
    grid, _ = read_grid(name, base_revision, frame)
    h, w = len(grid), len(grid[0])
    opaque = _cells_where(grid, lambda c: not c.endswith("00"))
    ldx, ldy = hl.LIGHTS[light]
    full_c = hl.norm_hex(color)
    existing = sorted({c for row in grid for c in row if not c.endswith("00")})
    colors: dict = {}
    clipped = 0
    for (x, y) in opaque:
        for dx, dy in hl._N4:
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
                nbrs = [grid[oy + ey][ox + ex] for ex, ey in hl._N4
                        if (ox + ex, oy + ey) in opaque]
                base_c = min(nbrs, key=lambda c: hl.luma(hl.hex_to_rgba(c)))
                colors[(ox, oy)] = _selout_color(base_c, darken, existing)
    if not colors:
        raise AdapterError("no outline pixels to draw (empty frame, or every edge skipped/clipped)")
    out = adapter.apply_ops(name, base_revision, _pixel_ops(colors, layer, frame, _layer_names(cur)))
    out["outline_pixels"] = len(colors)
    out["outline_clipped"] = clipped
    return out


def _selout_color(neighbour: str, factor: float, existing: list[str]) -> str:
    """Selective-outline colour for one pixel. Reuse a colour already in the sprite when one is
    clearly darker than the neighbouring fill (keeps the palette small: a per-neighbour invented
    colour multiplied a 16px knight to 19 colours); otherwise fall back to a darkened neighbour."""
    want = _darken(neighbour, factor)
    wr, wg, wb, _ = hl.hex_to_rgba(want)
    limit = hl.luma(hl.hex_to_rgba(neighbour)) * 0.7
    darker = [c for c in existing if hl.luma(hl.hex_to_rgba(c)) <= limit]
    if not darker:
        return want

    def dist(c):
        r, g, b, _ = hl.hex_to_rgba(c)
        return ((r - wr) ** 2 + (g - wg) ** 2 + (b - wb) ** 2, c)

    return min(darker, key=dist)


def _darken(value: str, factor: float) -> str:
    import colorsys
    r, g, b, a = hl.hex_to_rgba(value)
    hh, ss, vv = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    hh = hl._hue_toward(hh * 360.0, 250.0, 15.0) / 360.0
    rr, gg, bb = colorsys.hsv_to_rgb(hh, min(1.0, ss * 1.05), vv * factor)
    return hl.rgba_to_hex(round(rr * 255), round(gg * 255), round(bb * 255), 255).ljust(9, "f")


def remap_palette(
    name: str, base_revision: str, palette: list[str], frame: int = 1
) -> dict:
    """Snap every opaque pixel to the nearest colour in `palette` (perceptually weighted RGB).
    Reads the flattened frame, so it refuses sprites whose pixels live on more than one layer."""
    if not isinstance(palette, list) or not 1 <= len(palette) <= adapter.MAX_PALETTE:
        raise AdapterError(f"palette must hold 1..{adapter.MAX_PALETTE} colours")
    pal = [(hl.norm_hex(c), hl.hex_to_rgba(c)) for c in palette]
    cur = adapter.inspect_sprite(name)
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
            rgba = hl.hex_to_rgba(c)
            best = min(pal, key=lambda p: (dist(rgba, p[1]), p[0]))
            new = best[0][:7] + c[7:]  # keep the pixel's own alpha
            if new != c:
                changed += 1
            colors[(x, y)] = new
    if not colors:
        raise AdapterError("no opaque pixels to remap")
    ops = _pixel_ops(colors, active[0], frame, _layer_names(cur))
    ops.append({"op": "set_palette", "colors": [c for c, _ in pal]})
    out = adapter.apply_ops(name, base_revision, ops)
    out["remapped_pixels"] = changed
    return out


def lint(name: str, revision: str | None = None, frame: int = 1) -> dict:
    grid, _ = read_grid(name, revision, frame)
    return hl.lint_grid(grid)


def ascii_view(name: str, revision: str | None = None, frame: int = 1) -> dict:
    grid, info = read_grid(name, revision, frame)
    rows, legend = hl.ascii_grid(grid)
    return {"revision": info["revision"], "width": info["width"], "height": info["height"],
            "rows": rows, "legend": legend}


# --------------------------------------------------------------------------- MCP wiring


def register(mcp) -> None:
    """Attach the high-level tools to a FastMCP server."""

    def _call(fn, *a, **k):
        try:
            return fn(*a, **k)
        except adapter.AdapterError as exc:
            raise ValueError(str(exc)) from None

    @mcp.tool()
    def make_ramp(base: str, steps: int = 5, hue_shift: float = 14.0) -> dict:
        """Hue-shifted colour ramp, dark to light, with `base` at the middle (shadows drift blue/purple,
        highlights drift yellow; saturation falls toward the light end). 3-5 steps for 16px sprites.
        Pure computation: nothing is drawn."""
        return _call(ramp, base, steps, hue_shift)

    @mcp.tool()
    def shade(
        name: str, base_revision: str, target: dict, ramp: list[str] | None = None,
        base: str | None = None, steps: int = 5, light: str = "tl", bands: int = 3,
        form: str = "auto", contrast: float = 0.12, layer: str | None = None, frame: int = 1,
    ) -> dict:
        """Hard-banded light-direction shading (no pillow shading, no orphan pixels). target is exactly
        one of {"color": "#hex"} (every pixel of that flat colour), {"opaque": true},
        {"ellipse": {x,y,width,height}} or {"rect": {...}}. Give `ramp` (list, dark->light) or `base`
        (auto hue-shifted ramp). light: tl,t,tr,l,r,bl,b,br. bands: 3 (16px) or 5. form: round|bevel|auto."""
        return _call(globals()["shade"], name, base_revision, target, ramp, base, steps, light,
                     bands, form, contrast, layer, frame)

    @mcp.tool()
    def dither(
        name: str, base_revision: str, color_dark: str, color_light: str, level: float,
        region: dict | None = None, target_color: str | None = None, level_to: float | None = None,
        axis: str = "x", matrix: int = 4, layer: str | None = None, frame: int = 1,
    ) -> dict:
        """Ordered Bayer dither between two colours over a rect region {x,y,width,height} or over all
        pixels of `target_color`. level = light colour coverage 0..1; with level_to it ramps along
        axis x|y|diag. matrix 2|4|8."""
        return _call(globals()["dither"], name, base_revision, color_dark, color_light, level,
                     region, target_color, level_to, axis, matrix, layer, frame)

    @mcp.tool()
    def stroke(
        name: str, base_revision: str, points: list, color: str, closed: bool = False,
        pixel_perfect: bool = True, layer: str | None = None, frame: int = 1,
    ) -> dict:
        """Polyline through [[x,y],...]. pixel_perfect removes the middle pixel of L-shaped doubles from
        freehand trace (a vertex whose two adjacent segments are both single steps); end points and any
        vertex next to a longer segment are intentional corners and are kept."""
        return _call(globals()["stroke"], name, base_revision, points, color, closed,
                     pixel_perfect, layer, frame)

    @mcp.tool()
    def auto_outline(
        name: str, base_revision: str, mode: str = "full", color: str = "#000000",
        darken: float = 0.45, light: str = "tl", lit_edges: str = "outline",
        layer: str | None = "outline", frame: int = 1,
    ) -> dict:
        """Outline the silhouette on its own layer. mode full (one colour) or selout (darkened,
        blue-shifted neighbour colour); lit_edges 'skip' leaves edges facing the light open."""
        return _call(globals()["auto_outline"], name, base_revision, mode, color, darken, light,
                     lit_edges, layer, frame)

    @mcp.tool()
    def remap_palette(name: str, base_revision: str, palette: list[str], frame: int = 1) -> dict:
        """Snap every opaque pixel to the nearest colour in `palette` and set it as the sprite palette.
        Needs all pixels on one layer."""
        return _call(globals()["remap_palette"], name, base_revision, palette, frame)

    @mcp.tool()
    def lint_sprite(name: str, revision: str | None = None, frame: int = 1) -> dict:
        """Check a frame against pixel-art guidance: colour budget by size, orphan pixels, grayscale value
        separation, canvas-edge clipping, outline consistency. Findings are advice, not gates."""
        return _call(globals()["lint"], name, revision, frame)

    @mcp.tool()
    def ascii_view(name: str, revision: str | None = None, frame: int = 1) -> dict:
        """Text rendering of a frame ('.' = transparent, letters = colours) with a legend, for
        inspecting structure without an image."""
        return _call(globals()["ascii_view"], name, revision, frame)
