# Compliance IDs: CLI-001, INFRA-013, INFRA-014, INFRA-017, INFRA-018, INFRA-020, INFRA-031, INFRA-050, INFRA-051, INFRA-059, INFRA-061, INFRA-066, INFRA-070
from __future__ import annotations
import argparse
import sys
import logging
import time
from pathlib import Path

from src.config.profiles import RuntimeProfile, HardwareClass
from src.engine.kernel import Kernel
from src.core.state import AuthoritativeState
from src.platform.rng import DeterministicRNG
from src.systems.world_systems.generator import EntityGenerator

logger = logging.getLogger(__name__)

def _build_parser():
    parser = argparse.ArgumentParser(description="Deterministic Concurrent RPG Engine (V2)")
    sub = parser.add_subparsers(dest="command")

    # Serve mode
    srv = sub.add_parser("serve", help="Start the FastAPI server")
    srv.add_argument("--host", type=str, default="127.0.0.1")
    srv.add_argument("--port", type=int, default=8000)
    srv.add_argument("--seed", type=int, default=None)
    srv.add_argument("--entities", type=int, default=None)
    srv.add_argument("--workers", type=int, default=None)
    srv.add_argument("--log-level", type=str, default="INFO")

    # CLI mode
    cli = sub.add_parser("cli", help="Headless CLI simulation")
    cli.add_argument("--ticks", type=int, default=None)
    cli.add_argument("--entities", type=int, default=None)
    cli.add_argument("--seed", type=int, default=None)
    cli.add_argument("--workers", type=int, default=None)
    cli.add_argument("--replay", type=str, default=None)
    cli.add_argument("--log-level", type=str, default="INFO")

    # Inspect mode
    insp = sub.add_parser("inspect", help="Inspect entity state")
    insp.add_argument("--id", type=int, required=True)
    insp.add_argument("--seed", type=int, default=42)
    insp.add_argument("--ticks", type=int, default=10)
    insp.add_argument("--log-level", type=str, default="INFO")

    # Sweep mode
    swp = sub.add_parser("sweep", help="Execute simulation run sweep matrix")
    swp.add_argument("config_path", type=str, help="Path to sweep config JSON file")

    # List sweeps subcommand
    sub.add_parser("list-sweeps", help="List all executed multi-run sweeps")

    # Inspect sweep subcommand
    ins_swp = sub.add_parser("inspect-sweep", help="Inspect detailed sweep summary")
    ins_swp.add_argument("sweep_id", type=str, help="ID of the sweep to inspect")

    # Generate baseline subcommand
    gen_bs = sub.add_parser("generate-baseline", help="Generate scenario baseline from sweep outcomes")
    gen_bs.add_argument("sweep_id", type=str, help="ID of the sweep to generate baseline for")

    # Compare run subcommand
    comp_rn = sub.add_parser("compare-run", help="Compare a single simulation run report against baseline thresholds")
    comp_rn.add_argument("run_id", type=str, help="ID of the run to compare")
    comp_rn.add_argument("--baseline", type=str, required=True, help="Path to baseline.json file")
    comp_rn.add_argument("--envelope", type=str, default=None, help="Path to balance_envelope.json file")

    # Compare sweep subcommand
    comp_swp = sub.add_parser("compare-sweep", help="Compare a multi-run sweep index against baseline thresholds")
    comp_swp.add_argument("sweep_id", type=str, help="ID of the sweep matrix to compare")
    comp_swp.add_argument("--baseline", type=str, required=True, help="Path to baseline.json file")
    comp_swp.add_argument("--envelope", type=str, default=None, help="Path to balance_envelope.json file")

    # Gate subcommand
    gate_cmd = sub.add_parser("gate", help="Evaluate scenario sweep outcomes against baseline with CI gating")
    gate_cmd.add_argument("sweep_id", type=str, help="ID of the sweep matrix to evaluate")
    gate_cmd.add_argument("--baseline", type=str, required=True, help="Path to baseline.json file")
    gate_cmd.add_argument("--envelope", type=str, default=None, help="Path to balance_envelope.json file")
    gate_cmd.add_argument("--warn-as-fail", action="store_true", help="Fail CI if warnings are raised")
    gate_cmd.add_argument("--insufficient-as-fail", action="store_true", help="Fail CI if insufficient data is detected")

    # Global options
    parser.add_argument("--config", type=str, default=None, help="Path to YAML config file")
    parser.add_argument("--json-logs", action="store_true", help="Enable JSON-formatted logging")
    
    return parser



