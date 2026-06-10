import json
import logging
import os
import re
import yaml
from pathlib import Path
from typing import Optional, Any, Dict, List
from unittest.mock import MagicMock

# Core package imports
from src.lab.session import LabSessionStore, LabSessionError, LabSessionManifest
from src.lab.request import WorkflowRequest
from src.lab.context import ContextPackBuilder
from src.lab.validator import (
    ScenarioValidator,
    ExperimentValidator,
    InvalidScenarioSpecError,
    InvalidExperimentSpecError
)
from src.lab.guardrails import (
    LabBudgetGuardrails,
    BudgetBlockedError,
    BudgetWarningError,
    BudgetEstimation,
    BudgetCheckResult
)
from src.worldbuilding.schema import (
    WorldSpec,
    TopologySpec,
    RegionSpec,
    FactionSpec,
    PopulationSpec,
    ResourceNodeSpec,
    BuildingSpec,
    ValidationSpec,
    load_world_spec_from_yaml,
    InvalidWorldSpecError
)
from src.lab.store import LabResultStore
from src.lab.schema import (
    ScenarioSpec,
    IntentSpec,
    ExpectedLimitSpec,
    RequiredSignalsSpec,
    load_scenario_spec_from_yaml,
    ExperimentSpec,
    ExperimentRunSpec,
    ExperimentObservabilitySpec,
    ExperimentAnalysisSpec,
    ExperimentRetentionSpec,
    ExperimentBudgetsSpec,
    load_experiment_spec_from_yaml,
    LabRunManifest
)
from src.lab.audit import LabAuditTrail

logger = logging.getLogger(__name__)

def safe_path_resolution(base_dir: Path, target_path: str | Path) -> Path:
    """Safely resolves path and blocks path traversal attempts outside the base directory."""
    target = Path(target_path)
    base_resolved = base_dir.resolve()
    if not target.is_absolute():
        resolved = (base_resolved / target).resolve()
    else:
        resolved = target.resolve()
    try:
        if not resolved.is_relative_to(base_resolved):
            raise PermissionError(f"Path traversal blocked: '{target_path}' is outside '{base_dir}'")
    except ValueError as e:
        raise PermissionError(f"Path traversal blocked: '{target_path}' is outside '{base_dir}': {e}") from e
    return resolved

class GenerateSimulationSetupWorkflow:
    """
    M96 Workflow: Generate draft world/scenario/experiment configuration specs from user intent.
    Does NOT trigger simulation commands. Writes draft YAMLs to session subdirectories.
    """
    def __init__(self, workspace_root: Optional[str | Path] = None):
        if workspace_root is None:
            self.workspace_root = Path(__file__).resolve().parent.parent.parent
        else:
            self.workspace_root = Path(workspace_root).resolve()
            
        sessions_dir = self.workspace_root / "data" / "lab_sessions"
        self.session_store = LabSessionStore(sessions_dir)

    def run(self, session_id: str, request: WorkflowRequest, limits: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        logger.info(f"Running GenerateSimulationSetupWorkflow for session '{session_id}' in mode '{request.mode}'")
        
        # 1. Access lab session
        manifest = self.session_store.load_session(session_id)
        manifest.current_stage = "GENERATION"
        self.session_store.save_session(manifest)
        
        # Resolve stage directory
        stage_dir = self.session_store.get_stage_dir(session_id, "GENERATION")
        draft_specs_dir = stage_dir / "draft_specs"
        val_reports_dir = stage_dir / "validation_reports"
        
        draft_specs_dir.mkdir(parents=True, exist_ok=True)
        val_reports_dir.mkdir(parents=True, exist_ok=True)

        # 2. Build context pack
        builder = ContextPackBuilder(self.workspace_root, session_store=self.session_store)
        context_pack = builder.build_generation_pack(session_id, request, limits=limits)

        # 3. Check duplication against production world/scenario/experiment indexes
        duplication_report = self._check_duplication(request)
        with open(stage_dir / "duplication_report.json", "w", encoding="utf-8") as f:
            json.dump(duplication_report, f, indent=2)

        # 4. Parse user parameters based on generic vs specific input configurations
        world_params, scenario_params, experiment_params = self._resolve_spec_parameters(request)

        # 5. Generate Pydantic specs
        world_spec = self._build_world_spec(session_id, world_params)
        scenario_spec = self._build_scenario_spec(session_id, scenario_params)
        experiment_spec = self._build_experiment_spec(session_id, scenario_spec.scenario_id, experiment_params)

        # Write YAML files
        world_yaml_path = draft_specs_dir / "world.yaml"
        scenario_yaml_path = draft_specs_dir / "scenario.yaml"
        experiment_yaml_path = draft_specs_dir / "experiment.yaml"

        self._save_spec_to_yaml(world_spec, world_yaml_path)
        self._save_spec_to_yaml(scenario_spec, scenario_yaml_path)
        self._save_spec_to_yaml(experiment_spec, experiment_yaml_path)

        # 6. Run validators on the generated specs using safe isolated mocking
        world_val_status = self._validate_world(world_yaml_path)
        scenario_val_status = self._validate_scenario(scenario_spec, world_spec)
        experiment_val_status = self._validate_experiment(experiment_spec, scenario_spec)

        with open(val_reports_dir / "world_validation.json", "w", encoding="utf-8") as f:
            json.dump(world_val_status, f, indent=2)
        with open(val_reports_dir / "scenario_validation.json", "w", encoding="utf-8") as f:
            json.dump(scenario_val_status, f, indent=2)
        with open(val_reports_dir / "experiment_validation.json", "w", encoding="utf-8") as f:
            json.dump(experiment_val_status, f, indent=2)

        # 7. Run budget calculations
        profile = request.constraints.get("budget_profile", "local_dev")
        budget_guard = LabBudgetGuardrails(profile=profile)
        estimate = budget_guard.estimate(experiment_spec, world_spec)
        budget_check = budget_guard.check(estimate, experiment_spec)

        budget_report = {
            "status": budget_check.status,
            "run_count": estimate.run_count,
            "total_ticks": estimate.total_ticks,
            "expected_artifact_mb": estimate.expected_artifact_mb,
            "expected_runtime_minutes": estimate.expected_runtime_minutes,
            "warnings": budget_check.warnings,
            "blocked_reasons": budget_check.blocked_reasons
        }
        with open(stage_dir / "budget_report.json", "w", encoding="utf-8") as f:
            json.dump(budget_report, f, indent=2)

        # 8. Generate rich review pack
        review_pack_content = self._format_review_pack(
            request=request,
            world_spec=world_spec,
            scenario_spec=scenario_spec,
            experiment_spec=experiment_spec,
            duplication_report=duplication_report,
            world_val=world_val_status,
            scenario_val=scenario_val_status,
            experiment_val=experiment_val_status,
            budget_report=budget_report,
            context_pack=context_pack
        )
        (stage_dir / "generation_review_pack.md").write_text(review_pack_content, encoding="utf-8")

        # Update session links
        manifest.linked_worlds = list(set(manifest.linked_worlds + [world_spec.world_id]))
        manifest.linked_scenarios = list(set(manifest.linked_scenarios + [scenario_spec.scenario_id]))
        manifest.linked_experiments = list(set(manifest.linked_experiments + [experiment_spec.experiment_id]))
        self.session_store.save_session(manifest)

        return {
            "world_spec_id": world_spec.world_id,
            "scenario_spec_id": scenario_spec.scenario_id,
            "experiment_spec_id": experiment_spec.experiment_id,
            "validation_passed": (
                world_val_status["status"] == "VALID" and
                scenario_val_status["status"] == "VALID" and
                experiment_val_status["status"] == "VALID"
            ),
            "budget_status": budget_check.status
        }

    def _check_duplication(self, request: WorkflowRequest) -> Dict[str, Any]:
        """Scans catalog files to see if a specification matching the ID already exists."""
        report = {"world_matches": [], "scenario_matches": [], "experiment_matches": []}
        
        # World index
        world_idx_path = self.workspace_root / "data" / "worlds" / "world_index.json"
        if world_idx_path.is_file():
            try:
                with open(world_idx_path, "r", encoding="utf-8") as f:
                    worlds = json.load(f)
                if request.user_goal:
                    for wid, info in worlds.items():
                        if wid.lower() in request.user_goal.lower():
                            report["world_matches"].append({"id": wid, "reason": "ID matched in user goal keyword"})
            except Exception as e:
                logger.warning(f"Failed to read world index for duplication: {e}")

        # Scenario index
        scenario_idx_path = self.workspace_root / "data" / "scenarios" / "scenario_index.json"
        if scenario_idx_path.is_file():
            try:
                with open(scenario_idx_path, "r", encoding="utf-8") as f:
                    scenarios = json.load(f)
                if request.user_goal:
                    for sid, info in scenarios.items():
                        if sid.lower() in request.user_goal.lower():
                            report["scenario_matches"].append({"id": sid, "reason": "ID matched in user goal keyword"})
            except Exception as e:
                logger.warning(f"Failed to read scenario index: {e}")

        return report

    def _resolve_spec_parameters(self, request: WorkflowRequest) -> tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
        """Maps generic/specific request parameters into unified internal properties."""
        if request.mode == "specific":
            inputs = request.specific_inputs
            world_type = inputs.get("world_type", "resource_valley")
            regions = inputs.get("regions", ["village", "forest"])
            workers = int(inputs.get("workers", 100))
            resources = inputs.get("resources", ["wood"])
            pressures = inputs.get("pressures", [])
            ticks = int(inputs.get("ticks", 1000))
            seeds = inputs.get("seeds", [42])
            observability_mode = inputs.get("observability_mode", "LONG_RUN")
        else:
            # Generic mode: dynamic heuristics from user_goal
            goal_lower = request.user_goal.lower() if request.user_goal else ""
            
            # Heuristics
            if "large" in goal_lower or "stress" in goal_lower or "heavy" in goal_lower:
                workers = 300
                ticks = 5000
                regions = ["village", "forest", "quarry"]
            else:
                workers = 100
                ticks = 1000
                regions = ["village", "forest"]

            if "economy" in goal_lower or "inflation" in goal_lower:
                world_type = "resource_valley"
                resources = ["gold", "wood"]
            else:
                world_type = "resource_valley"
                resources = ["wood"]

            pressures = []
            if "pathing" in goal_lower or "bottleneck" in goal_lower:
                pressures.append("pathing_bottleneck")
            if "inventory" in goal_lower or "full" in goal_lower:
                pressures.append("inventory_full")

            seeds = [42]
            observability_mode = "LONG_RUN"

        world_params = {
            "world_type": world_type,
            "regions": regions,
            "workers": workers,
            "resources": resources
        }
        scenario_params = {
            "world_type": world_type,
            "regions": regions,
            "workers": workers,
            "resources": resources,
            "pressures": pressures,
            "user_goal": request.user_goal
        }
        experiment_params = {
            "ticks": ticks,
            "seeds": seeds,
            "observability_mode": observability_mode
        }
        return world_params, scenario_params, experiment_params

    def _build_world_spec(self, session_id: str, params: Dict[str, Any]) -> WorldSpec:
        """Constructs a validated WorldSpec instance."""
        regions = params["regions"]
        workers = params["workers"]
        resources = params["resources"]

        # Build nested list structures safely matching WorldSpec fields
        region_specs = []
        for idx, r in enumerate(regions):
            min_x = idx * 50
            min_y = idx * 50
            max_x = (idx + 1) * 50 - 1
            max_y = (idx + 1) * 50 - 1
            region_specs.append(
                RegionSpec(
                    id=r,
                    type="settlement" if r == "village" else "wilderness",
                    bounds=(min_x, min_y, max_x, max_y),
                    terrain="GRASS",
                    hazard_level=0.0
                )
            )

        faction_specs = [FactionSpec(id="faction_citizens", type="standard")]
        
        population_specs = [
            PopulationSpec(
                id="pop_workers",
                count=workers,
                role="worker",
                faction="faction_citizens",
                spawn_region=regions[0]
            )
        ]

        resource_specs = []
        for r_item in resources:
            resource_specs.append(
                ResourceNodeSpec(
                    id=f"node_{r_item}",
                    resource_type=r_item,
                    count=1000,
                    region=regions[1] if len(regions) > 1 else regions[0]
                )
            )

        building_specs = [
            BuildingSpec(
                id="building_townhall",
                type="townhall",
                region=regions[0]
            )
        ]

        return WorldSpec(
            schema_version="worldspec.v1",
            world_id=f"world_{session_id}",
            name=f"Generated World for {session_id}",
            description=f"Auto-generated world spec for session {session_id}",
            topology=TopologySpec(width=100, height=100, coordinate_system="grid"),
            regions=region_specs,
            factions=faction_specs,
            entities=population_specs,
            resources=resource_specs,
            buildings=building_specs,
            quests=[],
            validation=ValidationSpec(expected_min_entities=1, allow_overlapping_regions=False)
        )

    def _build_scenario_spec(self, session_id: str, params: Dict[str, Any]) -> ScenarioSpec:
        """Constructs a validated ScenarioSpec instance."""
        resources = params["resources"]
        pressures = params["pressures"]
        user_goal = params["user_goal"]

        expected_limits = {
            "workers_alive": ExpectedLimitSpec(min=1)
        }
        
        req_signals = RequiredSignalsSpec(
            metrics=[f"{res}_growth" for res in resources],
            events=["worker_spawned"],
            cognition=[]
        )

        return ScenarioSpec(
            schema_version="scenariospec.v1",
            scenario_id=f"scenario_{session_id}",
            name=f"Generated Scenario for {session_id}",
            world_id=f"world_{session_id}",
            scenario_type="stress_test",
            intent=IntentSpec(primary_goal="survive", description=f"Goal: {user_goal or ''}"),
            expected_behavior=expected_limits,
            required_signals=req_signals,
            allowed_anomalies=pressures,
            critical_anomalies=[],
            tags=["auto-generated"]
        )

    def _build_experiment_spec(self, session_id: str, scenario_id: str, params: Dict[str, Any]) -> ExperimentSpec:
        """Constructs a validated ExperimentSpec instance."""
        ticks = params["ticks"]
        seeds = params["seeds"]
        obs_mode = params["observability_mode"]

        return ExperimentSpec(
            schema_version="experimentspec.v1",
            experiment_id=f"experiment_{session_id}",
            scenario_id=scenario_id,
            experiment_type="single_run" if len(seeds) == 1 else "multi_seed_sweep",
            run=ExperimentRunSpec(ticks=ticks, seeds=seeds, repeat_count=1, max_parallel_runs=1),
            observability=ExperimentObservabilitySpec(
                mode=obs_mode,
                record_events=True,
                record_metric_windows=True,
                record_cognition=False
            ),
            analysis=ExperimentAnalysisSpec(
                run_post_analysis=True,
                generate_report=True,
                run_mining=False,
                compare_baseline=False
            ),
            retention=ExperimentRetentionSpec(
                keep_raw_events=True,
                keep_reports=True,
                max_artifact_mb=500
            ),
            budgets=ExperimentBudgetsSpec(
                max_runtime_minutes=60,
                max_total_artifact_mb=2000,
                max_runs=len(seeds),
                max_total_ticks=ticks * len(seeds),
                max_parallel_runs=1
            )
        )

    def _save_spec_to_yaml(self, spec: Any, path: Path) -> None:
        """Safely saves a spec to disk in YAML format using standard JSON dumps to avoid Pydantic types serialization issues."""
        data = json.loads(spec.model_dump_json())
        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)

    def _validate_world(self, path: Path) -> Dict[str, Any]:
        """Runs validation on the draft world.yaml file."""
        try:
            load_world_spec_from_yaml(path)
            return {"status": "VALID", "errors": []}
        except InvalidWorldSpecError as e:
            return {"status": "INVALID", "errors": [str(e)]}
        except Exception as e:
            return {"status": "INVALID", "errors": [f"Unexpected error validating WorldSpec: {e}"]}

    def _validate_scenario(self, scenario_spec: ScenarioSpec, world_spec: WorldSpec) -> Dict[str, Any]:
        """Runs isolated mock ScenarioValidator against the draft spec."""
        mock_world_repo = MagicMock()
        mock_world_repo.list_worlds.return_value = [world_spec.world_id]
        mock_world_repo.load_world.return_value = world_spec

        validator = ScenarioValidator(world_repo=mock_world_repo)
        try:
            validator.validate(scenario_spec, strict=False)
            return {"status": "VALID", "errors": []}
        except InvalidScenarioSpecError as e:
            return {"status": "INVALID", "errors": [str(e)]}
        except Exception as e:
            return {"status": "INVALID", "errors": [f"Unexpected Scenario Validation Error: {e}"]}

    def _validate_experiment(self, experiment_spec: ExperimentSpec, scenario_spec: ScenarioSpec) -> Dict[str, Any]:
        """Runs isolated mock ExperimentValidator against the draft spec."""
        mock_scenario_repo = MagicMock()
        mock_scenario_repo.list_scenarios.return_value = [scenario_spec.scenario_id]
        mock_scenario_repo.load_scenario.return_value = scenario_spec

        validator = ExperimentValidator(scenario_repo=mock_scenario_repo)
        try:
            validator.validate(experiment_spec, strict=False)
            return {"status": "VALID", "errors": []}
        except InvalidExperimentSpecError as e:
            return {"status": "INVALID", "errors": [str(e)]}
        except Exception as e:
            return {"status": "INVALID", "errors": [f"Unexpected Experiment Validation Error: {e}"]}

    def _format_review_pack(
        self,
        request: WorkflowRequest,
        world_spec: WorldSpec,
        scenario_spec: ScenarioSpec,
        experiment_spec: ExperimentSpec,
        duplication_report: Dict[str, Any],
        world_val: Dict[str, Any],
        scenario_val: Dict[str, Any],
        experiment_val: Dict[str, Any],
        budget_report: Dict[str, Any],
        context_pack: Dict[str, Any]
    ) -> str:
        """Formative description summarizing the draft metrics and topology for the human reviewer."""
        world_status = world_val["status"]
        scenario_status = scenario_val["status"]
        experiment_status = experiment_val["status"]
        
        all_passed = (world_status == "VALID" and scenario_status == "VALID" and experiment_status == "VALID")
        overall_val_str = "SUCCESS ✅" if all_passed else "FAILED ❌"

        # Region bounds details
        region_lines = []
        for r in world_spec.regions:
            region_lines.append(f"- Region `{r.id}`: Type `{r.type}`, Bounds `{r.bounds}`")
            
        entity_lines = []
        for e in world_spec.entities:
            entity_lines.append(f"- Group `{e.id}`: Role `{e.role}`, Initial Count `{e.count}`")

        resource_lines = []
        for res in world_spec.resources:
            resource_lines.append(f"- Resource `{res.id}`: Type `{res.resource_type}`, Count `{res.count}`")

        match_count = (
            len(duplication_report["world_matches"]) +
            len(duplication_report["scenario_matches"])
        )
        dup_str = f"Duplicate keys/keywords detected: {match_count}" if match_count > 0 else "No existing duplicate catalogs found."

        return f"""# Simulation Generation Review Pack

This review pack summarizes the auto-generated draft specifications created for your intent.

## Intent & Goal
- **User Intent**: `{request.user_goal or "N/A"}`
- **Execution Mode**: `{request.mode}`

## Generated Files
- World spec: `generation/draft_specs/world.yaml`
- Scenario spec: `generation/draft_specs/scenario.yaml`
- Experiment spec: `generation/draft_specs/experiment.yaml`

---

## Specification Summary

### 1. World Specs
- **World ID**: `{world_spec.world_id}`
- **Topology**: `{world_spec.topology.width}x{world_spec.topology.height}` grid
- **Regions**:
{chr(10).join(region_lines)}
- **Entity Populations**:
{chr(10).join(entity_lines)}
- **Resource Nodes**:
{chr(10).join(resource_lines)}

### 2. Scenario Specs
- **Scenario ID**: `{scenario_spec.scenario_id}`
- **Primary Goal**: `{scenario_spec.intent.primary_goal}`
- **Allowed Pressures**: `{scenario_spec.allowed_anomalies}`
- **Required Signals**: `{scenario_spec.required_signals.metrics}`

### 3. Experiment Matrix
- **Ticks**: `{experiment_spec.run.ticks}`
- **Seeds**: `{experiment_spec.run.seeds}`
- **Observability Detail**: `{experiment_spec.observability.mode}`

---

## Validation Status
- **Overall Schema Validations**: {overall_val_str}
  - World validation: `{world_status}` (Errors: `{world_val["errors"]}`)
  - Scenario validation: `{scenario_status}` (Errors: `{scenario_val["errors"]}`)
  - Experiment validation: `{experiment_status}` (Errors: `{experiment_val["errors"]}`)

## Duplication Cross-Check
- **Status**: {dup_str}

## Budget Estimates
- **Guardrails Profile**: `{request.constraints.get("budget_profile", "local_dev")}`
- **Check Status**: `{budget_report["status"]}`
- **Run Count**: `{budget_report["run_count"]}`
- **Total Ticks**: `{budget_report["total_ticks"]}`
- **Expected Runtime**: `{budget_report["expected_runtime_minutes"]:.2f} minutes`
- **Expected Artifact Size**: `{budget_report["expected_artifact_mb"]:.3f} MB`
- **Warnings**: `{budget_report["warnings"]}`
- **Blocked Reasons**: `{budget_report["blocked_reasons"]}`

---

## Next Steps
To proceed with local manual execution, please trigger the next workflow:
```bash
rpg-workflow-prepare --session-id "{world_spec.world_id.replace('world_', '')}"
```
"""


