"""Validators for the primitive request fields (names, layers, colours, bounded integers, objects)."""

from __future__ import annotations

import re

from visual_assets.drawing import config
from visual_assets.drawing.colors import hex_to_rgba
from visual_assets.drawing.errors import AdapterError

NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,31}$")


LAYER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 _-]{0,31}$")


def check_name(name) -> str:
    if not isinstance(name, str) or not NAME_RE.fullmatch(name):
        raise AdapterError("name must match [a-z0-9][a-z0-9_-]{0,31}")
    return name


def check_layer_name(value, label="layer") -> str:
    if not isinstance(value, str) or not LAYER_RE.fullmatch(value):
        raise AdapterError(f"{label} must match [A-Za-z0-9][A-Za-z0-9 _-]{{0,31}}")
    return value


def check_color(value) -> list[int]:
    return list(hex_to_rgba(value))


def check_int(value, label: str, lo: int, hi: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not lo <= value <= hi:
        raise AdapterError(f"{label} must be an integer in [{lo}, {hi}]")
    return value


def check_coord(value, label: str) -> int:
    return check_int(value, label, 0, config.MAX_DIM - 1)


def check_dict(value, label: str) -> dict:
    if not isinstance(value, dict):
        raise AdapterError(f"{label} must be an object")
    return value


def check_no_extra(op: dict, allowed: set[str]) -> None:
    extra = set(op) - allowed - {"op", "layer", "frame"}
    if extra:
        raise AdapterError(f"op {op['op']}: unexpected field(s) {sorted(extra)}")
