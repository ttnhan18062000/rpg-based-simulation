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
    from src_v2.core.governance import RuntimeMode
    from src_v2.certification.models import HardwareClass, FailureKind
    
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

def test_link_integrity():
    """
    Basic check for local file links in documentation.
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
                # For this check, we treat / as project root (vboxuser context)
                # But actually, links in these docs are usually relative or file:///home/...
                if "home/vboxuser/Work/rpg-based-simulation/" in clean_link:
                    link_path = clean_link
                else:
                    continue # Skip strange absolute paths
            else:
                link_path = os.path.join(base_dir, clean_link)
                # Normalize (remove #L123 fragments)
                link_path = link_path.split("#")[0]
            
            if link_path.endswith(".md") or link_path.endswith(".json"):
                 # We only check internal md/json links
                 assert os.path.exists(link_path), f"Broken link in {path}: {link}"
