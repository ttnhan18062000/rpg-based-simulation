import os
import sys
import pytest

def test_observability_boundaries_doc_exists():
    doc_path = "docs/architecture/observability_behavior_profiling_boundary.md"
    assert os.path.exists(doc_path), f"Boundary document {doc_path} does not exist"
    
    with open(doc_path, "r", encoding="utf-8") as f:
        content = f.read().lower()
        
    # Check that it defines mandatory terms
    required_terms = [
        "runtime profiling",
        "raw simulation event",
        "behavior event",
        "behavior timeline",
        "behavior episode",
        "behavior metric",
        "behavior finding",
        "behavior insight",
        "scorecard",
        "run comparison"
    ]
    for term in required_terms:
        assert term in content, f"Boundary document is missing definition for term: {term}"

def test_hot_path_does_not_import_heavy_analyzers():
    # Define hot path modules/directories
    hot_path_paths = [
        "src/engine/",
        "src/observability/config.py",
        "src/observability/event_extractor.py",
        "src/observability/event_recorder.py"
    ]
    
    # Define forbidden heavy analysis import patterns
    forbidden_import_substrings = [
        "observability.anomaly",
        "observability.cognition",
        "observability.reporting"
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
                
            for forbidden in forbidden_import_substrings:
                # Basic check for direct or from imports
                assert f"import {forbidden}" not in content, f"Forbidden import '{forbidden}' found in hot path file {file_path}"
                assert f"from {forbidden}" not in content, f"Forbidden import '{forbidden}' found in hot path file {file_path}"
