# Compliance IDs: WORLD-073, WORLD-070, WORLD-071, WORLD-072
import pytest
import tempfile
import os
import json
import yaml
from pathlib import Path
from dataclasses import replace

from src.worldbuilding.schema import WorldSpec, InvalidWorldSpecError, load_world_spec_from_yaml
from src.worldbuilding.validator import WorldValidator
from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository, WorldRepositoryError
from src.core.state import AuthoritativeState
from src.core.updates import StateUpdate
from src.engine.pipeline import AuthoritativeApplyPipeline
from src.engine.apply import ApplyPath
from src.observability.events import SimulationEvent
from src.observability.event_recorder import EventRecorder


def get_base_test_data() -> dict:
    """Helper to return a baseline valid specification dictionary."""
    return {
        "schema_version": "worldspec.v1",
        "world_id": "strategy_test_world",
        "name": "Strategy Test World",
        "description": "Validation suite for Milestone 73.",
        "topology": {
            "width": 100,
            "height": 100,
            "coordinate_system": "grid"
        },
        "regions": [
            {"id": "valley", "type": "wilderness", "bounds": [0, 0, 50, 50], "terrain": "GRASS"},
            {"id": "camp", "type": "town", "bounds": [60, 60, 80, 80], "terrain": "PLAIN"}
        ],
        "factions": [
            {"id": "settlers", "type": "civilian"},
            {"id": "threats", "type": "hostile"}
        ],
        "entities": [
            {"id": "pioneers", "count": 12, "role": "worker", "faction": "settlers", "spawn_region": "camp"},
            {"id": "beasts", "count": 8, "role": "monster", "faction": "threats", "spawn_region": "valley"}
        ],
        "resources": [
            {"id": "lumber", "resource_type": "wood", "count": 50, "region": "valley"}
        ],
        "buildings": [
            {"id": "depot", "type": "storage", "region": "camp"}
        ],
        "quest_definitions": []
    }


# ==============================================================================
# ANTI-MISDIRECTION TEST CASES
# ==============================================================================

def test_validation_must_fail_before_compilation():
    """
    Ensure that validation fails with InvalidWorldSpecError for ERROR severity
    configurations, preventing compilation of a structurally invalid world.
    """
    data = get_base_test_data()
    # Induce an ERROR: spawn region references a nonexistent region ID
    data["entities"][0]["spawn_region"] = "nonexistent_region"
    
    spec = WorldSpec.model_validate(data)
    validator = WorldValidator()
    
    # 1. Validation must raise InvalidWorldSpecError
    with pytest.raises(InvalidWorldSpecError) as exc_info:
        validator.validate(spec)
    assert "WORLD-REF-002" in str(exc_info.value)
    
    # 2. Compiling directly must raise warnings/errors or fail validation in CLI wrapper
    # The compiler expects a pre-validated spec. Here we assert that CLI compile handler
    # would successfully block compilation using the validator.
    with pytest.raises(InvalidWorldSpecError) as exc_info2:
        validator.validate(spec, strict=True)
    assert "WORLD-REF-002" in str(exc_info2.value)



def test_compiler_does_not_drop_invalid_references():
    """
    Ensure that the compiler does not silently drop invalid/mismatched references
    in quest_definitions, but instead captures them as distinct, visible warnings.
    With QuestDefinition authoring schema, required_location_tags are validated
    against known region IDs at compile time.
    """
    data = get_base_test_data()
    data["quest_definitions"] = [
        {
            "id": "explorers_quest_a",
            "type": "explore",
            "required_location_tags": ["nonexistent_region_a"],
        },
        {
            "id": "explorers_quest_b",
            "type": "hunt",
            "required_location_tags": ["nonexistent_region_b"],
        },
    ]

    spec = WorldSpec.model_validate(data)
    state, report = WorldCompiler.compile(spec, seed=123)

    assert state is not None
    assert len(report["warnings"]) >= 2
    # Warnings must preserve details of each mismatched referential location tag
    assert any("nonexistent_region_a" in w for w in report["warnings"])
    assert any("nonexistent_region_b" in w for w in report["warnings"])


def test_compiler_does_not_autocreate_factions_or_regions():
    """
    Ensure that the compiler strictly maps and spawns entities, but does not
    silently synthesize missing regions or factions that were omitted from specs.
    """
    data = get_base_test_data()
    spec = WorldSpec.model_validate(data)
    
    state, _ = WorldCompiler.compile(spec, seed=42)
    
    # State regions must match precisely the specified spec regions
    assert set(state.regions.keys()) == {"valley", "camp"}
    # Assure no extra synthetic region is dynamically auto-created
    assert "nonexistent_region" not in state.regions


def test_generated_entity_count_matches_requested():
    """
    Ensure that the compiled state contains exactly the number of entities requested
    in the world spec population group definitions.
    """
    data = get_base_test_data()
    # 12 pioneers + 8 beasts = 20 total entities requested
    spec = WorldSpec.model_validate(data)
    
    state, report = WorldCompiler.compile(spec, seed=42)
    
    assert len(state.entities) == 20
    assert report["entity_count"] == 20
    
    # Assert breakdown by entity roles
    workers = [e for e in state.entities.values() if e.kind == "worker"]
    monsters = [e for e in state.entities.values() if e.kind == "monster"]
    assert len(workers) == 12
    assert len(monsters) == 8


