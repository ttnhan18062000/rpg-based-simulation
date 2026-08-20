import json
import logging
import os
from pathlib import Path
from typing import Optional
from unittest.mock import MagicMock

from src.lab.results import PrepareSimulationExecutionResult

# Core package imports
from src.lab.session import LabSessionStore
from src.lab.request import WorkflowRequest
from src.lab.validator import ScenarioValidator, ExperimentValidator
from src.lab.guardrails import LabBudgetGuardrails, BudgetCheckResult
from src.worldbuilding.schema import load_world_spec_from_yaml
from src.lab.schema import load_scenario_spec_from_yaml, load_experiment_spec_from_yaml
from src.lab.audit import LabAuditTrail
from src.lab.workflows._path_safety import safe_path_resolution

logger = logging.getLogger(__name__)

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

    def run(self, session_id: str, request: WorkflowRequest) -> PrepareSimulationExecutionResult:
        logger.info(f"Running PrepareSimulationExecutionWorkflow for session '{session_id}'")

        # 1. Resolve targeted paths safely
        manifest = self.session_store.load_session(session_id)
        manifest.current_stage = "EXECUTION_SUPPORT"
        self.session_store.save_session(manifest)
        trail = LabAuditTrail(self.workspace_root)
        trail.log_event(session_id, "workflow_started", {"workflow": "PrepareSimulationExecution"})

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

        trail.log_event(session_id, "workflow_completed", {"workflow": "PrepareSimulationExecution"})
        trail.log_event(session_id, "manual_boundary_declared", {
            "stage": "EXECUTION",
            "command_script": str(cmd_script_path.relative_to(self.workspace_root)),
        })
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
