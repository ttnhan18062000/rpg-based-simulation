import pytest
import re
from pathlib import Path
from src.api.schemas import StrategicStateSchema, CognitionCapacitySchema, CognitionBudgetUsageSchema, CognitionOverloadSchema

def test_ui_contract_alignment():
    """Verify that every field in bounded_cognition_ui_contract.md exists in Pydantic schemas."""
    doc_path = Path("docs/bounded_cognition_ui_contract.md")
    assert doc_path.exists()
    
    content = doc_path.read_text()
    
    # Extract field names from markdown tables
    # Simplified regex to find | field_name | type |
    fields_in_doc = re.findall(r"\|\s*`([^`]+)`\s*\|\s*`[^`]+`\s*\|", content)
    
    # Collect all fields in relevant schemas
    schema_fields = set()
    schema_fields.update(CognitionCapacitySchema.model_fields.keys())
    schema_fields.update(CognitionBudgetUsageSchema.model_fields.keys())
    schema_fields.update(CognitionOverloadSchema.model_fields.keys())
    
    # Also check StrategicStateSchema wrapper fields
    schema_fields.update(StrategicStateSchema.model_fields.keys())
    
    for f in fields_in_doc:
        # Some fields might be descriptive labels in the table, 
        # but the document uses backticks for exact field names.
        assert f in schema_fields, f"Field '{f}' documented in UI contract but missing in schemas."

def test_feature_spec_replay_alignment():
    """Verify that replay fields mentioned in feature spec are present in recorder."""
    doc_path = Path("docs/bounded_cognition_feature_spec.md")
    content = doc_path.read_text()
    
    # Look for the Replay & Export Exposure section
    fields_to_check = [
        "active_slice_used",
        "is_overloaded",
        "dropped_candidates_count"
    ]
    
    from src.utils.replay import ReplayRecorder
    import inspect
    
    # Check ReplayRecorder.record_tick implementation source code for field names
    source = inspect.getsource(ReplayRecorder.record_tick)
    for f in fields_to_check:
        assert f in source, f"Replay field '{f}' mentioned in feature spec but missing in ReplayRecorder."

def test_feature_spec_graph_export_alignment():
    """Verify that graph export fields mentioned in feature spec are present in exporter."""
    doc_path = Path("docs/bounded_cognition_feature_spec.md")
    content = doc_path.read_text()
    
    # Attributes mentioned for the cognition_profile node
    fields_to_check = [
        "planning_budget",
        "judgment_stability",
        "evidence_quality",
        "social_bandwidth",
        "active_slice_limit",
        "active_slice_used",
        "is_overloaded",
        "overload_score"
    ]
    
    from src.core.logic.cognition_graph_exporter import EntityCognitionExporter
    import inspect
    
    source = inspect.getsource(EntityCognitionExporter.export)
    for f in fields_to_check:
        assert f in source, f"Graph field '{f}' mentioned in feature spec but missing in EntityCognitionExporter."

def test_test_matrix_existence():
    """Verify that all test modules mentioned in test_matrix.md actually exist."""
    doc_path = Path("docs/bounded_cognition_test_matrix.md")
    content = doc_path.read_text()
    
    # Find patterns like .py
    test_modules = re.findall(r"[\w_]+\.py", content)
    
    for module in test_modules:
        # Search for this module in tests/
        found = list(Path("tests").rglob(module))
        assert len(found) > 0, f"Test module '{module}' mentioned in test matrix but not found in tests/ directory."

def test_populated_artifact_consistency():
    """Verify that a live HeadlessRunner execution produces populated and consistent artifacts.
    [TRACK 1 HARDENING]
    """
    from src.testing.headless_regression_runner import HeadlessRunner
    from src.testing.assertions import load_json, assert_strategic_consistency
    
    runner = HeadlessRunner(output_root="logs/regression/integrity_check")
    result = runner.run(seed=123, ticks=2)
    
    assert result.success
    replay_data = load_json(result.replay_path)
    
    # 1. Verify that Replay is actually populated with strategy data
    found_strategy = False
    for entity in replay_data["ticks"][-1]["entities"]:
        if "strategy" in entity:
            strat = entity["strategy"]
            # Check for core cognition fields that MUST be populated
            assert strat["last_capacity_profile"]["planning_budget"] > 0
            assert "active_slice_used" in strat
            assert "is_overloaded" in strat
            found_strategy = True
            break
    
    assert found_strategy, "No strategy data found in replay entities"
    
    # 2. Verify Graph Consistency (Relational Parity)
    cognition_graphs = {}
    for eid, gpath in result.cognition_paths.items():
        cognition_graphs[eid] = load_json(gpath)
        
    # This calls our repaired assert_strategic_consistency
    assert_strategic_consistency(replay_data, cognition_graphs)