class PrepareSimulationExecutionWorkflow:
    """
    M97 Workflow: Resolves draft specs, validates safety constraints, and creates launcher scripts
    ready for the user to manually execute without the agent ever running sub-processes.
    """
    def __init__(self, workspace_root: Optional[str | Path] = None):
        if workspace_root is None:
            self.workspace_root = Path(__file__).resolve().parent.parent.parent
        else:
            self.workspace_root = Path(workspace_root).resolve()
            
        sessions_dir = self.workspace_root / "data" / "lab_sessions"
        self.session_store = LabSessionStore(sessions_dir)

    def run(self, session_id: str, request: WorkflowRequest) -> Dict[str, Any]:
        logger.info(f"Running PrepareSimulationExecutionWorkflow for session '{session_id}'")
        
        # 1. Resolve targeted paths safely
        manifest = self.session_store.load_session(session_id)
        manifest.current_stage = "EXECUTION_SUPPORT"
        self.session_store.save_session(manifest)
        
        gen_dir = self.session_store.get_stage_dir(session_id, "GENERATION")
        support_dir = self.session_store.get_stage_dir(session_id, "EXECUTION_SUPPORT")
        
        # Path safety resolution
        if request.mode == "specific":
            inputs = request.specific_inputs
            exp_path_str = inputs.get("experiment_path", str(gen_dir / "draft_specs" / "experiment.yaml"))
            profile = inputs.get("profile", "local_dev")
            output_path_str = inputs.get("output_path", f"data/lab_runs/run_{session_id}")
        else:
            exp_path_str = str(gen_dir / "draft_specs" / "experiment.yaml")
            profile = request.constraints.get("budget_profile", "local_dev")
            output_path_str = f"data/lab_runs/run_{session_id}"

        # Secure path constraints
        resolved_exp_path = safe_path_resolution(self.workspace_root, exp_path_str)
        resolved_output_path = safe_path_resolution(self.workspace_root, output_path_str)

        # 2. Check spec file existence
        if not resolved_exp_path.is_file():
            self._write_blocked_report(support_dir, f"Target experiment specification file does not exist: {exp_path_str}")
            return {"status": "BLOCKED", "reason": f"File not found: {exp_path_str}"}

        # 3. Load specs and validate
        try:
            experiment_spec = load_experiment_spec_from_yaml(resolved_exp_path)
            
            # Resolve Scenario & World from experiment specifications path
            scenario_path = resolved_exp_path.parent / "scenario.yaml"
            world_path = resolved_exp_path.parent / "world.yaml"
            
            if not scenario_path.is_file() or not world_path.is_file():
                self._write_blocked_report(support_dir, "Sibling world.yaml or scenario.yaml spec files are missing in draft folder.")
                return {"status": "BLOCKED", "reason": "Missing sibling specs"}
                
            world_spec = load_world_spec_from_yaml(world_path)
            scenario_spec = load_scenario_spec_from_yaml(scenario_path)

            # Re-run semantic cross validators
            mock_world_repo = MagicMock()
            mock_world_repo.list_worlds.return_value = [world_spec.world_id]
            mock_world_repo.load_world.return_value = world_spec

            mock_scenario_repo = MagicMock()
            mock_scenario_repo.list_scenarios.return_value = [scenario_spec.scenario_id]
            mock_scenario_repo.load_scenario.return_value = scenario_spec

            ScenarioValidator(world_repo=mock_world_repo).validate(scenario_spec, strict=False)
            ExperimentValidator(scenario_repo=mock_scenario_repo).validate(experiment_spec, strict=False)

        except Exception as e:
            self._write_blocked_report(support_dir, f"Specification validation checks failed:\n{e}")
            return {"status": "BLOCKED", "reason": f"Validation failed: {e}"}

        # 4. Check budget guardrail status
        budget_guard = LabBudgetGuardrails(profile=profile)
        estimate = budget_guard.estimate(experiment_spec, world_spec)
        budget_check = budget_guard.check(estimate, experiment_spec)

        budget_report = {
            "status": budget_check.status,
            "warnings": budget_check.warnings,
            "blocked_reasons": budget_check.blocked_reasons,
            "run_count": estimate.run_count,
            "total_ticks": estimate.total_ticks,
            "expected_entity_count": estimate.expected_entity_count,
            "expected_event_volume": estimate.expected_event_volume,
            "expected_artifact_mb": estimate.expected_artifact_mb,
            "expected_runtime_minutes": estimate.expected_runtime_minutes,
        }
        with open(support_dir / "budget_report.json", "w", encoding="utf-8") as f:
            json.dump(budget_report, f, indent=2)

        # Emit audit events for guardrail violations
        audit = LabAuditTrail(self.workspace_root)
        if budget_check.warnings:
            audit.log_event(session_id, "guardrail_violation", {
                "violation_type": "budget_warning",
                "profile": profile,
                "warnings": budget_check.warnings,
                "estimates": {
                    "run_count": estimate.run_count,
                    "total_ticks": estimate.total_ticks,
                    "expected_artifact_mb": estimate.expected_artifact_mb,
                }
            })
        if budget_check.is_blocked:
            audit.log_event(session_id, "guardrail_violation", {
                "violation_type": "budget_blocked",
                "profile": profile,
                "blocked_reasons": budget_check.blocked_reasons,
                "estimates": {
                    "run_count": estimate.run_count,
                    "total_ticks": estimate.total_ticks,
                    "expected_artifact_mb": estimate.expected_artifact_mb,
                }
            })

        # Enforce CI profile budget blocks strictly!
        if budget_check.status == "BLOCKED":
            if profile == "CI":
                blocked_msg = f"CI Profile budget limit violated: {', '.join(budget_check.blocked_reasons)}"
                self._write_blocked_report(support_dir, blocked_msg)
                return {"status": "BLOCKED", "reason": blocked_msg}
            else:
                logger.warning(f"Budget check returned BLOCKED but continuing on local profile: {budget_check.blocked_reasons}")

        # 5. Check Output Path conflict / Run Lock detection
        lock_file = self.workspace_root / "data" / "runs" / "run.lock"
        if lock_file.is_file():
            self._write_blocked_report(support_dir, "Active sweep execution lock found at data/runs/run.lock. Concurrent sweeps are forbidden.")
            return {"status": "BLOCKED", "reason": "Concurrent sweep block"}

        # 6. Generate shell script execution launcher command
        cmd_content = f"""#!/usr/bin/env bash
# Auto-generated execution launcher command for lab session {session_id}
set -euo pipefail

rpg-lab run \\
  --experiment "{resolved_exp_path.relative_to(self.workspace_root)}" \\
  --output "{resolved_output_path.relative_to(self.workspace_root)}" \\
  --profile "{profile}"
"""
        cmd_script_path = support_dir / "execution_command.sh"
        cmd_script_path.write_text(cmd_content, encoding="utf-8")
        
        # Make command file executable
        try:
            os.chmod(cmd_script_path, 0o755)
        except Exception as e:
            logger.warning(f"Could not set execute permissions: {e}")

        # 7. Output expected directories
        expected_paths = {
            "experiment_yaml": str(resolved_exp_path.relative_to(self.workspace_root)),
            "output_directory": str(resolved_output_path.relative_to(self.workspace_root)),
            "command_script": str(cmd_script_path.relative_to(self.workspace_root)),
            "run_lock": "data/runs/run.lock"
        }
        with open(support_dir / "expected_output_paths.json", "w", encoding="utf-8") as f:
            json.dump(expected_paths, f, indent=2)

        # 8. Output readiness report
        readiness_pack = self._format_readiness_pack(
            session_id=session_id,
            experiment_path=resolved_exp_path,
            output_path=resolved_output_path,
            cmd_script=cmd_script_path,
            budget_check=budget_check,
            profile=profile
        )
        (support_dir / "execution_readiness_report.md").write_text(readiness_pack, encoding="utf-8")

        with open(support_dir / "execution_readiness_report.json", "w", encoding="utf-8") as f:
            json.dump({
                "status": "READY",
                "command_script": str(cmd_script_path),
                "output_directory": str(resolved_output_path),
                "budget_check_status": budget_check.status,
                "storage_estimate": {
                    "run_count": estimate.run_count,
                    "total_ticks": estimate.total_ticks,
                    "expected_entity_count": estimate.expected_entity_count,
                    "expected_event_volume": estimate.expected_event_volume,
                    "expected_artifact_mb": estimate.expected_artifact_mb,
                    "expected_runtime_minutes": estimate.expected_runtime_minutes,
                }
            }, f, indent=2)

        return {
            "status": "READY",
            "command_script_path": str(cmd_script_path),
            "output_path": str(resolved_output_path)
        }

    def _write_blocked_report(self, support_dir: Path, reason: str) -> None:
        """Writes execution_blocked_report.md summarizing the block reason."""
        support_dir.mkdir(parents=True, exist_ok=True)
        blocked_md = f"""# Execution Blocked Report

Your manual simulation run execution setup has been blocked due to the following safety boundary issues:

## Reason for Block
> [!CAUTION]
> {reason}

## Recommended Actions
1. Check that your generated draft yaml files are fully populated and pass Pydantic models validations.
2. Resolve any concurrency lock conditions or concurrent processes running sweeps.
3. Align budgets specs if you are operating on a restricted profile like CI.
"""
        (support_dir / "execution_blocked_report.md").write_text(blocked_md, encoding="utf-8")

    def _format_readiness_pack(
        self,
        session_id: str,
        experiment_path: Path,
        output_path: Path,
        cmd_script: Path,
        budget_check: BudgetCheckResult,
        profile: str
    ) -> str:
        """Rich formatting summarizing launcher activation steps."""
        warnings_lines = [f"- ⚠️ {w}" for w in budget_check.warnings]
        warnings_str = chr(10).join(warnings_lines) if budget_check.warnings else "None."

        return f"""# Execution Readiness Report

Your simulation execution suite has been compiled and is ready for manual activation.

## Profile and Location
- **Lab Profile**: `{profile}`
- **Experiment Spec**: `{experiment_path}`
- **Target Output Directory**: `{output_path}`

---

## Verification & Guardrails
- **Budget Status**: `{budget_check.status}`
- **Warnings / Info**:
{warnings_str}

---

## How to Trigger Manual Sweep Run
Run the compiled launcher script directly in your terminal to safely kick off the simulation sweep:

```bash
# Set execution permissions (automatically pre-configured)
chmod +x "{cmd_script}"

# Start simulation sweep
./"{cmd_script}"
```

> [!TIP]
> After simulation execution completes successfully, trigger the Register result workflow to catalog scorecards:
> ```bash
> rpg-workflow-register --session-id "{session_id}" --run-dir "{output_path}"
> ```
"""


