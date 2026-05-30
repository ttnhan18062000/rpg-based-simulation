# Compliance IDs: WORLD-MOD-004, WORLD-MOD-005
from __future__ import annotations

import os
import yaml
import hashlib
from typing import Dict, List, Optional, Any
from src.worldmodules.schema import WorldModuleSpec


class WorldModuleRepository:
    """
    Authoritative repository that loads and parses reusable structural layout packages
    from data/world_modules/ directories.
    """

    def __init__(self, modules_dir: str):
        self.modules_dir = modules_dir
        self.modules: Dict[str, WorldModuleSpec] = {}
        self.raw_data: Dict[str, Dict[str, Any]] = {}

    def load_all(self) -> None:
        """Discovers and parses all module YAML specifications recursively inside the directory."""
        if not os.path.exists(self.modules_dir):
            return

        for root, _, files in os.walk(self.modules_dir):
            for file in files:
                if file.endswith(".yaml") or file.endswith(".yml"):
                    self._load_module_file(os.path.join(root, file))

    def _load_module_file(self, filepath: str) -> None:
        """Helper to read, load, and validate a module specification file."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not data:
            return

        # Handle simple single definition structure or lists
        items = data if isinstance(data, list) else [data]
        for item in items:
            if not isinstance(item, dict) or "module_id" not in item:
                raise ValueError(f"Module definition in {filepath} is malformed or missing 'module_id'")

            module_id = item["module_id"]
            if module_id in self.modules:
                raise ValueError(f"Duplicate module ID '{module_id}' found in repository load pipeline.")

            validated = WorldModuleSpec(**item)
            self.modules[module_id] = validated
            self.raw_data[module_id] = item

    def get_module(self, module_id: str) -> Optional[WorldModuleSpec]:
        return self.modules.get(module_id)

    def list_modules(self) -> List[WorldModuleSpec]:
        return list(self.modules.values())

    def list_modules_by_type(self, module_type: str) -> List[WorldModuleSpec]:
        target = module_type.lower()
        return [m for m in self.modules.values() if m.module_type == target]

    def module_fingerprint(self, module_id: str) -> Optional[str]:
        """Generates a unique deterministic SHA256 checksum signature representing the loaded module content."""
        raw = self.raw_data.get(module_id)
        if not raw:
            return None
        serialized = str(sorted(raw.items()))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
