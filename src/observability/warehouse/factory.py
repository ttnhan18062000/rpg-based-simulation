from __future__ import annotations
import threading
from typing import Dict, Optional

from src.observability.warehouse.base import WarehouseAdapter
from src.observability.warehouse.adapters import NullWarehouseAdapter, LocalWarehouseAdapter
from src.observability.warehouse.clickhouse import ClickHouseWarehouseAdapter
from src.observability.config import ObservabilityConfig

class WarehouseAdapterFactory:
    """Thread-safe factory caching resolved WarehouseAdapter instances."""
    _instance: Optional[WarehouseAdapter] = None
    _lock = threading.Lock()

    @classmethod
    def get_adapter(cls) -> WarehouseAdapter:
        """Resolves and caches the active warehouse adapter instance."""
        with cls._lock:
            if cls._instance is not None:
                return cls._instance

            backend = ObservabilityConfig.get_warehouse_backend().lower().strip()
            if backend == "null":
                cls._instance = NullWarehouseAdapter()
            elif backend == "clickhouse":
                cls._instance = ClickHouseWarehouseAdapter()
            else:
                # Default to Local dry-run adapter
                cls._instance = LocalWarehouseAdapter()


            return cls._instance

    @classmethod
    def reset_adapter(cls) -> None:
        """Resets the cached instance, e.g. for dynamic testing overrides."""
        with cls._lock:
            if cls._instance is not None:
                cls._instance.close()
                cls._instance = None


def get_warehouse_adapter() -> WarehouseAdapter:
    """Convenience helper to retrieve the cached active database warehouse adapter."""
    return WarehouseAdapterFactory.get_adapter()
