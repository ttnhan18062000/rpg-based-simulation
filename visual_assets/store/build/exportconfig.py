"""`catalog/build-config/export.toml`: the pinned export rules. Parsed strictly (stdlib `tomllib`); unknown keys are rejected."""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass
from pathlib import Path

from visual_assets.store import config
from visual_assets.store.errors import BuildError
from visual_assets.store.intake.validator import file_hash

_NAME = re.compile(r"[a-z0-9][a-z0-9_]{0,31}")
_TOP = {"format", "frame", "scale_class"}
_CLASS = {"name", "scale"}


@dataclass(frozen=True)
class ScaleClass:
    name: str
    scale: int


@dataclass(frozen=True)
class ExportConfig:
    format: str
    frame: int
    scale_classes: tuple[ScaleClass, ...]
    file_hash: str  # FileHash of the exact file bytes: part of every artifact's build fingerprint


def _bad(message: str) -> BuildError:
    return BuildError("export_config_invalid", message)


def load_export_config(path: Path | None = None) -> ExportConfig:
    target = path if path is not None else config.CATALOG_ROOT / "build-config" / "export.toml"
    try:
        data = target.read_bytes() if target.stat().st_size <= config.MAX_RECORD_BYTES else b""
    except OSError as exc:
        raise _bad(f"cannot read {target.name}: {exc.strerror}") from None
    if not data:
        raise _bad(f"{target.name} is empty or over {config.MAX_RECORD_BYTES} bytes")
    try:
        raw = tomllib.loads(data.decode("utf-8"))
    except (tomllib.TOMLDecodeError, UnicodeDecodeError) as exc:
        raise _bad(f"{target.name} is not valid TOML ({exc})") from None
    if set(raw) - _TOP or "format" not in raw or "frame" not in raw or "scale_class" not in raw:
        raise _bad(f"{target.name} must have exactly the keys {sorted(_TOP)}")
    if raw["format"] != "png":
        raise _bad("format must be \"png\"")
    if type(raw["frame"]) is not int or raw["frame"] != 1:
        raise _bad("frame must be the integer 1 (only the first frame is exported)")
    classes_raw = raw["scale_class"]
    if not isinstance(classes_raw, list) or not classes_raw:
        raise _bad("scale_class must be a non-empty array of tables")
    classes = []
    for entry in classes_raw:
        if not isinstance(entry, dict) or set(entry) != _CLASS:
            raise _bad(f"each scale_class needs exactly the keys {sorted(_CLASS)}")
        name, scale = entry["name"], entry["scale"]
        if not isinstance(name, str) or not _NAME.fullmatch(name) or type(scale) is not int or not 1 <= scale <= 16:
            raise _bad("scale_class name is [a-z0-9_]{1,32} and scale is an integer 1..16")
        classes.append(ScaleClass(name, scale))
    if len({c.name for c in classes}) != len(classes):
        raise _bad("scale_class names must be unique")
    if [(c.name, c.scale) for c in classes] != [("x1", 1)]:
        raise _bad("this foundation exports exactly one scale class, x1 (scale 1); more are out of scope")
    return ExportConfig("png", 1, tuple(classes), file_hash(data))