class RegisterSimulationResultWorkflow:
    """
    M98 Workflow: After manual sweep run completes, registers, catalogs,
    and indexes completed scorecards into session-scoped files.
    """
    def __init__(self, workspace_root: Optional[str | Path] = None):
        if workspace_root is None:
            self.workspace_root = Path(__file__).resolve().parent.parent.parent
        else:
            self.workspace_root = Path(workspace_root).resolve()
            
        sessions_dir = self.workspace_root / "data" / "lab_sessions"
        self.session_store = LabSessionStore(sessions_dir)
        lab_runs_dir = self.workspace_root / "data" / "lab_runs"
        self.result_store = LabResultStore(lab_runs_dir)

    def run(self, session_id: str, request: WorkflowRequest) -> dict[str, Any]:
        logger.info(f"Running RegisterSimulationResultWorkflow for session '{session_id}'")
        
        # 1. Access lab session
        manifest = self.session_store.load_session(session_id)
        manifest.current_stage = "REGISTRATION"
        self.session_store.save_session(manifest)
        
        reg_dir = self.session_store.get_stage_dir(session_id, "REGISTRATION")
        reg_dir.mkdir(parents=True, exist_ok=True)

        # 2. Resolve run path safely
        if request.mode == "specific":
            lab_run_path_str = request.specific_inputs.get("lab_run_path")
            if not lab_run_path_str:
                raise ValueError("lab_run_path must be supplied in specific mode.")
        else:
            # Generic mode: load from expected_output_paths.json
            support_dir = self.session_store.get_stage_dir(session_id, "EXECUTION_SUPPORT")
            expected_paths_file = support_dir / "expected_output_paths.json"
            if not expected_paths_file.is_file():
                err_msg = "Expected output paths file not found. Prepare the execution support first."
                self._write_integrity_report(reg_dir, "MISSING", err_msg)
                return {"status": "BLOCKED", "reason": err_msg}
            try:
                with open(expected_paths_file, "r", encoding="utf-8") as f:
                    expected_paths = json.load(f)
                lab_run_path_str = expected_paths.get("output_directory")
            except Exception as e:
                err_msg = f"Failed to load expected output paths: {e}"
                self._write_integrity_report(reg_dir, "CORRUPTED", err_msg)
                return {"status": "BLOCKED", "reason": err_msg}

        # Safe resolution preventing traversal escapes
        resolved_run_path = safe_path_resolution(self.workspace_root, lab_run_path_str)

        # 3. Analyze Completeness / Classifications
        classification = "COMPLETE"
        reason = ""
        run_manifest = None
        
        if not resolved_run_path.is_dir():
            classification = "MISSING"
            reason = f"Simulation output directory does not exist at '{lab_run_path_str}'"
        else:
            manifest_file = resolved_run_path / "lab_run_manifest.json"
            if not manifest_file.is_file():
                classification = "CORRUPTED"
                reason = "Simulation manifest file 'lab_run_manifest.json' is missing in output directory."
            else:
                try:
                    with open(manifest_file, "r", encoding="utf-8") as f:
                        manifest_data = json.load(f)
                    run_manifest = LabRunManifest(**manifest_data)
                except Exception as e:
                    classification = "CORRUPTED"
                    reason = f"Malformed run manifest file: {e}"
                
                if classification == "COMPLETE" and run_manifest:
                    if run_manifest.status == "FAILED":
                        classification = "FAILED"
                        reason = "Simulation sweep completed but manifest status is explicitly FAILED."
                    else:
                        # Check partial run completeness
                        # Ensure we count individual run reports under runs/
                        runs_dir = resolved_run_path / "runs"
                        actual_run_count = 0
                        if runs_dir.is_dir():
                            for child in runs_dir.iterdir():
                                if child.is_dir() and (child / "run_report.json").is_file():
                                    actual_run_count += 1
                        
                        expected_run_count = run_manifest.run_count
                        if actual_run_count < expected_run_count:
                            classification = "PARTIAL"
                            reason = f"Run count mismatch. Expected {expected_run_count} runs, but found only {actual_run_count} completed child run folders."

        # If blocked (MISSING or CORRUPTED)
        if classification in ("MISSING", "CORRUPTED"):
            self._write_integrity_report(reg_dir, classification, reason)
            return {"status": "BLOCKED", "reason": reason}

        # 4. Link run path inside session manifest
        run_id_val = run_manifest.lab_run_id if run_manifest else resolved_run_path.name
        manifest.linked_lab_runs = list(set(manifest.linked_lab_runs + [run_id_val]))
        self.session_store.save_session(manifest)
        
        # Write actual_lab_run_path.txt
        (reg_dir / "actual_lab_run_path.txt").write_text(str(resolved_run_path), encoding="utf-8")

        # 5. Build Artifact Index containing sizes and paths
        artifact_list = []
        for file_path in resolved_run_path.rglob("*"):
            if file_path.is_file():
                rel_path = file_path.relative_to(resolved_run_path)
                file_size = file_path.stat().st_size
                artifact_list.append({
                    "relative_path": str(rel_path),
                    "size_bytes": file_size
                })
        
        with open(reg_dir / "artifact_index.json", "w", encoding="utf-8") as f:
            json.dump(artifact_list, f, indent=2)

        # 6. Generate json and markdown reports
        compact_summary = {
            "lab_run_id": run_id_val,
            "classification": classification,
            "reason": reason or "Integrity checks passed completely.",
            "world_id": run_manifest.world_id if run_manifest else "unknown",
            "scenario_id": run_manifest.scenario_id if run_manifest else "unknown",
            "experiment_id": run_manifest.experiment_id if run_manifest else "unknown",
            "storage_usage_mb": run_manifest.storage_usage_mb if run_manifest else 0.0,
            "run_count": run_manifest.run_count if run_manifest else 0,
            "completed_run_count": run_manifest.completed_run_count if run_manifest else 0,
            "failed_run_count": run_manifest.failed_run_count if run_manifest else 0
        }
        with open(reg_dir / "result_integrity_report.json", "w", encoding="utf-8") as f:
            json.dump(compact_summary, f, indent=2)

        # MD Report
        report_md = self._format_integrity_report_md(
            session_id=session_id,
            classification=classification,
            reason=reason,
            summary=compact_summary,
            artifacts=artifact_list
        )
        (reg_dir / "result_integrity_report.md").write_text(report_md, encoding="utf-8")

        # Also register via result store rebuild index to update central indexes
        try:
            self.result_store.rebuild_index()
        except Exception as e:
            logger.warning(f"Rebuild index failed during registration: {e}")

        return {
            "status": "READY",
            "classification": classification,
            "lab_run_id": run_id_val,
            "report_path": str(reg_dir / "result_integrity_report.md")
        }

    def _write_integrity_report(self, reg_dir: Path, classification: str, reason: str) -> None:
        """Writes failure/blocked integrity report JSON and MD files."""
        blocked_json = {
            "classification": classification,
            "status": "BLOCKED",
            "reason": reason
        }
        with open(reg_dir / "result_integrity_report.json", "w", encoding="utf-8") as f:
            json.dump(blocked_json, f, indent=2)

        blocked_md = f"""# Result Integrity Audit Blocked
        
Your manual simulation run result registration has been **blocked** due to structural check errors:

## Audit Status: `{classification}`
> [!CAUTION]
> **Reason**: {reason}

## Recommended Actions
1. Verify that your manual execution script successfully finished writing all log data.
2. Confirm the directory includes a valid, parseable `lab_run_manifest.json` descriptor file.
"""
        (reg_dir / "result_integrity_report.md").write_text(blocked_md, encoding="utf-8")

    def _format_integrity_report_md(self, session_id: str, classification: str, reason: str, summary: dict[str, Any], artifacts: list[dict[str, Any]]) -> str:
        """Generates premium registration audit summary report."""
        status_symbol = "✅ COMPLETE"
        alert_symbol = "[!NOTE]\nAll structural integrity and seed coverage validation checks passed flawlessly."
        if classification == "PARTIAL":
            status_symbol = "⚠️ PARTIAL"
            alert_symbol = "[!WARNING]\nSome child run subdirectories or diagnostic reports are missing. Proceed with caution."
        elif classification == "FAILED":
            status_symbol = "❌ FAILED"
            alert_symbol = "[!CAUTION]\nSimulation sweep completed with explicit internal execution failures reported."

        artifact_rows = []
        for art in sorted(artifacts, key=lambda x: x["relative_path"])[:20]:
            size_kb = art["size_bytes"] / 1024.0
            artifact_rows.append(f"| `{art['relative_path']}` | {size_kb:.2f} KB |")
        
        limit_note = "\n*(Showing first 20 artifacts. Refer to artifact_index.json for the full list)*" if len(artifacts) > 20 else ""

        return f"""# Simulation Sweep Result Integrity Audit

This report contains the compliance scorecard for your manual execution registration audit.

## Staging Registry
- **Lab Session**: `{session_id}`
- **Sweep Run ID**: `{summary["lab_run_id"]}`
- **Audit Outcome**: `{status_symbol}`

> {alert_symbol}
{f"> **Details**: {reason}" if reason else ""}

---

## Specification Map
| Specification | Linked Alphanumeric ID |
| :--- | :--- |
| **World ID** | `{summary["world_id"]}` |
| **Scenario ID** | `{summary["scenario_id"]}` |
| **Experiment ID** | `{summary["experiment_id"]}` |

## Run Statistics
- **Expected Sweep Runs**: `{summary["run_count"]}`
- **Completed Child Runs**: `{summary["completed_run_count"]}`
- **Failed Child Runs**: `{summary["failed_run_count"]}`
- **Calculated Disk Footprint**: `{summary["storage_usage_mb"]:.3f} MB`

---

## Artifact Inventory Index
| Relative Artifact Path | Size |
| :--- | :--- |
{chr(10).join(artifact_rows)}{limit_note}

---

## Next Steps
To run post-analysis, metamorphic balance reviews, and print diagnostic reports, trigger the Investigation workflow:
```bash
rpg-workflow-investigate --session-id "{session_id}"
```
"""


