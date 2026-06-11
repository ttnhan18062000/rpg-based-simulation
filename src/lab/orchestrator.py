# Compliance IDs: SCENARIO-012, SCENARIO-013, SCENARIO-014, SCENARIO-015
import os
import json
import shutil
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any

from src.lab.schema import LabRunManifest, InvalidLabRunManifestError
from src.lab.repository import (
    ScenarioRepository,
    ScenarioRepositoryError,
    ExperimentRepository,
    ExperimentRepositoryError,
    LabRunRepository,
    LabRunRepositoryError
)
from src.worldbuilding.repository import WorldRepository, WorldRepositoryError
from src.worldbuilding.validator import WorldValidator
from src.lab.validator import ScenarioValidator, ExperimentValidator
from src.observability.config import ObservabilityConfig, ObservabilityMode
from src.config.loader import ConfigLoader

logger = logging.getLogger(__name__)


class ScenarioLabOrchestrator:
    """
    Central workflow engine that coordinates:
    1. loading and validating World, Scenario, and Experiment specs.
    2. instantiating secure, isolated lab runs.
    3. compiling the world and driving simulation ticks.
    4. triggering post-run analysis and summary compilation.
    """

    def __init__(
        self,
        world_repo: WorldRepository,
        scenario_repo: ScenarioRepository,
        experiment_repo: ExperimentRepository,
        lab_run_repo: LabRunRepository
    ):
        self.world_repo = world_repo
        self.scenario_repo = scenario_repo
        self.experiment_repo = experiment_repo
        self.lab_run_repo = lab_run_repo

    def run_lab(
        self,
        experiment_id: str,
        lab_run_id: str,
        profile: str = "local_dev",
        force: bool = False,
        confirm: bool = False
    ) -> LabRunManifest:
        """
        Executes a Scenario Lab execution from end-to-end sequentially.
        """
        # 1. Load Experiment Spec
        experiment_spec = self.experiment_repo.load_experiment(experiment_id)

        # 2. Validate Experiment Spec
        ExperimentValidator(scenario_repo=self.scenario_repo).validate(experiment_spec)

        # 3. Load and Validate Scenario Spec
        scenario_spec = self.scenario_repo.load_scenario(experiment_spec.scenario_id)
        ScenarioValidator(world_repo=self.world_repo).validate(scenario_spec)

        # 4. Load and Validate World Spec
        world_spec = self.world_repo.load_world(scenario_spec.world_id)
        WorldValidator().validate(world_spec)

        # 4b. Perform Budget Guardrails Check (Pre-flight, before any filesystem or manifest updates)
        from src.lab.guardrails import LabBudgetGuardrails, BudgetBlockedError, BudgetWarningError
        guardrails = LabBudgetGuardrails(profile=profile)
        estimate = guardrails.estimate(experiment_spec, world_spec)
        check_result = guardrails.check(estimate, experiment_spec)
        
        self.budget_warnings = check_result.warnings
        
        if check_result.is_blocked:
            if force and profile != "CI":
                logger.warning(
                    f"[AUDIT] Budget guardrail BLOCKED bypassed via --force for lab run '{lab_run_id}'. "
                    f"Reasons: {check_result.blocked_reasons}"
                )
            else:
                raise BudgetBlockedError(
                    f"Execution blocked by budget guardrails under '{profile}' profile: "
                    + "; ".join(check_result.blocked_reasons)
                )
        elif check_result.is_warning:
            if profile == "CI":
                raise BudgetBlockedError(
                    f"Execution blocked under 'CI' profile due to warnings: "
                    + "; ".join(check_result.warnings)
                )
            elif not confirm:
                raise BudgetWarningError(
                    f"Execution requires confirmation due to budget warnings: "
                    + "; ".join(check_result.warnings)
                )

        # 5. Build schema versions tracking
        schema_versions = {
            "world": getattr(world_spec, "schema_version", "worldspec.v1"),
            "scenario": getattr(scenario_spec, "schema_version", "scenariospec.v1"),
            "experiment": getattr(experiment_spec, "schema_version", "experimentspec.v1")
        }

        # 6. Initialize LabRunManifest
        manifest = LabRunManifest(
            lab_run_id=lab_run_id,
            world_id=world_spec.world_id,
            scenario_id=scenario_spec.scenario_id,
            experiment_id=experiment_spec.experiment_id,
            status="CREATED",
            started_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            run_count=len(experiment_spec.run.seeds),
            completed_run_count=0,
            failed_run_count=0,
            artifact_root="",
            schema_versions=schema_versions,
            budgets={"max_runtime_minutes": experiment_spec.budgets.max_runtime_minutes},
            storage_usage_mb=0.0
        )

        # 7. Create safe folder layout (raises FileExistsError if folder already exists)
        run_dir = self.lab_run_repo.create_lab_run(manifest)

        # 8. Store spec copies in their respective directories
        import yaml
        with open(run_dir / "world" / "world.yaml", "w", encoding="utf-8") as f:
            yaml.safe_dump(json.loads(world_spec.model_dump_json()), f, default_flow_style=False, sort_keys=False)
        with open(run_dir / "scenario" / "scenario.yaml", "w", encoding="utf-8") as f:
            yaml.safe_dump(json.loads(scenario_spec.model_dump_json()), f, default_flow_style=False, sort_keys=False)
        with open(run_dir / "experiment" / "experiment.yaml", "w", encoding="utf-8") as f:
            yaml.safe_dump(json.loads(experiment_spec.model_dump_json()), f, default_flow_style=False, sort_keys=False)

        # 9. Shift to RUNNING state
        manifest.status = "RUNNING"
        self.lab_run_repo.save_lab_run(manifest)

        # 10. Sequential execution of simulation run matrix
        original_mode = ObservabilityConfig.get_mode()
        obs_mode_mapping = {
            "LIGHTWEIGHT": ObservabilityMode.LIGHT,
            "MINIMAL": ObservabilityMode.LIGHT,
            "STANDARD": ObservabilityMode.LIGHT,
            "LONG_RUN": ObservabilityMode.LONG_RUN
        }
        target_obs_mode = obs_mode_mapping.get(experiment_spec.observability.mode, ObservabilityMode.LIGHT)
        ObservabilityConfig.set_override_mode(target_obs_mode)

        try:
            completed_count = 0
            failed_count = 0

            for seed in experiment_spec.run.seeds:
                run_id = f"run_{lab_run_id}_seed_{seed}"
                temp_run_dir = os.path.abspath(os.path.join("data/runs", run_id))
                if os.path.exists(temp_run_dir):
                    shutil.rmtree(temp_run_dir)

                run_success = False
                try:
                    os.makedirs(temp_run_dir, exist_ok=True)
                    
                    # Load compile context and resolved paths if resolved files exist
                    world_dir = self.world_repo.worlds_dir / scenario_spec.world_id
                    compile_context_path = world_dir / "resolved" / "compile_context.json"
                    resolved_world_path = world_dir / "resolved" / "world.resolved.yaml"
                    provenance_manifest_path = world_dir / "resolved" / "provenance_manifest.json"
                    assembly_report_path = world_dir / "resolved" / "assembly_report.json"
                    validation_report_path = world_dir / "resolved" / "validation_report.json"
                    
                    compile_context = None
                    if compile_context_path.is_file():
                        from src.worldassembly.context import CompileContext
                        with open(compile_context_path, "r", encoding="utf-8") as f:
                            context_data = json.load(f)
                        compile_context = CompileContext.from_dict(context_data)
                    
                    # Compile the world dynamically for this seed
                    from src.worldbuilding.compiler import WorldCompiler
                    compile_report_path = os.path.join(temp_run_dir, "world_compile_report.json")
                    initial_state, compile_report = WorldCompiler.compile(
                        world_spec,
                        seed,
                        output_report_path=compile_report_path,
                        context=compile_context
                    )

                    # Initialize profile and Kernel
                    profile = ConfigLoader.load_profile(
                        profile_name="cli_default",
                        cli_overrides={
                            "name": "cli_default"
                        }
                    )

                    from src.platform.rng import DeterministicRNG
                    from src.engine.kernel import Kernel

                    rng = DeterministicRNG(seed)
                    
                    if compile_context:
                        kernel = Kernel(
                            profile=profile,
                            state=initial_state,
                            rng=rng,
                            run_id=run_id,
                            resolved_world_path=str(resolved_world_path),
                            compile_context_path=str(compile_context_path),
                            provenance_manifest_path=str(provenance_manifest_path),
                            assembly_report_path=str(assembly_report_path),
                            validation_report_path=str(validation_report_path) if validation_report_path.is_file() else None,
                            compile_report_path=str(compile_report_path)
                        )
                    else:
                        kernel = Kernel(
                            profile=profile,
                            state=initial_state,
                            rng=rng,
                            run_id=run_id
                        )

                    # Ticks execution
                    for _ in range(experiment_spec.run.ticks):
                        kernel.tick_once()

                    kernel.shutdown()
                    run_success = True
                    completed_count += 1
                except Exception as e:
                    failed_count += 1
                    logger.exception(f"Simulation execution failed on seed {seed}: {e}")
                    # Write failure reason back to child run manifest
                    try:
                        from src.observability.reporting.artifact_repository import RunArtifactRepository
                        repo = RunArtifactRepository()
                        if os.path.exists(os.path.join("data/runs", run_id, "run_manifest.json")):
                            repo.update_manifest(run_id, status="FAILED", failure_reason=str(e))
                    except Exception:
                        pass

                # Post-simulation analysis
                if experiment_spec.analysis.run_post_analysis:
                    try:
                        from src.observability.anomaly.pipeline import AnalysisPipeline
                        pipeline = AnalysisPipeline()
                        pipeline.run(run_id, allow_partial=True)
                    except Exception as ap_err:
                        logger.error(f"Failed running AnalysisPipeline for run {run_id}: {ap_err}")

                # Copy run artifacts from data/runs/run_id to isolated lab folder
                target_run_dir = run_dir / "runs" / run_id
                if os.path.exists(temp_run_dir):
                    if target_run_dir.exists():
                        shutil.rmtree(target_run_dir)
                    shutil.copytree(temp_run_dir, target_run_dir)

                # Persist incremental progress manifest
                manifest.completed_run_count = completed_count
                manifest.failed_run_count = failed_count
                manifest.storage_usage_mb = self.lab_run_repo._calculate_storage_usage_mb(run_dir)
                self.lab_run_repo.save_lab_run(manifest)

            # 11. Aggregate child run report diagnostics
            completed_reports = []
            missing_reports = []
            
            for seed in experiment_spec.run.seeds:
                run_id = f"run_{lab_run_id}_seed_{seed}"
                target_run_dir = run_dir / "runs" / run_id
                report_path = target_run_dir / "run_report.json"
                
                if report_path.is_file():
                    try:
                        with open(report_path, "r", encoding="utf-8") as rf:
                            report_data = json.load(rf)
                            completed_reports.append((run_id, report_data))
                    except Exception as e:
                        logger.error(f"Failed loading run report for {run_id}: {e}")
                        missing_reports.append(run_id)
                else:
                    logger.warning(f"Run report not found for {run_id}")
                    missing_reports.append(run_id)

            health_scores = []
            critical_count_total = 0
            warning_count_total = 0
            anomaly_counts = {}
            best_run_id = None
            best_score = -1.0
            worst_run_id = None
            worst_score = 101.0
            
            for run_id, report in completed_reports:
                score = report.get("health_score", report.get("metadata", {}).get("health_score", 100.0))
                health_scores.append(score)
                
                if score > best_score:
                    best_score = score
                    best_run_id = run_id
                if score < worst_score:
                    worst_score = score
                    worst_run_id = run_id
                
                crit = report.get("critical_count", report.get("metadata", {}).get("critical_count", 0))
                warn = report.get("warning_count", report.get("metadata", {}).get("warning_count", 0))
                critical_count_total += crit
                warning_count_total += warn
                
                anoms = report.get("anomalies", [])
                for a in anoms:
                    rule = a.get("rule_name", "UnknownRule")
                    anomaly_counts[rule] = anomaly_counts.get(rule, 0) + 1
            
            average_health_score = sum(health_scores) / len(health_scores) if health_scores else 0.0
            if worst_score > 100.0:
                worst_score = 0.0
            if best_score < 0.0:
                best_score = 0.0
                
            sorted_anom = sorted(anomaly_counts.items(), key=lambda x: x[1], reverse=True)
            top_anomalies = {rule: count for rule, count in sorted_anom[:5]}

            # 12. Determine overall status and finalize
            if failed_count == 0 and (not missing_reports or not experiment_spec.analysis.run_post_analysis):
                manifest.status = "COMPLETED"
            elif completed_count == 0:
                manifest.status = "FAILED"
            else:
                manifest.status = "PARTIAL"

            ended_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            manifest.ended_at = ended_at
            manifest.storage_usage_mb = self.lab_run_repo._calculate_storage_usage_mb(run_dir)
            self.lab_run_repo.save_lab_run(manifest)

            # 13. Write lab summary JSON
            summary_data = {
                "lab_run_id": manifest.lab_run_id,
                "world_id": manifest.world_id,
                "scenario_id": manifest.scenario_id,
                "experiment_id": manifest.experiment_id,
                "status": manifest.status,
                "started_at": manifest.started_at,
                "ended_at": ended_at,
                "total_runs": manifest.run_count,
                "completed_runs": completed_count,
                "failed_runs": failed_count,
                "run_count": manifest.run_count,
                "completed_run_count": completed_count,
                "failed_run_count": failed_count,
                "average_health_score": average_health_score,
                "critical_count_total": critical_count_total,
                "warning_count_total": warning_count_total,
                "top_anomalies": top_anomalies,
                "worst_run_id": worst_run_id,
                "best_run_id": best_run_id,
                "storage_usage_mb": manifest.storage_usage_mb,
                "budget_warnings": getattr(self, "budget_warnings", [])
            }
            with open(run_dir / "lab_summary.json", "w", encoding="utf-8") as f:
                json.dump(summary_data, f, indent=2)

            # 14. Write lab summary MD report
            md_path = run_dir / "lab_summary.md"
            try:
                status_badge = "🟢 **COMPLETED**" if manifest.status == "COMPLETED" else "🟡 **PARTIAL**" if manifest.status == "PARTIAL" else "🔴 **FAILED**"
                health_badge = "🟢 **HEALTHY**" if average_health_score >= 90 else "🟡 **DEGRADED**" if average_health_score >= 60 else "🔴 **CRITICAL**"
                
                with open(md_path, "w", encoding="utf-8") as f:
                    f.write(f"# Scenario Lab Summary Report — {manifest.lab_run_id}\n\n")
                    f.write(f"> [!NOTE]\n> **Execution Summary:** The experiment has executed {manifest.run_count} total seeds. Status: {status_badge}.\n\n")
                    
                    # Budget warnings header
                    warnings_list = getattr(self, "budget_warnings", [])
                    if warnings_list:
                        f.write("> [!WARNING]\n> **Budget Guardrail Warnings triggered for this run:**\n")
                        for w in warnings_list:
                            f.write(f"> - {w}\n")
                        f.write("\n")
                    
                    f.write("## Executive Scorecard\n\n")
                    f.write(f"- **Overall Lab Status**: {status_badge}\n")
                    f.write(f"- **World Reference**: `{manifest.world_id}`\n")
                    f.write(f"- **Scenario Intent**: `{manifest.scenario_id}`\n")
                    f.write(f"- **Experiment Sweep ID**: `{manifest.experiment_id}`\n")
                    f.write(f"- **Average Seed Health**: `{average_health_score:.2f}/100` ({health_badge})\n")
                    f.write(f"- **Storage Footprint**: `{manifest.storage_usage_mb:.2f} MB`\n\n")
                    
                    f.write("## Telemetry Summary Dashboard\n\n")
                    f.write("| Seed Run ID | Status | Health Score | Criticals | Warnings | Report |\n")
                    f.write("| :--- | :--- | :--- | :--- | :--- | :--- |\n")
                    
                    for run_id, report in completed_reports:
                        r_score = report.get("health_score", 100.0)
                        r_crit = report.get("critical_count", 0)
                        r_warn = report.get("warning_count", 0)
                        r_status = "🟢 COMPLETED"
                        f.write(f"| `{run_id}` | {r_status} | `{r_score:.1f}` | `{r_crit}` | `{r_warn}` | [View Report](runs/{run_id}/run_report.md) |\n")
                        
                    for run_id in missing_reports:
                        f.write(f"| `{run_id}` | 🔴 FAILED/MISSING | `0.0` | `-` | `-` | *N/A* |\n")
                    
                    f.write("\n")
                    
                    f.write("## 🔍 Spacetime Triage Guide\n\n")
                    f.write(f"- **Best Performing Run**: `{best_run_id}` (Score: `{best_score:.1f}`)\n")
                    f.write(f"- **Worst Performing Run**: `{worst_run_id}` (Score: `{worst_score:.1f}`)\n\n")
                    
                    f.write("## ⚠️ Top Anomaly Frequency across Sweep\n\n")
                    if not top_anomalies:
                        f.write("🟢 **Triage Clear**: Zero anomalies recorded across the seed matrix sweep.\n")
                    else:
                        f.write("| Anomaly Rule ID | Trigger Count |\n")
                        f.write("| :--- | :--- |\n")
                        for rule, count in top_anomalies.items():
                            f.write(f"| `{rule}` | `{count}` |\n")
                        f.write("\n")
            except Exception as md_err:
                logger.error(f"Failed to generate lab_summary.md: {md_err}")

            return manifest

        finally:
            ObservabilityConfig.set_override_mode(original_mode)
