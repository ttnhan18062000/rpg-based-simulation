from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

_CATALOG_PATH_HINT = "CatalogRepository('data/content')"

_FORBIDDEN_FALLBACK_MODES = frozenset({"catalog_strict", "catalog_with_compatibility"})


class RuntimeContentMode(Enum):
    CATALOG_STRICT = "catalog_strict"
    CATALOG_WITH_COMPATIBILITY = "catalog_with_compatibility"
    LEGACY_FALLBACK = "legacy_fallback"
    TEST_MANUAL = "test_manual"


class FallbackRestrictedError(RuntimeError):
    """Raised when a mode that forbids hardcoded fallback encounters a missing catalog."""

    def __init__(self, mode: RuntimeContentMode, detail: str = "") -> None:
        self.mode = mode
        suffix = f" {detail}" if detail else ""
        super().__init__(
            f"[mode={mode.value}] Fallback to hardcoded content is restricted in this mode."
            f" Load a catalog via {_CATALOG_PATH_HINT} and pass it to bootstrap_registries() instead."
            f"{suffix}"
        )


@dataclass(frozen=True)
class AdapterHeuristicUsage:
    """Records a single heuristic inference performed by an adapter."""
    record_id: str
    family: str
    adapter: str
    heuristic_type: str
    reason: str
    mode: RuntimeContentMode
