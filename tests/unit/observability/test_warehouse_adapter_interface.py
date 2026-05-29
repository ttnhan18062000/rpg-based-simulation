import pytest
from src.observability.warehouse.base import WarehouseAdapter
from src.observability.warehouse.models import WarehouseIngestionResult, WarehouseHealthStatus

def test_cannot_instantiate_base_warehouse_adapter():
    """Verify that WarehouseAdapter cannot be directly instantiated because it is an abstract base class."""
    with pytest.raises(TypeError):
        WarehouseAdapter()

def test_concrete_subclass_instantiation():
    """Verify that a concrete class implementing the WarehouseAdapter interface can be instantiated."""
    class DummyWarehouse(WarehouseAdapter):
        def ingest_run(self, run_id: str, dry_run: bool = False):
            return WarehouseIngestionResult(ingestion_id="dummy", run_id=run_id, status="COMPLETED", duration_ms=0.0)

        def ingest_sweep(self, sweep_id: str, dry_run: bool = False):
            return WarehouseIngestionResult(ingestion_id="dummy", sweep_id=sweep_id, status="COMPLETED", duration_ms=0.0)

        def query_runs(self, filters):
            return []

        def query_events(self, filters):
            return []

        def query_anomalies(self, filters):
            return []

        def query_metric_windows(self, filters):
            return []

        def query_violations(self, filters):
            return []

        def query_behavior_episodes(self, filters):
            return []

        def query_behavior_events(self, filters):
            return []

        def query_behavior_findings(self, filters):
            return []

        def query_behavior_insights(self, filters):
            return []

        def query_behavior_metric_windows(self, filters):
            return []

        def query_cohort_behavior_reports(self, filters):
            return []

        def query_entity_behavior_scorecards(self, filters):
            return []

        def query_run_behavior_comparisons(self, filters):
            return []

        def query_run_behavior_scorecards(self, filters):
            return []

        def health(self):
            return WarehouseHealthStatus(connected=True, latency_ms=1.2)

        def close(self):
            pass

    dummy = DummyWarehouse()
    assert dummy.health().connected is True
    assert dummy.health().latency_ms == 1.2
    assert dummy.ingest_run("run_123").status == "COMPLETED"