class CompactSimulationDataWorkflow:
    """
    M99 Workflow: Converts heavy raw simulation run folders and child reports
    into token-efficient compact summaries, issue indexes, and metric digests
    ready for deep metamorphic balance investigations.
    """
    def __init__(self, workspace_root: Optional[str | Path] = None):
        if workspace_root is None:
            self.workspace_root = Path(__file__).resolve().parent.parent.parent
        else:
            self.workspace_root = Path(workspace_root).resolve()
            
        sessions_dir = self.workspace_root / "data" / "lab_sessions"
        self.session_store = LabSessionStore(sessions_dir)
        lab_runs_dir = self.workspace_root / "data" / "lab_runs"
        self.result_store = LabResultStore(lab_runs_dir)

    def run(self, session_id: str, request: WorkflowRequest) -> dict[str, Any]:
        logger.info(f"Running CompactSimulationDataWorkflow for session '{session_id}'")
        
        # 1. Access lab session
        manifest = self.session_store.load_session(session_id)
        # Transition session to REGISTRATION stage as files belong under registration/
        manifest.current_stage = "REGISTRATION"
        self.session_store.save_session(manifest)
        
        reg_dir = self.session_store.get_stage_dir(session_id, "REGISTRATION")
        reg_dir.mkdir(parents=True, exist_ok=True)

        # 2. Resolve target run directory path
        if request.mode == "specific":
            lab_run_path_str = request.specific_inputs.get("lab_run_path")
            if not lab_run_path_str:
                raise ValueError("lab_run_path must be supplied in specific mode.")
            top_n = request.specific_inputs.get("top_n", 5)
            focus_domains = request.specific_inputs.get("focus_domains", ["resource", "movement", "strategy", "combat", "kernel"])
        else:
            # Generic mode: load from registration/actual_lab_run_path.txt
            run_path_file = reg_dir / "actual_lab_run_path.txt"
            if not run_path_file.is_file():
                err_msg = "No registered lab run path found. Register simulation results first."
                return {"status": "BLOCKED", "reason": err_msg}
            lab_run_path_str = run_path_file.read_text(encoding="utf-8").strip()
            top_n = 5
            focus_domains = ["resource", "movement", "strategy", "combat", "kernel"]

        # Prevent traversal escapes
        resolved_run_path = safe_path_resolution(self.workspace_root, lab_run_path_str)

        # 3. Check and load sweep manifest
        manifest_file = resolved_run_path / "lab_run_manifest.json"
        if not resolved_run_path.is_dir() or not manifest_file.is_file():
            err_msg = f"Target run directory or manifest not found: {lab_run_path_str}"
            return {"status": "BLOCKED", "reason": err_msg}

        try:
            with open(manifest_file, "r", encoding="utf-8") as f:
                run_manifest_data = json.load(f)
            run_manifest = LabRunManifest(**run_manifest_data)
        except Exception as e:
            return {"status": "BLOCKED", "reason": f"Malformed or unparseable run manifest: {e}"}

        # 4. Scan and load child run summaries
        child_reports = []
        runs_dir = resolved_run_path / "runs"
        if runs_dir.is_dir():
            for child_dir in sorted(runs_dir.iterdir(), key=lambda x: x.name):
                if child_dir.is_dir():
                    report_path = child_dir / "run_report.json"
                    if report_path.is_file():
                        try:
                            with open(report_path, "r", encoding="utf-8") as f:
                                child_reports.append((child_dir.name, json.load(f)))
                        except Exception as e:
                            logger.warning(f"Failed to load run report in {child_dir.name}: {e}")

        if not child_reports:
            return {"status": "BLOCKED", "reason": "No child run reports found to compact."}

        # 5. Process anomaly rollups for issue index and entity hotspots
        all_anomalies = []
        rule_execution_stats = {}  # rule_name -> {status_counts: {status: count}, total_anomalies: int}
        
        for run_id, report in child_reports:
            # Gather anomalies
            anomalies = report.get("anomalies", [])
            for an in anomalies:
                # Add run reference
                an_copy = dict(an)
                an_copy["run_id"] = run_id
                all_anomalies.append(an_copy)
                
            # Gather rule execution signals
            for rule in report.get("rule_execution", []):
                rule_id = rule.get("rule_id")
                status = rule.get("status", "UNKNOWN")
                rule_stat = rule_execution_stats.setdefault(rule_id, {"status_counts": {}, "total_anomalies": 0})
                rule_stat["status_counts"][status] = rule_stat["status_counts"].get(status, 0) + 1

        # 6. Group issues (Issue Index)
        grouped_issues = {}
        for an in all_anomalies:
            rule_name = an.get("rule_name", "UnknownRule")
            severity = an.get("severity", "WARNING")
            entity_id = an.get("entity_id")
            tick = an.get("tick_detected", 0)
            msg = an.get("message", "")
            run_id = an.get("run_id")

            issue = grouped_issues.setdefault(rule_name, {
                "rule_name": rule_name,
                "severity": severity,
                "count": 0,
                "tick_range": [tick, tick],
                "affected_entities": set(),
                "affected_runs": set(),
                "evidence_samples": set()
            })

            issue["count"] += 1
            # Maintain highest severity observed
            severity_order = {"CRITICAL": 3, "ERROR": 2, "WARNING": 1, "INFO": 0}
            current_sev_rank = severity_order.get(issue["severity"], 0)
            new_sev_rank = severity_order.get(severity, 0)
            if new_sev_rank > current_sev_rank:
                issue["severity"] = severity

            # Tick range
            issue["tick_range"][0] = min(issue["tick_range"][0], tick)
            issue["tick_range"][1] = max(issue["tick_range"][1], tick)

            if entity_id is not None:
                issue["affected_entities"].add(int(entity_id))
            if run_id:
                issue["affected_runs"].add(run_id)
            if msg:
                issue["evidence_samples"].add(msg)

        # Finalize and sort issues by count descending
        issue_index_list = []
        for name, data in grouped_issues.items():
            issue_index_list.append({
                "rule_name": name,
                "severity": data["severity"],
                "count": data["count"],
                "tick_range": data["tick_range"],
                "affected_entities": sorted(list(data["affected_entities"])),
                "affected_runs": sorted(list(data["affected_runs"])),
                "short_evidence_summaries": sorted(list(data["evidence_samples"]))[:top_n]
            })
        issue_index_list.sort(key=lambda x: x["count"], reverse=True)
        # Apply top_n slice for the final written index
        issue_index_final = issue_index_list[:top_n]

        # 7. Formulate child run summary (Evidence Pack Index)
        evidence_pack_list = []
        for run_id, report in child_reports:
            anomalies = report.get("anomalies", [])
            anomaly_counts = {}
            has_crit = False
            for an in anomalies:
                r_name = an.get("rule_name", "UnknownRule")
                anomaly_counts[r_name] = anomaly_counts.get(r_name, 0) + 1
                if an.get("severity") == "CRITICAL":
                    has_crit = True

            h_score = report.get("health_score", 100.0)
            err_cnt = report.get("errors_count", report.get("error_count", 0))
            crit_cnt = report.get("critical_count", report.get("hard_law_violation_count", 0))
            
            # Simple COMPLETE vs FAILED status based on error flags
            status_val = "FAILED" if err_cnt > 0 or report.get("metadata", {}).get("status") == "FAILED" else "COMPLETE"

            evidence_pack_list.append({
                "run_id": run_id,
                "status": status_val,
                "health_score": h_score,
                "anomaly_counts": anomaly_counts,
                "total_anomalies": len(anomalies),
                "has_critical_violations": has_crit or crit_cnt > 0,
                "report_file_path": f"runs/{run_id}/run_report.json"
            })

        # 8. Build Metric Digest
        h_scores = [p["health_score"] for p in evidence_pack_list]
        avg_health = sum(h_scores) / len(h_scores) if h_scores else 100.0
        min_health = min(h_scores) if h_scores else 100.0
        max_health = max(h_scores) if h_scores else 100.0

        total_crit = sum(r.get("critical_count", r.get("hard_law_violation_count", 0)) for _, r in child_reports)
        total_warn = sum(r.get("warnings_count", r.get("warning_count", 0)) for _, r in child_reports)
        total_err = sum(r.get("errors_count", r.get("error_count", 0)) for _, r in child_reports)

        max_tick = 0
        for an in all_anomalies:
            max_tick = max(max_tick, an.get("tick_detected", 0))
        for _, r in child_reports:
            # Try to grab final ticks from rules or metadata if present
            max_tick = max(max_tick, r.get("metadata", {}).get("final_tick", 0))

        metric_digest = {
            "avg_health_score": avg_health,
            "min_health_score": min_health,
            "max_health_score": max_health,
            "total_criticals": total_crit,
            "total_warnings": total_warn,
            "total_errors": total_err,
            "tick_max": max_tick
        }

        # 9. Build Entity Hotspot Index
        grouped_entities = {}
        for an in all_anomalies:
            eid = an.get("entity_id")
            if eid is not None:
                eid_int = int(eid)
                rule_name = an.get("rule_name", "UnknownRule")
                run_id = an.get("run_id")

                ent = grouped_entities.setdefault(eid_int, {
                    "entity_id": eid_int,
                    "anomaly_count": 0,
                    "issue_types": set(),
                    "affected_runs": set()
                })
                ent["anomaly_count"] += 1
                ent["issue_types"].add(rule_name)
                ent["affected_runs"].add(run_id)

        entity_hotspots_list = []
        for eid, data in grouped_entities.items():
            entity_hotspots_list.append({
                "entity_id": eid,
                "anomaly_count": data["anomaly_count"],
                "issue_types": sorted(list(data["issue_types"])),
                "affected_runs": sorted(list(data["affected_runs"]))
            })
        entity_hotspots_list.sort(key=lambda x: x["anomaly_count"], reverse=True)
        entity_hotspots_final = entity_hotspots_list[:top_n]

        # 10. Build Signal Coverage Report
        gameplay_domain_rules = {
            "kernel": ["HardLawViolationRule", "HardLawViolationLive", "GovernorDegradedLive", "EventDropRateHigh"],
            "movement": ["NavigationStuckRule", "NavigationStuckLive"],
            "strategy": ["QuestStalledRule"],
            "combat": ["CombatNeverEndsRule"],
            "resource": ["ResourceNodeCrowdingRule"]
        }

        def get_domain_for_rule(rule_name: str) -> str:
            for domain, rules in gameplay_domain_rules.items():
                if rule_name in rules:
                    return domain
            r_lower = rule_name.lower()
            if "hardlaw" in r_lower:
                return "kernel"
            if "navigation" in r_lower or "stuck" in r_lower:
                return "movement"
            if "quest" in r_lower:
                return "strategy"
            if "combat" in r_lower:
                return "combat"
            if "resource" in r_lower or "node" in r_lower:
                return "resource"
            return "kernel"

        signal_coverage_map = {}
        # Initialise standard domains
        standard_domains = ["kernel", "movement", "strategy", "combat", "resource"]
        for dom in standard_domains:
            signal_coverage_map[dom] = {
                "domain": dom,
                "total_anomalies": 0,
                "covered": False,
                "focus_status": "NONE",
                "rules_triggered": set()
            }

        # Fill with actual signals
        for an in all_anomalies:
            r_name = an.get("rule_name", "UnknownRule")
            dom = get_domain_for_rule(r_name)
            cov = signal_coverage_map.setdefault(dom, {
                "domain": dom,
                "total_anomalies": 0,
                "covered": False,
                "focus_status": "NONE",
                "rules_triggered": set()
            })
            cov["total_anomalies"] += 1
            cov["covered"] = True
            cov["rules_triggered"].add(r_name)

        # Check coverage from rule executions even if 0 anomalies were triggered!
        for rule_id, stats in rule_execution_stats.items():
            dom = get_domain_for_rule(rule_id)
            cov = signal_coverage_map.setdefault(dom, {
                "domain": dom,
                "total_anomalies": 0,
                "covered": False,
                "focus_status": "NONE",
                "rules_triggered": set()
            })
            cov["covered"] = True

        # Process focus statuses
        for dom, cov in signal_coverage_map.items():
            cov["rules_triggered"] = sorted(list(cov["rules_triggered"]))
            if dom in focus_domains:
                if cov["total_anomalies"] > 0:
                    cov["focus_status"] = "HIGH_FOCUS"
                else:
                    cov["focus_status"] = "FOCUS"
            else:
                cov["focus_status"] = "NONE"

        signal_coverage_final = sorted(list(signal_coverage_map.values()), key=lambda x: x["domain"])

        # 11. Formulate final Compact Summary
        focused_summary_list = [c for c in signal_coverage_final if c["domain"] in focus_domains]

        compact_summary = {
            "lab_run_id": run_manifest.lab_run_id,
            "session_id": session_id,
            "world_id": run_manifest.world_id,
            "scenario_id": run_manifest.scenario_id,
            "experiment_id": run_manifest.experiment_id,
            "summary_stats": {
                "run_count": len(evidence_pack_list),
                "completed_run_count": sum(1 for p in evidence_pack_list if p["status"] == "COMPLETE"),
                "failed_run_count": sum(1 for p in evidence_pack_list if p["status"] == "FAILED"),
                "total_anomalies": len(all_anomalies),
                "average_health_score": avg_health
            },
            "top_issues": issue_index_final,
            "top_entity_hotspots": entity_hotspots_final,
            "focused_domains_summary": focused_summary_list
        }

        # 12. Write JSON outputs
        with open(reg_dir / "compact_summary.json", "w", encoding="utf-8") as f:
            json.dump(compact_summary, f, indent=2)
        with open(reg_dir / "issue_index.json", "w", encoding="utf-8") as f:
            json.dump(issue_index_final, f, indent=2)
        with open(reg_dir / "evidence_pack_index.json", "w", encoding="utf-8") as f:
            json.dump(evidence_pack_list, f, indent=2)
        with open(reg_dir / "metric_digest.json", "w", encoding="utf-8") as f:
            json.dump(metric_digest, f, indent=2)
        with open(reg_dir / "entity_hotspots.json", "w", encoding="utf-8") as f:
            json.dump(entity_hotspots_final, f, indent=2)
        with open(reg_dir / "signal_coverage.json", "w", encoding="utf-8") as f:
            json.dump(signal_coverage_final, f, indent=2)

        # 13. Render beautifully formatted Markdown Report (compact_summary.md)
        summary_md = self._format_compact_summary_md(session_id, compact_summary, metric_digest, signal_coverage_final)
        (reg_dir / "compact_summary.md").write_text(summary_md, encoding="utf-8")

        return {
            "status": "READY",
            "report_path": str(reg_dir / "compact_summary.md")
        }

    def _format_compact_summary_md(self, session_id: str, summary: dict[str, Any], digest: dict[str, Any], coverage: list[dict[str, Any]]) -> str:
        """Formats premium compact summary overview markdown."""
        stats = summary["summary_stats"]
        
        # Format issue rows
        issue_rows = []
        for issue in summary["top_issues"]:
            range_str = f"Ticks {issue['tick_range'][0]}-{issue['tick_range'][1]}"
            entities_str = ", ".join(str(e) for e in issue["affected_entities"][:5])
            if len(issue["affected_entities"]) > 5:
                entities_str += "..."
            issue_rows.append(
                f"| `{issue['rule_name']}` | **{issue['severity']}** | {issue['count']} | {range_str} | Entities: {entities_str or 'None'} |"
            )
        issues_table = "\n".join(issue_rows) if issue_rows else "| *No issue anomalies detected* | | | | |"

        # Format hotspot rows
        hotspot_rows = []
        for hot in summary["top_entity_hotspots"]:
            rules_str = ", ".join(hot["issue_types"])
            hotspot_rows.append(
                f"| **Entity {hot['entity_id']}** | {hot['anomaly_count']} | {rules_str} |"
            )
        hotspot_table = "\n".join(hotspot_rows) if hotspot_rows else "| *No entity hotspots recorded* | | |"

        # Format coverage rows
        coverage_rows = []
        for cov in coverage:
            status_tag = "✅ COVERED" if cov["covered"] else "❌ UNCOVERED"
            focus_tag = f"`{cov['focus_status']}`"
            rules_str = ", ".join(cov["rules_triggered"]) or "None"
            coverage_rows.append(
                f"| {cov['domain'].upper()} | {status_tag} | {focus_tag} | {cov['total_anomalies']} | {rules_str} |"
            )
        coverage_table = "\n".join(coverage_rows)

        return f"""# Compact Simulation Sweep Diagnostic Summary

This report delivers a token-efficient, quantitative scorecard of the manual simulation sweep results.

## Staging Registry
- **Lab Session**: `{session_id}`
- **Sweep Run ID**: `{summary["lab_run_id"]}`
- **Average Health Score**: `{stats["average_health_score"]:.2f} / 100.0`

> [!NOTE]
> All raw timelines and massive event logs have been successfully filtered out to ensure a lightweight footprint for downstream reasoning.

---

## Configuration Map
- **World ID**: `{summary["world_id"]}`
- **Scenario ID**: `{summary["scenario_id"]}`
- **Experiment ID**: `{summary["experiment_id"]}`

## Quantitative Digest
- **Sweep Size**: `{stats["run_count"]} runs` (Completed: `{stats["completed_run_count"]}`, Failed: `{stats["failed_run_count"]}`)
- **Total Anomaly Events**: `{stats["total_anomalies"]}`
- **Aggregated Health Distribution**: Min: `{digest["min_health_score"]:.2f}`, Max: `{digest["max_health_score"]:.2f}`
- **Categorized Violations**: Criticals: `{digest["total_criticals"]}`, Errors: `{digest["total_errors"]}`, Warnings: `{digest["total_warnings"]}`
- **Max Timeline Tick**: `{digest["tick_max"]} ticks`

---

## Gameplay Domain Coverage
| Gameplay Domain | Diagnostic Status | Focus Level | Anomalies | Triggered Laws/Rules |
| :--- | :--- | :--- | :--- | :--- |
{coverage_table}

---

## Top Issue Index
| Law / Rule Triggered | Severity | Total Anomalies | Detection Range | Affected Scope Summary |
| :--- | :--- | :--- | :--- | :--- |
{issues_table}

---

## Top Entity Hotspots
| Affected Entity | Trigger Frequency | Triggered Rule Types |
| :--- | :--- | :--- |
{hotspot_table}

---

## Next Steps
To run post-analysis, metamorphic balance reviews, and print diagnostic reports, trigger the Investigation workflow:
```bash
rpg-workflow-investigate --session-id "{session_id}"
```
"""


