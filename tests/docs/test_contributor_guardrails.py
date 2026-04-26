import pytest
import json
import os
import re

MANIFEST_PATH = "docs/engine/manifest.json"

def load_manifest():
    with open(MANIFEST_PATH, "r") as f:
        return json.load(f)

def test_forbidden_terminology():
    """
    Search all Markdown files in docs/engine for vanity/universal claims.
    """
    manifest = load_manifest()
    forbidden = manifest["forbidden_terms"]
    
    docs_dir = "docs/engine"
    for root, _, files in os.walk(docs_dir):
        for file in files:
            if not file.endswith(".md"):
                continue
                
            path = os.path.join(root, file)
            with open(path, "r") as f:
                content = f.read().lower()
                
            for term in forbidden:
                assert term not in content, f"Forbidden term '{term}' found in {path}"

def test_extension_templates_present():
    """
    Verify that the Engineering Playbook contains mandatory extension templates.
    """
    playbook_path = "docs/engine/engineering_playbook_m10.md"
    with open(playbook_path, "r") as f:
        content = f.read()
        
    assert "## Extension Templates" in content
    assert "### Runtime Profile Template" in content
    assert "### Certification Scenario Template" in content

def test_contributing_guide_guardrails():
    """
    Verify root CONTRIBUTING.md contains critical safety pillars.
    """
    contrib_path = "CONTRIBUTING.md"
    assert os.path.exists(contrib_path)
    
    with open(contrib_path, "r") as f:
        content = f.read()
        
    pillars = [
        "Unbounded Collections",
        "Universal Performance Claims",
        "Alternate Authority Paths",
        "Implicit Dependencies",
        "Telemetry Leakage"
    ]
    for pillar in pillars:
        assert pillar in content, f"Contributing guide missing safety pillar: {pillar}"
