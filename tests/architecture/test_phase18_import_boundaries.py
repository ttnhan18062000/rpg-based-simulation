import pytest
import os
import re

def test_entity_models_do_not_import_domain_services():
    # Enforce static analysis check: src/core/ must never import src/domains/
    core_dir = "src/core"
    for root, _, files in os.walk(core_dir):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                    assert "import src.domains" not in content, f"Violation: core file {path} imports domain services!"
                    assert "from src.domains" not in content, f"Violation: core file {path} imports domain services!"
