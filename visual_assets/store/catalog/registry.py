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
