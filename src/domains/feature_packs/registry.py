"""
src/domains/feature_packs/registry.py
───────────────────────────────────────────────────────────────────────────────
FeatureRegistry[T] — dict-based generic registry for feature pack extensions.

One instance per domain extension point type.  Canonical entries are drawn
from an Enum class provided at construction; pack entries are added at load
time via register().  list_all() merges both sets deterministically.
"""

from __future__ import annotations

from enum import Enum
from typing import Generic, Optional, Type, TypeVar

T = TypeVar("T")


class FeatureRegistry(Generic[T]):
    """Generic dict-based registry for a single domain extension point.

    Parameters
    ----------
    enum_class:
        Optional Enum whose members provide the canonical (built-in) entries.
        list_all() emits their .value strings before pack-registered keys.

    Usage
    -----
    registry: FeatureRegistry[type] = FeatureRegistry(enum_class=RouteFamily)
    registry.register("ESCORT_DIGNITARY", EscortDignitaryGenerator)
    assert "ESCORT_DIGNITARY" in registry.list_all()
    """

    def __init__(self, enum_class: Optional[Type[Enum]] = None) -> None:
        self._enum_class = enum_class
        self._pack_entries: dict[str, T] = {}

    def register(self, key: str, value: T) -> None:
        """Register a pack-contributed entry under *key*.  Overwrites on duplicate."""
        self._pack_entries[key] = value

    def lookup(self, key: str) -> T:
        """Return the registered value for *key*.

        Raises
        ------
        KeyError
            If *key* has not been registered by any pack.
        """
        if key in self._pack_entries:
            return self._pack_entries[key]
        raise KeyError(key)

    def list_all(self) -> list[str]:
        """Return all known keys: canonical enum values first, then pack-registered.

        Both groups are sorted alphabetically within themselves.  Canonical
        keys and pack keys are deduplicated: a pack key that shadows a canonical
        name appears only in the canonical section.
        """
        canonical: list[str] = []
        if self._enum_class is not None:
            canonical = sorted(member.value for member in self._enum_class)

        canonical_set = set(canonical)
        pack_only = sorted(k for k in self._pack_entries if k not in canonical_set)
        return canonical + pack_only
