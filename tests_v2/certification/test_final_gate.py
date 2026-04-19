import pytest
import json
import os
import subprocess
import time
from pathlib import Path

MANIFEST_PATH = "docs/engine/manifest.json"
PROOF_BUNDLE_DIR = "reports/release_proof"

def load_manifest():
    with open(MANIFEST_PATH, "r") as f:
        return json.load(f)

def get_current_sha():
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], 
            stderr=subprocess.STDOUT
        ).decode().strip()
    except Exception:
        return None

def test_proof_bundle_existence():
    """
    M10 Law: A release is blocked unless the Proof Bundle Directory exists.
    """
    assert os.path.isdir(PROOF_BUNDLE_DIR), "M10 Law: releases are blocked without a Proof Bundle in reports/release_proof/"

def test_proof_artifact_completeness():
    """
    M10 Law: The bundle must contain the MD report and manifest snapshot.
    Note: JSON proofs are verified in test_manifest_target_compliance.
    """
    md_path = os.path.join(PROOF_BUNDLE_DIR, "release_report.md")
    snapshot_path = os.path.join(PROOF_BUNDLE_DIR, "manifest_snapshot.json")
    
    assert os.path.exists(md_path), "Missing release_report.md"
    assert os.path.exists(snapshot_path), "Missing manifest_snapshot.json"

def test_manifest_target_compliance():
    """
    M10 Law: The gate must verify all manifest-declared release targets have passed.
    Targets include the full Matrix of (profile x scenario).
    """
    manifest = load_manifest()
    targets = manifest["declared_release_targets"]
    required_profiles = targets["required_profiles"]
    required_classes = targets["required_hardware_classes"]
    required_scenarios = targets.get("required_scenarios", [])
    
    current_sha = get_current_sha()
    
    for profile in required_profiles:
        for scenario in required_scenarios:
            json_filename = f"release_proof_{profile}_{scenario}.json"
            json_path = os.path.join(PROOF_BUNDLE_DIR, json_filename)
            
            assert os.path.exists(json_path), f"M10 Law: Missing proof for required target: profile='{profile}', scenario='{scenario}'"
            
            with open(json_path, "r") as f:
                data = json.load(f)
                
            # 1. Performance/Conformance Verification
            assert data["conformance_passed"] is True, f"Certification FAILED for {profile} x {scenario} [{data['failure_kind']}]: {data['failure_reason']}"
            
            # 2. Hardware Class Verification
            effective_class = data["environment"]["effective_class"]
            assert effective_class in required_classes, f"Certified hardware class '{effective_class}' for {profile} is not a declared release target."
            
            # 3. Freshness Verification (24h)
            stat = os.stat(json_path)
            age_seconds = time.time() - stat.st_mtime
            assert age_seconds < 86400, f"Proof artifact for {profile} x {scenario} is too old: {age_seconds/3600:.1f} hours"
            
            # 4. SHA Provenance
            if current_sha:
                assert data["commit_sha"] == current_sha, f"Stale proof artifact for {profile} x {scenario}: artifact SHA={data['commit_sha']}, current SHA={current_sha}"
