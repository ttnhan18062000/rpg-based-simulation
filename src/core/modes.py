from __future__ import annotations
from dataclasses import dataclass
from enum import Enum


class RuntimeContentMode(Enum):
    CATALOG_STRICT = "catalog_strict"
    CATALOG_WITH_COMPATIBILITY = "catalog_with_compatibility"
    LEGACY_FALLBACK = "legacy_fallback"
    TEST_MANUAL = "test_manual"


@dataclass(frozen=True)
class AdapterHeuristicUsage:
    """Records a single heuristic inference performed by an adapter."""
    record_id: str
    family: str
    adapter: str
    heuristic_type: str
    reason: str
    mode: RuntimeContentMode