def test_truth_surface_parity():
    """Verify that Replay, API Schema, and Cognition Graph maintain strict parity.
    [TRUTH SURFACE OWNERSHIP PROOF]
    """
    from src.core.models.world_state import WorldState
    from src.core.entities.entity import Entity
    from src.config import SimulationConfig
    from src.platform.rng import DeterministicRNG
    from src.core.world.grid import Grid
    from src.platform.spatial_hash import SpatialHash
    from src.api.presenters.entity_presenter import EntityPresenter
    from src.core.logic.cognition_graph_exporter import EntityCognitionExporter
    from src.utils.replay import ReplayRecorder
    from src.core.models.cognition import CognitionCapacityProfile
    
    # 1. Setup minimal state
    cfg = SimulationConfig()
    rng = DeterministicRNG(42)
    grid = Grid(10, 10)
    spatial = SpatialHash(8)
    world = WorldState(seed=42, grid=grid, spatial_index=spatial)
    
    hero = Entity(id=1, kind="hero")
    # Manually populate some strategic usage data
    hero.mind.strategic.last_capacity_profile = CognitionCapacityProfile(
        planning_budget=100, judgment_stability=0.8, evidence_quality=0.9, social_bandwidth=5,
        detour_depth_limit=2, active_slice_limit=50, concern_intake_limit=10, 
        lead_retention_limit=5, candidate_zone_limit=5, ally_evaluation_limit=5,
        blocker_resolution_patience=0.5, resume_reliability=0.8, interruption_resistance=0.7,
        abandonment_threshold_mod=1.0, contradiction_sensitivity=0.6, source_trust_learning_rate=0.1
    )
    hero.mind.strategic.active_slice_used = 42
    hero.mind.strategic.dropped_candidates_count = 7
    hero.mind.strategic.is_overloaded = True
    hero.mind.strategic.primary_overload_source = "complexity"
    hero.mind.strategic.last_overload_tick = 10
    
    world.add_entity(hero)
    
    # 2. Extract from API Presenter
    api_out = EntityPresenter.to_full_schema(hero, world=world)
    api_strat = api_out.strategy
    
    # 3. Extract from Replay Recorder
    recorder = ReplayRecorder("dummy.json", seed=42)
    recorder.record_tick(tick=10, applied_actions=[], world=world)
    replay_tick = recorder._ticks[0]
    replay_strat = replay_tick["entities"][0]["strategy"]
    
    # 4. Extract from Graph Exporter
    graph = EntityCognitionExporter.export(hero, tick=10)
    cp_node = next(n for n in graph.nodes if n.kind == "cognition_profile")
    graph_attr = cp_node.attributes
    
    # 5. CROSS-SURFACE ASSERTIONS
    
    # Planning Budget
    assert api_strat.capacity.planning_budget == 100
    assert replay_strat["last_capacity_profile"]["planning_budget"] == 100
    assert graph_attr["planning_budget"] == 100
    
    # Usage
    assert api_strat.usage.active_slice_used == 42
    assert replay_strat["active_slice_used"] == 42
    assert graph_attr["active_slice_used"] == 42
    
    # Dropped Candidates (Mapping check)
    assert api_strat.usage.dropped_candidates_count == 7
    assert replay_strat["dropped_candidates_count"] == 7
    assert graph_attr["dropped_candidates"] == 7 # Re-mapped in exporter
    
    # Overload
    assert api_strat.overload.is_overloaded is True
    assert replay_strat["is_overloaded"] is True
    assert graph_attr["is_overloaded"] is True
    
    # Overload Source
    assert api_strat.overload.primary_overload_source == "complexity"
    assert replay_strat["primary_overload_source"] == "complexity"
    assert graph_attr["primary_overload_source"] == "complexity"
    
    # Overload Tick
    assert api_strat.overload.last_overload_tick == 10
    assert replay_strat["last_overload_tick"] == 10
    assert graph_attr["last_overload_tick"] == 10

def test_documentation_alignment():
    """Verify that documented fields in intel_capacity_implementation_updated.md are real.
    [MILESTONE 8 PROOF]
    """
    import os
    doc_path = "docs/archive/intel_capacity_implementation_updated.md"
    assert os.path.exists(doc_path), f"Documentation missing: {doc_path}"
    
    with open(doc_path, "r") as f:
        content = f.read()
    
    # Verify that we've documented the fields we just fixed/aligned
    required_mentions = [
        "primary_overload_source",
        "last_overload_tick",
        "planning_budget",
        "active_slice_used",
        "dropped_candidates_count"
    ]
    
    for field in required_mentions:
        assert field in content, f"Field {field} should be documented in {doc_path}"
    
    # Verify that Milestone 6, 7, and 8 sections exist
    assert "## Milestone 6" in content
    assert "## Milestone 7" in content
    assert "## Milestone 8" in content
