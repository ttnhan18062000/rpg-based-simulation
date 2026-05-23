# Compliance IDs: SCENARIO-007, SCENARIO-008, SCENARIO-009
from __future__ import annotations

import re
import json
import yaml
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional
from src.lab.schema import (
    ScenarioSpec,
    load_scenario_spec_from_yaml,
    InvalidScenarioSpecError,
    ExperimentSpec,
    load_experiment_spec_from_yaml,
    LabRunManifest,
    InvalidLabRunManifestError,
    MutationSpec,
    load_mutation_spec_from_yaml
)

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
            self.rebuild_index()
            with open(self.index_path, "r") as f:
                return json.load(f)
        except Exception:
            self.rebuild_index()
            with open(self.index_path, "r") as f:
                return json.load(f)


class ExperimentRepositoryError(Exception):
    """Base exception for ExperimentRepository operations."""
    pass


class ExperimentRepository:
    """
    File-based repository layer for loading, saving, listing, and index-tracking
    experiment specifications under a safe experiments root directory.
    """
    def __init__(self, experiments_dir: str | Path):
        self.experiments_dir = Path(experiments_dir).resolve()
        self.index_path = self.experiments_dir / "experiment_index.json"

    def _validate_experiment_id(self, experiment_id: str) -> None:
        """Enforces a strict safe pattern on experiment identifier strings."""
        if not experiment_id or not re.match(r"^[a-zA-Z0-9_-]+$", experiment_id):
            raise ValueError(f"Invalid or unsafe experiment_id pattern: '{experiment_id}'")

    def _resolve_experiment_path(self, experiment_id: str) -> Path:
        """
        Safely resolves an experiment's target folder and YAML path, blocking path traversal.
        """
        self._validate_experiment_id(experiment_id)
        target_dir = (self.experiments_dir / experiment_id).resolve()
        
        # Verify target is strictly a descendant of experiments_dir
        try:
            if not target_dir.is_relative_to(self.experiments_dir) or target_dir == self.experiments_dir:
                raise PermissionError(f"Path traversal attempt blocked for experiment_id: '{experiment_id}'")
        except ValueError as e:
            raise PermissionError(f"Path traversal attempt blocked for experiment_id: '{experiment_id}'") from e
            
        return target_dir / "experiment.yaml"

    def list_experiments(self) -> list[str]:
        """Lists IDs of all available experiments that have a valid directory and experiment.yaml."""
        if not self.experiments_dir.is_dir():
            return []
        
        experiments = []
        for path in self.experiments_dir.iterdir():
            if path.is_dir():
                try:
                    self._validate_experiment_id(path.name)
                    if (path / "experiment.yaml").is_file():
                        experiments.append(path.name)
                except ValueError:
                    continue
        return sorted(experiments)

    def load_experiment(self, experiment_id: str) -> ExperimentSpec:
        """Safely loads and parses an experiment specification by its ID."""
        yaml_path = self._resolve_experiment_path(experiment_id)
        if not yaml_path.is_file():
            raise FileNotFoundError(f"Experiment file not found for experiment_id: '{experiment_id}'")
        try:
            return load_experiment_spec_from_yaml(yaml_path)
        except Exception as e:
            raise ExperimentRepositoryError(f"Failed to load experiment '{experiment_id}': {e}") from e

    def save_experiment(self, spec: ExperimentSpec) -> None:
        """Safely serializes and saves an experiment specification to the filesystem."""
        experiment_id = spec.experiment_id
        yaml_path = self._resolve_experiment_path(experiment_id)
        
        # Ensure parent folder exists
        yaml_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # Dump to YAML safely using pure dictionaries
            data = json.loads(spec.model_dump_json())
            with open(yaml_path, "w") as f:
                yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)
        except Exception as e:
            raise ExperimentRepositoryError(f"Failed to save experiment '{experiment_id}': {e}") from e
            
        # Rebuild index to keep metadata synchronized
        self.rebuild_index()

    def rebuild_index(self) -> None:
        """
        Scans the experiments directory, loads and validates each experiment,
        and saves a consolidated experiment_index.json manifest.
        """
        self.experiments_dir.mkdir(parents=True, exist_ok=True)
        index_data = {}
        
        experiment_ids = self.list_experiments()
        for e_id in experiment_ids:
            try:
                spec = self.load_experiment(e_id)
                status = "VALIDATED"
            except Exception:
                status = "BROKEN"
                spec = None

            if spec:
                index_data[e_id] = {
                    "experiment_id": e_id,
                    "scenario_id": spec.scenario_id,
                    "experiment_type": spec.experiment_type,
                    "schema_version": spec.schema_version,
                    "updated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    "status": status,
                    "ticks": spec.run.ticks,
                    "seeds": spec.run.seeds
                }
            else:
                index_data[e_id] = {
                    "experiment_id": e_id,
                    "scenario_id": "Unknown",
                    "experiment_type": "Unknown",
                    "schema_version": "Unknown",
                    "updated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    "status": status,
                    "ticks": 0,
                    "seeds": []
                }
                
        # Write cleanly to index file
        try:
            with open(self.index_path, "w") as f:
                json.dump(index_data, f, indent=2)
        except Exception as e:
            raise ExperimentRepositoryError(f"Failed to write index manifest: {e}") from e

    def get_index(self) -> dict:
        """Loads and returns the experiment manifest index data."""
        if not self.index_path.is_file():
            self.rebuild_index()
        try:
            with open(self.index_path, "r") as f:
                return json.load(f)
        except Exception:
            self.rebuild_index()
            with open(self.index_path, "r") as f:
                return json.load(f)


