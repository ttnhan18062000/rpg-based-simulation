---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260520-SIM-OBS-M34
artifact_type: plan
tags: [sim, obs, m34]
---

# Implementation Plan: Warehouse Adapter & Schema Stabilization

Defining the high-volume data warehouse boundary for the RPG simulation's Observatory, establishing standardized logical schema representations, adding a schema registry with descriptive validation error alerts, and implementing a database-free dry-run verification pipeline.

---

## 1. Proposed Changes

### [NEW] [base.py](file:///home/vboxuser/Work/rpg-based-simulation/src/observability/warehouse/base.py)
Define the primary abstract database adapter interface:
```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from src.observability.warehouse.models import *

class WarehouseAdapter(ABC):
    @abstractmethod
    def ingest_run(self, run_id: str, dry_run: bool = False) -> WarehouseIngestionResult:
        pass

    @abstractmethod
    def ingest_sweep(self, sweep_id: str, dry_run: bool = False) -> WarehouseIngestionResult:
        pass

    @abstractmethod
    def query_runs(self, filters: Dict[str, Any]) -> List[RunRecord]:
        pass

    @abstractmethod
    def query_events(self, filters: Dict[str, Any]) -> List[EventRecord]:
        pass

    @abstractmethod
    def query_anomalies(self, filters: Dict[str, Any]) -> List[AnomalyRecord]:
        pass

    @abstractmethod
    def health(self) -> WarehouseHealthStatus:
        pass

    @abstractmethod
    def close(self) -> None:
        pass
```

### [NEW] [models.py](file:///home/vboxuser/Work/rpg-based-simulation/src/observability/warehouse/models.py)
Logical schema representations of warehouse records using Pydantic:
- `RunRecord`: Maps run details, retaining dynamic properties in a serialized JSON string.
- `SweepRecord`: Maps scenario sweeps.
- `EventRecord`: Maps line-separated spacetime events.
- `MetricWindowRecord`: Maps RSS, computation averages, and entity telemetry.
- `AnomalyRecord`: Maps post-run rule violation records.
- `HardLawViolationRecord`: Maps spacetime physics/invariant infractions.
- `BaselineRecord`: Maps standard target parameters.
- `ComparisonRecord`: Maps delta results.
- `WarehouseIngestionResult`: Tracks count of parsed, successfully converted, and skipped rows, as well as timing metrics and execution statuses (`COMPLETED`, `FAILED`, `DRY_RUN`).
- `WarehouseHealthStatus`: Dynamic database health state metrics (`connected`, `latency_ms`, `error`).

### [NEW] [registry.py](file:///home/vboxuser/Work/rpg-based-simulation/src/observability/warehouse/registry.py)
Schema management and validation:
- Tracks `observability_artifact_v1` as the supported local artifact version.
- Tracks `warehouse_schema_v1` as the supported warehouse target.
- Performs structured validations of json and jsonl contents.
- Raises descriptive `WarehouseSchemaVersionMismatchError` if incompatible.

### [NEW] [adapters.py](file:///home/vboxuser/Work/rpg-based-simulation/src/observability/warehouse/adapters.py)
- **`NullWarehouseAdapter`**: Implements basic no-op interface.
- **`LocalWarehouseAdapter`**: Implements dry-run conversions. Performs full schema validation, file parsing, object mapping, and counts calculation.

### [NEW] [factory.py](file:///home/vboxuser/Work/rpg-based-simulation/src/observability/warehouse/factory.py)
Singleton resolver dynamic mapping based on config toggles.

### [MODIFY] [entry.py](file:///home/vboxuser/Work/rpg-based-simulation/src/cli/entry.py)
- Add subcommand parser: `warehouse ingest-run <run_id> --dry-run` and `warehouse ingest-sweep <sweep_id> --dry-run`.
- Print beautiful, structured statistics summary reports.

---

## 2. Ingestion Mapping Specifics

- **Run ID propagation**: All relational models (`EventRecord`, `AnomalyRecord`, etc.) will have their corresponding `run_id` explicitly populated on conversion.
- **JSON Field Serialization**: Fields containing complex dynamic lists or dictionaries (such as `payload`, `evidence`, `metrics`) will be serialized into JSON string formats using Pydantic's native `.model_dump_json()` or `json.dumps()` encoders to maintain stability.