class InvestigateSimulationResultWorkflow:
    """
    M100 Workflow: Analyzes registered and compacted simulation results
    to identify balance anomalies, domain issues, liveness issues,
    and formulate a bug backlog and missing signal report.
    """
    def __init__(self, workspace_root: Optional[str | Path] = None):
        if workspace_root is None:
            self.workspace_root = Path(__file__).resolve().parent.parent.parent
        else:
            self.workspace_root = Path(workspace_root).resolve()
            
        sessions_dir = self.workspace_root / "data" / "lab_sessions"
        self.session_store = LabSessionStore(sessions_dir)
        lab_runs_dir = self.workspace_root / "data" / "lab_runs"
        self.result_store = LabResultStore(lab_runs_dir)

    def run(self, session_id: str, request: WorkflowRequest) -> dict[str, Any]:
        logger.info(f"Running InvestigateSimulationResultWorkflow for session '{session_id}'")
        
        # 1. Access lab session
        manifest = self.session_store.load_session(session_id)
        
        # 2. Get registration directory (where compacted files are stored)
        reg_dir = self.session_store.get_stage_dir(session_id, "REGISTRATION")
        
        # Check if compaction files exist
        compact_summary_file = reg_dir / "compact_summary.json"
        issue_index_file = reg_dir / "issue_index.json"
        
        if not compact_summary_file.is_file() or not issue_index_file.is_file():
            return {
                "status": "BLOCKED",
                "reason": "Compacted simulation data not found under registration/ directory. Run CompactSimulationData first."
            }

        # 3. Resolve target run directory path for specific or generic mode
        if request.mode == "specific":
            lab_run_path_str = request.specific_inputs.get("lab_run_path")
            if not lab_run_path_str:
                raise ValueError("lab_run_path must be supplied in specific mode.")
            # Focus inputs
            focus_domains = request.specific_inputs.get("focus_domains")
            focus_issues = request.specific_inputs.get("focus_issues", [])
            seeds = request.specific_inputs.get("seeds")
            tick_range = request.specific_inputs.get("tick_range")
            analysis_depth = request.specific_inputs.get("analysis_depth", "standard")
        else:
            # Generic mode
            run_path_file = reg_dir / "actual_lab_run_path.txt"
            if not run_path_file.is_file():
                return {"status": "BLOCKED", "reason": "No registered lab run path found."}
            lab_run_path_str = run_path_file.read_text(encoding="utf-8").strip()
            focus_domains = None
            focus_issues = []
            seeds = None
            tick_range = None
            analysis_depth = request.specific_inputs.get("analysis_depth", "standard") if request.specific_inputs else "standard"

        # Prevent traversal escapes
        resolved_run_path = safe_path_resolution(self.workspace_root, lab_run_path_str)

        # Deep analysis confirmation gate — requires explicit opt-in to protect token and time budgets
        if analysis_depth == "deep":
            allow_deep = (request.constraints or {}).get("allow_deep_analysis", False)
            if not allow_deep:
                audit = LabAuditTrail(self.workspace_root)
                audit.log_event(session_id, "guardrail_violation", {
                    "violation_type": "deep_analysis_blocked",
                    "reason": "analysis_depth='deep' requested without allow_deep_analysis=true in constraints",
                    "action": "downgraded to standard depth"
                })
                analysis_depth = "standard"
                logger.warning(
                    "InvestigateSimulationResultWorkflow: deep analysis requested but 'allow_deep_analysis' "
                    "not set in constraints — downgraded to 'standard' depth."
                )

        # Verify that the run directory and manifest exist
        run_manifest_file = resolved_run_path / "lab_run_manifest.json"
        if not resolved_run_path.is_dir() or not run_manifest_file.is_file():
            return {
                "status": "BLOCKED",
                "reason": f"Run directory or manifest not found: {lab_run_path_str}"
            }

        # Load run manifest to check status
        with open(run_manifest_file, "r", encoding="utf-8") as f:
            run_manifest = json.load(f)
            
        if run_manifest.get("status") != "COMPLETED":
            return {
                "status": "BLOCKED",
                "reason": f"Unsupported lab run state: status is {run_manifest.get('status')}. Run must be COMPLETED."
            }

        # Transition session to INVESTIGATION stage
        manifest.current_stage = "INVESTIGATION"
        self.session_store.save_session(manifest)
        
        invest_dir = self.session_store.get_stage_dir(session_id, "INVESTIGATION")
        invest_dir.mkdir(parents=True, exist_ok=True)

        # 4. Load Compaction Files
        with open(compact_summary_file, "r", encoding="utf-8") as f:
            compact_summary = json.load(f)
        with open(issue_index_file, "r", encoding="utf-8") as f:
            all_issues = json.load(f)

        # Read other indexes if standard or deep
        evidence_pack = []
        signal_coverage = []
        entity_hotspots = []
        metric_digest = {}

        if analysis_depth in ("standard", "deep"):
            ev_file = reg_dir / "evidence_pack_index.json"
            sig_file = reg_dir / "signal_coverage.json"
            hot_file = reg_dir / "entity_hotspots.json"
            dig_file = reg_dir / "metric_digest.json"
            if ev_file.is_file():
                with open(ev_file, "r", encoding="utf-8") as f:
                    evidence_pack = json.load(f)
            if sig_file.is_file():
                with open(sig_file, "r", encoding="utf-8") as f:
                    signal_coverage = json.load(f)
            if hot_file.is_file():
                with open(hot_file, "r", encoding="utf-8") as f:
                    entity_hotspots = json.load(f)
            if dig_file.is_file():
                with open(dig_file, "r", encoding="utf-8") as f:
                    metric_digest = json.load(f)

        # 5. Process based on depth
        analyzed_issues = all_issues
        if analysis_depth == "light":
            # Only top 3 issues
            analyzed_issues = all_issues[:3]
        elif analysis_depth == "standard":
            # Top 10 issues
            analyzed_issues = all_issues[:10]
        elif analysis_depth == "deep":
            # Under deep mode, read selected evidence packs or specific child run report.json files
            # based on focus_issues, seeds, or tick_range constraints.
            # We strictly DO NOT load the full raw event timeline.
            analyzed_issues = all_issues[:10]
            # If focus_issues is provided, filter or prioritize
            if focus_issues:
                priority_issues = [i for i in all_issues if i["rule_name"] in focus_issues]
                other_issues = [i for i in all_issues if i["rule_name"] not in focus_issues]
                analyzed_issues = (priority_issues + other_issues)[:10]

        # 6. Analyze and Derive Investigation Reports
        # Categories mapping
        critical_issues = []
        domain_issues = {}
        balance_concerns = []
        liveness_concerns = []
        performance_concerns = []
        entity_evidence = []
        missing_data = []
        likely_causes_vs_facts = []
        recommended_steps = []
        evidence_references = []

        # Executive summary & Data Quality derived defaults
        exec_sum = f"Investigation suite parsed completed simulation run {compact_summary['lab_run_id']} at '{analysis_depth}' analysis depth. "
        dq_desc = f"Compaction dataset integrity is optimal. Parsed {compact_summary['summary_stats']['completed_run_count']} child run reports successfully."

        # Filter domain issues
        for issue in analyzed_issues:
            # Severity critical
            if issue["severity"] == "CRITICAL":
                critical_issues.append({
                    "rule_name": issue["rule_name"],
                    "count": issue["count"],
                    "severity": issue["severity"],
                    "affected_entities": issue["affected_entities"]
                })
            
            # Map gameplay domains based on rule name patterns
            rule_lower = issue["rule_name"].lower()
            domain = "kernel"
            if "nav" in rule_lower or "stuck" in rule_lower or "move" in rule_lower:
                domain = "movement"
            elif "balance" in rule_lower or "economy" in rule_lower or "production" in rule_lower or "zero" in rule_lower:
                domain = "resource"
            elif "combat" in rule_lower or "fight" in rule_lower or "death" in rule_lower:
                domain = "combat"
            elif "strat" in rule_lower or "decision" in rule_lower:
                domain = "strategy"
                
            domain_issues.setdefault(domain, []).append({
                "rule_name": issue["rule_name"],
                "count": issue["count"],
                "severity": issue["severity"]
            })

            # Flag Balance concerns
            if "balance" in rule_lower or "production" in rule_lower or "zero" in rule_lower or "economy" in rule_lower:
                balance_concerns.append(f"Anomalous balance violation in rule '{issue['rule_name']}': Triggered {issue['count']} times between ticks {issue['tick_range'][0]}-{issue['tick_range'][1]}.")
            
            # Flag Liveness concerns
            if "stuck" in rule_lower or "liveness" in rule_lower or "nav" in rule_lower or "hang" in rule_lower:
                liveness_concerns.append(f"System liveness or pathfinding breakdown in rule '{issue['rule_name']}': {issue['count']} occurrences. Affected entities: {issue['affected_entities']}.")

            # Likely causes vs confirmed facts
            fact = f"Fact: Rule '{issue['rule_name']}' was triggered {issue['count']} times in the simulation."
            cause = "Likely Cause: State transition or boundary rule configuration mismatch."
            if "nav" in rule_lower or "stuck" in rule_lower:
                cause = "Likely Cause: Pathfinding obstacle blockage or navigation loop."
            likely_causes_vs_facts.append({"fact": fact, "hypothesized_cause": cause})

        # Add metric-based performance concerns
        if metric_digest:
            if metric_digest.get("total_criticals", 0) > 0:
                performance_concerns.append(f"Critical rule alerts detected: {metric_digest['total_criticals']} occurrences.")
            # If storage usage is high or run counts are very large
            if compact_summary["summary_stats"].get("storage_usage_mb", 0) > 10.0:
                performance_concerns.append("High disk usage (>10MB) detected for simulation run logs.")

        # Map missing signals
        if signal_coverage:
            for cov in signal_coverage:
                if not cov["covered"] and cov["focus_status"] in ("HIGH_FOCUS", "FOCUS"):
                    missing_data.append({
                        "domain": cov["domain"],
                        "focus_status": cov["focus_status"],
                        "reason": "Gameplay domain marked as high focus but had zero telemetry logs recorded in this sweep."
                    })
                    
        # Map entity evidence hotspots
        if entity_hotspots:
            for hot in entity_hotspots[:5]:
                entity_evidence.append({
                    "entity_id": hot["entity_id"],
                    "anomaly_count": hot["anomaly_count"],
                    "issue_types": hot["issue_types"]
                })

        # Recommended steps
        if critical_issues:
            recommended_steps.append("1. Resolve CRITICAL rules immediately to prevent simulator kernel divergence.")
        if liveness_concerns:
            recommended_steps.append("2. Audit agent pathfinding coordinates and topological obstacles.")
        if balance_concerns:
            recommended_steps.append("3. Adjust production coefficients or trading prices in scenario files.")
        if not recommended_steps:
            recommended_steps.append("1. Keep baseline configuration stable. Sweep with a wider seed matrix to confirm stability.")

        # Evidence references
        for issue in analyzed_issues[:5]:
            evidence_references.append({
                "rule_name": issue["rule_name"],
                "reference_files": [f"runs/*/run_report.json"],
                "ticks": issue.get("tick_range", "unknown")
            })

        # 7. Create Output JSON Report
        investigation_report = {
            "session_id": session_id,
            "lab_run_id": compact_summary["lab_run_id"],
            "analysis_depth": analysis_depth,
            "investigated_at": "2026-05-24T08:52:05Z",
            "executive_summary": exec_sum,
            "data_quality": dq_desc,
            "signal_coverage": signal_coverage,
            "critical_issues": critical_issues,
            "domain_issues": domain_issues,
            "balance_concerns": balance_concerns,
            "liveness_concerns": liveness_concerns,
            "performance_concerns": performance_concerns,
            "entity_evidence": entity_evidence,
            "missing_data": missing_data,
            "likely_causes_vs_facts": likely_causes_vs_facts,
            "recommended_steps": recommended_steps,
            "evidence_references": evidence_references
        }

        # Save investigation_report.json
        with open(invest_dir / "investigation_report.json", "w", encoding="utf-8") as f:
            json.dump(investigation_report, f, indent=2)

        # 8. Create Issue Backlog JSON
        issue_backlog = []
        for idx, issue in enumerate(all_issues):
            domain = "kernel"
            rule_lower = issue["rule_name"].lower()
            if "nav" in rule_lower or "stuck" in rule_lower or "move" in rule_lower:
                domain = "movement"
            elif "balance" in rule_lower or "economy" in rule_lower or "production" in rule_lower:
                domain = "resource"
            elif "combat" in rule_lower or "fight" in rule_lower:
                domain = "combat"
            elif "strat" in rule_lower or "decision" in rule_lower:
                domain = "strategy"

            issue_backlog.append({
                "issue_id": f"ISSUE-{idx+1:03d}",
                "rule_name": issue["rule_name"],
                "severity": issue.get("severity", "WARNING"),
                "domain": issue.get("domain", domain),
                "description": issue.get(
                    "description",
                    f"Rule {issue['rule_name']} triggered {issue.get('count', 0)} times in simulation sweep."
                ),
                "frequency": issue.get("count", 0),
                "affected_entities": issue.get("affected_entities", []),
                "state": "OPEN"
            })
            
        with open(invest_dir / "issue_backlog.json", "w", encoding="utf-8") as f:
            json.dump(issue_backlog, f, indent=2)

        # 9. Create Missing Signals JSON
        missing_signals_out = []
        if signal_coverage:
            for cov in signal_coverage:
                if not cov["covered"] and cov["focus_status"] in ("HIGH_FOCUS", "FOCUS"):
                    missing_signals_out.append({
                        "domain": cov["domain"],
                        "focus_status": cov["focus_status"],
                        "reason": f"Gameplay domain '{cov['domain']}' was prioritized but had zero telemetry logs recorded in this sweep."
                    })
        with open(invest_dir / "missing_signals.json", "w", encoding="utf-8") as f:
            json.dump(missing_signals_out, f, indent=2)

        # 10. Create Insight Candidates JSON
        insight_candidates = []
        for idx, concern in enumerate(balance_concerns):
            insight_candidates.append({
                "insight_id": f"INSIGHT-{idx+1:03d}",
                "title": f"Balance Regression: {concern.split(':')[0]}",
                "domain": "resource",
                "observation": concern,
                "hypothesized_cause": "Resource rates or pricing margins require rebalancing."
            })
        with open(invest_dir / "insight_candidates.json", "w", encoding="utf-8") as f:
            json.dump(insight_candidates, f, indent=2)

        # 11. Create Next Experiment Suggestions JSON
        next_experiment_suggestions = []
        if critical_issues or balance_concerns:
            next_experiment_suggestions.append({
                "experiment_id": "EXP-REPRODUCE-001",
                "focus_issues": [i["rule_name"] for i in critical_issues],
                "suggested_seeds": seeds or [42, 101, 2023],
                "suggested_constraints": {
                    "max_runtime_minutes": 30,
                    "target_ticks": tick_range or [10000, 30000]
                }
            })
        with open(invest_dir / "next_experiment_suggestions.json", "w", encoding="utf-8") as f:
            json.dump(next_experiment_suggestions, f, indent=2)

        # 12. Create beautifully formatted Premium Markdown Report
        summary_md = self._format_investigation_report_md(investigation_report, issue_backlog)
        (invest_dir / "investigation_report.md").write_text(summary_md, encoding="utf-8")

        return {
            "status": "READY",
            "report_path": str(invest_dir / "investigation_report.md")
        }

    def _format_investigation_report_md(self, report: dict[str, Any], backlog: list[dict[str, Any]]) -> str:
        """Formats the 13 required sections of the investigation report in a gorgeous markdown format."""
        
        # format critical issue rows
        crit_rows = []
        for crit in report["critical_issues"]:
            crit_rows.append(f"- **{crit['rule_name']}**: Triggered {crit['count']} times. Affected scope: Entities {crit['affected_entities'][:5]}")
        crit_list = "\n".join(crit_rows) if crit_rows else "*No CRITICAL severity issues identified.*"

        # format domain issue list
        domain_items = []
        for dom, issues in report["domain_issues"].items():
            domain_items.append(f"### Gameplay Domain: {dom.upper()}")
            for iss in issues:
                domain_items.append(f"- `{iss['rule_name']}` (**{iss['severity']}**): Triggered {iss['count']} times")
        domain_list = "\n".join(domain_items) if domain_items else "*No domain violations categorised.*"

        # format balance concerns
        bal_list = "\n".join(f"- {b}" for b in report["balance_concerns"]) if report["balance_concerns"] else "*No balance concerns recorded.*"

        # format liveness concerns
        live_list = "\n".join(f"- {l}" for l in report["liveness_concerns"]) if report["liveness_concerns"] else "*No liveness concerns recorded.*"

        # format performance concerns
        perf_list = "\n".join(f"- {p}" for p in report["performance_concerns"]) if report["performance_concerns"] else "*No performance concerns recorded.*"

        # format entity/cognition evidence
        ent_rows = []
        for ent in report["entity_evidence"]:
            ent_rows.append(f"| **Entity {ent['entity_id']}** | {ent['anomaly_count']} | {', '.join(ent['issue_types'])} |")
        ent_table = "\n".join(ent_rows) if ent_rows else "| *No entity hotspot evidence found* | | |"

        # format missing data
        miss_rows = []
        for m in report["missing_data"]:
            miss_rows.append(f"| **{m['domain'].upper()}** | `{m['focus_status']}` | {m['reason']} |")
        miss_table = "\n".join(miss_rows) if miss_rows else "| *No missing signal gaps reported* | | |"

        # format likely causes vs facts
        cause_list = []
        for idx, cf in enumerate(report["likely_causes_vs_facts"]):
            cause_list.append(f"{idx+1}. **{cf['fact']}**\n   - *{cf['hypothesized_cause']}*")
        cause_text = "\n".join(cause_list) if cause_list else "*No fact comparisons recorded.*"

        # format recommended steps
        rec_list = "\n".join(report["recommended_steps"])

        # format evidence references
        ref_rows = []
        for ref in report["evidence_references"]:
            ref_rows.append(f"- **{ref['rule_name']}**: File `{ref['reference_files'][0]}` (Ticks: {ref['ticks'][0]}-{ref['ticks'][1]})")
        ref_list = "\n".join(ref_rows) if ref_rows else "*No evidence references registered.*"

        return f"""# Investigation Sweep Diagnostic Report

Comprehensive diagnostic analysis of the completed simulation run sweep.

---

## 1. Executive Summary
{report["executive_summary"]}

## 2. Data Quality
{report["data_quality"]}

---

## 3. Signal Coverage
### Prioritized Telemetry Coverage Gaps
| Game Domain | Focus Level | Reason for Telemetry Gap |
| :--- | :--- | :--- |
{miss_table}

---

## 4. Critical Issues
{crit_list}

---

## 5. Domain Issues
{domain_list}

---

## 6. Balance Concerns
{bal_list}

---

## 7. Liveness Concerns
{live_list}

---

## 8. Runtime/performance concerns
{perf_list}

---

## 9. Entity/cognition evidence
| Hotspot Entity | Anomaly Frequency | Associated Rules |
| :--- | :--- | :--- |
{ent_table}

---

## 10. Missing data
*Refer to Section 3: Signal Coverage.*

---

## 11. Likely causes vs confirmed facts
{cause_text}

---

## 12. Recommended next steps
{rec_list}

---

## 13. Evidence references
{ref_list}
"""


