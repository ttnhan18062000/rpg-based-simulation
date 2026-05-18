import pytest
import json
import os
import re

MANIFEST_PATH = "docs/engine/manifest.json"

def load_manifest():
    with open(MANIFEST_PATH, "r") as f:
        return json.load(f)

def test_mandatory_doc_existence():
    """
    STRICT LAW: Every document listed in manifest.json must exist in the workspace.
    """
    manifest = load_manifest()
    for doc in manifest["mandatory_documents"]:
        path = doc["path"]
        assert os.path.exists(path), f"TRUTH GAP: Mandatory documentation missing: {path}"

def test_doc_header_compliance():
    """
    STRICT LAW: Mandatory docs must follow the structure required by the manifest.
    """
    manifest = load_manifest()
    for doc in manifest["mandatory_documents"]:
        path = doc["path"]
        required_headers = doc.get("required_headers", [])
        
        if not os.path.exists(path):
            continue
            
        with open(path, "r") as f:
            content = f.read()
            
        for header in required_headers:
            # We look for ## HeaderName or ## 1. HeaderName
            pattern = rf"^##\s+(?:\d+\.\s+)?{re.escape(header)}\b"
            match = re.search(pattern, content, re.MULTILINE | re.IGNORECASE)
            assert match, f"STRUCTURAL DRIFT: Document {path} missing required header: ## {header}"

def test_no_broken_internal_links():
    """
    LAW: Documentation must have valid local links.
    Broken links erode the truth surface.
    """
    manifest = load_manifest()
    # Check all mandatory docs and the Phase 5 package
    docs_to_check = [d["path"] for d in manifest["mandatory_documents"]]
    docs_to_check.append("docs/engine/supported_progression_package_phase5.md")
    
    for path in docs_to_check:
        if not os.path.exists(path):
            continue
            
        base_dir = os.path.dirname(path)
        with open(path, "r") as f:
            content = f.read()
            
        # Match [label](relative/path/to/file.md) or [label](file:///absolute/path)
        links = re.findall(r"\[.*?\]\((.*?)\)", content)
        for link in links:
            if link.startswith("http"):
                continue
            
            # Normalize link
            clean_link = link.replace("file://", "").split("#")[0]
            
            if clean_link.startswith("/"):
                # Avoid doubling the base path if already absolute
                if clean_link.startswith("/home/vboxuser/Work/rpg-based-simulation"):
                    link_path = clean_link
                else:
                    link_path = os.path.join("/home/vboxuser/Work/rpg-based-simulation", clean_link.lstrip("/"))
            else:
                link_path = os.path.join(base_dir, clean_link)
            
            # Check existence if it looks like a local coordinate (not empty, not just a tag)
            if clean_link and not clean_link.startswith("mailto:"):
                assert os.path.exists(link_path), f"BROKEN LINK: {path} links to non-existent {link} (Resolved: {link_path})"
