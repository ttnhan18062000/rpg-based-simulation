"""Load and query the semantic `visual_key` registry (`catalog/definitions/visual_keys.yaml`).

Read-only. The key namespace is finite and fixed by the file: nothing is ever registered dynamically, and a
`fixture.*` key is rejected unless the caller opts in (synthetic test data only).
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType
from typing import Any

import yaml

from visual_assets.store import config
from visual_assets.store.contracts.base import parse_record
from visual_assets.store.contracts.definitions import VisualKeyDefinition, VisualKeyRegistry
from visual_assets.store.errors import ContractError, RegistryError
from visual_assets.store.identities import is_fixture_key


def safety_problems(definition: VisualKeyDefinition, *, require_class: bool = True) -> list[str]:
    """Every rule a key breaks (`AM1-W02.7`, `W03.1`; text for the loader's `RegistryError`); empty when it passes.

    `variant_axes` must be empty (D17: the only axis is `detail`, so a non-empty list would promise a precedence nothing implements). The class and the structured fallback are required
    (`require_class`; synthetic `fixture.*` keys are exempt): `identifying` needs a fallback that is not `none`, `critical` needs one that carries `text`; the parts must fit the kind. An
    icon key that is not decorative carries `label_key == "label." + key` and a `label`; a decorative one carries neither."""
    key = definition.key
    problems: list[str] = []
    if definition.variant_axes:
        problems.append(f"{key}: variant_axes must be empty (D17: only the detail axis exists)")
    cls, fb = definition.safety_class, definition.fallback
    if cls is None or fb is None:
        if require_class:
            problems.append(f"{key}: safety_class and fallback are required (AM1-W02.7)")
        return problems
    parts = {"none": (False, False), "flat_fill": (True, False), "text": (True, False), "glyph_and_text": (True, True)}[fb.kind]
    if (fb.text is not None and fb.text.strip() != "") != parts[0] or (fb.glyph is not None and fb.glyph.strip() != "") != parts[1]:
        problems.append(f"{key}: fallback kind {fb.kind!r} needs " + {"none": "no text and no glyph", "flat_fill": "text and no glyph", "text": "text and no glyph", "glyph_and_text": "text and a glyph"}[fb.kind])
    if cls == "identifying" and fb.kind == "none":
        problems.append(f"{key}: an identifying key needs a fallback that carries its fact, not 'none'")
    if cls == "critical" and fb.kind not in ("text", "glyph_and_text"):
        problems.append(f"{key}: a critical key needs a text alternative that works with no image")
    if definition.family == "icon":
        if cls == "decorative":
            if definition.label_key is not None or definition.label is not None:
                problems.append(f"{key}: a decorative key carries no label (empty alt)")
        elif definition.label_key != f"label.{key}" or not (definition.label or "").strip():
            problems.append(f"{key}: an icon that is not decorative needs label_key 'label.{key}' and a label")
    return problems


def fallback_problems(registry: "Registry", present: set[str]) -> list[str]:
    """`AM1-W06.3`: what would be shown for every registry key that has NO artifact in a release (`present` = keys with one).

    Usable at build, release and activation: an `identifying` or `critical` key without an image must still have an alternative that carries its fact. The loader already refuses a
    malformed key; this is the explicit check a release or an activation can run on any registry object, however it was built."""
    out: list[str] = []
    for key in sorted(registry.keys):
        definition = registry.keys[key]
        if key in present or definition.safety_class is None or definition.safety_class == "decorative":
            continue
        fb = definition.fallback
        if fb is None or fb.kind == "none" or not (fb.text or "").strip():
            out.append(f"{key}: {definition.safety_class} key has no image in this release and no alternative that carries its fact")
    return out


class _StrictLoader(yaml.SafeLoader):
    """`safe_load` that rejects duplicate mapping keys and anchors/aliases (no expansion tricks)."""

    def compose_node(self, parent, index):  # type: ignore[no-untyped-def]
        if self.check_event(yaml.events.AliasEvent):
            raise RegistryError("YAML aliases are not allowed in the registry")
        return super().compose_node(parent, index)

    def construct_mapping(self, node, deep=False):  # type: ignore[no-untyped-def]
        seen: set[Any] = set()
        for key_node, _ in node.value:
            key = self.construct_object(key_node, deep=True)
            if key in seen:
                raise RegistryError(f"duplicate YAML key {key!r}")
            seen.add(key)
        return super().construct_mapping(node, deep)


class Registry:
    """An immutable, validated registry. `resolve` follows at most one alias."""

    def __init__(self, keys: Mapping[str, VisualKeyDefinition], aliases: Mapping[str, str], file_hash: str) -> None:
        self._keys = MappingProxyType(dict(keys))
        self._aliases = MappingProxyType(dict(aliases))
        self.file_hash = file_hash

    @property
    def keys(self) -> Mapping[str, VisualKeyDefinition]:
        return self._keys

    @property
    def aliases(self) -> Mapping[str, str]:
        return self._aliases

    def resolve(self, key: str) -> VisualKeyDefinition:
        target = self._aliases.get(key, key)
        try:
            return self._keys[target]
        except KeyError:
            raise RegistryError(f"unknown visual key {key!r}") from None


def _default_path() -> Path:
    return config.CATALOG_ROOT / "definitions" / "visual_keys.yaml"


def _read_bounded(path: Path) -> bytes:
    limit = config.MAX_REGISTRY_BYTES
    try:
        with path.open("rb") as handle:
            data = handle.read(limit + 1)
    except OSError as exc:
        raise RegistryError(f"cannot read registry {path}: {exc.strerror}") from None
    if len(data) > limit:
        raise RegistryError(f"registry exceeds {limit} bytes")
    return data


def _parse(data: bytes) -> VisualKeyRegistry:
    try:
        raw = yaml.load(data.decode("utf-8"), Loader=_StrictLoader)  # noqa: S506 - SafeLoader subclass
        body = json.dumps(raw, allow_nan=False, separators=(",", ":")).encode("utf-8")
    except RegistryError:
        raise
    except (yaml.YAMLError, UnicodeDecodeError, TypeError, ValueError, RecursionError) as exc:
        raise RegistryError(f"registry is not valid YAML data: {exc}") from None
    try:
        return parse_record(VisualKeyRegistry, body)
    except ContractError as exc:
        raise RegistryError(f"registry rejected ({exc.code}): {exc.message}") from None


def load_registry(path: Path | None = None, *, allow_fixture_namespace: bool = False) -> Registry:
    data = _read_bounded(path if path is not None else _default_path())
    record = _parse(data)

    if len(record.keys) > config.MAX_VISUAL_KEYS:
        raise RegistryError(f"more than {config.MAX_VISUAL_KEYS} keys")
    if len(record.aliases) > config.MAX_ALIASES:
        raise RegistryError(f"more than {config.MAX_ALIASES} aliases")

    if sum(1 for definition in record.keys if definition.detail is not None) > config.MAX_DETAIL_KEYS:
        raise RegistryError(f"more than {config.MAX_DETAIL_KEYS} keys declare a detail axis")

    keys: dict[str, VisualKeyDefinition] = {}
    for definition in record.keys:
        if definition.key in keys:
            raise RegistryError(f"duplicate key {definition.key!r}")
        if is_fixture_key(definition.key) and not allow_fixture_namespace:
            raise RegistryError(f"fixture key {definition.key!r} is not allowed here")
        problems = safety_problems(definition, require_class=not is_fixture_key(definition.key))
        if problems:
            raise RegistryError("; ".join(problems))
        keys[definition.key] = definition

    aliases: dict[str, str] = {}
    for entry in record.aliases:
        if entry.alias in aliases:
            raise RegistryError(f"duplicate alias {entry.alias!r}")
        if entry.alias in keys:
            raise RegistryError(f"alias {entry.alias!r} is also a key")
        if is_fixture_key(entry.alias) and not allow_fixture_namespace:
            raise RegistryError(f"fixture alias {entry.alias!r} is not allowed here")
        aliases[entry.alias] = entry.target
    for alias, target in aliases.items():
        if target in aliases:
            raise RegistryError(f"alias {alias!r} points at alias {target!r} (chains are not allowed)")
        if target not in keys:
            raise RegistryError(f"alias {alias!r} points at missing key {target!r}")

    return Registry(keys, aliases, "sha256:" + hashlib.sha256(data).hexdigest())
