import os
import pytest

def test_hot_path_safety_contract_doc_exists():
    contract_path = "docs/architecture/observability_hot_path_safety_contract.md"
    assert os.path.exists(contract_path), f"Safety contract {contract_path} does not exist"
    
    with open(contract_path, "r", encoding="utf-8") as f:
        content = f.read().lower()
        
    assert "allowed" in content
    assert "forbidden" in content
    assert "safety contract" in content

def test_hot_path_safety_contract_imports():
    hot_path_paths = [
        "src/engine/",
        "src/observability/config.py",
        "src/observability/event_extractor.py",
        "src/observability/event_recorder.py"
    ]
    
    # We check that there are no static imports of post-run/async components in the hot path
    # Check for actual module names or class names rather than lowercase flag names
    forbidden_terms = [
        "EpisodeDetector",
        "ScorecardGenerator",
        "RunComparisonAnalyzer",
        "CohortAnalysisAnalyzer",
        "InsightGenerator"
    ]
    
    for path in hot_path_paths:
        full_path = os.path.abspath(path)
        if not os.path.exists(full_path):
            continue
            
        if os.path.isdir(full_path):
            files_to_check = []
            for root, _, files in os.walk(full_path):
                for file in files:
                    if file.endswith(".py") and not file.startswith("__"):
                        files_to_check.append(os.path.join(root, file))
        else:
            files_to_check = [full_path]
            
        for file_path in files_to_check:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            for term in forbidden_terms:
                assert term not in content, f"Forbidden heavy analyzer reference/import '{term}' found in hot path file {file_path}"