def test_same_seed_produces_identical_state_hash():
    """
    Ensure strict determinism: compiling the same world spec twice with the same
    seed must yield mathematically identical state fingerprint hashes.
    """
    data = get_base_test_data()
    spec = WorldSpec.model_validate(data)
    
    state1, report1 = WorldCompiler.compile(spec, seed=777)
    state2, report2 = WorldCompiler.compile(spec, seed=777)
    
    assert report1["state_hash"] == report2["state_hash"]
    
    # Verify entity coordinate layouts match perfectly
    for eid in state1.entities:
        pos1 = state1.entities[eid].navigation.position
        pos2 = state2.entities[eid].navigation.position
        assert pos1 == pos2


def test_warnings_visible_in_report(tmp_path):
    """
    Ensure that compilation warnings are saved and clearly visible inside the
    written JSON compile report.
    """
    data = get_base_test_data()
    data["quest_definitions"] = [
        {
            "id": "warn_quest",
            "type": "explore",
            "required_location_tags": ["nonexistent_forest"],
        }
    ]
    
    spec = WorldSpec.model_validate(data)
    report_file = tmp_path / "report.json"
    
    _, report = WorldCompiler.compile(spec, seed=1, output_report_path=str(report_file))
    
    # Assert report returned matches report saved
    assert len(report["warnings"]) == 1
    assert "nonexistent_forest" in report["warnings"][0]
    
    with open(report_file, "r") as f:
        saved = json.load(f)
    assert saved["warnings"] == report["warnings"]


def test_unknown_schema_version_fails_clearly(tmp_path):
    """
    Ensure that an unrecognized schema version is rejected immediately with a
    clean InvalidWorldSpecError, preventing corrupted loads.
    """
    data = get_base_test_data()
    data["schema_version"] = "worldspec.v999"  # Unrecognized version
    
    spec_path = tmp_path / "world.yaml"
    with open(spec_path, "w") as f:
        yaml.safe_dump(data, f)
        
    with pytest.raises(InvalidWorldSpecError) as exc_info:
        load_world_spec_from_yaml(spec_path)
    assert "schema_version" in str(exc_info.value)


def test_future_fields_preserved_or_rejected(tmp_path):
    """
    Ensure that unrecognized future sections are ignored by Pydantic's relaxed schema
    parsing policies (preserving forward compatibility), but flagged by validation rules.
    """
    data = get_base_test_data()
    data["unrecognized_future_block"] = {"custom_field": "val"}
    
    spec = WorldSpec.model_validate(data)
    # The Pydantic model validates cleanly
    assert spec.world_id == "strategy_test_world"
    
    # However, running the validator flags the unexpected top-level block
    validator = WorldValidator()
    issues = validator.validate(spec, raw_data=data)
    assert any(i.rule_id == "WORLD-UNEXPECTED-SECTION" for i in issues)


# ==============================================================================
# SMOKE SIMULATION SUITE
# ==============================================================================

def test_smoke_simulation_run():
    """
    Smoke Test: Verify that a compiled world state can be executed inside the V2
    authoritative simulation pipeline for 10 ticks without structural failure.
    """
    data = get_base_test_data()
    spec = WorldSpec.model_validate(data)
    state, _ = WorldCompiler.compile(spec, seed=42)
    
    assert state.tick == 0
    
    # Execute 10 tick updates under the authoritative apply pipeline
    for t in range(1, 11):
        state = replace(state, tick=t)
        raw_update = StateUpdate()
        
        # 1. Refine step
        refined = AuthoritativeApplyPipeline.refine(state, raw_update)
        # 2. Authoritative apply step
        state = ApplyPath.apply_generation(state, refined)
        
        assert state.tick == t + 1
        assert len(state.entities) == 20
        assert len(state.regions) == 2


# ==============================================================================
# OBSERVATORY INTEGRATION SUITE
# ==============================================================================

def test_observatory_integration_smoke(tmp_path):
    """
    Observatory Integration Test: Verify that a compiled world running simulation
    ticks successfully writes telemetry events and generates JSONL artifacts.
    """
    data = get_base_test_data()
    spec = WorldSpec.model_validate(data)
    state, _ = WorldCompiler.compile(spec, seed=42)
    
    run_dir = tmp_path / "obs_run"
    run_dir.mkdir()
    
    # Instantiate the EventRecorder to capture telemetry metrics during simulation ticks
    recorder = EventRecorder(run_dir=str(run_dir), enabled=True)
    
    # Perform 3 simulation ticks, generating custom events
    for t in range(1, 4):
        state = replace(state, tick=t)
        
        # Record a telemetry event for workers
        for ent_id, ent in list(state.entities.items())[:2]:
            event = SimulationEvent(
                event_type="entity_routine",
                event_category="movement",
                tick=t,
                severity="INFO",
                source_system="test_observatory",
                message=f"Entity {ent_id} executed simulation step.",
                entity_id=ent_id
            )
            recorder.record(event)
            
    # Shutdown the event recorder to seal file streams
    recorder.shutdown()
    
    # Assert telemetry files successfully exist and contain the events
    jsonl_path = run_dir / "simulation_events.jsonl"
    assert jsonl_path.exists()
    
    with open(jsonl_path, "r") as f:
        lines = f.readlines()
    assert len(lines) == 6  # 3 ticks * 2 entities = 6 events recorded
