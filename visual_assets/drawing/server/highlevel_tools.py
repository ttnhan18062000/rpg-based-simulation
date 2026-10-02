"""MCP registration of the high-level (composed) pixel-art tools. Logic lives in `compose`."""

from __future__ import annotations

from visual_assets.drawing import compose
from visual_assets.drawing.server.app import call


def register(mcp) -> None:
    """Attach the high-level tools to a FastMCP server."""

    @mcp.tool()
    def make_ramp(base: str, steps: int = 5, hue_shift: float = 14.0) -> dict:
        """Hue-shifted colour ramp, dark to light, with `base` at the middle (shadows drift blue/purple,
        highlights drift yellow; saturation falls toward the light end). 3-5 steps for 16px sprites.
        Pure computation: nothing is drawn."""
        return call(compose.ramp, base, steps, hue_shift)

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
        return call(compose.shade, name, base_revision, target, ramp, base, steps, light,
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
        return call(compose.dither, name, base_revision, color_dark, color_light, level,
                     region, target_color, level_to, axis, matrix, layer, frame)

    @mcp.tool()
    def stroke(
        name: str, base_revision: str, points: list, color: str, closed: bool = False,
        pixel_perfect: bool = True, layer: str | None = None, frame: int = 1,
    ) -> dict:
        """Polyline through [[x,y],...]. pixel_perfect removes the middle pixel of L-shaped doubles from
        freehand trace (a vertex whose two adjacent segments are both single steps); end points and any
        vertex next to a longer segment are intentional corners and are kept."""
        return call(compose.stroke, name, base_revision, points, color, closed,
                     pixel_perfect, layer, frame)

    @mcp.tool()
    def auto_outline(
        name: str, base_revision: str, mode: str = "full", color: str = "#000000",
        darken: float = 0.45, light: str = "tl", lit_edges: str = "outline",
        layer: str | None = "outline", frame: int = 1,
    ) -> dict:
        """Outline the silhouette on its own layer. mode full (one colour) or selout (darkened,
        blue-shifted neighbour colour); lit_edges 'skip' leaves edges facing the light open."""
        return call(compose.auto_outline, name, base_revision, mode, color, darken, light,
                     lit_edges, layer, frame)

    @mcp.tool()
    def remap_palette(name: str, base_revision: str, palette: list[str], frame: int = 1) -> dict:
        """Snap every opaque pixel to the nearest colour in `palette` and set it as the sprite palette.
        Needs all pixels on one layer."""
        return call(compose.remap_palette, name, base_revision, palette, frame)

    @mcp.tool()
    def lint_sprite(name: str, revision: str | None = None, frame: int = 1) -> dict:
        """Check a frame against pixel-art guidance: colour budget by size, orphan pixels, grayscale value
        separation, canvas-edge clipping, outline consistency. Findings are advice, not gates."""
        return call(compose.lint, name, revision, frame)

    @mcp.tool()
    def ascii_view(name: str, revision: str | None = None, frame: int = 1) -> dict:
        """Text rendering of a frame ('.' = transparent, letters = colours) with a legend, for
        inspecting structure without an image."""
        return call(compose.ascii_view, name, revision, frame)
