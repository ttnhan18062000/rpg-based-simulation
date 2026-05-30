# Compliance IDs: WORLD-102, WORLD-103
import os
import json
import pytest
import tempfile
from pathlib import Path

from src.observability.warehouse.models import RunRecord
from src.observability.warehouse.adapters import LocalWarehouseAdapter
from src.observability.warehouse.provenance_lookup import ProvenanceLookupService
from src.observability.reporting.artifact_repository import RunArtifactRepository


def test_run_record_model_schema_extension():
    """Verify that RunRecord correctly accepts all new optional resolved world assembly fields."""
    record = RunRecord(
        run_id="run_test_99",
        scenario_name="Test Scenario",
        scenario_type="test",
        seed=123,
        status="COMPLETED",
        ticks_completed=100,
        health_score=95.0,
        started_at="2026-05-30T12:00:00Z",
        manifest_json="{}",
        resolved_world_path="/path/to/resolved_world.json",
        provenance_manifest_path="/path/to/provenance_manifest.json",
        assembly_report_path="/path/to/assembly_report.json",
        validation_report_path="/path/to/validation_report.json",
        compile_report_path="/path/to/compile_report.json",
        catalog_fingerprint="cat_f123",
        module_fingerprints={"module_a": "mod_f456"},
        state_hash="state_h789"
    )

    assert record.resolved_world_path == "/path/to/resolved_world.json"
    assert record.catalog_fingerprint == "cat_f123"
    assert record.module_fingerprints == {"module_a": "mod_f456"}
    assert record.state_hash == "state_h789"


def test_local_warehouse_ingest_run_extended_fields():
    """Verify LocalWarehouseAdapter parses and ingests the extended resolved world assembly fields."""
    with tempfile.TemporaryDirectory() as tmpdir:
        run_repo = RunArtifactRepository(base_dir=tmpdir)
        adapter = LocalWarehouseAdapter(run_repo=run_repo)

        # 1. Create a dummy run directory and mock run_manifest.json carrying the fields
        run_id = "run_full_world_99"
        run_dir = Path(tmpdir) / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        manifest_data = {
            "run_id": run_id,
            "scenario_name": "Assembled Scenario",
            "scenario_type": "assembled",
            "seed": 42,
            "status": "COMPLETED",
            "ticks_requested": 100,
            "ticks_completed": 100,
            "started_at": "2026-05-30T12:00:00Z",
            "observability_mode": "full",
            "engine_version": "2.0.0",
            "artifact_schema_version": "observability_artifact_v1",
            "resolved_world_path": "resolved_world.json",
            "provenance_manifest_path": "provenance_manifest.json",
            "assembly_report_path": "assembly_report.json",
            "validation_report_path": "validation_report.json",
            "compile_report_path": "compile_report.json",
            "catalog_fingerprint": "catalog_sha256",
            "module_fingerprints": {"core_layout": "layout_sha256"},
            "state_hash": "assembled_state_sha256"
        }

        with open(run_dir / "run_manifest.json", "w", encoding="utf-8") as f:
            json.dump(manifest_data, f)

        # 2. Ingest the run
        res = adapter.ingest_run(run_id, dry_run=True)
        assert res.status == "DRY_RUN"
        assert res.records_ingested["runs"] == 1

        # 3. Query the runs and verify mapping properties
        records = adapter.query_runs({"limit": 10})
        assert len(records) == 1
        rec = records[0]
        assert rec.run_id == run_id
        assert rec.resolved_world_path == "resolved_world.json"
        assert rec.provenance_manifest_path == "provenance_manifest.json"
        assert rec.catalog_fingerprint == "catalog_sha256"
        assert rec.module_fingerprints == {"core_layout": "layout_sha256"}
        assert rec.state_hash == "assembled_state_sha256"


