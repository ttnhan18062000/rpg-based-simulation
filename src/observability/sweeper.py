# Compliance IDs: OBS-031, OBS-032, OBS-033, OBS-034
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
from src.observability.reporting.artifact_repository import RunArtifactRepository, RunManifest
from src.config.profiles import RuntimeProfile
from src.config.loader import ConfigLoader
from src.perf.scenarios import SCENARIO_BUILDERS
from src.platform.rng import DeterministicRNG
from src.engine.kernel import Kernel

logger = logging.getLogger(__name__)


class ScenarioSweepConfig(BaseModel):
    """Configuration structure defining scenario execution parameters across seeds."""
    sweep_id: Optional[str] = None
    scenario_name: str
    scenario_type: str
    seeds: List[int]
    ticks: int
    observability_mode: ObservabilityMode
    profile_name: str = "cli_default"
    max_parallel_runs: int = Field(default=1, ge=1)
    stop_on_first_critical: bool = False
    output_dir: str = "data/run_sets"

    @field_validator("observability_mode", mode="before")
    @classmethod
    def parse_observability_mode(cls, v: Any) -> Any:
        if isinstance(v, str):
            normalized = v.strip().lower()
            mapping = {
                "none": "OFF",
                "off": "OFF",
                "light": "LIGHT",
                "production": "LIGHT",
                "full": "DEBUG",
                "debug": "DEBUG",
                "cert": "CERTIFICATION",
                "certification": "CERTIFICATION",
                "long_run": "LONG_RUN",
                "longrun": "LONG_RUN"
            }
            mapped = mapping.get(normalized)
            if mapped:
                return ObservabilityMode(mapped)
        return v

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


class ScenarioRunSpec(BaseModel):
    """Metadata detailing the parameter mapping of a single run spec in the matrix."""
    run_id: str
    seed: int
    ticks: int
    scenario_name: str
    scenario_type: str


class RunSetManifest(BaseModel):
    """Structured report index documenting execution results across a completed scenario sweep."""
    sweep_id: str
    scenario_name: str
    scenario_type: str
    started_at: str
    ended_at: Optional[str] = None
    status: str = "CREATED"  # CREATED, RUNNING, COMPLETED, FAILED, PARTIAL
    run_ids: List[str] = Field(default_factory=list)
    seed_by_run_id: Dict[str, int] = Field(default_factory=dict)
    ticks_requested: int
    completed_count: int = 0
    failed_count: int = 0
    artifact_schema_version: str = "run_set_v1"
    failures: Dict[str, str] = Field(default_factory=dict)


