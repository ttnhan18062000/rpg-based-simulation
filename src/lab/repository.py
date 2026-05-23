# Compliance IDs: SCENARIO-007, SCENARIO-008, SCENARIO-009
from __future__ import annotations

import re
import json
import yaml
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional
from src.lab.schema import ScenarioSpec, load_scenario_spec_from_yaml, InvalidScenarioSpecError

class ScenarioRepositoryError(Exception):
    """Base exception for ScenarioRepository operations."""
    pass

class ScenarioRepository:
    """
    File-based repository layer for loading, saving, listing, and index-tracking
    scenario specifications under a safe scenarios root directory.
    """
    def __init__(self, scenarios_dir: str | Path):
        self.scenarios_dir = Path(scenarios_dir).resolve()
        self.index_path = self.scenarios_dir / "scenario_index.json"

    def _validate_scenario_id(self, scenario_id: str) -> None:
        """Enforces a strict safe pattern on scenario identifier strings."""
        if not scenario_id or not re.match(r"^[a-zA-Z0-9_-]+$", scenario_id):
            raise ValueError(f"Invalid or unsafe scenario_id pattern: '{scenario_id}'")

    def _resolve_scenario_path(self, scenario_id: str) -> Path:
        """
        Safely resolves a scenario's target folder and YAML path, blocking path traversal.
        """
        self._validate_scenario_id(scenario_id)
        target_dir = (self.scenarios_dir / scenario_id).resolve()
        
        # Verify target is strictly a descendant of scenarios_dir
        try:
            if not target_dir.is_relative_to(self.scenarios_dir) or target_dir == self.scenarios_dir:
                raise PermissionError(f"Path traversal attempt blocked for scenario_id: '{scenario_id}'")
        except ValueError as e:
            raise PermissionError(f"Path traversal attempt blocked for scenario_id: '{scenario_id}'") from e
            
        return target_dir / "scenario.yaml"

    def list_scenarios(self) -> list[str]:
        """Lists IDs of all available scenarios that have a valid directory and scenario.yaml."""
        if not self.scenarios_dir.is_dir():
            return []
        
        scenarios = []
        for path in self.scenarios_dir.iterdir():
            if path.is_dir():
                try:
                    self._validate_scenario_id(path.name)
                    if (path / "scenario.yaml").is_file():
                        scenarios.append(path.name)
                except ValueError:
                    continue
        return sorted(scenarios)

    def load_scenario(self, scenario_id: str) -> ScenarioSpec:
        """Safely loads and parses a scenario specification by its ID."""
        yaml_path = self._resolve_scenario_path(scenario_id)
        if not yaml_path.is_file():
            raise FileNotFoundError(f"Scenario file not found for scenario_id: '{scenario_id}'")
        return load_scenario_spec_from_yaml(yaml_path)

    def save_scenario(self, spec: ScenarioSpec) -> None:
        """Safely serializes and saves a scenario specification to the filesystem."""
        scenario_id = spec.scenario_id
        yaml_path = self._resolve_scenario_path(scenario_id)
        
        # Ensure parent folder exists
        yaml_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Dump to YAML safely using pure dictionaries
        data = json.loads(spec.model_dump_json())
        with open(yaml_path, "w") as f:
            yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)
            
        # Rebuild index to keep metadata synchronized
        self.rebuild_index()

    def rebuild_index(self) -> None:
        """
        Scans the scenarios directory, loads and validates each scenario,
        and saves a consolidated scenario_index.json manifest tracking tags and statuses.
        """
        self.scenarios_dir.mkdir(parents=True, exist_ok=True)
        index_data = {}
        
        scenario_ids = self.list_scenarios()
        for s_id in scenario_ids:
            try:
                spec = self.load_scenario(s_id)
                status = "VALIDATED"
            except Exception:
                status = "BROKEN"
                spec = None

            if spec:
                index_data[s_id] = {
                    "scenario_id": s_id,
                    "name": spec.name,
                    "world_id": spec.world_id,
                    "scenario_type": spec.scenario_type,
                    "schema_version": spec.schema_version,
                    "updated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    "status": status,
                    "tags": spec.tags
                }
            else:
                index_data[s_id] = {
                    "scenario_id": s_id,
                    "name": "Unknown (Broken)",
                    "world_id": "Unknown",
                    "scenario_type": "Unknown",
                    "schema_version": "Unknown",
                    "updated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    "status": status,
                    "tags": []
                }
                
        # Write cleanly to index file
        with open(self.index_path, "w") as f:
            json.dump(index_data, f, indent=2)

    def get_index(self) -> dict:
        """Loads and returns the scenario manifest index data."""
        if not self.index_path.is_file():
            self.rebuild_index()
        try:
            with open(self.index_path, "r") as f:
                return json.load(f)
        except Exception:
            self.rebuild_index()
            with open(self.index_path, "r") as f:
                return json.load(f)
