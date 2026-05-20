from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from src.observability.warehouse.models import (
    WarehouseIngestionResult,
    WarehouseHealthStatus,
    RunRecord,
    EventRecord,
    AnomalyRecord,
    MetricWindowRecord,
    HardLawViolationRecord
)

class WarehouseAdapter(ABC):
    """
    Abstract interface for high-volume telemetry event warehouses.
    Core simulation services and historical search APIs interact with this abstraction,
    enabling clickhouse, local file databases, or dry-run validation engines to be hot-swapped.
    """

    @abstractmethod
    def ingest_run(self, run_id: str, dry_run: bool = False, force: bool = False) -> WarehouseIngestionResult:
        """
        Parses and validates local run artifacts (manifest, events, anomalies, violations)
        and streams/batches them to the database. If dry_run is True, validates and parses
        without performing database writes.
        """
        pass

    @abstractmethod
    def ingest_sweep(self, sweep_id: str, dry_run: bool = False, force: bool = False) -> WarehouseIngestionResult:
        """
        Parses and validates a multi-run sweep (including sweep summaries and indexes)
        and streams them to the database.
        """
        pass

    @abstractmethod
    def query_runs(self, filters: Dict[str, Any]) -> List[RunRecord]:
        """
        Queries historical runs filtered by given parameters (limit, scenario_name, health, etc.).
        """
        pass

    @abstractmethod
    def query_events(self, filters: Dict[str, Any]) -> List[EventRecord]:
        """
        Queries historical simulation events (severity, event_type, tick range).
        """
        pass

    @abstractmethod
    def query_anomalies(self, filters: Dict[str, Any]) -> List[AnomalyRecord]:
        """
        Queries historical anomalies.
        """
        pass

    @abstractmethod
    def query_metric_windows(self, filters: Dict[str, Any]) -> List[MetricWindowRecord]:
        """
        Queries historical metric windows.
        """
        pass

    @abstractmethod
    def query_violations(self, filters: Dict[str, Any]) -> List[HardLawViolationRecord]:
        """
        Queries historical hard law violations.
        """
        pass

    @abstractmethod
    def health(self) -> WarehouseHealthStatus:
        """
        Checks database connection status and latencies.
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """
        Flushes background queues and safely terminates database connection pools.
        """
        pass