def _run_cli(args):
    # Setup logging
    from src.logging.formatter import setup_v2_logging
    setup_v2_logging(level=args.log_level, json_format=args.json_logs)
    
    from src.config.loader import ConfigLoader
    cli_overrides = {
        "max_worker_count": args.workers
    }
    profile = ConfigLoader.load_profile(
        profile_name="cli_default",
        config_path=args.config,
        cli_overrides=cli_overrides
    )
    logging.info(f"Loaded Profile: {profile}")
    
    ticks = args.ticks if args.ticks is not None else 100
    entities_count = args.entities if args.entities is not None else 10
    seed = args.seed if args.seed is not None else 42

    rng = DeterministicRNG(seed)
    gen = EntityGenerator(seed)
    
    # Use DeterministicRNG for initial positions (Phase 2 Law: No bare random)
    from src.core.enums import Domain
    init_rng = DeterministicRNG(seed)
    
    entities = {}
    # Spawn hero at center
    hero = gen.spawn_hero((64.0, 64.0))
    entities[hero.id] = hero
    
    # Spawn monsters
    for i in range(entities_count - 1):
        monster = gen.spawn_goblin((
            64.0 + (init_rng.get_float(Domain.INIT, 0, i, sub_id=0) * 40 - 20), 
            64.0 + (init_rng.get_float(Domain.INIT, 0, i, sub_id=1) * 40 - 20)
        ))
        entities[monster.id] = monster
        
    state = AuthoritativeState(
        tick=0,
        seed=seed,
        entities=entities
    )
    
    # Handle replay path override
    replay_manager = None
    if args.replay:
        from src.engine.replay_manager import ReplayManager as DefaultReplayManager
        replay_path = Path(args.replay)
        replay_manager = DefaultReplayManager(
            run_dir=replay_path,
            profile_name=profile.name,
            buffer_capacity_kb=profile.max_replay_buffer_kb
        )
    
    kernel = Kernel(profile=profile, state=state, rng=rng, replay=replay_manager)
    
    print(f"V2 Simulation Started: seed={seed}, entities={entities_count}, ticks={ticks}")
    if args.replay:
        print(f"Replay Path: {args.replay}")
    
    start_time = time.time()
    
    try:
        for _ in range(ticks):
            kernel.tick_once()
            if kernel.state.tick % 10 == 0:
                print(f"Tick {kernel.state.tick} complete.")
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    except Exception as e:
        print(f"\nSimulation error: {e}")
        raise
            
    end_time = time.time()
    print(f"Simulation finished in {end_time - start_time:.2f}s")
    
    outcome = kernel.shutdown()
    print(f"Final State Hash: {outcome.final_hash}")
    print(f"Replay Artifacts: {outcome.replay_outcome}")

