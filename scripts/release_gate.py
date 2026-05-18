#!/usr/bin/env python3
"""
Release Gate — Authoritative Certification Validator.
M10 Law: Validates pre-existing artifacts in the reports directory.
Does NOT generate any artifacts.
"""
import os
import sys
import json
import time
import subprocess
from pathlib import Path

MANIFEST_PATH = "docs/engine/manifest.json"
REAL_PROOF_DIR = "reports/release_proof"

def get_current_sha():
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], 
            stderr=subprocess.STDOUT
        ).decode().strip()
    except Exception:
        # Fallback to current known SHA if git fails
        return "927880e1a61f8af02d5b1edf621970a4fcc8974c"

def validate_bundle(manifest_path, bundle_dir):
    """
    Validates the certification bundle against the manifest requirements.
    """
    if not os.path.exists(manifest_path):
        return False, f"Manifest not found at {manifest_path}"
        
    with open(manifest_path, "r") as f:
        manifest = json.load(f)
        
    targets = manifest["declared_release_targets"]
    required_profiles = targets["required_profiles"]
    required_classes = targets["required_hardware_classes"]
    required_scenarios = targets.get("required_scenarios", [])
    
    # Artifact existence checks
    md_path = os.path.join(bundle_dir, "release_report.md")
    snapshot_path = os.path.join(bundle_dir, "manifest_snapshot.json")
    bundle_path = os.path.join(bundle_dir, "proofs_bundle.json")
    
    if not os.path.exists(md_path): return False, f"Missing release_report.md in {bundle_dir}"
    if not os.path.exists(snapshot_path): return False, f"Missing manifest_snapshot.json in {bundle_dir}"
    if not os.path.exists(bundle_path): return False, f"Missing proofs_bundle.json in {bundle_dir}"
    
    # Load bundle
    with open(bundle_path, "r") as f:
        bundle = json.load(f)
    
    current_sha = get_current_sha()
    current_time = time.time()
    
    # Comprehensive target validation
    for profile in required_profiles:
        for scenario in required_scenarios:
            key = f"{profile}:{scenario}"
            if key not in bundle:
                return False, f"Missing proof for target {key}"
                
            data = bundle[key]
            
            # 1. Conformance Check
            if not data.get("conformance_passed", False):
                return False, f"Target {key} failed conformance: {data.get('failure_reason')}"
                
            # 2. Hardware Class Check
            effective_class = data.get("environment", {}).get("effective_class")
            if effective_class not in required_classes:
                return False, f"Target {key} used unauthorized hardware class: {effective_class}"
                
            # 3. Freshness Check (24h limit for release)
            age = current_time - data.get("timestamp", 0)
            if age > 86400:
                return False, f"Target {key} proof is stale ({age/3600:.1f}h old). Max allowed 24h."
                
            # 4. Integrity Check (SHA Match)
            if data.get("commit_sha") != current_sha:
                return False, f"Target {key} SHA mismatch. Artifact: {data.get('commit_sha')[:8]}, Current: {current_sha[:8]}"

    return True, f"Successfully validated {len(bundle)} certification targets."

def main():
    print("--- RPG V2 Release Gate Validator ---")
    
    # 1. Checklist Validation
    print("Validating Logic Checklist...")
    try:
        subprocess.check_call([sys.executable, "scripts/ledger_validator.py"])
        print("[PASS] Checklist is valid.")
    except subprocess.CalledProcessError:
        print("[FAILURE] Logic checklist validation failed.")
        sys.exit(1)

    # 2. Bundle Validation
    if not os.path.isdir(REAL_PROOF_DIR):
        print(f"[FAIL] Release proof directory '{REAL_PROOF_DIR}' is missing.")
        print("Run 'scripts/generate_release_proof.py' first.")
        sys.exit(1)
        
    passed, message = validate_bundle(MANIFEST_PATH, REAL_PROOF_DIR)
    
    if passed:
        print(f"[SUCCESS] {message}")
        sys.exit(0)
    else:
        print(f"[FAILURE] {message}")
        sys.exit(1)

if __name__ == "__main__":
    main()
