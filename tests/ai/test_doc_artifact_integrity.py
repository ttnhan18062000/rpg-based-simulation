import pytest
import re
from pathlib import Path
from src.testing.headless_regression_runner import HeadlessRunner
from src.testing.assertions import load_json

def test_doc_artifact_integrity():
    """Verify that documented cognition fields appear in real artifacts. [BATCH 9]"""
    doc_path = Path("docs/bounded_cognition_feature_spec.md")
    assert doc_path.exists()
    
    with open(doc_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 1. Extract capacity fields from the Data Contract table
    # Regex targets backticked identifiers in the first column of the table
    capacity_fields = re.findall(r"\| `([a-z_]+)` \|", content)
    # We expect 16 fields total in Milestone 2
    assert len(capacity_fields) >= 16, f"Expected at least 16 capacity fields in doc, found {len(capacity_fields)}"
    
    # 2. Extract usage fields from the Exposure section
    # Regex targets backticked identifiers in the Replay/Graph bullet points
    exposure_section = content.split("## Replay & Export Exposure")[-1]
    usage_fields = re.findall(r"`([a-z_]+)`", exposure_section)
    # Filtering for actual usage metrics
    expected_usage = {"active_slice_used", "is_overloaded", "dropped_candidates_count"}
    found_usage = {f for f in usage_fields if f in expected_usage}
    assert expected_usage.issubset(found_usage), f"Spec missing required usage metrics: {expected_usage - found_usage}"

    # 3. Run a simulation to generate artifacts
    # Increased ticks to ensure entities act and populate strategic state
    runner = HeadlessRunner(output_root="tests/artifacts/doc_integrity")
    result = runner.run(seed=20260415, ticks=15)
    
    assert result.success, f"Simulation failed: {result.error}"
    
    replay = load_json(result.replay_path)
    
    # Search for any entity snapshot that has acted strategically (has last_capacity_profile)
    # We scan ticks from latest to earliest to find the most populated state
    sample_strat = None
    sample_eid = None
    
    for tick_data in reversed(replay["ticks"]):
        for entity in tick_data.get("entities", []):
            strat = entity.get("strategy")
            if strat and strat.get("last_capacity_profile"):
                sample_strat = strat
                sample_eid = entity["id"]
                break
        if sample_strat:
            break
            
    assert sample_strat is not None, "No entity found with populated strategic capacity profile in replay after 15 ticks"
    
    cp = sample_strat["last_capacity_profile"]
    
    # 4. Assert Capacity Field Presence (Replay)
    for field in capacity_fields:
        assert field in cp, f"Documented capacity field '{field}' missing from replay['strategy']['last_capacity_profile']"
        
    # 5. Assert Usage Field Presence (Replay)
    for field in expected_usage:
        assert field in sample_strat, f"Documented usage field '{field}' missing from replay['strategy']"
        
    # 6. Assert Cognition Node Field Presence (Graph)
    graph_file = result.cognition_paths.get(sample_eid)
    assert graph_file is not None, f"No graph exported for entity {sample_eid}"
    graph = load_json(graph_file)
    
    nodes = graph["elements"]["nodes"]
    cp_node = next((n for n in nodes if n["data"]["kind"] == "cognition_profile"), None)
    assert cp_node is not None, f"Graph for entity {sample_eid} missing cognition_profile node"
    
    data = cp_node["data"]
    for field in capacity_fields:
        assert field in data, f"Documented capacity field '{field}' missing from cognition_profile node in graph"
        
    # Special case: dropped_candidates_count is mapped to dropped_candidates in graph
    assert "dropped_candidates" in data, "Usage field 'dropped_candidates' missing from graph node"
    assert "is_overloaded" in data, "Usage field 'is_overloaded' missing from graph node"
