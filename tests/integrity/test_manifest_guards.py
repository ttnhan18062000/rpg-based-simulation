import pytest
import json
import os
from src.core.governance import RuntimeMode
from src.certification.models import FailureKind, HardwareClass
from src.certification.scenarios import build_scenario_state

MANIFEST_PATH = "docs/engine/manifest.json"

def load_manifest():
    with open(MANIFEST_PATH, "r") as f:
        return json.load(f)

def test_governance_enum_sync():
    """
    STRICT LAW: manifest.json 'RuntimeMode' must match src.core.governance.RuntimeMode.
    """
    manifest = load_manifest()
    monitored = manifest["monitored_terminology"]
    
    actual_modes = {m.name for m in RuntimeMode}
    manifest_modes = set(monitored["RuntimeMode"])
    
    # Check for missing modes in manifest
    missing_in_manifest = actual_modes - manifest_modes
    assert not missing_in_manifest, f"STALE MANIFEST: RuntimeMode(s) {missing_in_manifest} missing from manifest.json"
    
    # Check for stale modes in manifest (defined in manifest but not in code)
    stale_in_manifest = manifest_modes - actual_modes
    assert not stale_in_manifest, f"STALE MANIFEST: manifest.json contains non-existent RuntimeMode(s) {stale_in_manifest}"

def test_certification_enum_sync():
    """
    STRICT LAW: manifest.json 'FailureKind' and 'HardwareClass' must match src.certification.models.
    """
    manifest = load_manifest()
    monitored = manifest["monitored_terminology"]
    
    # FailureKind
    actual_failures = {f.name for f in FailureKind}
    manifest_failures = set(monitored["FailureKind"])
    
    missing_failures = actual_failures - manifest_failures
    assert not missing_failures, f"STALE MANIFEST: FailureKind(s) {missing_failures} missing from manifest.json"
    
    stale_failures = manifest_failures - actual_failures
    assert not stale_failures, f"STALE MANIFEST: manifest.json contains non-existent FailureKind(s) {stale_failures}"
    
    # HardwareClass
    actual_hw = {h.name for h in HardwareClass}
    manifest_hw = {h.upper() for h in monitored["HardwareClass"]}
    
    missing_hw = actual_hw - manifest_hw
    # Note: HardwareClass Enum uses CLASS_A, CLASS_B, manifest uses class_a, class_b
    assert not missing_hw, f"STALE MANIFEST: HardwareClass(es) {missing_hw} missing from manifest.json"

def test_scenario_registration_integrity():
    """
    LAW: Every scenario listed as a 'required_scenario' in the manifest 
    must be buildable by the certification scenarios factory.
    """
    manifest = load_manifest()
    required_scenarios = manifest["declared_release_targets"]["required_scenarios"]
    
    for sid in required_scenarios:
        try:
            state = build_scenario_state(sid)
            assert state is not None, f"SCENARIO GAP: Factory returned None for required scenario {sid}"
        except Exception as e:
            pytest.fail(f"SCENARIO GAP: Required scenario {sid} failed to build in factory. Error: {str(e)}")

def test_forbidden_terminology_guard():
    """
    LAW: Phase 5 support docs must not use forbidden 'overclaim' terminology.
    """
    manifest = load_manifest()
    forbidden = manifest.get("forbidden_terms", [])
    
    # Check the support package specifically
    package_path = "docs/engine/supported_progression_package_phase5.md"
    if not os.path.exists(package_path):
        pytest.skip("Phase 5 package missing, skipping forbidden term check.")
        
    with open(package_path, "r") as f:
        content = f.read().lower()
        
    for term in forbidden:
        assert term.lower() not in content, f"OVERCLAIM DETECTED: Phase 5 package uses forbidden term: '{term}'"
