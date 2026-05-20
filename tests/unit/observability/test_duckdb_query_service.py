# Compliance IDs: OBS-058, OBS-059
from __future__ import annotations

import os
import shutil
import tempfile
import pytest
from src.observability.analytics.query import DuckDBQueryService

@pytest.fixture
def sample_dataset_dir():
    temp_dir = tempfile.mkdtemp()
    
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError:
        yield None
        shutil.rmtree(temp_dir)
        return

    # 1. Create mock runs parquet
    run_schema = pa.schema([
        ("run_id", pa.string()),
        ("seed", pa.int64()),
        ("health_score", pa.float64()),
        ("status", pa.string()),
        ("critical_count", pa.int64()),
        ("warning_count", pa.int64())
    ])
    run_data = {
        "run_id": ["run_low", "run_high", "run_mid"],
        "seed": [10, 20, 30],
        "health_score": [55.0, 99.0, 75.0],
        "status": ["COMPLETED", "COMPLETED", "COMPLETED"],
        "critical_count": [3, 0, 1],
        "warning_count": [5, 0, 2]
    }
    pq.write_table(pa.Table.from_pydict(run_data, schema=run_schema), os.path.join(temp_dir, "runs.parquet"))

    # 2. Create mock anomalies parquet
    anom_schema = pa.schema([
        ("run_id", pa.string()),
        ("rule_id", pa.string()),
        ("severity", pa.string())
    ])
    anom_data = {
        "run_id": ["run_low", "run_low", "run_mid", "run_low"],
        "rule_id": ["RuleA", "RuleB", "RuleA", "RuleA"],
        "severity": ["CRITICAL", "WARNING", "CRITICAL", "CRITICAL"]
    }
    pq.write_table(pa.Table.from_pydict(anom_data, schema=anom_schema), os.path.join(temp_dir, "anomalies.parquet"))

    yield temp_dir
    shutil.rmtree(temp_dir)


def test_duckdb_worst_runs_query(sample_dataset_dir):
    if sample_dataset_dir is None:
        pytest.skip("pyarrow or duckdb not available in test environment.")

    service = DuckDBQueryService(dataset_dir=sample_dataset_dir)
    if not service.enabled:
        pytest.skip("duckdb is not installed in test environment.")

    results = service.execute_predefined_query("worst-runs")
    
    # Assert return types and record counts
    assert isinstance(results, list)
    assert len(results) == 3

    # Assert health_score sorting ASC: run_low (55.0) -> run_mid (75.0) -> run_high (99.0)
    assert results[0]["run_id"] == "run_low"
    assert results[0]["health_score"] == 55.0
    
    assert results[1]["run_id"] == "run_mid"
    assert results[1]["health_score"] == 75.0

    assert results[2]["run_id"] == "run_high"
    assert results[2]["health_score"] == 99.0


def test_duckdb_anomaly_summary_query(sample_dataset_dir):
    if sample_dataset_dir is None:
        pytest.skip("pyarrow or duckdb not available in test environment.")

    service = DuckDBQueryService(dataset_dir=sample_dataset_dir)
    if not service.enabled:
        pytest.skip("duckdb is not installed in test environment.")

    results = service.execute_predefined_query("anomaly-summary")
    
    # Expected groups:
    # 1. RuleA, CRITICAL -> count = 3
    # 2. RuleB, WARNING -> count = 1
    assert len(results) == 2
    
    first = results[0]
    assert first["rule_id"] == "RuleA"
    assert first["severity"] == "CRITICAL"
    assert first["count"] == 3

    second = results[1]
    assert second["rule_id"] == "RuleB"
    assert second["severity"] == "WARNING"
    assert second["count"] == 1


def test_duckdb_unsupported_query(sample_dataset_dir):
    if sample_dataset_dir is None:
        pytest.skip("pyarrow or duckdb not available in test environment.")

    service = DuckDBQueryService(dataset_dir=sample_dataset_dir)
    if not service.enabled:
        pytest.skip("duckdb is not installed in test environment.")

    with pytest.raises(ValueError):
        service.execute_predefined_query("random-query")
