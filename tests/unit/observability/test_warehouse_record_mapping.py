import pytest
import json
from src.observability.warehouse.registry import WarehouseSchemaRegistry, WarehouseSchemaVersionMismatchError
from src.observability.warehouse.models import RunRecord, EventRecord, AnomalyRecord
from src.observability.warehouse.adapters import LocalWarehouseAdapter

def test_registry_validation_correct_version():
    """Verify registry accepts manifest declaring observability_artifact_v1 version."""
    manifest = {
        "run_id": "run_1",
        "scenario_name": "test_scenario",
        "scenario_type": "standard",
        "seed": 42,
        "status": "COMPLETED",
        "artifact_schema_version": "observability_artifact_v1"
    }
    # Should not raise exception
    WarehouseSchemaRegistry.validate_manifest(manifest)

def test_registry_validation_missing_version_raises():
    """Verify registry raises error if version property is omitted."""
    manifest = {
        "run_id": "run_2"
    }
    with pytest.raises(WarehouseSchemaVersionMismatchError) as exc_info:
        WarehouseSchemaRegistry.validate_manifest(manifest)
    assert "MISSING" in str(exc_info.value)

def test_registry_validation_mismatched_version_raises():
    """Verify registry raises version mismatch on foreign/legacy format version."""
    manifest = {
        "run_id": "run_3",
        "artifact_schema_version": "observability_artifact_v999"
    }
    with pytest.raises(WarehouseSchemaVersionMismatchError) as exc_info:
        WarehouseSchemaRegistry.validate_manifest(manifest)
    assert "observability_artifact_v999" in str(exc_info.value)
    assert "observability_artifact_v1" in str(exc_info.value)

def test_run_record_preserves_raw_manifest_json():
    """Verify that a RunRecord converts successfully and retains manifest_json copy."""
    raw_manifest = {
        "run_id": "run_abc",
        "scenario_name": "combat_scenario",
        "scenario_type": "combat",
        "seed": 100,
        "status": "COMPLETED",
        "ticks_completed": 50,
        "health_score": 98.5,
        "started_at": "2026-05-20T10:00:00Z",
        "artifact_schema_version": "observability_artifact_v1"
    }
    record = RunRecord(
        run_id=raw_manifest["run_id"],
        scenario_name=raw_manifest["scenario_name"],
        scenario_type=raw_manifest["scenario_type"],
        seed=raw_manifest["seed"],
        status=raw_manifest["status"],
        ticks_completed=raw_manifest["ticks_completed"],
        health_score=raw_manifest["health_score"],
        started_at=raw_manifest["started_at"],
        manifest_json=json.dumps(raw_manifest)
    )
    assert record.run_id == "run_abc"
    assert record.health_score == 98.5
    parsed_manifest = json.loads(record.manifest_json)
    assert parsed_manifest["scenario_name"] == "combat_scenario"

def test_event_record_serializes_payload():
    """Verify that EventRecord successfully serializes dynamic dictionary payloads to string."""
    payload_dict = {
        "attacker": "goblin_1",
        "damage": 12.5,
        "critical": True
    }
    record = EventRecord(
        run_id="run_1",
        tick=5,
        event_type="entity_attack",
        event_category="combat",
        severity="INFO",
        message="Goblin 1 attacked Hero",
        payload_json=json.dumps(payload_dict),
        created_at="2026-05-20T10:05:00Z"
    )
    assert record.tick == 5
    assert record.severity == "INFO"
    payload_parsed = json.loads(record.payload_json)
    assert payload_parsed["attacker"] == "goblin_1"
    assert payload_parsed["damage"] == 12.5