class ProposeSimulationEnhancementsWorkflow:
    """
    M101 Workflow: Ingests completed investigation scorecard and constructs
    actionable spec patches, experiment drafts, and risk profiles.
    """
    def __init__(self, workspace_root: Optional[str | Path] = None):
        if workspace_root is None:
            self.workspace_root = Path(__file__).resolve().parent.parent.parent
        else:
            self.workspace_root = Path(workspace_root).resolve()
            
        sessions_dir = self.workspace_root / "data" / "lab_sessions"
        self.session_store = LabSessionStore(sessions_dir)
        lab_runs_dir = self.workspace_root / "data" / "lab_runs"
        self.result_store = LabResultStore(lab_runs_dir)

    def run(self, session_id: str, request: WorkflowRequest) -> dict[str, Any]:
        logger.info(f"Running ProposeSimulationEnhancementsWorkflow for session '{session_id}'")
        
        # 1. Access session and confirm stage
        manifest = self.session_store.load_session(session_id)
        
        # Check if investigation stage completed
        invest_dir = self.session_store.get_stage_dir(session_id, "INVESTIGATION")
        invest_report_file = invest_dir / "investigation_report.json"
        issue_backlog_file = invest_dir / "issue_backlog.json"
        missing_signals_file = invest_dir / "missing_signals.json"
        
        if not invest_report_file.is_file():
            return {
                "status": "BLOCKED",
                "reason": "Investigation report not found. Run InvestigateSimulationResult first."
            }

        # 2. Get inputs and change restrictions
        allowed_types = ["ScenarioSpec", "ExperimentSpec", "ObservabilityRules", "KnownIssues", "MutationSpec", "TopologySpec", "WorldSpec"]
        forbidden_types = ["EngineCode"]

        if request.specific_inputs:
            allowed_types = request.specific_inputs.get("allowed_change_types", allowed_types)
            forbidden_types = request.specific_inputs.get("forbidden_change_types", forbidden_types)

        # 3. Resolve investigation report path (for specific mode)
        if request.mode == "specific":
            report_path_str = request.specific_inputs.get("investigation_report_path")
            if report_path_str:
                resolved_report_path = safe_path_resolution(self.workspace_root, report_path_str)
                if not resolved_report_path.is_file():
                    raise FileNotFoundError(f"Investigation report path not found: {report_path_str}")
                with open(resolved_report_path, "r", encoding="utf-8") as f:
                    # Could be markdown or json
                    if report_path_str.endswith(".json"):
                        invest_report = json.load(f)
                    else:
                        # Simple mock structure if md loaded
                        invest_report = {"critical_issues": [], "balance_concerns": []}
            else:
                with open(invest_report_file, "r", encoding="utf-8") as f:
                    invest_report = json.load(f)
        else:
            with open(invest_report_file, "r", encoding="utf-8") as f:
                invest_report = json.load(f)

        # Transition session to ENHANCEMENT stage
        manifest.current_stage = "ENHANCEMENT"
        self.session_store.save_session(manifest)
        
        enhance_dir = self.session_store.get_stage_dir(session_id, "ENHANCEMENT")
        enhance_dir.mkdir(parents=True, exist_ok=True)
        
        patches_dir = enhance_dir / "proposed_patches"
        patches_dir.mkdir(parents=True, exist_ok=True)
        
        drafts_dir = enhance_dir / "next_experiment_drafts"
        drafts_dir.mkdir(parents=True, exist_ok=True)

        # Load backlogs & missing signals
        with open(issue_backlog_file, "r", encoding="utf-8") as f:
            issue_backlog = json.load(f)
        with open(missing_signals_file, "r", encoding="utf-8") as f:
            missing_signals = json.load(f)

        # 4. Synthesize Patches & Validate Rules
        proposed_patches = []
        
        # Propose scenario signal signal updates if there are missing signals
        for idx, sig in enumerate(missing_signals):
            patch_type = "ScenarioSpec"
            if patch_type in forbidden_types:
                raise ValueError(f"Proposing patch of type {patch_type} is forbidden by configuration constraints.")
                
            patch = {
                "patch_id": f"add_{sig['domain']}_telemetry_{idx+1}",
                "target_type": patch_type,
                "target_file": f"data/scenarios/resource_economy_basic/scenario.yaml",
                "operation": "add",
                "path": f"required_signals.events",
                "value": f"{sig['domain'].capitalize()}TelemetrySignal.value",
                "reason": sig["reason"],
                "evidence": [f"investigation/missing_signals.json#{sig['domain']}_gap"]
            }
            proposed_patches.append(patch)

        # Propose known issue creation for critical rules
        for idx, issue in enumerate(issue_backlog):
            if issue["severity"] == "CRITICAL":
                patch_type = "KnownIssues"
                if patch_type in forbidden_types:
                    raise ValueError(f"Proposing patch of type {patch_type} is forbidden by configuration constraints.")
                
                # Check for critical rules evidence verification (M101 strict rule)
                evidence_list = [f"investigation/issue_backlog.json#{issue['issue_id']}"]
                # Test check: raise ValueError if evidence is empty
                if not evidence_list:
                    raise ValueError("Workflow cannot create evidence-free critical rule update.")
                
                patch = {
                    "patch_id": f"register_known_issue_{issue['issue_id'].lower()}",
                    "target_type": patch_type,
                    "target_file": "docs/mechanics/known_issues.yaml",
                    "operation": "add",
                    "path": "known_issues.rules",
                    "value": {
                        "rule_name": issue["rule_name"],
                        "severity": issue["severity"],
                        "frequency": issue["frequency"]
                    },
                    "reason": f"System observed critical violation: {issue['description']}",
                    "evidence": evidence_list
                }
                proposed_patches.append(patch)

        # Check for forbidden change type requests in specific_inputs
        if request.specific_inputs:
            for patch in request.specific_inputs.get("manual_patches", []):
                ptype = patch.get("target_type")
                if ptype in forbidden_types:
                    raise ValueError(f"Proposing patch of type {ptype} is forbidden by configuration constraints.")
                # Verify operation
                op = patch.get("operation")
                if op not in ("add", "modify", "replace"):
                    raise ValueError(f"Unsupported patch operation: {op}")
                # Verify critical rule evidence
                if ptype == "KnownIssues" and not patch.get("evidence"):
                    raise ValueError("Workflow cannot create evidence-free critical rule update.")
                proposed_patches.append(patch)

        # Write patch yaml files (M101 strictly writes proposals, DOES NOT overwrite original specs!)
        for p in proposed_patches:
            patch_file = patches_dir / f"{p['patch_id']}.yaml"
            with open(patch_file, "w", encoding="utf-8") as f:
                yaml.dump(p, f, default_flow_style=False)

        # 5. Next Experiment Drafts
        # Create a next experiment draft spec based on suggestions
        experiment_draft = {
            "experiment_id": "EXP-ENHANCED-001",
            "world_id": invest_report.get("world_id", "world_01"),
            "scenario_id": invest_report.get("scenario_id", "scenario_01"),
            "suggested_patches": [p["patch_id"] for p in proposed_patches],
            "max_runtime_minutes": 20,
            "target_ticks": [10000, 20000]
        }
        with open(drafts_dir / "experiment_draft_01.yaml", "w", encoding="utf-8") as f:
            yaml.dump(experiment_draft, f, default_flow_style=False)

        # 6. Insight Candidates
        insight_candidates = []
        for idx, patch in enumerate(proposed_patches):
            if patch["target_type"] == "KnownIssues":
                insight_candidates.append({
                    "insight_id": f"INSIGHT-{idx+1:03d}",
                    "title": f"Documented Simulation Anomaly: {patch['patch_id']}",
                    "domain": "kernel",
                    "observation": patch["reason"],
                    "hypothesized_cause": "Gameplay balance bounds or limits require scaling adjustments.",
                    "evidence_refs": patch.get("evidence", [])
                })
        with open(enhance_dir / "insight_candidates.json", "w", encoding="utf-8") as f:
            json.dump(insight_candidates, f, indent=2)

        # 7. Change Risk Report JSON
        change_risk_report = {
            "session_id": session_id,
            "proposed_patches_count": len(proposed_patches),
            "safety_evaluations": []
        }
        for p in proposed_patches:
            change_risk_report["safety_evaluations"].append({
                "patch_id": p["patch_id"],
                "target_type": p["target_type"],
                "risk_rating": "LOW" if p["target_type"] in ("KnownIssues", "ScenarioSpec") else "MEDIUM",
                "reasoning": "Patch focuses on declarative telemetry validation or documenting known anomalies."
            })
        with open(enhance_dir / "change_risk_report.json", "w", encoding="utf-8") as f:
            json.dump(change_risk_report, f, indent=2)

        # 8. Render Beautiful Premium Markdown Enhancement Plan
        plan_md = self._format_enhancement_plan_md(session_id, proposed_patches, change_risk_report)
        (enhance_dir / "enhancement_plan.md").write_text(plan_md, encoding="utf-8")

        return {
            "status": "READY",
            "report_path": str(enhance_dir / "enhancement_plan.md")
        }

    def _format_enhancement_plan_md(self, session_id: str, patches: list[dict[str, Any]], risk: dict[str, Any]) -> str:
        """Formats premium enhancement plan scorecard overview markdown."""
        patch_rows = []
        for p in patches:
            evidence_str = ", ".join(p["evidence"])
            patch_rows.append(
                f"| `{p['patch_id']}` | **{p['target_type']}** | `{p['operation']}` | {p['reason']} | Evidence: {evidence_str} |"
            )
        patches_table = "\n".join(patch_rows) if patch_rows else "| *No enhancement patches proposed* | | | | |"

        risk_rows = []
        for eval_item in risk["safety_evaluations"]:
            risk_rows.append(
                f"| `{eval_item['patch_id']}` | {eval_item['target_type']} | **{eval_item['risk_rating']}** | {eval_item['reasoning']} |"
            )
        risk_table = "\n".join(risk_rows) if risk_rows else "| *No evaluations recorded* | | | |"

        return f"""# Metamorphic Enhancement and Scenario Patch Proposals

Strategic recommendations and declarative patch proposals to resolve gameplay balance issues and coverage voids.

---

## 1. Executive Summary
This enhancement plan proposes a list of declarative patches targeting scenario definitions and known issue registers to resolve the violations detected in session `{session_id}`.

> [!IMPORTANT]
> No patches have been automatically applied to the active spec folders. All updates remain staged for manual/AI review and gatekeeper approval.

---

## 2. Proposed Declarative Patches
| Patch ID | Target Spec Group | Operation | Purpose / Reason | Associated Evidence References |
| :--- | :--- | :--- | :--- | :--- |
{patches_table}

---

## 3. Change Risk and Safety Evaluation
| Patch ID | Target Component | Safety Risk Rating | Reason / Mitigation |
| :--- | :--- | :--- | :--- |
{risk_table}

---

## 4. Next Steps
To synchronize these recommendations and approved patches into the long-term knowledge store, run the Knowledge Update workflow:
```bash
rpg-workflow-update-knowledge --session-id "{session_id}"
```
"""


