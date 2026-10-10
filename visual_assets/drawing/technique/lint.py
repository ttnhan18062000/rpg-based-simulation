"""Advisory pixel-art lint over a flattened frame. Findings are advice, never gates."""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Sequence
from pathlib import Path

from visual_assets.drawing.colors import hex_to_rgba, luma
from visual_assets.drawing.technique.shading import N4

def _load_rules() -> tuple[tuple[tuple[int, int], ...], int]:
    """The colour budgets, read once from the committed `style_rules.json` next to this module (the same numbers the code held before; a test pins them)."""
    data = json.loads(Path(__file__).with_name("style_rules.json").read_text(encoding="utf-8"))
    return tuple((int(side), int(budget)) for side, budget in data["color_budgets"]), int(data["color_budget_above"])


_BUDGETS, _BUDGET_ABOVE = _load_rules()  # (max side, colour budget) rows; above the last row: _BUDGET_ABOVE


OUTLINE_LUMA_MAX = 70.0


def lint_grid(grid: list[list[str]], layers_hint: dict | None = None, palette: Sequence[str] | None = None) -> dict:
    """Check a flattened frame against the researched rules. Findings are advice, not gates.

    `palette` (optional, `#rrggbb` strings) adds an advisory `off_palette` finding: opaque pixels whose RGB is not in it, as a count, the distinct colours and the first coordinates. It is reported, never ruled
    (level `info`, so it never turns `ok` false)."""
    h, w = len(grid), len(grid[0]) if grid else 0
    rgba = [[hex_to_rgba(c) for c in row] for row in grid]
    opaque = {(x, y) for y in range(h) for x in range(w) if rgba[y][x][3] > 0}
    findings: list[dict] = []
    stats: dict = {"width": w, "height": h, "opaque_pixels": len(opaque)}

    def add(level, code, message, **data):
        findings.append({"level": level, "code": code, "message": message, **data})

    if not opaque:
        add("warn", "empty", "frame has no opaque pixels")
        return {"ok": False, "findings": findings, "stats": stats}

    colors = Counter(grid[y][x] for x, y in opaque)
    side = max(w, h)
    budget = next((b for s, b in _BUDGETS if side <= s), _BUDGET_ABOVE)
    stats["colors"] = len(colors)
    stats["color_budget"] = budget
    if len(colors) > budget:
        add("warn", "palette_budget",
            f"{len(colors)} colours on a {w}x{h} sprite; guidance is <= {budget} "
            "(extra colours read as noise at this size)", count=len(colors), budget=budget)

    xs, ys = [p[0] for p in opaque], [p[1] for p in opaque]
    bbox = (min(xs), min(ys), max(xs), max(ys))
    stats["bbox"] = bbox
    if bbox[0] == 0 or bbox[1] == 0 or bbox[2] == w - 1 or bbox[3] == h - 1:
        add("info", "touches_edge",
            "artwork touches the canvas edge; leave 1px padding if overlays (HP bar, status) need room",
            bbox=bbox)

    orphans = []
    for x, y in sorted(opaque, key=lambda p: (p[1], p[0])):
        c = grid[y][x]
        same = sum(1 for dx, dy in N4 if (x + dx, y + dy) in opaque and grid[y + dy][x + dx] == c)
        if same == 0:
            orphans.append((x, y))
    stats["orphan_pixels"] = len(orphans)
    if orphans:
        add("info", "orphan_pixels",
            f"{len(orphans)} single-pixel islands (a colour touching nothing of itself). Fine for "
            "deliberate details such as eyes; otherwise merge them into a cluster",
            pixels=orphans[:20])

    distinct = sorted(colors, key=lambda c: luma(hex_to_rgba(c)))
    close = []
    for a, b in zip(distinct, distinct[1:]):
        if abs(luma(hex_to_rgba(a)) - luma(hex_to_rgba(b))) < 12:
            close.append((a, b))
    if close:
        add("warn", "value_separation",
            "colours with almost equal brightness merge in grayscale (ART-W06: critical distinctions "
            "must survive without hue); separate their values or merge them", pairs=close[:5])

    boundary = {
        p for p in opaque
        if any((p[0] + dx, p[1] + dy) not in opaque for dx, dy in N4)
    }
    dark = [p for p in boundary if luma(rgba[p[1]][p[0]]) <= OUTLINE_LUMA_MAX]
    frac = len(dark) / len(boundary) if boundary else 0.0
    stats["dark_boundary_fraction"] = round(frac, 3)
    if 0.15 < frac < 0.85:
        add("info", "mixed_outline",
            f"{frac:.0%} of the silhouette edge is dark. Sources disagree on mixed outlines: selective "
            "outlining is a valid style when intentional, but check it is not accidental",
            fraction=round(frac, 3))
    if palette is not None:
        allowed = {c.lower()[:7] for c in palette}
        off = [(x, y) for y, x in sorted((y, x) for x, y in opaque) if grid[y][x].lower()[:7] not in allowed]
        stats["off_palette_pixels"] = len(off)
        if off:
            distinct = sorted({grid[y][x].lower()[:7] for x, y in off})
            add("info", "off_palette", f"{len(off)} opaque pixels use {len(distinct)} colours that are not in the given palette (reported, not ruled)",
                count=len(off), colors=distinct[:10], pixels=off[:20])
    return {"ok": not any(f["level"] == "warn" for f in findings), "findings": findings, "stats": stats}
