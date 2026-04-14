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
