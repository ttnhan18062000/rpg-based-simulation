from enum import Enum
from typing import Dict, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src.content.repository import CatalogRepository


class CatalogMissError(RuntimeError):
    """Raised by GracefulDegradationManager when catalog is absent in strict mode."""


class DegradationLevel(str, Enum):
    NORMAL = "NORMAL"
    CONSTRAINED = "CONSTRAINED"
    DEGRADED = "DEGRADED"
    CRITICAL = "CRITICAL"


class GracefulDegradationManager:
    """Monitors load metrics and enters degraded execution states to preserve frame rate.

    Also provides catalog-driven content-source resolution via resolve_content_source().
    In degraded or critical mode, catalog entries are always preferred over hardcoded
    static defaults to prevent serving stale content under resource pressure.
    """
    def __init__(self) -> None:
        self._level = DegradationLevel.NORMAL
        self._reason = "Normal operation"

    def get_level(self) -> DegradationLevel:
        return self._level

    def update_pressure(self, tick_time_ms: float, limit_ms: float) -> DegradationLevel:
        ratio = tick_time_ms / limit_ms
        if ratio >= 1.0:
            self._level = DegradationLevel.CRITICAL
            self._reason = "Time limit exceeded"
        elif ratio >= 0.95:
            self._level = DegradationLevel.DEGRADED
            self._reason = "Time pressure high (>95%)"
        elif ratio >= 0.8:
            self._level = DegradationLevel.CONSTRAINED
            self._reason = "Time pressure moderate (>80%)"
        else:
            self._level = DegradationLevel.NORMAL
            self._reason = "Normal operation"
        return self._level

    def get_provider_cap(self, original_cap: int) -> int:
        if self._level == DegradationLevel.CRITICAL:
            return max(1, original_cap // 4)
        if self._level == DegradationLevel.DEGRADED:
            return max(1, original_cap // 3)
        if self._level == DegradationLevel.CONSTRAINED:
            return max(1, original_cap // 2)
        return original_cap

    def should_skip_phase(self, phase_name: str) -> bool:
        # Crucial/base phases like capability layer should never be skipped in CRITICAL unless hard-forced.
        # But optional optimization/emergence/campaigns should be degraded first.
        if self._level == DegradationLevel.CRITICAL:
            return phase_name in ("ENABLE_WORLD_EMERGENCE", "ENABLE_LIFE_ARC_CAMPAIGNS", "ENABLE_COOPERATION")
        if self._level == DegradationLevel.DEGRADED:
            return phase_name in ("ENABLE_WORLD_EMERGENCE", "ENABLE_LIFE_ARC_CAMPAIGNS")
        return False

    def resolve_content_source(
        self,
        catalog_repo: "Optional[CatalogRepository]",
        content_type: str,
        strict: bool = False,
    ) -> Dict[str, Any]:
        """Return catalog entries for content_type, honoring the degradation level.

        In degraded or critical mode, catalog-driven entries are always preferred
        over hardcoded static paths.  Returns entries cheapest-first so callers
        under resource pressure can take only what they need.

        Args:
            catalog_repo: A loaded CatalogRepository, or None if unavailable.
            content_type: Content family to resolve ('items', 'resources', ...).
            strict: If True and catalog_repo is None, raise CatalogMissError
                    instead of returning an empty dict.

        Returns:
            Dict mapping record_id to catalog definition, cheapest-first.

        Raises:
            CatalogMissError: If strict=True and catalog_repo is None.
        """
        if catalog_repo is None:
            if strict:
                raise CatalogMissError(
                    f"Catalog unavailable for content type '{content_type}' in strict mode."
                )
            return {}
        return catalog_repo.get_lowest_cost_for_type(content_type)

    def generate_report(self) -> Dict[str, Any]:
        return {
            "degradation_level": self._level.value,
            "reason": self._reason
        }
