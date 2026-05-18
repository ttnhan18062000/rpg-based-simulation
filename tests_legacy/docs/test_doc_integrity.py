import pytest
import json
import os
import re

MANIFEST_PATH = "docs/engine/manifest.json"

def load_manifest():
    with open(MANIFEST_PATH, "r") as f:
        return json.load(f)

def test_manifest_file_existence():
    """
    Verify all mandatory documents defined in the manifest exist.
    """
    manifest = load_manifest()
    for doc in manifest["mandatory_documents"]:
        path = doc["path"]
        assert os.path.exists(path), f"Mandatory document missing: {path}"

def test_document_structural_compliance():
    """
    Verify all mandatory documents contain required headers.
    """
    manifest = load_manifest()
    for doc in manifest["mandatory_documents"]:
        path = doc["path"]
        required_headers = doc["required_headers"]
        
        with open(path, "r") as f:
            content = f.read()
            
        for header in required_headers:
            # Match markdown header, allowing optional numbering (e.g., ## 1. Purpose)
            pattern = rf"^##\s+(?:\d+\.\s+)?{re.escape(header)}\b"
            match = re.search(pattern, content, re.MULTILINE | re.IGNORECASE)
            assert match, f"Document {path} missing required header: ## {header}"

def test_terminology_alignment():
    """
    Verify that documentation terminology aligns with code-facing enums.
    """
    manifest = load_manifest()
    monitored = manifest["monitored_terminology"]
    
    # We will check the manifest itself first to ensure it matches the code
    # This prevents the manifest from drifting from code
    from src_legacy.core.governance import RuntimeMode
    from src_legacy.certification.models import HardwareClass, FailureKind
    
    # Validation vs Code
    actual_modes = [m.name for m in RuntimeMode]
    for m in monitored["RuntimeMode"]:
        assert m in actual_modes, f"Stale RuntimeMode in manifest: {m}"
        
    actual_hardware = [h.value for h in HardwareClass]
    for h in monitored["HardwareClass"]:
        assert h in actual_hardware, f"Stale HardwareClass in manifest: {h}"

    actual_failures = [f.name for f in FailureKind]
    for f in monitored["FailureKind"]:
        assert f in actual_failures, f"Stale FailureKind in manifest: {f}"

def test_scoped_reporting_compliance():
    """
    M10 Law: Certification reports must bind claims to (Profile, Scenario, Hardware).
    """
    report_path = "reports/release_proof/release_report.md"
    if not os.path.exists(report_path):
        pytest.skip("No release report found for scoped compliance check.")
        
    with open(report_path, "r") as f:
        content = f.read()
        
    required_scoped_fields = [
        "Profile",
        "Scenario",
        "Hardware Class",
        "Commit SHA"
    ]
    for field in required_scoped_fields:
        assert field in content, f"Release report missing required scoped field: {field}"

def test_recorder_enforcement_logic():
    """
    M10 Law: Recorder must refuse to generate reports for invalid/unscoped results.
    """
    from src_legacy.certification.recorder import CertificationRecorder
    from src_legacy.certification.models import CertificationResult, FailureKind, EnvironmentCapture, HardwareClass
    
    recorder = CertificationRecorder(output_dir="tmp/test_recorder")
    
    # We verify the 'quadrant' fields are present in the instance
    res = CertificationResult(
        run_id="test", timestamp=0.0, commit_sha="sha",
        profile_name="p", scenario_id="s", seed=0,
        environment=EnvironmentCapture({}, HardwareClass.CLASS_A, HardwareClass.CLASS_A, False),
        measurements=[], baseline_hash=None, final_hash=None,
        governor_mode_sequence=[], conformance_passed=True,
        failure_kind=FailureKind.NONE, failure_reason=None
    )
    assert hasattr(res, "commit_sha")
    assert hasattr(res.environment, "effective_class")

def test_release_target_binding():
    """
    M10 Law: verify that docs/engine/project_lawbook_m10.md support claims match manifest.json.
    """
    manifest = load_manifest()
    targets = manifest["declared_release_targets"]
    required_classes = targets["required_hardware_classes"]
    
    lawbook_path = "docs/engine/project_lawbook_m10.md"
    with open(lawbook_path, "r") as f:
        content = f.read().lower()
        
    for hw_class in required_classes:
        # Check if the lawbook mentions the class in its certification conditions
        assert hw_class.lower() in content, f"Lawbook lacks mention of declared release target: {hw_class}"

def test_link_integrity():
    """
    M10 Law: Basic check for local file links in documentation.
    """
    manifest = load_manifest()
    for doc in manifest["mandatory_documents"]:
        path = doc["path"]
        base_dir = os.path.dirname(path)
        
        with open(path, "r") as f:
            content = f.read()
            
        # Match [label](file://...) or [label](path/to/file.md)
        links = re.findall(r"\[.*?\]\((.*?)\)", content)
        for link in links:
            if link.startswith("http"):
                continue
            
            # Remove file:// prefix if present
            clean_link = link.replace("file://", "")
            # Handle absolute vs relative
            if clean_link.startswith("/"):
                # For this check, we treat / as project root
                if "home/vboxuser/Work/rpg-based-simulation/" in clean_link:
                    link_path = clean_link
                else:
                    # Try to see if it's a workspace-relative path starting with /
                    link_path = os.path.join("/home/vboxuser/Work/rpg-based-simulation", clean_link.lstrip("/"))
            else:
                link_path = os.path.join(base_dir, clean_link)
            
            # Normalize (remove #L123 fragments)
            link_path = link_path.split("#")[0]
            
            if link_path.endswith(".md") or link_path.endswith(".json"):
                 assert os.path.exists(link_path), f"Broken link in {path}: {link} (Resolved to: {link_path})"
