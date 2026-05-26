# Compliance IDs: MUTATION-ORCHESTRATOR-001, MUTATION-ORCHESTRATOR-002, MUTATION-ORCHESTRATOR-003
import os
import json
import shutil
import logging
import time
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, List

import yaml
from src.lab.schema import (
    MutationSpec,
    load_mutation_spec_from_yaml,
    ExperimentSpec,
    VariantManifest,
    ExpectedRelationshipSpec,
    LabRunManifest
)
from src.worldbuilding.repository import WorldRepository
from src.lab.repository import (
    ScenarioRepository,
    ExperimentRepository,
    LabRunRepository,
    MutationRepository
)
from src.lab.validator import MutationValidator, ExperimentValidator
from src.lab.guardrails import BudgetBlockedError
from src.lab.mutation import VariantMatrixBuilder
from src.lab.metamorphic import MetamorphicRuleEngine, MetamorphicComparisonResult
from src.lab.comparison import BalanceComparisonEngine, BalanceComparisonReport
from src.worldbuilding.validator import WorldValidator
from src.lab.validator import ScenarioValidator
from src.lab.orchestrator import ScenarioLabOrchestrator

logger = logging.getLogger(__name__)


class MutationLabOrchestrator:
    """
    Central workflow orchestrator for Mutation and Balance sweeps.
    Coordinates:
    1. Validating world, scenario, experiment, and mutation specs.
    2. Enforcing budget limits (matrix size, ticks limit).
    3. Generating mutated variants using VariantMatrixBuilder.
    4. SEQUENTIALLY executing isolated simulation sweeps per variant.
    5. Aggregating run report metrics.
    6. Running metamorphic validations and differential scorecards.
    7. Generating a consolidated mutation lab markdown report.
    """

    def __init__(
        self,
        world_repo: WorldRepository,
        scenario_repo: ScenarioRepository,
        experiment_repo: ExperimentRepository,
        lab_run_repo: LabRunRepository,
        mutation_repo: MutationRepository
    ):
        self.world_repo = world_repo
        self.scenario_repo = scenario_repo
        self.experiment_repo = experiment_repo
        self.lab_run_repo = lab_run_repo
        self.mutation_repo = mutation_repo

    def run_mutation_lab(
        self,
        mutation_id: str,
        experiment_id: str,
        mutation_lab_id: str,
        profile: str = "local_dev",
        force: bool = False,
        confirm: bool = False
    ) -> Dict[str, Any]:
        """
        Runs an end-to-end mutation and balance sweep sequence.
        """
        start_time = time.time()
        started_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        # 1. Load specs
        mutation_spec = self.mutation_repo.load_mutation(mutation_id)
        experiment_spec = self.experiment_repo.load_experiment(experiment_id)

        # 2. Validate specs (will raise InvalidMutationSpecError or InvalidExperimentSpecError on failure)
        MutationValidator(world_repo=self.world_repo, scenario_repo=self.scenario_repo).validate(mutation_spec)
        ExperimentValidator(scenario_repo=self.scenario_repo).validate(experiment_spec)

        # Ensure base world and scenario validate correctly
        base_world = self.world_repo.load_world(mutation_spec.base_world_id)
        base_scenario = self.scenario_repo.load_scenario(mutation_spec.base_scenario_id)
        WorldValidator().validate(base_world)
        ScenarioValidator(world_repo=self.world_repo).validate(base_scenario)

        # 3. Budget Guardrails Pre-flight Checks
        max_variants_allowed = 20
        max_ticks_allowed = 100000

        if mutation_spec.budgets:
            max_variants_allowed = mutation_spec.budgets.max_variant_count
            max_ticks_allowed = mutation_spec.budgets.max_total_ticks

        # Calculate variant count based on matrix mode
        mutations_count = len(mutation_spec.mutations)
        matrix_mode = mutation_spec.matrix.mode
        matrix_max = mutation_spec.matrix.max_variants

        estimated_variants = 1  # includes base
        if matrix_mode == "one_at_a_time":
            estimated_variants += mutations_count
        elif matrix_mode == "combined":
            estimated_variants += 1 if mutations_count > 0 else 0
        elif matrix_mode == "factorial_limited":
            # Factorial combinations count up to matrix_max
            import itertools
            comb_count = 0
            for size in range(1, mutations_count + 1):
                comb_count += len(list(itertools.combinations(range(mutations_count), size)))
            estimated_variants += min(comb_count, matrix_max)

        # Block huge mutation matrix count preemptively
        if estimated_variants > max_variants_allowed:
            raise BudgetBlockedError(
                f"Mutation matrix exceeds budget: estimated {estimated_variants} variants (limit: {max_variants_allowed})"
            )

        # Block cumulative ticks limit
        seed_count = len(experiment_spec.run.seeds)
        ticks_per_run = experiment_spec.run.ticks
        estimated_total_ticks = estimated_variants * seed_count * ticks_per_run
        if estimated_total_ticks > max_ticks_allowed:
            raise BudgetBlockedError(
                f"Mutation sweep tick footprint {estimated_total_ticks} exceeds budget (limit: {max_ticks_allowed})"
            )

        # 4. Initialize mutation lab folder layout
        mutation_lab_dir = Path("data/mutation_labs") / mutation_lab_id
        if mutation_lab_dir.exists():
            if force:
                shutil.rmtree(mutation_lab_dir)
            else:
                raise FileExistsError(f"Mutation lab folder already exists: {mutation_lab_dir}")

        mutation_lab_dir.mkdir(parents=True, exist_ok=True)
        variants_dir = mutation_lab_dir / "variants"
        variants_dir.mkdir(parents=True, exist_ok=True)
        analysis_dir = mutation_lab_dir / "analysis"
        analysis_dir.mkdir(parents=True, exist_ok=True)

        # Save copy of mutation spec
        with open(mutation_lab_dir / "mutation.yaml", "w", encoding="utf-8") as f:
            yaml.safe_dump(json.loads(mutation_spec.model_dump_json()), f, default_flow_style=False, sort_keys=False)

        # 5. Build variant matrix specifications
        matrix_builder = VariantMatrixBuilder()
        variant_manifests = matrix_builder.build_matrix(
            base_world=base_world,
            base_scenario=base_scenario,
            mutation_spec=mutation_spec,
            output_dir=variants_dir
        )

        # 6. Execute variant sweeps sequentially
        variant_run_results = {}
        completed_count = 0
        failed_count = 0

        for var_manifest in variant_manifests:
            var_id = var_manifest.variant_id
            
            # Skip executing failed matrix elements
            if var_manifest.status == "FAILED":
                failed_count += 1
                variant_run_results[var_id] = {
                    "status": "FAILED",
                    "error": var_manifest.validation_result.get("error") if var_manifest.validation_result else "Matrix compilation failure"
                }
                continue

            # Create transient isolated repos for world compiler & scenario loader compatibility
            temp_repo_dir = mutation_lab_dir / "temp_repos" / var_id
            temp_worlds_dir = temp_repo_dir / "worlds"
            temp_scenarios_dir = temp_repo_dir / "scenarios"

            (temp_worlds_dir / base_world.world_id).mkdir(parents=True, exist_ok=True)
            (temp_scenarios_dir / base_scenario.scenario_id).mkdir(parents=True, exist_ok=True)

            shutil.copy2(var_manifest.world_spec_path, temp_worlds_dir / base_world.world_id / "world.yaml")
            shutil.copy2(var_manifest.scenario_spec_path, temp_scenarios_dir / base_scenario.scenario_id / "scenario.yaml")

            # Instantiate virtual repositories
            world_repo_var = WorldRepository(temp_worlds_dir)
            scenario_repo_var = ScenarioRepository(temp_scenarios_dir)
            
            # Isolated lab run repo for this variant under: variants/{var_id}/lab_run
            var_lab_run_dir = variants_dir / var_id
            lab_run_repo_var = LabRunRepository(var_lab_run_dir)

            orchestrator = ScenarioLabOrchestrator(
                world_repo=world_repo_var,
                scenario_repo=scenario_repo_var,
                experiment_repo=self.experiment_repo,
                lab_run_repo=lab_run_repo_var
            )

            try:
                # Run using "lab_run" as the subfolder ID
                lab_run_manifest = orchestrator.run_lab(
                    experiment_id=experiment_id,
                    lab_run_id="lab_run",
                    profile=profile,
                    force=force,
                    confirm=confirm
                )

                if lab_run_manifest.status == "COMPLETED" or lab_run_manifest.status == "PARTIAL":
                    completed_count += 1
                    variant_run_results[var_id] = {
                        "status": lab_run_manifest.status,
                        "manifest": lab_run_manifest
                    }
                else:
                    failed_count += 1
                    variant_run_results[var_id] = {
                        "status": "FAILED",
                        "error": "Simulation execution resulted in FAILED state"
                    }
            except Exception as e:
                failed_count += 1
                logger.exception(f"Variant execution failed on '{var_id}': {e}")
                variant_run_results[var_id] = {
                    "status": "FAILED",
                    "error": str(e)
                }

        # Clean up transient temp repos folder
        temp_repos_dir = mutation_lab_dir / "temp_repos"
        if temp_repos_dir.exists():
            shutil.rmtree(temp_repos_dir)

        # Block overall success if ALL variants failed
        if completed_count == 0:
            overall_status = "FAILED"
        elif failed_count > 0:
            overall_status = "PARTIAL"
        else:
            overall_status = "COMPLETED"

        # 7. Collect high-fidelity variant metrics
        variant_metrics = {}
        for var_id, result in variant_run_results.items():
            if result["status"] == "FAILED":
                continue
            metrics = self._extract_variant_metrics(variants_dir, var_id)
            if metrics:
                variant_metrics[var_id] = metrics

        # 8. Metamorphic Rule Evaluation
        metamorphic_results = []
        if "base" in variant_metrics and len(variant_metrics) > 1:
            resolved_relationships = []
            for rel in mutation_spec.expected_relationships:
                comp_var = rel.compared_variant
                # If comp_var is a mutation ID, find the variant ID that applied it
                matched_var_id = None
                for m in variant_manifests:
                    if comp_var in m.applied_mutations:
                        matched_var_id = m.variant_id
                        break
                
                if matched_var_id:
                    resolved_rel = ExpectedRelationshipSpec(
                        id=rel.id,
                        type=rel.type,
                        metric=rel.metric,
                        baseline_variant=rel.baseline_variant,
                        compared_variant=matched_var_id,
                        tolerance=rel.tolerance
                    )
                    resolved_relationships.append(resolved_rel)
                else:
                    resolved_relationships.append(rel)

            metamorphic_results = MetamorphicRuleEngine.evaluate_rules(
                resolved_relationships,
                variant_metrics
            )

        # Write metamorphic results JSON
        with open(analysis_dir / "metamorphic_results.json", "w", encoding="utf-8") as f:
            json.dump([res.model_dump() for res in metamorphic_results], f, indent=2)

        # 9. Differential Balance Comparisons
        balance_comparison_reports = {}
        if "base" in variant_metrics:
            base_metrics = variant_metrics["base"]
            for var_id, var_m in variant_metrics.items():
                if var_id == "base":
                    continue
                
                # Validation: do not compare differing/unrelated scenarios
                var_manifest_obj = next((m for m in variant_manifests if m.variant_id == var_id), None)
                base_manifest_obj = next((m for m in variant_manifests if m.variant_id == "base"), None)
                if var_manifest_obj and base_manifest_obj:
                    if var_manifest_obj.base_scenario_id != base_manifest_obj.base_scenario_id:
                        logger.warning(f"Skipping balance comparison between variants with mismatched scenarios: {var_id} vs base")
                        continue

                # Filter rule metamorphic results relevant to this variant
                filtered_meta = [
                    r for r in metamorphic_results
                    if r.rule_id in [
                        rel.id for rel in mutation_spec.expected_relationships
                        if rel.compared_variant == var_id or (
                            any(
                                m.variant_id == var_id and rel.compared_variant in m.applied_mutations
                                for m in variant_manifests
                            )
                        )
                    ]
                ]

                report = BalanceComparisonEngine.compare(
                    baseline_metrics=base_metrics,
                    mutated_metrics=var_m,
                    metamorphic_results=filtered_meta
                )
                balance_comparison_reports[var_id] = report

        # Write balance comparisons JSON
        with open(analysis_dir / "balance_comparison.json", "w", encoding="utf-8") as f:
            json.dump({var_id: rep.model_dump() for var_id, rep in balance_comparison_reports.items()}, f, indent=2)


        # Calculate metrics costs
        ended_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        total_duration = time.time() - start_time
        storage_footprint = self._calculate_directory_size_mb(mutation_lab_dir)

        # 10. Central Mutation Lab Manifest
        variants_summary = {}
        for var_manifest in variant_manifests:
            var_id = var_manifest.variant_id
            status_str = "VALIDATED" if var_manifest.status == "VALIDATED" else "FAILED"
            if var_id in variant_run_results:
                status_str = variant_run_results[var_id]["status"]
            variants_summary[var_id] = status_str

        cost_profile = {
            "runtime_seconds": round(total_duration, 2),
            "storage_footprint_mb": round(storage_footprint, 3),
            "event_volume": sum(
                res["manifest"].completed_run_count * ticks_per_run
                for res in variant_run_results.values()
                if "manifest" in res
            ),
            "analysis_time_seconds": round(time.time() - start_time - sum(
                res["manifest"].budgets.get("max_runtime_minutes", 0) * 60 if "manifest" in res else 0
                for res in variant_run_results.values()
            ), 2)
        }

        mutation_lab_manifest = {
            "mutation_lab_id": mutation_lab_id,
            "mutation_id": mutation_id,
            "experiment_id": experiment_id,
            "status": overall_status,
            "started_at": started_at,
            "ended_at": ended_at,
            "variants": variants_summary,
            "cost": cost_profile
        }

        with open(mutation_lab_dir / "mutation_lab_manifest.json", "w", encoding="utf-8") as f:
            json.dump(mutation_lab_manifest, f, indent=2)

        # 11. Consolidated Markdown Report
        self._write_mutation_lab_report(
            report_path=analysis_dir / "mutation_lab_report.md",
            manifest=mutation_lab_manifest,
            variant_metrics=variant_metrics,
            metamorphic_results=metamorphic_results,
            balance_reports=balance_comparison_reports
        )

        return mutation_lab_manifest

    def _extract_variant_metrics(self, variants_dir: Path, var_id: str) -> Optional[Dict[str, Any]]:
        """
        Averages standard metric telemetries over all completed seed run reports for a variant.
        """
        lab_run_dir = variants_dir / var_id / "lab_run"
        manifest_path = lab_run_dir / "lab_run_manifest.json"
        if not manifest_path.is_file():
            return None

        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest_data = json.load(f)
        except Exception:
            return None

        runs_dir = lab_run_dir / "runs"
        if not runs_dir.is_dir():
            return None

        completed_reports = []
        for run_dir in runs_dir.iterdir():
            if run_dir.is_dir():
                report_path = run_dir / "run_report.json"
                if report_path.is_file():
                    try:
                        with open(report_path, "r", encoding="utf-8") as f:
                            completed_reports.append(json.load(f))
                    except Exception:
                        pass

        if not completed_reports:
            # Fallback to general statistics from manifest
            return {
                "health_score": manifest_data.get("average_health_score", 100.0),
                "run_count": manifest_data.get("completed_run_count", 0)
            }

        # Accumulate metrics
        metrics = {
            "health_score": [],
            "hard_law_violations": [],
            "critical_anomalies": [],
            "stuck_ratio": [],
            "resource_production": [],
            "quest_completion": [],
            "combat_resolution": [],
            "runtime_performance": [],
            "memory_usage": [],
            "event_volume": []
        }

        for r in completed_reports:
            metrics["health_score"].append(r.get("health_score", 100.0))
            metrics["hard_law_violations"].append(r.get("hard_law_violations", r.get("hard_law_violation_count", 0)))
            metrics["critical_anomalies"].append(r.get("critical_count", r.get("critical_anomalies", 0)))
            metrics["stuck_ratio"].append(r.get("stuck_ratio", r.get("stuck_entity_ratio", 0.0)))
            metrics["resource_production"].append(r.get("resource_production", r.get("resource_production_rate", 0.0)))
            metrics["quest_completion"].append(r.get("quest_completion", r.get("quest_completion_rate", 0.0)))
            metrics["combat_resolution"].append(r.get("combat_resolution", 0.0))
            metrics["runtime_performance"].append(r.get("runtime_performance", 0.0))
            metrics["memory_usage"].append(r.get("memory_usage", r.get("memory_usage_mb", 0.0)))
            metrics["event_volume"].append(r.get("event_volume", 0.0))

        averaged_metrics = {}
        for k, values in metrics.items():
            if values:
                averaged_metrics[k] = sum(values) / len(values)
            else:
                averaged_metrics[k] = 0.0

        averaged_metrics["run_count"] = len(completed_reports)
        return averaged_metrics

    def _calculate_directory_size_mb(self, directory: Path) -> float:
        total_bytes = 0
        if directory.is_dir():
            for p in directory.rglob("*"):
                if p.is_file():
                    try:
                        total_bytes += p.stat().st_size
                    except Exception:
                        pass
        return round(total_bytes / (1024 * 1024), 3)

    def _write_mutation_lab_report(
        self,
        report_path: Path,
        manifest: Dict[str, Any],
        variant_metrics: Dict[str, Dict[str, Any]],
        metamorphic_results: List[MetamorphicComparisonResult],
        balance_reports: Dict[str, BalanceComparisonReport]
    ) -> None:
        """
        Saves a gorgeous consolidated Markdown sweep report.
        """
        status_badge = (
            "🟢 **COMPLETED**" if manifest["status"] == "COMPLETED"
            else "🟡 **PARTIAL**" if manifest["status"] == "PARTIAL"
            else "🔴 **FAILED**"
        )

        with open(report_path, "w", encoding="utf-8") as f:
            f.write(f"# Mutation and Balance Lab Sweeps — {manifest['mutation_lab_id']}\n\n")
            f.write(f"> [!NOTE]\n> **Execution Summary:** end-to-end balance sweep completes with overall status {status_badge}.\n\n")

            f.write("## 📊 Sweep Manifest Details\n\n")
            f.write(f"- **Mutation Matrix Sweep ID**: `{manifest['mutation_id']}`\n")
            f.write(f"- **Experiment Setup ID**: `{manifest['experiment_id']}`\n")
            f.write(f"- **Started At**: `{manifest['started_at']}`\n")
            f.write(f"- **Ended At**: `{manifest['ended_at']}`\n")
            f.write(f"- **Run Duration**: `{manifest['cost']['runtime_seconds']:.2f} seconds`\n")
            f.write(f"- **Storage foot-print**: `{manifest['cost']['storage_footprint_mb']:.2f} MB`\n\n")

            f.write("## 🎛️ Variant Sweep Registry Status\n\n")
            f.write("| Variant ID | Status | Metric Seed Count |\n")
            f.write("| :--- | :--- | :--- |\n")
            for var_id, v_status in sorted(manifest["variants"].items()):
                m_count = variant_metrics.get(var_id, {}).get("run_count", 0) if v_status != "FAILED" else 0
                badge = (
                    "🟢 COMPLETED" if v_status == "COMPLETED"
                    else "🟡 PARTIAL" if v_status == "PARTIAL"
                    else "🔴 FAILED/INVALID"
                )
                f.write(f"| `{var_id}` | {badge} | `{m_count}` |\n")
            f.write("\n")

            f.write("## 🔬 Metamorphic Assertions validation\n\n")
            if not metamorphic_results:
                f.write("⚪ *No metamorphic rules were executed for this sweep.*\n\n")
            else:
                f.write("| Rule Assertion ID | Metric Dimension | Baseline Variant | Compared Variant | Status | Metamorphic Value Delta |\n")
                f.write("| :--- | :--- | :--- | :--- | :--- | :--- |\n")
                for r in metamorphic_results:
                    p_badge = "🟢 PASSED" if r.status == "PASSED" else "🔴 FAILED" if r.status == "FAILED" else "➖ INSUFFICIENT"
                    weak_indicator = " ⚠️ (Weak Evidence)" if r.weak_evidence else ""
                    delta = r.compared_value - r.baseline_value if (r.compared_value is not None and r.baseline_value is not None) else 0.0
                    f.write(f"| `{r.rule_id}` | `{r.message}` | `{r.baseline_value:.2f}` | `{r.compared_value:.2f}` | {p_badge}{weak_indicator} | `{delta:+.2f}` |\n")
                f.write("\n")

            f.write("## ⚖️ Differential Balance Scorecard comparison\n\n")
            if not balance_reports:
                f.write("⚪ *No differential scorecards could be generated.*\n\n")
            else:
                for var_id, r in sorted(balance_reports.items()):
                    c_badge = (
                        "🟢 **IMPROVED**" if r.status == "IMPROVED"
                        else "🔴 **REGRESSED**" if r.status == "REGRESSED"
                        else "🟡 **MIXED**" if r.status == "MIXED"
                        else "⚪ **UNCHANGED**" if r.status == "UNCHANGED"
                        else "➖ **INSUFFICIENT**"
                    )
                    f.write(f"### Variant: `{var_id}` (Status: {c_badge})\n\n")
                    f.write(f"> **Correlative Analysis:** {r.explanation}\n\n")
                    f.write("| Dimension Metric Name | Baseline Value | Compared Value | Delta Shift |\n")
                    f.write("| :--- | :--- | :--- | :--- |\n")
                    for metric, d in sorted(r.evidence.items()):
                        sign = "+" if d["shift"] > 0 else ""
                        f.write(f"| `{metric}` | `{d['baseline']:.2f}` | `{d['compared']:.2f}` | `{sign}{d['shift']:.2f}` |\n")
                    f.write("\n")