def _run_serve(args):
    """Start the FastAPI server."""
    import uvicorn
    from src.api.server import create_v2_app
    from src.config.loader import ConfigLoader
    
    # Setup logging
    from src.logging.formatter import setup_v2_logging
    setup_v2_logging(level=args.log_level, json_format=args.json_logs)
    
    cli_overrides = {
        "max_worker_count": args.workers
    }
    profile = ConfigLoader.load_profile(
        profile_name="cli_default",
        config_path=args.config,
        cli_overrides=cli_overrides
    )
    
    app = create_v2_app(profile)
    
    logger.info(f"Starting V2 server on {args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port, log_level=args.log_level.lower())

def _run_sweep(args):
    """Start multi-run sweep execution."""
    import json
    # Setup logging
    from src.logging.formatter import setup_v2_logging
    setup_v2_logging(level="INFO", json_format=args.json_logs)

    config_path = Path(args.config_path)
    if not config_path.exists():
        print(f"Sweep config file not found: {config_path}")
        sys.exit(1)

    with open(config_path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except Exception as e:
            print(f"Failed to parse sweep config JSON: {e}")
            sys.exit(1)

    from src.observability.sweeper import ScenarioSweepConfig, ScenarioSweeper
    try:
        config = ScenarioSweepConfig.model_validate(data)
    except Exception as e:
        print(f"Invalid sweep configuration: {e}")
        sys.exit(1)

    print(f"Starting Multi-Run Sweep: ID={config.sweep_id or 'Auto'}, Scenario={config.scenario_name}, Seeds={config.seeds}")
    
    manifest = ScenarioSweeper.run_sweep(config)
    
    print("\n--- Sweep Execution Completed ---")
    print(f"Sweep ID: {manifest.sweep_id}")
    print(f"Status: {manifest.status}")
    print(f"Total Ticks: {manifest.ticks_requested}")
    print(f"Completed Runs: {manifest.completed_count}")
    print(f"Failed Runs: {manifest.failed_count}")
    if manifest.failures:
        print("\nFailures:")
        for rid, err in manifest.failures.items():
            print(f"  - {rid}: {err}")

def _run_list_sweeps(args):
    """List all executed sweeps."""
    from src.observability.reporting.run_set_repository import RunSetArtifactRepository
    
    repo = RunSetArtifactRepository()
    sweeps = repo.list_sweeps()
    
    if not sweeps:
        print("No multi-seed sweeps found under data/run_sets/.")
        return
        
    print(f"{'SWEEP ID':<35} {'SCENARIO':<15} {'STATUS':<12} {'RUNS':<6}")
    print("-" * 72)
    for sweep_id, manifest in sweeps.items():
        runs_count = len(manifest.run_ids)
        print(f"{sweep_id:<35} {manifest.scenario_name:<15} {manifest.status:<12} {runs_count:<6}")

def _run_inspect_sweep(args):
    """Inspect summary details of a specific sweep."""
    import sys
    from src.observability.reporting.run_set_repository import RunSetArtifactRepository
    
    repo = RunSetArtifactRepository()
    sweep_id = args.sweep_id
    
    sweeps = repo.list_sweeps()
    if sweep_id not in sweeps:
        print(f"Sweep '{sweep_id}' not found under data/run_sets/.")
        sys.exit(1)
        
    manifest = sweeps[sweep_id]
    
    try:
        summary = repo.read_sweep_summary(sweep_id)
    except Exception as e:
        print(f"Failed to load sweep summary: {e}")
        print(f"Sweep ID: {manifest.sweep_id}")
        print(f"Scenario: {manifest.scenario_name} ({manifest.scenario_type})")
        print(f"Status:   {manifest.status}")
        return
        
    print(f"=== Sweep Observatory: {summary.sweep_id} ===")
    print(f"Scenario:          {summary.scenario_name} ({summary.scenario_type})")
    print(f"Status:            {manifest.status}")
    print(f"Time Range:        {manifest.started_at} to {manifest.ended_at or 'Running'}")
    print(f"Runs Executed:     {summary.total_runs} (Completed: {summary.completed_runs}, Failed: {summary.failed_runs})")
    print(f"Avg Health Score:  {summary.average_health_score:.1f}%")
    print(f"Critical Runs:     {summary.critical_run_count}")
    print(f"Warning Runs:      {summary.warning_run_count}")
    print(f"Best Run:          {summary.best_run_id or 'None'}")
    print(f"Worst Run:         {summary.worst_run_id or 'None'}")
    
    if summary.most_common_anomaly_rule_ids:
        print("\nAnomalies Encountered:")
        sorted_anom = sorted(summary.most_common_anomaly_rule_ids.items(), key=lambda x: x[1], reverse=True)
        for rule_id, count in sorted_anom:
            print(f"  - {rule_id}: {count} occurrences")
            
    records = repo.read_run_index(sweep_id)
    if records:
        print("\nRun Matrix Details:")
        print(f"  {'RUN ID':<40} {'SEED':<6} {'STATUS':<10} {'HEALTH':<6}")
        print("  " + "-" * 66)
        for r in records:
            print(f"  {r.run_id:<40} {r.seed:<6} {r.status:<10} {r.health_score:>5.1f}%")

def _run_generate_baseline(args):
    """Generate statistical baseline from a sweep set."""
    import sys
    from src.observability.reporting.baseline_generator import BaselineGenerator
    
    sweep_id = args.sweep_id
    print(f"Generating statistical baseline for sweep: {sweep_id}...")
    
    try:
        baseline = BaselineGenerator.generate_baseline(sweep_id)
    except Exception as e:
        print(f"Failed to generate baseline: {e}")
        sys.exit(1)
        
    print(f"Baseline successfully generated: {baseline.baseline_id}")
    print(f"Scenario:     {baseline.scenario_name} ({baseline.scenario_type})")
    print(f"Runs:         {baseline.accepted_run_count} accepted (out of {baseline.run_count})")
    
    if baseline.is_weak_baseline:
        print("WARNING: Sample size is extremely small (< 5 runs). This baseline is flagged as WEAK and has low statistical confidence.")
        
    print("\nCalculated Distribution Metrics:")
    for metric, dist in baseline.metrics.items():
        print(f"  - {metric:<26}: Mean={dist.mean:>7.2f}, p10={dist.p10:>7.2f}, p50={dist.p50:>7.2f}, p90={dist.p90:>7.2f}, p95={dist.p95:>7.2f}")
        
    print("\nRecommended Threshold Rules:")
    for metric, spec in baseline.threshold_recommendations.items():
        print(f"  - {metric:<26} {spec.comparison_operator} {spec.threshold_value:>7.2f}")

def _run_compare_run(args):
    """Compare a single run against a baseline."""
    import sys
    from src.observability.reporting.baseline_comparator import BaselineComparator
    
    run_id = args.run_id
    baseline_path = args.baseline
    envelope_path = getattr(args, "envelope", None)
    if envelope_path and not isinstance(envelope_path, str):
        envelope_path = None
    
    if envelope_path:
        print(f"Comparing run {run_id} against baseline {baseline_path} with envelope {envelope_path}...")
    else:
        print(f"Comparing run {run_id} against baseline {baseline_path}...")
    
    try:
        res = BaselineComparator.compare_run(run_id, baseline_path, envelope_path=envelope_path)
    except Exception as e:
        print(f"Failed to compare run: {e}")
        sys.exit(1)
        
    print(f"\nComparison Result: {res.status}")
    if res.envelope_name:
        print(f"Envelope Name:     {res.envelope_name}")
    print(f"Summary:           {res.summary}\n")
    
    print(f"  {'METRIC':<26} {'BASELINE/TARGET':<16} {'ACTUAL':<12} {'STATUS':<10}")
    print(f"  " + "-" * 70)
    for metric, comp in res.metric_comparisons.items():
        print(f"  {metric:<26} {comp.baseline_value:>16.2f} {comp.actual_value:>12.2f} {comp.status:<10}")
        
    if res.status == "FAIL":
        sys.exit(1)
    sys.exit(0)

def _run_compare_sweep(args):
    """Compare a sweep against a baseline."""
    import sys
    from src.observability.reporting.baseline_comparator import BaselineComparator
    
    sweep_id = args.sweep_id
    baseline_path = args.baseline
    envelope_path = getattr(args, "envelope", None)
    if envelope_path and not isinstance(envelope_path, str):
        envelope_path = None
    
    if envelope_path:
        print(f"Comparing sweep {sweep_id} against baseline {baseline_path} with envelope {envelope_path}...")
    else:
        print(f"Comparing sweep {sweep_id} against baseline {baseline_path}...")
    
    try:
        res = BaselineComparator.compare_sweep(sweep_id, baseline_path, envelope_path=envelope_path)
    except Exception as e:
        print(f"Failed to compare sweep: {e}")
        sys.exit(1)
        
    print(f"\nComparison Result: {res.status}")
    if res.envelope_name:
        print(f"Envelope Name:     {res.envelope_name}")
    print(f"Summary:           {res.summary}\n")
    
    if res.drifts:
        print("Statistical Metric Drifts:")
        print(f"  {'METRIC':<26} {'BASELINE MEAN':<15} {'SWEEP MEAN':<15} {'DRIFT':<15} {'MAGNITUDE':<10}")
        print(f"  " + "-" * 86)
        for metric, d in res.drifts.items():
            print(f"  {metric:<26} {d.baseline_mean:>15.2f} {d.sweep_mean:>15.2f} {d.drift_direction:<15} {d.magnitude:>+10.2f}")
            
    if res.status == "FAIL":
        sys.exit(1)
    sys.exit(0)

def _run_gate(args):
    """Run CI gate and generate scenario-level reports for a sweep."""
    import sys
    from src.observability.reporting.sweep_report import SweepReportGenerator
    
    sweep_id = args.sweep_id
    baseline_path = args.baseline
    envelope_path = getattr(args, "envelope", None)
    if envelope_path and not isinstance(envelope_path, str):
        envelope_path = None
        
    warn_as_fail = args.warn_as_fail
    insufficient_as_fail = args.insufficient_as_fail
    
    print(f"Executing CI Gate for sweep: {sweep_id}...")
    try:
        md_path, json_path, gate_result = SweepReportGenerator.generate(
            sweep_id=sweep_id,
            baseline_path=baseline_path,
            envelope_path=envelope_path,
            warn_as_fail=warn_as_fail,
            insufficient_as_fail=insufficient_as_fail
        )
    except Exception as e:
        print(f"Failed executing CI Gate: {e}")
        sys.exit(1)
        
    print(f"\nCI Gate Evaluation Result: {gate_result.status}")
    print(f"Message:                  {gate_result.message}")
    print(f"Baseline ID:              {gate_result.baseline_id}")
    print(f"Markdown Report Generated: {md_path}")
    print(f"JSON Report Generated:     {json_path}")
    
    if gate_result.failed_runs:
        print(f"Crashed/Failed Runs ({len(gate_result.failed_runs)}): {', '.join(gate_result.failed_runs)}")
    if gate_result.outlier_runs:
        print(f"Outlier Run Seeds ({len(gate_result.outlier_runs)}): {', '.join(gate_result.outlier_runs)}")
    if gate_result.failed_metrics:
        print(f"Failed Telemetry Metrics: {', '.join(gate_result.failed_metrics)}")
        
    if gate_result.status == "FAIL":
        sys.exit(1)
    sys.exit(0)

def main():
    parser = _build_parser()
    
    # Handle default mode (no subcommand)
    if len(sys.argv) == 1:
        args = parser.parse_args(["serve"])
    else:
        args = parser.parse_args()
    
    if args.command == "cli":
        _run_cli(args)
    elif args.command == "serve":
        _run_serve(args)
    elif args.command == "sweep":
        _run_sweep(args)
    elif args.command == "list-sweeps":
        _run_list_sweeps(args)
    elif args.command == "inspect-sweep":
        _run_inspect_sweep(args)
    elif args.command == "generate-baseline":
        _run_generate_baseline(args)
    elif args.command == "compare-run":
        _run_compare_run(args)
    elif args.command == "compare-sweep":
        _run_compare_sweep(args)
    elif args.command == "gate":
        _run_gate(args)
    elif args.command == "inspect":
        print("V2 Inspect mode not yet fully implemented. Entity state inspection logic pending M4.")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