class ScenarioSweeper:
    """Sequential engine sweeper executing parameterized simulation matrices."""

    @classmethod
    def run_sweep(cls, config: ScenarioSweepConfig) -> RunSetManifest:
        # 1. Setup sweep directory
        sweep_id = config.sweep_id
        if not sweep_id:
            sweep_id = f"sweep_{int(time.time())}_{uuid.uuid4().hex[:6]}"
            config = config.model_copy(update={"sweep_id": sweep_id})

        sweep_dir = os.path.abspath(os.path.join(config.output_dir, sweep_id))
        os.makedirs(sweep_dir, exist_ok=True)

        # Write active configuration
        with open(os.path.join(sweep_dir, "sweep_config.json"), "w", encoding="utf-8") as f:
            f.write(config.model_dump_json(indent=2))

        started_at = datetime.now(timezone.utc).isoformat()

        # 2. Build Run Matrix
        run_specs: List[ScenarioRunSpec] = []
        for seed in config.seeds:
            run_id = f"run_{sweep_id}_seed_{seed}"
            run_specs.append(ScenarioRunSpec(
                run_id=run_id,
                seed=seed,
                ticks=config.ticks,
                scenario_name=config.scenario_name,
                scenario_type=config.scenario_type
            ))

        manifest = RunSetManifest(
            sweep_id=sweep_id,
            scenario_name=config.scenario_name,
            scenario_type=config.scenario_type,
            started_at=started_at,
            status="RUNNING",
            run_ids=[spec.run_id for spec in run_specs],
            seed_by_run_id={spec.run_id: spec.seed for spec in run_specs},
            ticks_requested=config.ticks
        )

        manifest_path = os.path.join(sweep_dir, "run_set_manifest.json")
        cls._write_manifest(manifest, manifest_path)

        # 3. Setup programmatic override mode
        original_mode = ObservabilityConfig.get_mode()
        ObservabilityConfig.set_override_mode(config.observability_mode)

        try:
            completed_count = 0
            failed_count = 0
            failures = {}

            # Execute run specifications sequentially
            for spec in run_specs:
                logger.info(f"Executing run {spec.run_id} (Seed: {spec.seed}, Ticks: {spec.ticks})")
                
                if spec.scenario_name not in SCENARIO_BUILDERS:
                    err_msg = f"Unknown scenario name: {spec.scenario_name}"
                    logger.error(err_msg)
                    failed_count += 1
                    failures[spec.run_id] = err_msg
                    manifest = manifest.model_copy(update={
                        "failed_count": failed_count,
                        "failures": failures
                    })
                    cls._write_manifest(manifest, manifest_path)
                    if config.stop_on_first_critical:
                        break
                    continue

                run_success = False
                temp_run_dir = os.path.abspath(os.path.join("data/runs", spec.run_id))
                
                try:
                    builder = SCENARIO_BUILDERS[spec.scenario_name]
                    sig = inspect.signature(builder)
                    kwargs = {"seed": spec.seed}
                    if "entity_count" in sig.parameters:
                        kwargs["entity_count"] = 10
                    elif "team_a_count" in sig.parameters:
                        kwargs["team_a_count"] = 5
                        kwargs["team_b_count"] = 5

                    initial_state = builder(**kwargs)

                    profile = ConfigLoader.load_profile(
                        profile_name=config.profile_name,
                        cli_overrides={
                            "name": config.profile_name
                        }
                    )

                    rng = DeterministicRNG(spec.seed)
                    kernel = Kernel(
                        profile=profile,
                        state=initial_state,
                        rng=rng,
                        run_id=spec.run_id
                    )

                    try:
                        for _ in range(spec.ticks):
                            kernel.tick_once()
                        run_success = True
                    finally:
                        kernel.shutdown()

                except Exception as e:
                    err_msg = f"Simulation error on seed {spec.seed}: {str(e)}"
                    logger.exception(err_msg)
                    failures[spec.run_id] = err_msg
                    
                    try:
                        repo = RunArtifactRepository()
                        if os.path.exists(os.path.join("data/runs", spec.run_id, "run_manifest.json")):
                            repo.update_manifest(spec.run_id, status="FAILED", failure_reason=str(e))
                    except Exception:
                        pass

                # Run post-simulation analysis pipeline to generate run_report.json, anomalies.json, etc.
                try:
                    from src.observability.anomaly.pipeline import AnalysisPipeline
                    pipeline = AnalysisPipeline()
                    pipeline.run(spec.run_id, allow_partial=True)
                except Exception as ap_err:
                    logger.error(f"Failed running AnalysisPipeline for run {spec.run_id}: {ap_err}")

                # Copy run artifacts to the localized sweep runs folder and keep under data/runs
                target_run_dir = os.path.join(sweep_dir, "runs", spec.run_id)
                os.makedirs(os.path.dirname(target_run_dir), exist_ok=True)
                
                if os.path.exists(temp_run_dir):
                    if os.path.exists(target_run_dir):
                        shutil.rmtree(target_run_dir)
                    shutil.copytree(temp_run_dir, target_run_dir)

                if run_success:
                    completed_count += 1
                else:
                    failed_count += 1

                # Progressively write back manifest to satisfy atomic durability
                manifest = manifest.model_copy(update={
                    "completed_count": completed_count,
                    "failed_count": failed_count,
                    "failures": failures
                })
                cls._write_manifest(manifest, manifest_path)

                if not run_success and config.stop_on_first_critical:
                    logger.warning("Critical run failure and stop_on_first_critical enabled. Terminating sweep.")
                    break

            # 4. Finalize run set manifest
            ended_at = datetime.now(timezone.utc).isoformat()
            
            if failed_count == 0:
                status = "COMPLETED"
            elif completed_count == 0:
                status = "FAILED"
            else:
                status = "PARTIAL"

            manifest = manifest.model_copy(update={
                "ended_at": ended_at,
                "status": status
            })
            cls._write_manifest(manifest, manifest_path)

            # 5. Build Run Index and Sweep Summary (Milestone 16)
            try:
                from src.observability.reporting.run_set_repository import RunIndexRecord, SweepSummary, RunSetArtifactRepository
                repo_inst = RunSetArtifactRepository(base_dir=config.output_dir)
                records: List[RunIndexRecord] = []
                
                for spec in run_specs:
                    run_dir = os.path.join(sweep_dir, "runs", spec.run_id)
                    manifest_file = os.path.join(run_dir, "run_manifest.json")
                    report_file = os.path.join(run_dir, "run_report.json")
                    
                    ticks_completed = spec.ticks
                    r_status = "FAILED"
                    health_score = 0.0
                    critical_count = 0
                    warning_count = 0
                    hard_law_violation_count = 0
                    
                    if os.path.exists(manifest_file):
                        try:
                            with open(manifest_file, "r", encoding="utf-8") as f:
                                m_data = json.load(f)
                                ticks_completed = m_data.get("ticks_completed", spec.ticks)
                                r_status = m_data.get("status", "FAILED")
                        except Exception:
                            pass
                    
                    if os.path.exists(report_file):
                        try:
                            with open(report_file, "r", encoding="utf-8") as f:
                                r_data = json.load(f)
                                health_score = r_data.get("health_score", 100.0)
                                critical_count = r_data.get("critical_count", 0)
                                warning_count = r_data.get("warning_count", 0)
                                hard_law_violation_count = r_data.get("hard_law_violation_count", 0)
                        except Exception:
                            pass
                    else:
                        if r_status in ("COMPLETED", "ANALYZED"):
                            health_score = 100.0

                    records.append(RunIndexRecord(
                        sweep_id=sweep_id,
                        run_id=spec.run_id,
                        seed=spec.seed,
                        scenario_name=spec.scenario_name,
                        scenario_type=spec.scenario_type,
                        status=r_status,
                        ticks_completed=ticks_completed,
                        health_score=health_score,
                        critical_count=critical_count,
                        warning_count=warning_count,
                        hard_law_violation_count=hard_law_violation_count,
                        artifact_path=run_dir
                    ))
                
                repo_inst.write_run_index(sweep_id, records)
                
                # Build Sweep Summary
                total_runs = len(records)
                completed_runs = sum(1 for r in records if r.status in ("COMPLETED", "ANALYZED"))
                failed_runs = sum(1 for r in records if r.status == "FAILED")
                avg_health = sum(r.health_score for r in records) / total_runs if total_runs > 0 else 0.0
                
                critical_run_count = sum(1 for r in records if r.health_score < 60.0 or r.status == "FAILED")
                warning_run_count = sum(1 for r in records if 60.0 <= r.health_score < 90.0)
                
                best_run_id = None
                worst_run_id = None
                if records:
                    sorted_best = sorted(
                        records,
                        key=lambda r: (r.status in ("COMPLETED", "ANALYZED"), r.health_score, r.ticks_completed),
                        reverse=True
                    )
                    best_run_id = sorted_best[0].run_id
                    
                    sorted_worst = sorted(
                        records,
                        key=lambda r: (r.status in ("COMPLETED", "ANALYZED"), r.health_score, r.ticks_completed)
                    )
                    worst_run_id = sorted_worst[0].run_id

                anomaly_counts: Dict[str, int] = {}
                for spec in run_specs:
                    run_dir = os.path.join(sweep_dir, "runs", spec.run_id)
                    anomalies_file = os.path.join(run_dir, "anomalies.json")
                    if os.path.exists(anomalies_file):
                        try:
                            with open(anomalies_file, "r", encoding="utf-8") as f:
                                a_list = json.load(f)
                                for a in a_list:
                                    rule_id = a.get("rule_id")
                                    if rule_id:
                                        anomaly_counts[rule_id] = anomaly_counts.get(rule_id, 0) + 1
                        except Exception:
                            pass
                            
                summary = SweepSummary(
                    sweep_id=sweep_id,
                    scenario_name=config.scenario_name,
                    scenario_type=config.scenario_type,
                    total_runs=total_runs,
                    completed_runs=completed_runs,
                    failed_runs=failed_runs,
                    average_health_score=avg_health,
                    critical_run_count=critical_run_count,
                    warning_run_count=warning_run_count,
                    worst_run_id=worst_run_id,
                    best_run_id=best_run_id,
                    most_common_anomaly_rule_ids=anomaly_counts
                )
                repo_inst.write_sweep_summary(sweep_id, summary)

            except Exception as e:
                logger.error(f"Failed to generate sweep index and summary: {e}", exc_info=True)

            return manifest

        finally:
            ObservabilityConfig.set_override_mode(original_mode)

    @classmethod
    def _write_manifest(cls, manifest: RunSetManifest, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            f.write(manifest.model_dump_json(indent=2))
