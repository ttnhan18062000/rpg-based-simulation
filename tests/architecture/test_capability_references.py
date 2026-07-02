"""Architecture guard: capability IDs in the registry are unique."""
from pathlib import Path

import yaml


def test_capability_ids_are_unique():
    registry_path = Path("docs/engine/capability_registry.yaml")
    assert registry_path.exists(), "capability_registry.yaml must exist"
    with open(registry_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    ids = [e["capability_id"] for e in data.get("capabilities", [])]
    duplicates = {cid for cid in ids if ids.count(cid) > 1}
    assert not duplicates, f"Duplicate capability_ids in registry: {duplicates}"