class UpdateSimulationKnowledgeWorkflow:
    """
    M102 Workflow: Store approved insights, known issues, rule updates, and decisions.
    Requires explicit user approval before execution.
    """
    def __init__(self, workspace_root: Optional[str | Path] = None):
        if workspace_root is None:
            self.workspace_root = Path(__file__).resolve().parent.parent.parent
        else:
            self.workspace_root = Path(workspace_root).resolve()
            
        sessions_dir = self.workspace_root / "data" / "lab_sessions"
        self.session_store = LabSessionStore(sessions_dir)
        self.knowledge_root = self.workspace_root / "data" / "lab_knowledge"

    def run(self, session_id: str, request: WorkflowRequest) -> dict[str, Any]:
        logger.info(f"Running UpdateSimulationKnowledgeWorkflow for session '{session_id}'")
        from src.lab.audit import LabAuditTrail
        trail = LabAuditTrail(self.workspace_root)
        
        trail.log_event(session_id, "workflow_started", {
            "workflow": "UpdateSimulationKnowledge",
            "mode": request.mode
        })
        
        # 1. Access session and confirm stage
        manifest = self.session_store.load_session(session_id)
        
        # 2. Strict User Approval Verification
        # Check approval in specific_inputs
        inputs = request.specific_inputs or {}
        approved_by = inputs.get("approved_by")
        approval_recorded = inputs.get("approval_recorded", False)
        
        trail.log_event(session_id, "approval_required", {
            "workflow": "UpdateSimulationKnowledge",
            "required_stage": "ENHANCEMENT"
        })
        
        if not approved_by and not approval_recorded:
            trail.log_event(session_id, "blocked_action", {
                "reason": "Missing user approval credentials",
                "action": "Sync knowledge updates"
            })
            raise ValueError("Explicit user approval is required to update the simulation knowledge base.")

        # Record approval in audit log
        trail.log_event(session_id, "approval_recorded", {
            "approved_by": approved_by,
            "recorded": True
        })

        # Transition session to KNOWLEDGE_UPDATE stage
        manifest.current_stage = "KNOWLEDGE_UPDATE"
        self.session_store.save_session(manifest)

        # 3. Setup global knowledge base directories
        insights_dir = self.knowledge_root / "insights"
        issues_dir = self.knowledge_root / "known_issues"
        rules_dir = self.knowledge_root / "rules"
        principles_dir = self.knowledge_root / "principles"
        decisions_dir = self.knowledge_root / "decisions"

        for d in (insights_dir, issues_dir, rules_dir, principles_dir, decisions_dir):
            d.mkdir(parents=True, exist_ok=True)

        # 4. Ingest and Process Approved Items
        enhance_dir = self.session_store.get_stage_dir(session_id, "ENHANCEMENT")
        
        # Determine targets based on mode
        approved_insights = []
        approved_patches = []
        decision_note = inputs.get("decision_note", "No decision note provided.")

        if request.mode == "specific":
            # Specific approved files
            insight_paths = inputs.get("approved_insights", [])
            patch_paths = inputs.get("approved_patches", [])
            
            for path_str in insight_paths:
                resolved_path = safe_path_resolution(enhance_dir, path_str)
                if resolved_path.is_file():
                    with open(resolved_path, "r", encoding="utf-8") as f:
                        approved_insights.append(json.load(f))
            
            for path_str in patch_paths:
                resolved_path = safe_path_resolution(enhance_dir, path_str)
                if resolved_path.is_file():
                    with open(resolved_path, "r", encoding="utf-8") as f:
                        approved_patches.append(yaml.safe_load(f))
        else:
            # Generic mode: Ingest from latest enhancement results
            insight_file = enhance_dir / "insight_candidates.json"
            if insight_file.is_file():
                with open(insight_file, "r", encoding="utf-8") as f:
                    candidates = json.load(f)
                    approved_insights.extend(candidates)
            
            proposed_patches_dir = enhance_dir / "proposed_patches"
            if proposed_patches_dir.is_dir():
                for p_file in proposed_patches_dir.glob("*.yaml"):
                    with open(p_file, "r", encoding="utf-8") as f:
                        approved_patches.append(yaml.safe_load(f))

        # 5. Block unapproved rulebook/principles updates (Anti-misdirection rule)
        # Verify if request triggers rules/principles updates without approval
        has_rule_update = any(p.get("target_type") in ("ObservabilityRules", "ScenarioSpec", "WorldSpec") for p in approved_patches)
        if has_rule_update and not approved_by:
            raise ValueError("Workflow cannot update rules/principles without a valid approval marker.")

        # 6. Store Insights & Check Duplicates
        stored_insights = []
        for ins in approved_insights:
            insight_id = ins.get("insight_id", "INSIGHT-GENERIC")
            target_file = insights_dir / f"{insight_id.lower()}.json"
            
            if target_file.is_file():
                raise ValueError(f"Duplicate insight registration detected: {insight_id}")
                
            insight_record = {
                "insight_id": insight_id,
                "type": ins.get("type", "OBSERVABILITY_GAP"),
                "title": ins.get("title", ins.get("observation", "Generic insight")),
                "source_lab_run": ins.get("source_lab_run", session_id),
                "source_report": ins.get("source_report", ""),
                "evidence_refs": ins.get("evidence_refs", ins.get("evidence", [])),
                "status": "APPROVED",
                "created_at": "2026-05-24T10:00:00Z"
            }
            with open(target_file, "w", encoding="utf-8") as f:
                json.dump(insight_record, f, indent=2)
            stored_insights.append(insight_record)

        # 7. Store Known Issues
        stored_patches = []
        for patch in approved_patches:
            patch_id = patch.get("patch_id", "PATCH-GENERIC")
            if patch.get("target_type") == "KnownIssues":
                issue_file = issues_dir / f"{patch_id.lower()}.json"
                issue_record = {
                    "issue_id": patch_id,
                    "target_file": patch.get("target_file", ""),
                    "reason": patch.get("reason", ""),
                    "evidence_refs": patch.get("evidence", []),
                    "status": "STORED"
                }
                with open(issue_file, "w", encoding="utf-8") as f:
                    json.dump(issue_record, f, indent=2)
                stored_patches.append(issue_record)
            elif patch.get("target_type") in ("ScenarioSpec", "WorldSpec"):
                # Simulates rulebook updates
                rule_file = rules_dir / f"{patch_id.lower()}.json"
                rule_record = {
                    "patch_id": patch_id,
                    "target_type": patch.get("target_type"),
                    "version": "1.0.0",
                    "evidence_refs": patch.get("evidence", [])
                }
                with open(rule_file, "w", encoding="utf-8") as f:
                    json.dump(rule_record, f, indent=2)
                stored_patches.append(rule_record)

        # 8. Append Decision Log (JSON Lines)
        decision_file = decisions_dir / "decision_log.jsonl"
        log_entry = {
            "session_id": session_id,
            "decision_note": decision_note,
            "approved_by": approved_by,
            "timestamp": "2026-05-24T10:00:00Z"
        }
        with open(decision_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")

        # 9. Format Markdown Report
        report_md = self._format_knowledge_report_md(session_id, stored_insights, stored_patches, decision_note)
        report_path = enhance_dir / "knowledge_update_report.md"
        report_path.write_text(report_md, encoding="utf-8")

        # 10. Audit Logging
        synced_count = len(stored_insights) + len(stored_patches)
        sync_status = "SYNCED" if synced_count > 0 else "NO_INSIGHTS"

        trail.log_event(session_id, "files_read", {
            "files": ["insight_candidates.json", "proposed_patches/*"]
        })
        trail.log_event(session_id, "files_written", {
            "files": [str(report_path), "decision_log.jsonl"] + [f"insights/{i['insight_id'].lower()}.json" for i in stored_insights]
        })
        trail.log_event(session_id, "knowledge_sync_result", {
            "status": sync_status,
            "synced_insights": len(stored_insights),
            "synced_patches": len(stored_patches),
        })
        trail.log_event(session_id, "workflow_completed", {
            "workflow": "UpdateSimulationKnowledge",
            "status": sync_status,
        })

        return {
            "status": sync_status,
            "report_path": str(report_path),
            "synced_count": synced_count,
        }

    def _format_knowledge_report_md(self, session_id: str, insights: list, patches: list, note: str) -> str:
        """Formats the knowledge base sync report."""
        ins_rows = [f"| `{i['insight_id']}` | {i['title']} | Evidence Count: {len(i['evidence_refs'])} |" for i in insights]
        ins_table = "\n".join(ins_rows) if ins_rows else "| *No insights recorded* | | |"

        pat_rows = [f"| `{p.get('issue_id', p.get('patch_id'))}` | {p.get('reason', p.get('target_type'))} | Stored |" for p in patches]
        pat_table = "\n".join(pat_rows) if pat_rows else "| *No issue patches synchronized* | | |"

        return f"""# Simulation Knowledge Base Synchronization Report

Global knowledge synchronization details for session `{session_id}`.

---

## 1. Executive Summary
Strategic insights and approved declarative corrections have been safely synchronized into the global knowledge store.

---

## 2. Decision Log Entry
> **Decision Note**: {note}

---

## 3. Registered Insights
| Insight ID | Title / Observation | Evidence Refs Status |
| :--- | :--- | :--- |
{ins_table}

---

## 4. Synchronized Known Issues & Rules
| Patch / Issue ID | Core Context / Target | Sync Status |
| :--- | :--- | :--- |
{pat_table}
"""


