"""Read-only access to the committed palettes (`visual_assets/palettes/<id>.json`) for the drawing tools' advisory lint.

One palette source for drawing and lint: the same files the review tooling generates and drift-guards. Only an id of the form `name-vN` that names an existing file is accepted (no path ever comes from the caller).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from visual_assets.drawing.errors import AdapterError

PALETTES_DIR = Path(__file__).resolve().parents[1] / "palettes"
_ID = re.compile(r"[a-z][a-z0-9]*-v[0-9]{1,3}")
_COLOR = re.compile(r"#[0-9a-f]{6}")


def palette_ids() -> list[str]:
    return sorted(p.stem for p in PALETTES_DIR.glob("*.json") if _ID.fullmatch(p.stem))


def load_palette(palette_id: str) -> list[str]:
    """The `colors` of the named palette (`#rrggbb`, lowercase)."""
    if not isinstance(palette_id, str) or not _ID.fullmatch(palette_id) or palette_id not in palette_ids():
        raise AdapterError(f"unknown palette id; known: {', '.join(palette_ids())}")
    colors = json.loads((PALETTES_DIR / f"{palette_id}.json").read_text(encoding="utf-8"))["colors"]
    if not isinstance(colors, list) or not colors or not all(isinstance(c, str) and _COLOR.fullmatch(c) for c in colors):
        raise AdapterError(f"palette {palette_id} is malformed")
    return colors
