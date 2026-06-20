from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

import yaml

_REGISTRY_PATH = Path(__file__).parent.parent.parent / "docs" / "engine" / "capability_registry.yaml"

VALID_STATUSES = frozenset({"OFFICIAL", "SUPPORTED", "EXPERIMENTAL", "DEPRECATED", "UNSUPPORTED"})
_SUPPORTED_STATUSES = frozenset({"OFFICIAL", "SUPPORTED", "EXPERIMENTAL"})


class CapabilityRegistry:
    """Read-only view of the engine capability registry (docs/engine/capability_registry.yaml)."""

    def __init__(self, registry_path: Path = _REGISTRY_PATH) -> None:
        with open(registry_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        self._entries: Dict[str, dict] = {
            entry["capability_id"]: entry for entry in data.get("capabilities", [])
        }

    def is_supported(self, capability_id: str) -> bool:
        """Return True if the capability has status OFFICIAL, SUPPORTED, or EXPERIMENTAL."""
        entry = self._entries.get(capability_id)
        if entry is None:
            return False
        return entry.get("status") in _SUPPORTED_STATUSES

    def get_status(self, capability_id: str) -> Optional[str]:
        """Return the status string for a capability_id, or None if not found."""
        entry = self._entries.get(capability_id)
        return entry.get("status") if entry else None

    def all_capabilities(self) -> List[dict]:
        """Return all capability entries as a list of dicts."""
        return list(self._entries.values())

    def capabilities_by_status(self, status: str) -> List[dict]:
        """Return all entries with the given status."""
        return [e for e in self._entries.values() if e.get("status") == status]


_default_registry: Optional[CapabilityRegistry] = None


def get_registry() -> CapabilityRegistry:
    """Return the singleton CapabilityRegistry (lazy-loaded)."""
    global _default_registry
    if _default_registry is None:
        _default_registry = CapabilityRegistry()
    return _default_registry