class LabRunRepositoryError(Exception):
    """Base exception for LabRunRepository operations."""
    pass


class LabRunRepository:
    """
    File-based repository layer managing LabRun directory layouts, 
    manifest updates, and index aggregation under a safe lab runs root directory.
    """
    def __init__(self, lab_runs_dir: str | Path):
        self.lab_runs_dir = Path(lab_runs_dir).resolve()
        self.index_path = self.lab_runs_dir / "lab_runs_index.json"

    def _validate_lab_run_id(self, lab_run_id: str) -> None:
        if not lab_run_id:
            raise LabRunRepositoryError("lab_run_id cannot be empty")
        if not re.match("^[a-zA-Z0-9_-]+$", lab_run_id):
            raise LabRunRepositoryError(
                f"Invalid lab_run_id: '{lab_run_id}'. Must be alphanumeric plus hyphens/underscores."
            )

    def _resolve_run_dir(self, lab_run_id: str) -> Path:
        self._validate_lab_run_id(lab_run_id)
        resolved = (self.lab_runs_dir / lab_run_id).resolve()
        
        # Absolute path traversal prevention check
        try:
            if not resolved.is_relative_to(self.lab_runs_dir):
                raise LabRunRepositoryError(
                    f"Path traversal detected: resolved location '{resolved}' escapes base directory '{self.lab_runs_dir}'"
                )
        except ValueError as e:
            raise LabRunRepositoryError(
                f"Path traversal check failed: '{lab_run_id}' is outside '{self.lab_runs_dir}': {e}"
            ) from e
        return resolved

    def _calculate_storage_usage_mb(self, run_dir: Path) -> float:
        """Calculates directory storage usage in MB."""
        total_bytes = 0
        if run_dir.is_dir():
            for p in run_dir.rglob("*"):
                if p.is_file():
                    try:
                        total_bytes += p.stat().st_size
                    except Exception:
                        pass
        return round(total_bytes / (1024 * 1024), 3)

    def create_lab_run(self, manifest: LabRunManifest) -> Path:
        """
        Initializes a safe directory layout and writes the starting manifest.
        Raises FileExistsError if directory already exists.
        """
        run_dir = self._resolve_run_dir(manifest.lab_run_id)
        if run_dir.exists():
            raise FileExistsError(f"Lab run directory already exists: {run_dir}")

        # Construct safe layout subdirectories
        subdirs = ["world", "scenario", "experiment", "runs", "analysis", "logs"]
        try:
            run_dir.mkdir(parents=True, exist_ok=True)
            for subdir in subdirs:
                (run_dir / subdir).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise LabRunRepositoryError(f"Failed to create lab run folder layout: {e}") from e

        # Set accurate starting fields
        manifest.artifact_root = str(run_dir)
        manifest.storage_usage_mb = self._calculate_storage_usage_mb(run_dir)

        # Write manifest file
        self._write_manifest(run_dir, manifest)
        self.rebuild_index()
        return run_dir

    def _write_manifest(self, run_dir: Path, manifest: LabRunManifest) -> None:
        manifest_path = run_dir / "lab_run_manifest.json"
        try:
            with open(manifest_path, "w") as f:
                json.dump(manifest.model_dump(), f, indent=2)
        except Exception as e:
            raise LabRunRepositoryError(f"Failed to write lab run manifest: {e}") from e

    def load_lab_run(self, lab_run_id: str) -> LabRunManifest:
        """
        Loads and instantiates a LabRunManifest from a safe run folder.
        Raises FileNotFoundError if run folder or manifest is missing.
        """
        run_dir = self._resolve_run_dir(lab_run_id)
        manifest_path = run_dir / "lab_run_manifest.json"
        
        if not run_dir.is_dir():
            raise FileNotFoundError(f"Lab run directory not found: '{lab_run_id}'")
        if not manifest_path.is_file():
            raise FileNotFoundError(f"Lab run manifest file not found for run: '{lab_run_id}'")

        try:
            with open(manifest_path, "r") as f:
                raw = json.load(f)
        except Exception as e:
            raise LabRunRepositoryError(f"Failed to parse manifest JSON file: {e}") from e

        try:
            return LabRunManifest(**raw)
        except Exception as e:
            raise InvalidLabRunManifestError(f"Invalid lab run manifest in '{manifest_path}': {e}") from e

    def save_lab_run(self, manifest: LabRunManifest) -> None:
        """
        Saves changes to an existing LabRunManifest and updates the storage metrics.
        Raises FileNotFoundError if directory does not exist.
        """
        run_dir = self._resolve_run_dir(manifest.lab_run_id)
        if not run_dir.is_dir():
            raise FileNotFoundError(f"Lab run directory does not exist: {run_dir}")

        manifest.storage_usage_mb = self._calculate_storage_usage_mb(run_dir)
        self._write_manifest(run_dir, manifest)
        self.rebuild_index()

    def list_lab_runs(self) -> list[str]:
        """Scans the runs base directory and lists all valid lab run IDs."""
        if not self.lab_runs_dir.is_dir():
            return []
            
        run_ids = []
        for child in self.lab_runs_dir.iterdir():
            if child.is_dir():
                manifest_path = child / "lab_run_manifest.json"
                if manifest_path.is_file():
                    run_ids.append(child.name)
        return sorted(run_ids)

    def rebuild_index(self) -> None:
        """Aggregates all existing lab run manifests into a central manifest file."""
        self.lab_runs_dir.mkdir(parents=True, exist_ok=True)
        run_ids = self.list_lab_runs()
        index_data = {}

        for run_id in run_ids:
            try:
                manifest = self.load_lab_run(run_id)
                status = manifest.status
                record = {
                    "lab_run_id": run_id,
                    "world_id": manifest.world_id,
                    "scenario_id": manifest.scenario_id,
                    "experiment_id": manifest.experiment_id,
                    "status": status,
                    "started_at": manifest.started_at,
                    "ended_at": manifest.ended_at,
                    "run_count": manifest.run_count,
                    "completed_run_count": manifest.completed_run_count,
                    "failed_run_count": manifest.failed_run_count,
                    "storage_usage_mb": manifest.storage_usage_mb,
                    "updated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                }
            except Exception:
                record = {
                    "lab_run_id": run_id,
                    "world_id": "Unknown",
                    "scenario_id": "Unknown",
                    "experiment_id": "Unknown",
                    "status": "FAILED",
                    "started_at": "Unknown",
                    "ended_at": None,
                    "run_count": 0,
                    "completed_run_count": 0,
                    "failed_run_count": 0,
                    "storage_usage_mb": 0.0,
                    "updated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                }
            index_data[run_id] = record

        try:
            with open(self.index_path, "w") as f:
                json.dump(index_data, f, indent=2)
        except Exception as e:
            raise LabRunRepositoryError(f"Failed to write central lab run index: {e}") from e

    def get_index(self) -> dict:
        """Returns the central lab runs index manifest data."""
        if not self.index_path.is_file():
            self.rebuild_index()
        try:
            with open(self.index_path, "r") as f:
                return json.load(f)
        except Exception:
            self.rebuild_index()
            with open(self.index_path, "r") as f:
                return json.load(f)


class MutationRepositoryError(Exception):
    """Base exception for MutationRepository operations."""
    pass


class MutationRepository:
    """
    File-based repository layer for loading, saving, listing, and index-tracking
    mutation specifications under a safe mutations root directory.
    """
    def __init__(self, mutations_dir: str | Path):
        self.mutations_dir = Path(mutations_dir).resolve()
        self.index_path = self.mutations_dir / "mutation_index.json"

    def _validate_mutation_id(self, mutation_id: str) -> None:
        """Enforces a strict safe pattern on mutation identifier strings."""
        if not mutation_id or not re.match(r"^[a-zA-Z0-9_-]+$", mutation_id):
            raise ValueError(f"Invalid or unsafe mutation_id pattern: '{mutation_id}'")

    def _resolve_mutation_path(self, mutation_id: str) -> Path:
        """
        Safely resolves a mutation's target folder and YAML path, blocking path traversal.
        """
        self._validate_mutation_id(mutation_id)
        target_dir = (self.mutations_dir / mutation_id).resolve()
        
        # Verify target is strictly a descendant of mutations_dir
        try:
            if not target_dir.is_relative_to(self.mutations_dir) or target_dir == self.mutations_dir:
                raise PermissionError(f"Path traversal attempt blocked for mutation_id: '{mutation_id}'")
        except ValueError as e:
            raise PermissionError(f"Path traversal attempt blocked for mutation_id: '{mutation_id}'") from e
            
        return target_dir / "mutation.yaml"

    def list_mutations(self) -> list[str]:
        """Lists IDs of all available mutations that have a valid directory and mutation.yaml."""
        if not self.mutations_dir.is_dir():
            return []
        
        mutations = []
        for path in self.mutations_dir.iterdir():
            if path.is_dir():
                try:
                    self._validate_mutation_id(path.name)
                    if (path / "mutation.yaml").is_file():
                        mutations.append(path.name)
                except ValueError:
                    continue
        return sorted(mutations)

    def load_mutation(self, mutation_id: str) -> MutationSpec:
        """Safely loads and parses a mutation specification by its ID."""
        yaml_path = self._resolve_mutation_path(mutation_id)
        if not yaml_path.is_file():
            raise FileNotFoundError(f"Mutation file not found for mutation_id: '{mutation_id}'")
        try:
            return load_mutation_spec_from_yaml(yaml_path)
        except Exception as e:
            raise MutationRepositoryError(f"Failed to load mutation '{mutation_id}': {e}") from e

    def save_mutation(self, spec: MutationSpec) -> None:
        """Safely serializes and saves a mutation specification to the filesystem."""
        mutation_id = spec.mutation_id
        yaml_path = self._resolve_mutation_path(mutation_id)
        
        # Ensure parent folder exists
        yaml_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # Dump to YAML safely using pure dictionaries
            data = json.loads(spec.model_dump_json())
            with open(yaml_path, "w") as f:
                yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)
        except Exception as e:
            raise MutationRepositoryError(f"Failed to save mutation '{mutation_id}': {e}") from e
            
        # Rebuild index to keep metadata synchronized
        self.rebuild_index()

    def rebuild_index(self) -> None:
        """
        Scans the mutations directory, loads and validates each mutation,
        and saves a consolidated mutation_index.json manifest.
        """
        self.mutations_dir.mkdir(parents=True, exist_ok=True)
        index_data = {}
        
        mutation_ids = self.list_mutations()
        for m_id in mutation_ids:
            try:
                spec = self.load_mutation(m_id)
                status = "VALIDATED"
            except Exception:
                status = "BROKEN"
                spec = None

            if spec:
                index_data[m_id] = {
                    "mutation_id": m_id,
                    "name": spec.name,
                    "base_world_id": spec.base_world_id,
                    "base_scenario_id": spec.base_scenario_id,
                    "schema_version": spec.schema_version,
                    "updated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    "status": status,
                    "tags": spec.tags
                }
            else:
                index_data[m_id] = {
                    "mutation_id": m_id,
                    "name": "Unknown (Broken)",
                    "base_world_id": "Unknown",
                    "base_scenario_id": "Unknown",
                    "schema_version": "Unknown",
                    "updated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    "status": status,
                    "tags": []
                }
                
        # Write cleanly to index file
        try:
            with open(self.index_path, "w") as f:
                json.dump(index_data, f, indent=2)
        except Exception as e:
            raise MutationRepositoryError(f"Failed to write index manifest: {e}") from e

    def get_index(self) -> dict:
        """Loads and returns the mutation manifest index data."""
        if not self.index_path.is_file():
            self.rebuild_index()
        try:
            with open(self.index_path, "r") as f:
                return json.load(f)
        except Exception:
            self.rebuild_index()
            with open(self.index_path, "r") as f:
                return json.load(f)



