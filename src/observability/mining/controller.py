# Compliance IDs: OBS-PH9-M49
from __future__ import annotations

import os
import time
import json
import logging
import shutil
import uuid
import inspect
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator

from src.observability.config import ObservabilityConfig, ObservabilityMode
from src.observability.reporting.artifact_repository import RunArtifactRepository
from src.config.profiles import RuntimeProfile
from src.config.loader import ConfigLoader
from src.perf.scenarios import SCENARIO_BUILDERS
from src.platform.rng import DeterministicRNG
from src.engine.kernel import Kernel

logger = logging.getLogger(__name__)


class MiningExperimentConfig(BaseModel):
    """Configuration structure defining large-scale mining experiments."""
    experiment_id: Optional[str] = None
    experiment_type: str  # same_seed_repeat, multi_seed_sweep, version_comparison, profile_comparison, observability_comparison, stress_long_run
    scenario_name: str
    scenario_type: str
    seeds: List[int]
    repeat_count: int = 1
    ticks: int
    engine_version: str = "v2"
    balance_profile: str = "cli_default"
    expectation_pack: Optional[str] = None
    observability_profile: str = "production"
    max_parallel_runs: int = 1
    output_dir: str = "data/mining_experiments"

    @field_validator("seeds")
    @classmethod
    def validate_seeds(cls, v: List[int]) -> List[int]:
        if not v:
            raise ValueError("seeds list cannot be empty")
        return v

    @field_validator("ticks")
    @classmethod
    def validate_ticks(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("ticks must be positive")
        return v


class MiningRunSpec(BaseModel):
    """Parameter mapping for a single run inside the mining matrix."""
    run_id: str
    scenario: str
    seed: int
    repeat_index: int
    engine_version: str
    balance_profile: str
    observability_profile: str
    ticks: int


class MiningExperimentManifest(BaseModel):
    """Manifest documenting the progress, parameters, and outputs of an active/completed mining experiment."""
    experiment_id: str
    experiment_type: str
    scenario_name: str
    seed_count: int
    repeat_count: int
    run_count: int
    started_at: str
    ended_at: Optional[str] = None
    status: str = "CREATED"  # CREATED, RUNNING, COMPLETED, FAILED, PARTIAL
    run_ids: List[str] = Field(default_factory=list)
    artifact_paths: Dict[str, str] = Field(default_factory=dict)
    failures: Dict[str, str] = Field(default_factory=dict)
    artifact_schema_version: str = "mining_experiment_v1"


class MiningRunMatrixBuilder:
    """Builder generating concrete, sequential run specifications based on configuration profiles."""
    
    @classmethod
    def build_matrix(cls, config: MiningExperimentConfig, experiment_dir: str) -> List[MiningRunSpec]:
        run_specs: List[MiningRunSpec] = []
        
        # Determine runs based on type
        if config.experiment_type == "same_seed_repeat":
            # Repeatedly execute the same seed to test for determinism
            target_seed = config.seeds[0]
            for rep in range(config.repeat_count):
                run_id = f"run_{config.experiment_id}_seed_{target_seed}_rep_{rep}"
                run_specs.append(MiningRunSpec(
                    run_id=run_id,
                    scenario=config.scenario_name,
                    seed=target_seed,
                    repeat_index=rep,
                    engine_version=config.engine_version,
                    balance_profile=config.balance_profile,
                    observability_profile=config.observability_profile,
                    ticks=config.ticks
                ))
        else:
            # Standard multi-seed sweeps and custom comparisons
            for seed in config.seeds:
                for rep in range(config.repeat_count):
                    suffix = f"_rep_{rep}" if config.repeat_count > 1 else ""
                    run_id = f"run_{config.experiment_id}_seed_{seed}{suffix}"
                    run_specs.append(MiningRunSpec(
                        run_id=run_id,
                        scenario=config.scenario_name,
                        seed=seed,
                        repeat_index=rep,
                        engine_version=config.engine_version,
                        balance_profile=config.balance_profile,
                        observability_profile=config.observability_profile,
                        ticks=config.ticks
                    ))
                    
        # Write matrix specifications to disk
        matrix_path = os.path.join(experiment_dir, "run_matrix.jsonl")
        with open(matrix_path, "w", encoding="utf-8") as f:
            for spec in run_specs:
                f.write(spec.model_dump_json() + "\n")
                
        return run_specs


class MiningExperimentController:
    """Orchestrates large-scale simulation executions, tracks progress, and saves output matrix catalogs."""
    
    @classmethod
    def execute_experiment(cls, config: MiningExperimentConfig) -> MiningExperimentManifest:
        # 1. Establish experiment workspace
        experiment_id = config.experiment_id
        if not experiment_id:
            experiment_id = f"exp_{int(time.time())}_{uuid.uuid4().hex[:6]}"
            config = config.model_copy(update={"experiment_id": experiment_id})
            
        experiment_dir = os.path.abspath(os.path.join(config.output_dir, experiment_id))
        os.makedirs(experiment_dir, exist_ok=True)
        
        # Save config
        with open(os.path.join(experiment_dir, "experiment_config.json"), "w", encoding="utf-8") as f:
            f.write(config.model_dump_json(indent=2))
            
        started_at = datetime.now(timezone.utc).isoformat()
        
        # 2. Build parameter matrix
        run_specs = MiningRunMatrixBuilder.build_matrix(config, experiment_dir)
        
        manifest = MiningExperimentManifest(
            experiment_id=experiment_id,
            experiment_type=config.experiment_type,
            scenario_name=config.scenario_name,
            seed_count=len(config.seeds),
            repeat_count=config.repeat_count,
            run_count=len(run_specs),
            started_at=started_at,
            status="RUNNING",
            run_ids=[spec.run_id for spec in run_specs]
        )
        
        manifest_path = os.path.join(experiment_dir, "experiment_manifest.json")
        cls._write_manifest(manifest, manifest_path)
        
        # Save progress tracking structure
        status_path = os.path.join(experiment_dir, "experiment_status.json")
        cls._write_status(0, len(run_specs), "RUNNING", status_path)
        
        # 3. Configure Observability Mode dynamically
        original_mode = ObservabilityConfig.get_mode()
        # Map profile mode strings to Pydantic-valid ObservabilityMode
        obs_mode_mapping = {
            "production": ObservabilityMode.PRODUCTION if hasattr(ObservabilityMode, "PRODUCTION") else ObservabilityMode.FULL,
            "full": ObservabilityMode.FULL,
            "light": ObservabilityMode.LIGHT,
            "none": ObservabilityMode.NONE
        }
        target_mode = obs_mode_mapping.get(config.observability_profile.lower(), ObservabilityMode.FULL)
        ObservabilityConfig.set_override_mode(target_mode)
        
        completed_count = 0
        failed_count = 0
        failures = {}
        artifact_paths = {}
        
        try:
            for i, spec in enumerate(run_specs):
                logger.info(f"[{i+1}/{len(run_specs)}] Executing run {spec.run_id} (Seed: {spec.seed})")
                
                if spec.scenario not in SCENARIO_BUILDERS:
                    err_msg = f"Unknown scenario name: {spec.scenario}"
                    failures[spec.run_id] = err_msg
                    failed_count += 1
                    continue
                    
                temp_run_dir = os.path.abspath(os.path.join("data/runs", spec.run_id))
                run_success = False
                
                try:
                    builder = SCENARIO_BUILDERS[spec.scenario]
                    sig = inspect.signature(builder)
                    kwargs = {"seed": spec.seed}
                    if "entity_count" in sig.parameters:
                        kwargs["entity_count"] = 10
                    elif "team_a_count" in sig.parameters:
                        kwargs["team_a_count"] = 5
                        kwargs["team_b_count"] = 5
                        
                    initial_state = builder(**kwargs)
                    profile = ConfigLoader.load_profile(
                        profile_name=spec.balance_profile,
                        cli_overrides={"name": spec.balance_profile}
                    )
                    
                    rng = DeterministicRNG(spec.seed)
                    kernel = Kernel(
                        profile=profile,
                        state=initial_state,
                        rng=rng,
                        run_id=spec.run_id
                    )
                    
                    # Run deterministic tick loop
                    for _ in range(spec.ticks):
                        kernel.tick_once()
                        
                    kernel.shutdown()
                    run_success = True
                    
                except Exception as e:
                    err_msg = f"Simulation crash on run {spec.run_id}: {str(e)}"
                    logger.exception(err_msg)
                    failures[spec.run_id] = err_msg
                    
                    # Update internal single-run manifest
                    try:
                        repo = RunArtifactRepository()
                        if os.path.exists(os.path.join(temp_run_dir, "run_manifest.json")):
                            repo.update_manifest(spec.run_id, status="FAILED", failure_reason=str(e))
                    except Exception:
                        pass
                        
                # 4. Standardize run outputs location post-execution
                target_run_dir = os.path.abspath(os.path.join(experiment_dir, "runs", spec.run_id))
                os.makedirs(os.path.dirname(target_run_dir), exist_ok=True)
                
                if os.path.exists(temp_run_dir):
                    if os.path.exists(target_run_dir):
                        shutil.rmtree(target_run_dir)
                    shutil.move(temp_run_dir, target_run_dir)
                    
                if run_success:
                    completed_count += 1
                    artifact_paths[spec.run_id] = target_run_dir
                else:
                    failed_count += 1
                    
                # Incrementally save manifest & progress reports
                manifest = manifest.model_copy(update={
                    "artifact_paths": artifact_paths,
                    "failures": failures
                })
                cls._write_manifest(manifest, manifest_path)
                cls._write_status(completed_count + failed_count, len(run_specs), "RUNNING", status_path)
                
            # 5. Finalize manifest status
            ended_at = datetime.now(timezone.utc).isoformat()
            if failed_count == 0:
                final_status = "COMPLETED"
            elif completed_count == 0:
                final_status = "FAILED"
            else:
                final_status = "PARTIAL"
                
            manifest = manifest.model_copy(update={
                "ended_at": ended_at,
                "status": final_status
            })
            cls._write_manifest(manifest, manifest_path)
            cls._write_status(len(run_specs), len(run_specs), final_status, status_path)
            
            return manifest
            
        finally:
            ObservabilityConfig.set_override_mode(original_mode)
            
    @classmethod
    def _write_manifest(cls, manifest: MiningExperimentManifest, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            f.write(manifest.model_dump_json(indent=2))
            
    @classmethod
    def _write_status(cls, completed: int, total: int, status: str, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump({
                "completed_runs": completed,
                "total_runs": total,
                "status": status,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }, f, indent=2)
