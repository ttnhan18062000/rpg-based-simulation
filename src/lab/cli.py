import sys
import argparse
import json
from pathlib import Path
from datetime import datetime, timezone

from src.worldbuilding.repository import WorldRepository
from src.worldbuilding.validator import WorldValidator
from src.lab import (
    ScenarioRepository,
    ExperimentRepository,
    LabRunRepository,
    ScenarioValidator,
    ExperimentValidator,
    ScenarioLabOrchestrator,
    LabResultStore,
    LabResultStoreError,
    LabRunManifest,
    BudgetBlockedError,
    BudgetWarningError
)

def main(args=None):
    parser = argparse.ArgumentParser(
        prog="rpg-lab",
        description="Scenario Lab CLI tool for simulation sweeps and validations"
    )
    
    # Global Repository overrides (highly useful for integration tests)
    parser.add_argument("--worlds-dir", default="data/worlds", help="Path to worlds specifications directory")
    parser.add_argument("--scenarios-dir", default="data/scenarios", help="Path to scenarios specifications directory")
    parser.add_argument("--experiments-dir", default="data/experiments", help="Path to experiments specifications directory")
    parser.add_argument("--lab-runs-dir", default="data/lab_runs", help="Path to lab runs output directory")
    
    subparsers = parser.add_subparsers(dest="command", help="Subcommand to run")
    
    # 1. validate-world
    p_val_world = subparsers.add_parser("validate-world", help="Validate a world specification")
    p_val_world.add_argument("world_id", help="World spec identifier")
    
    # 2. validate-scenario
    p_val_scen = subparsers.add_parser("validate-scenario", help="Validate a scenario specification")
    p_val_scen.add_argument("scenario_id", help="Scenario spec identifier")
    
    # 3. validate-experiment
    p_val_exp = subparsers.add_parser("validate-experiment", help="Validate an experiment specification")
    p_val_exp.add_argument("experiment_id", help="Experiment spec identifier")
    
    # 4. run
    p_run = subparsers.add_parser("run", help="Run a lab experiment sweep")
    p_run.add_argument("experiment_id", help="Experiment spec identifier to execute")
    p_run.add_argument("--lab-run-id", help="Optional custom lab run ID (auto-generated if omitted)")
    p_run.add_argument("--profile", default="local_dev", help="Lab security/execution profile (e.g. local_dev, CI)")
    p_run.add_argument("--force", action="store_true", help="Bypass blocked budget checks (if profile allows)")
    p_run.add_argument("--confirm", action="store_true", help="Confirm high-resource sweep executions under warning checks")
    
    # 5. status
    p_status = subparsers.add_parser("status", help="Get the status of an executed lab run")
    p_status.add_argument("lab_run_id", help="Lab run identifier")
    
    # 6. report
    p_report = subparsers.add_parser("report", help="Locate and show the lab summary report")
    p_report.add_argument("lab_run_id", help="Lab run identifier")
    
    # 7. list
    subparsers.add_parser("list", help="List all executed lab runs")
    
    # 8. inspect
    p_inspect = subparsers.add_parser("inspect", help="Output raw JSON of a lab summary")
    p_inspect.add_argument("lab_run_id", help="Lab run identifier")
    
    parsed = parser.parse_args(args)
    if not parsed.command:
        parser.print_help()
        sys.exit(0)
        
    # Setup repositories
    world_repo = WorldRepository(parsed.worlds_dir)
    scenario_repo = ScenarioRepository(parsed.scenarios_dir)
    experiment_repo = ExperimentRepository(parsed.experiments_dir)
    lab_run_repo = LabRunRepository(parsed.lab_runs_dir)
    result_store = LabResultStore(parsed.lab_runs_dir)
    
    try:
        if parsed.command == "validate-world":
            try:
                world_spec = world_repo.load_world(parsed.world_id)
                validator = WorldValidator()
                issues = validator.validate(world_spec)
                print(f"World spec '{parsed.world_id}' is VALID.")
                for issue in issues:
                    if issue.severity == "WARNING":
                        print(f"  - WARNING: [{issue.rule_id}] {issue.message}")
                sys.exit(0)
            except Exception as e:
                print(f"World spec '{parsed.world_id}' is INVALID: {e}", file=sys.stderr)
                sys.exit(1)
            
        elif parsed.command == "validate-scenario":
            try:
                scenario_spec = scenario_repo.load_scenario(parsed.scenario_id)
                validator = ScenarioValidator(world_repo)
                issues = validator.validate(scenario_spec)
                print(f"Scenario spec '{parsed.scenario_id}' is VALID.")
                for issue in issues:
                    if issue.severity == "WARNING":
                        print(f"  - WARNING: [{issue.rule_id}] {issue.message}")
                sys.exit(0)
            except Exception as e:
                print(f"Scenario spec '{parsed.scenario_id}' is INVALID: {e}", file=sys.stderr)
                sys.exit(1)
            
        elif parsed.command == "validate-experiment":
            try:
                experiment_spec = experiment_repo.load_experiment(parsed.experiment_id)
                validator = ExperimentValidator(scenario_repo)
                issues = validator.validate(experiment_spec)
                print(f"Experiment spec '{parsed.experiment_id}' is VALID.")
                for issue in issues:
                    if issue.severity == "WARNING":
                        print(f"  - WARNING: [{issue.rule_id}] {issue.message}")
                sys.exit(0)
            except Exception as e:
                print(f"Experiment spec '{parsed.experiment_id}' is INVALID: {e}", file=sys.stderr)
                sys.exit(1)
            
        elif parsed.command == "run":
            # Auto-generate lab run ID if not provided
            lab_run_id = parsed.lab_run_id
            if not lab_run_id:
                timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
                lab_run_id = f"labrun_{timestamp}"
                
            print(f"Executing lab experiment '{parsed.experiment_id}' (Lab Run ID: {lab_run_id})...")
            orchestrator = ScenarioLabOrchestrator(world_repo, scenario_repo, experiment_repo, lab_run_repo)
            
            try:
                manifest = orchestrator.run_lab(
                    parsed.experiment_id,
                    lab_run_id,
                    profile=parsed.profile,
                    force=parsed.force,
                    confirm=parsed.confirm
                )
            except BudgetBlockedError as e:
                print(f"Budget Error: {e}", file=sys.stderr)
                print("To bypass this block, you must run with --force (if the execution profile permits it).", file=sys.stderr)
                sys.exit(2)
            except BudgetWarningError as e:
                print(f"Budget Warning: {e}", file=sys.stderr)
                print("To execute this sweep, you must acknowledge the budget warnings by supplying --confirm.", file=sys.stderr)
                sys.exit(3)
            
            print(f"Lab Execution Finished.")
            print(f"  Status: {manifest.status}")
            print(f"  Completed Runs: {manifest.completed_run_count}/{manifest.run_count}")
            print(f"  Failed Runs: {manifest.failed_run_count}/{manifest.run_count}")
            print(f"  Artifact Root: {manifest.artifact_root}")
            
            if manifest.status == "FAILED":
                sys.exit(1)
            sys.exit(0)
            
        elif parsed.command == "status":
            manifest = result_store.load_lab_run_manifest(parsed.lab_run_id)
            print(f"Lab Run: {manifest.lab_run_id}")
            print(f"  Status: {manifest.status}")
            print(f"  Experiment ID: {manifest.experiment_id}")
            print(f"  Scenario ID: {manifest.scenario_id}")
            print(f"  World ID: {manifest.world_id}")
            print(f"  Progress: {manifest.completed_run_count}/{manifest.run_count} completed, {manifest.failed_run_count} failed")
            print(f"  Storage Footprint: {manifest.storage_usage_mb:.3f} MB")
            sys.exit(0)
            
        elif parsed.command == "report":
            manifest = result_store.load_lab_run_manifest(parsed.lab_run_id)
            report_path = Path(manifest.artifact_root) / "lab_summary.md"
            if not report_path.is_file():
                print(f"Error: Summary report markdown file not found for lab run '{parsed.lab_run_id}'", file=sys.stderr)
                sys.exit(1)
            print(f"Lab Summary Report Path: {report_path.resolve()}")
            sys.exit(0)
            
        elif parsed.command == "list":
            index = result_store.get_index()
            if not index:
                print("No lab runs found.")
                sys.exit(0)
                
            print(f"{'LAB RUN ID':<30} {'EXPERIMENT ID':<30} {'STATUS':<15} {'STORAGE (MB)':<12} {'STARTED AT'}")
            print("-" * 100)
            for record in index.values():
                print(f"{record['lab_run_id']:<30} {record['experiment_id']:<30} {record['status']:<15} {record['storage_usage_mb']:<12.3f} {record['started_at']}")
            sys.exit(0)
            
        elif parsed.command == "inspect":
            summary = result_store.load_lab_summary(parsed.lab_run_id)
            print(json.dumps(summary, indent=2))
            sys.exit(0)
            
    except FileNotFoundError as e:
        print(f"Error: File or resource not found: {e}", file=sys.stderr)
        sys.exit(1)
    except PermissionError as e:
        print(f"Security Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Execution Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
