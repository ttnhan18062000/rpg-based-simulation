import json
import logging
import yaml
from pathlib import Path
from typing import Optional, Any, Dict
from unittest.mock import MagicMock

from src.lab.results import GenerateSimulationSetupResult

# Core package imports
from src.lab.session import LabSessionStore
from src.lab.request import WorkflowRequest
from src.lab.context import ContextPackBuilder
from src.lab.validator import (
    ScenarioValidator,
    ExperimentValidator,
    InvalidScenarioSpecError,
    InvalidExperimentSpecError
)
from src.lab.guardrails import LabBudgetGuardrails
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
from src.lab.schema import (
    ScenarioSpec,
    IntentSpec,
    ExpectedLimitSpec,
    RequiredSignalsSpec,
    ExperimentSpec,
    ExperimentRunSpec,
    ExperimentObservabilitySpec,
    ExperimentAnalysisSpec,
    ExperimentRetentionSpec,
    ExperimentBudgetsSpec
)
from src.lab.audit import LabAuditTrail

logger = logging.getLogger(__name__)

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

    def run(self, session_id: str, request: WorkflowRequest, limits: Optional[Dict[str, Any]] = None) -> GenerateSimulationSetupResult:
        logger.info(f"Running GenerateSimulationSetupWorkflow for session '{session_id}' in mode '{request.mode}'")

        # 1. Access lab session
        manifest = self.session_store.load_session(session_id)
        manifest.current_stage = "GENERATION"
        self.session_store.save_session(manifest)
        trail = LabAuditTrail(self.workspace_root)
        trail.log_event(session_id, "workflow_started", {"workflow": "GenerateSimulationSetup"})

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
        trail.log_event(session_id, "workflow_completed", {"workflow": "GenerateSimulationSetup"})

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
