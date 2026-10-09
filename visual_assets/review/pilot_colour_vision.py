"""The AM5-W05 colour-vision check of the pilot terrain tile, exactly as predeclared in `docs/assets/pilot_terrain_m5_criteria.md`.

Simulates protanopia, deuteranopia and tritanopia (Machado, Oliveira and Fernandes 2009, severity 1.0, in linear RGB), converts to CIE L*a*b* (D65) and
measures CIE76 `dE`. Pure Python; reads the committed pilot export and the Live Map's tile fills (read-only, by parsing `frontend/src/constants/colors.ts`).
No assistive-technology claim: this is arithmetic on colours.

    python -m visual_assets.review.pilot_colour_vision      # prints the evidence as JSON
"""

from __future__ import annotations

import json
import math
import re
from pathlib import Path

from visual_assets.store import pixels

REPO = Path(__file__).resolve().parents[2]
EXPORT = REPO / "frontend" / "src" / "visualAssets" / "__fixtures__" / "pilot"
COLORS_TS = REPO / "frontend" / "src" / "constants" / "colors.ts"

FOREST, SWAMP, MOUNTAIN, DESERT, JUNGLE, GRASSLAND = 6, 8, 9, 7, 17, 15
NEIGHBOURS = {"Swamp": SWAMP, "Mountain": MOUNTAIN, "Desert": DESERT, "Jungle": JUNGLE, "Grassland": GRASSLAND}
TOLERANCE = 2.0  # P1: the tile may be at most this much less distinguishable than the flat fill
TEXTURE_MIN = 2.0  # P2: standard deviation of L* over the tile

MACHADO = {
    "normal": ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
    "protan": ((0.152286, 1.052583, -0.204868), (0.114503, 0.786281, 0.099216), (-0.003882, -0.048116, 1.051998)),
    "deutan": ((0.367322, 0.860646, -0.227968), (0.280085, 0.672501, 0.047413), (-0.011820, 0.042940, 0.968881)),
    "tritan": ((1.255528, -0.076749, -0.178779), (-0.078411, 0.930809, 0.147602), (0.004733, 0.691367, 0.303900)),
}
VISIONS = tuple(MACHADO)

Rgb = tuple[float, float, float]  # 0..1, sRGB


def tile_fills() -> dict[int, str]:
    """`TILE_COLORS` of the Live Map: code -> '#rrggbb' (the first block of colors.ts only)."""
    block = COLORS_TS.read_text().split("export const TILE_COLORS: Record<number, string> = {", 1)[1].split("};", 1)[0]
    return {int(code): colour for code, colour in re.findall(r"(\d+):\s*'(#[0-9a-fA-F]{6})'", block)}


def from_hex(colour: str) -> Rgb:
    return tuple(int(colour[i : i + 2], 16) / 255 for i in (1, 3, 5))  # type: ignore[return-value]


def _linear(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _gamma(c: float) -> float:
    c = min(1.0, max(0.0, c))
    return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


def simulate(rgb: Rgb, vision: str) -> Rgb:
    lin = [_linear(c) for c in rgb]
    m = MACHADO[vision]
    return tuple(_gamma(sum(m[row][col] * lin[col] for col in range(3))) for row in range(3))  # type: ignore[return-value]


def to_lab(rgb: Rgb) -> tuple[float, float, float]:
    r, g, b = (_linear(c) for c in rgb)
    x = 0.4124564 * r + 0.3575761 * g + 0.1804375 * b
    y = 0.2126729 * r + 0.7151522 * g + 0.0721750 * b
    z = 0.0193339 * r + 0.1191920 * g + 0.9503041 * b
    white = (0.95047, 1.0, 1.08883)

    def f(t: float) -> float:
        return t ** (1 / 3) if t > 216 / 24389 else (24389 / 27 * t + 16) / 116

    fx, fy, fz = f(x / white[0]), f(y / white[1]), f(z / white[2])
    return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)


def delta_e(a: Rgb, b: Rgb, vision: str) -> float:
    return math.dist(to_lab(simulate(a, vision)), to_lab(simulate(b, vision)))


def tile_pixels() -> list[Rgb]:
    """The 256 opaque pixels of the pilot tile, as decoded by the store's own PNG reader."""
    png = next(EXPORT.glob("*.png"))
    image = pixels.decode_png(png.read_bytes())
    assert (image.width, image.height) == (16, 16)
    out: list[Rgb] = []
    for i in range(0, len(image.rgba), 4):
        assert image.rgba[i + 3] == 255, "the pilot tile is fully opaque"
        out.append((image.rgba[i] / 255, image.rgba[i + 1] / 255, image.rgba[i + 2] / 255))
    return out


def mean(colours: list[Rgb]) -> Rgb:
    return tuple(sum(c[i] for c in colours) / len(colours) for i in range(3))  # type: ignore[return-value]


def texture(colours: list[Rgb], vision: str) -> float:
    ls = [to_lab(simulate(c, vision))[0] for c in colours]
    mu = sum(ls) / len(ls)
    return math.sqrt(sum((v - mu) ** 2 for v in ls) / len(ls))


def evaluate(tile: list[Rgb], fills: dict[int, str]) -> dict:
    """The predeclared rule applied to `tile` (a list of pixels) against the Live Map's fills. Returns every number and the verdict."""
    forest_fill = from_hex(fills[FOREST])
    others = {name: from_hex(fills[code]) for name, code in NEIGHBOURS.items()}
    tile_mean = mean(tile)
    per_vision = {}
    for vision in VISIONS:
        tile_d = {name: delta_e(tile_mean, colour, vision) for name, colour in others.items()}
        fill_d = {name: delta_e(forest_fill, colour, vision) for name, colour in others.items()}
        tile_min, fill_min = min(tile_d.values()), min(fill_d.values())
        tex = texture(tile, vision)
        per_vision[vision] = {
            "dmin_tile": round(tile_min, 3), "dmin_fill": round(fill_min, 3),
            "closest_tile": min(tile_d, key=tile_d.get), "closest_fill": min(fill_d, key=fill_d.get),
            "p1": tile_min >= fill_min - TOLERANCE, "texture": round(tex, 3), "p2": tex >= TEXTURE_MIN,
        }
    p1 = all(v["p1"] for v in per_vision.values())
    p2 = all(v["p2"] for v in per_vision.values())
    return {
        "tile_mean_srgb255": [round(c * 255, 2) for c in tile_mean], "fill_srgb255": [round(c * 255, 2) for c in forest_fill],
        "per_vision": per_vision, "p1": p1, "p2": p2, "w05": "PASS" if p1 else "FAIL",
        "wording": "worse" if not p1 else ("better" if p2 else "same"),
    }


if __name__ == "__main__":
    print(json.dumps(evaluate(tile_pixels(), tile_fills()), indent=2))