def test_provenance_lookup_service_joins():
    """Verify that ProvenanceLookupService correctly resolves element origin mapping from sidecars."""
    with tempfile.TemporaryDirectory() as tmpdir:
        run_repo = RunArtifactRepository(base_dir=tmpdir)
        lookup_service = ProvenanceLookupService(run_repo=run_repo)

        run_id = "run_provenance_99"
        run_dir = Path(tmpdir) / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        # 1. Create a dummy provenance_manifest.json file in the run directory
        provenance_manifest = {
            "manifest_id": "prov_manifest_123",
            "world_id": "test_valley",
            "catalog_fingerprint": "catalog_sha256",
            "module_fingerprints": {"core_town": "town_sha256"},
            "records": {
                "citizen_group": {
                    "source_module": "core_town",
                    "recipe_type": "population",
                    "parameters": {"count": 5},
                    "profiles": {"role": "citizen"},
                    "details": {"region": "town_square"}
                },
                "ore_node": {
                    "source_module": "wilderness_layout",
                    "recipe_type": "resource",
                    "parameters": {"count": 3},
                    "profiles": {"resource_type": "ore"},
                    "details": {"region": "wilds"}
                },
                "tavern": {
                    "source_module": "core_town",
                    "recipe_type": "building",
                    "parameters": {},
                    "profiles": {"building_type": "shop"},
                    "details": {"region": "town_square"}
                },
                "town_square": {
                    "source_module": "core_town",
                    "recipe_type": "region",
                    "parameters": {},
                    "profiles": {},
                    "details": {"bounds": [0, 0, 10, 10]}
                }
            }
        }

        with open(run_dir / "provenance_manifest.json", "w", encoding="utf-8") as f:
            json.dump(provenance_manifest, f)

        # 2. Query provenance joins using ProvenanceLookupService
        entity_origin = lookup_service.get_entity_origin(run_id, "citizen_group")
        assert entity_origin is not None
        assert entity_origin["source_module"] == "core_town"
        assert entity_origin["element_type"] == "population"
        assert entity_origin["parameters"] == {"count": 5}

        resource_origin = lookup_service.get_resource_origin(run_id, "ore_node")
        assert resource_origin is not None
        assert resource_origin["source_module"] == "wilderness_layout"
        assert resource_origin["element_type"] == "resource"

        building_origin = lookup_service.get_building_origin(run_id, "tavern")
        assert building_origin is not None
        assert building_origin["source_module"] == "core_town"

        region_origin = lookup_service.get_region_origin(run_id, "town_square")
        assert region_origin is not None
        assert region_origin["source_module"] == "core_town"
        assert region_origin["details"] == {"bounds": [0, 0, 10, 10]}


def test_provenance_lookup_with_mapped_ids():
    """Verify that ProvenanceLookupService resolves concrete runtime IDs to their provenance keys."""
    with tempfile.TemporaryDirectory() as tmpdir:
        run_repo = RunArtifactRepository(base_dir=tmpdir)
        lookup_service = ProvenanceLookupService(run_repo=run_repo)

        run_id = "run_mapped_ids_99"
        run_dir = Path(tmpdir) / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        # 1. Create a dummy world.resolved.yaml
        resolved_world_content = {
            "schema_version": "worldspec.v1",
            "world_id": "test_valley",
            "name": "Test Valley",
            "regions": [
                {"id": "town_square", "bounds": [0, 0, 10, 10], "type": "town"},
                {"id": "wilds", "bounds": [10, 10, 20, 20], "type": "wilderness"}
            ],
            "factions": [],
            "resources": [
                {"id": "ore_node", "region": "wilds", "resource_type": "iron_ore", "count": 5}
            ],
            "buildings": [
                {"id": "tavern", "region": "town_square", "type": "shop"}
            ],
            "entities": [
                {"id": "citizen_group", "spawn_region": "town_square", "role": "citizen", "faction": "town_council", "count": 5}
            ],
            "topology": {"width": 100, "height": 100, "coordinate_system": "grid"}
        }
        resolved_world_path = run_dir / "world.resolved.yaml"
        import yaml
        with open(resolved_world_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(resolved_world_content, f)

        # 2. Create a dummy run_manifest.json pointing to it
        run_manifest = {
            "run_id": run_id,
            "scenario_name": "Test",
            "scenario_type": "test",
            "seed": 42,
            "status": "COMPLETED",
            "ticks_requested": 10,
            "started_at": "2026-05-30T12:00:00Z",
            "observability_mode": "full",
            "resolved_world_path": str(resolved_world_path)
        }
        with open(run_dir / "run_manifest.json", "w", encoding="utf-8") as f:
            json.dump(run_manifest, f)

        # 3. Create provenance manifest sidecar
        provenance_manifest = {
            "manifest_id": "prov_manifest_123",
            "world_id": "test_valley",
            "catalog_fingerprint": "catalog_sha256",
            "records": {
                "citizen_group": {
                    "source_module": "core_town",
                    "recipe_type": "population"
                },
                "ore_node": {
                    "source_module": "wilderness_layout",
                    "recipe_type": "resource"
                },
                "tavern": {
                    "source_module": "core_town",
                    "recipe_type": "building"
                }
            }
        }
        with open(run_dir / "provenance_manifest.json", "w", encoding="utf-8") as f:
            json.dump(provenance_manifest, f)

        # 4. Perform concrete lookup mappings
        entity_origin = lookup_service.get_entity_origin(run_id, "1")
        assert entity_origin is not None
        assert entity_origin["element_id"] == "citizen_group"
        assert entity_origin["source_module"] == "core_town"

        building_origin = lookup_service.get_building_origin(run_id, "20000")
        assert building_origin is not None
        assert building_origin["element_id"] == "tavern"
        assert building_origin["source_module"] == "core_town"

        resource_origin = lookup_service.get_resource_origin(run_id, "10000")
        assert resource_origin is not None
        assert resource_origin["element_id"] == "ore_node"
        assert resource_origin["source_module"] == "wilderness_layout"

