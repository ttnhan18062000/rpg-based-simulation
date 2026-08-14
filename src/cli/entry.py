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
    cli.add_argument("--world", type=str, default=None, help="Name of custom world specification folder to load and compile")
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

    # Export subcommand
    exp_parser = sub.add_parser("export", help="Export a single run artifact set")
    exp_parser.add_argument("run_id", type=str, help="ID of the run to export")
    exp_parser.add_argument("--format", type=str, choices=["jsonl", "parquet"], default="parquet", help="Target serialization format")

    # Export sweep subcommand
    exp_swp = sub.add_parser("export-sweep", help="Export a scenario sweep artifact set")
    exp_swp.add_argument("sweep_id", type=str, help="ID of the sweep to export")
    exp_swp.add_argument("--format", type=str, choices=["jsonl", "parquet"], default="parquet", help="Target serialization format")

    # Build dataset subcommand
    bld_ds = sub.add_parser("build-dataset", help="Compile scenario sweep artifacts into a local Parquet dataset")
    bld_ds.add_argument("sweep_id", type=str, help="ID of the sweep to compile")

    # Query dataset subcommand
    qry_ds = sub.add_parser("query-dataset", help="Execute a predefined DuckDB query on a built dataset")
    qry_ds.add_argument("dataset_id", type=str, help="ID of the dataset to query")
    qry_ds.add_argument("--query", type=str, choices=["worst-runs", "anomaly-summary"], required=True, help="Target predefined query")

    # Worker subcommand
    wrk_parser = sub.add_parser("worker", help="Standalone off-loop worker management")
    wrk_sub = wrk_parser.add_subparsers(dest="worker_command", required=True)
    wrk_an = wrk_sub.add_parser("analyze-run", help="Analyze a single run out-of-process")
    wrk_an.add_argument("run_id", type=str, help="ID of the completed run to analyze")

    # Retention subcommand
    ret_parser = sub.add_parser("retention", help="Retention and data lifecycle management")
    ret_sub = ret_parser.add_subparsers(dest="retention_command", required=True)
    ret_sub.add_parser("plan", help="Dry-run scan of expired/prunable observability files")
    ret_clean = ret_sub.add_parser("clean", help="Perform confirmation clean of expired logs")
    ret_clean.add_argument("--confirm", action="store_true", help="Confirm execution of prunes")

    # Warehouse subcommand
    wh_parser = sub.add_parser("warehouse", help="Database warehouse ingestion management")
    wh_sub = wh_parser.add_subparsers(dest="warehouse_command", required=True)
    
    wh_sub.add_parser("init", help="Initialize database warehouse schemas")
    
    wh_ing = wh_sub.add_parser("ingest-run", help="Ingest a single run artifact set")
    wh_ing.add_argument("run_id", type=str, help="ID of the completed run to ingest")
    wh_ing.add_argument("--dry-run", action="store_true", help="Perform schema mapping validation without writes")
    wh_ing.add_argument("--force", action="store_true", help="Overwrite existing database records for this run")
    
    wh_swp = wh_sub.add_parser("ingest-sweep", help="Ingest a multi-run sweep")
    wh_swp.add_argument("sweep_id", type=str, help="ID of the sweep to ingest")
    wh_swp.add_argument("--dry-run", action="store_true", help="Perform schema mapping validation without writes")
    wh_swp.add_argument("--force", action="store_true", help="Overwrite existing database records for this sweep")

    wh_qry = wh_sub.add_parser("query", help="Execute analytical database query")
    wh_qry_sub = wh_qry.add_subparsers(dest="query_command", required=True)
    
    wh_qry_worst = wh_qry_sub.add_parser("worst-runs", help="Fetch worst runs by health score")
    wh_qry_worst.add_argument("--limit", type=int, default=10, help="Max run records to return")
    
    wh_qry_events = wh_qry_sub.add_parser("entity-events", help="Fetch simulation event log of an entity")
    wh_qry_events.add_argument("--entity-id", type=str, required=True, help="Target entity unique ID")
    wh_qry_events.add_argument("--limit", type=int, default=50, help="Max events to return")

    # Cognition subcommand group
    cog_parser = sub.add_parser("cognition", help="Inspect strategic cognition data")
    cog_sub = cog_parser.add_subparsers(dest="cognition_command", required=True)
    
    # Snapshot sub-subcommand
    cog_snap = cog_sub.add_parser("snapshot", help="Query paginated cognition snapshots for an entity")
    cog_snap.add_argument("run_id", type=str, help="ID of the completed simulation run")
    cog_snap.add_argument("entity_id", type=str, help="ID of the target entity")
    cog_snap.add_argument("--page", type=int, default=1, help="Page number")
    cog_snap.add_argument("--page-size", type=int, default=20, help="Page size")
    cog_snap.add_argument("--full-graph", action="store_true", help="Include full nodes and edges details")

    # Diff sub-subcommand
    cog_diff = cog_sub.add_parser("diff", help="Retrieve all strategic graph diffs for an entity")
    cog_diff.add_argument("run_id", type=str, help="ID of the completed simulation run")
    cog_diff.add_argument("entity_id", type=str, help="ID of the target entity")

    # Features sub-subcommand
    cog_feat = cog_sub.add_parser("features", help="Retrieve feature timeline data for an entity")
    cog_feat.add_argument("run_id", type=str, help="ID of the completed simulation run")
    cog_feat.add_argument("entity_id", type=str, help="ID of the target entity")

    # Patterns sub-subcommand
    cog_patt = cog_sub.add_parser("patterns", help="Retrieve all strategic failure patterns for a run")
    cog_patt.add_argument("run_id", type=str, help="ID of the completed simulation run")

    # Diagnostics subcommand group
    diag_parser = sub.add_parser("diagnostics", help="Runtime resource diagnostics")
    diag_sub = diag_parser.add_subparsers(dest="diagnostics_command", required=True)

    # resources sub-subcommand
    diag_res = diag_sub.add_parser("resources", help="Show per-subsystem resource pressure snapshot")
    diag_res.add_argument("--run-id", type=str, default=None, help="Run ID for offline mode")
    diag_res.add_argument("--format", dest="fmt", choices=["table", "json"], default="table",
                          help="Output format (default: table)")

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
    seed = args.seed if args.seed is not None else 42

    rng = DeterministicRNG(seed)

    # Resolve world specification ID (fallback cleanly to 'sandbox_world' default spec)
    world_id = args.world if args.world is not None else "sandbox_world"

    # Load and compile the custom world spec using WorldRepository and WorldCompiler
    from src.worldbuilding.repository import WorldRepository
    from src.worldbuilding.compiler import WorldCompiler

    logging.info(f"Loading and compiling world specification: {world_id}...")
    repo = WorldRepository("data/worlds")
    # TCK-20260808-MONSTER-ROLE-MISTAGGING-INVESTIGATION: load_world_with_context() (not
    # load_world()) surfaces the compile_context.json role/faction mapping
    # WorldCompiler.compile() needs to correctly resolve entity.identity.role/.faction for
    # real, catalog-driven monster archetypes -- without it, resolution silently falls back to
    # naive keyword matching, defaulting almost every monster to CITIZEN.
    spec, context = repo.load_world_with_context(world_id)

    state, compile_report = WorldCompiler.compile(spec, seed=seed, context=context)
    logging.info(f"World successfully compiled! Entities spawned: {compile_report['entity_count']}, Hash: {compile_report['state_hash']}")
    
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
    
    kernel = Kernel(profile=profile, state=state, rng=rng, replay=replay_manager, world_id=world_id)
    
    print(f"V2 Simulation Started: seed={seed}, entities={len(state.entities)}, ticks={ticks}")
    if args.replay:
        print(f"Replay Path: {args.replay}")
    
    start_time = time.time()
    
    try:
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
    finally:
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

def _run_export(args):
    """Export a single run artifact set."""
    import os
    import sys
    from src.observability.reporting.artifact_repository import RunArtifactRepository
    from src.observability.analytics.exporter import ExportJob, ExportManager

    run_id = args.run_id
    fmt = args.format

    repo = RunArtifactRepository()
    run_dir = os.path.join(repo.base_dir, run_id)
    if not os.path.exists(run_dir):
        print(f"Run directory not found for ID: {run_id}")
        sys.exit(1)

    print(f"Exporting run {run_id} to format: {fmt}...")
    try:
        manager = ExportManager()
        job = ExportJob(
            source_run_id=run_id,
            source_path=run_dir,
            output_path=os.path.abspath(os.path.join("data/exports", f"export_{run_id}_{fmt}")),
            format=fmt,
            artifact_types=["simulation_events", "metric_windows", "hard_law_violations", "anomalies", "run_manifest"]
        )
        manifest = manager.execute_job(job)
        print(f"Export COMPLETED. Manifest saved: data/exports/{job.export_id}/export_manifest.json")
        print(f"Exported records: {manifest.record_counts}")
        if manifest.skipped_artifacts:
            print(f"Skipped artifacts: {manifest.skipped_artifacts}")
    except Exception as e:
        print(f"Export failed: {e}")
        sys.exit(1)

def _run_export_sweep(args):
    """Export an entire scenario sweep artifact set."""
    import os
    import sys
    from src.observability.reporting.run_set_repository import RunSetArtifactRepository
    from src.observability.analytics.exporter import ExportJob, ExportManager

    sweep_id = args.sweep_id
    fmt = args.format

    repo = RunSetArtifactRepository()
    sweep_dir = os.path.join(repo.base_dir, sweep_id)
    if not os.path.exists(sweep_dir):
        print(f"Sweep directory not found for ID: {sweep_id}")
        sys.exit(1)

    print(f"Exporting sweep {sweep_id} to format: {fmt}...")
    try:
        manager = ExportManager()
        job = ExportJob(
            source_sweep_id=sweep_id,
            source_path=sweep_dir,
            output_path=os.path.abspath(os.path.join("data/exports", f"export_{sweep_id}_{fmt}")),
            format=fmt,
            artifact_types=["simulation_events", "metric_windows", "hard_law_violations", "anomalies", "run_manifest", "run_index"]
        )
        manifest = manager.execute_job(job)
        print(f"Export COMPLETED. Manifest saved: data/exports/{job.export_id}/export_manifest.json")
        print(f"Exported files count: {len(manifest.output_files)}")
        if manifest.skipped_artifacts:
            print(f"Skipped artifacts: {manifest.skipped_artifacts}")
    except Exception as e:
        print(f"Sweep export failed: {e}")
        sys.exit(1)

def _run_build_dataset(args):
    """Compile scenario sweep artifacts into a local Parquet dataset."""
    import os
    import sys
    from src.observability.reporting.run_set_repository import RunSetArtifactRepository
    from src.observability.analytics.dataset import AnalyticsDatasetBuilder

    sweep_id = args.sweep_id
    repo = RunSetArtifactRepository()
    sweep_dir = os.path.join(repo.base_dir, sweep_id)
    if not os.path.exists(sweep_dir):
        print(f"Sweep directory not found for ID: {sweep_id}")
        sys.exit(1)

    print(f"Compiling Parquet analytics dataset for sweep {sweep_id}...")
    try:
        builder = AnalyticsDatasetBuilder()
        manifest = builder.build_dataset(sweep_id=sweep_id, source_sweep_dir=sweep_dir)
        print(f"Dataset successfully compiled: {manifest.dataset_id}")
        print(f"Table files: {manifest.table_files}")
        print(f"Record counts: {manifest.record_counts}")
    except Exception as e:
        print(f"Failed to build dataset: {e}")
        sys.exit(1)

def _run_query_dataset(args):
    """Execute a predefined DuckDB query on a built dataset."""
    import os
    import sys
    from src.observability.analytics.query import DuckDBQueryService

    dataset_id = args.dataset_id
    query_name = args.query

    dataset_dir = os.path.join("data/analytics", dataset_id)
    if not os.path.exists(dataset_dir):
        print(f"Dataset directory not found: {dataset_dir}")
        sys.exit(1)

    print(f"Running predefined query '{query_name}' on dataset '{dataset_id}'...")
    try:
        service = DuckDBQueryService(dataset_dir=dataset_dir)
        results = service.execute_predefined_query(query_name)
        
        if not results:
            print("Query returned 0 records.")
            return

        # Print beautiful ASCII table
        keys = list(results[0].keys())
        # Calculate max widths
        widths = {k: max(len(str(r.get(k) or "")) for r in results) for k in keys}
        widths = {k: max(widths[k], len(k)) for k in keys}

        # Print header
        header = " | ".join(f"{k:<{widths[k]}}" for k in keys)
        print(header)
        print("-" * len(header))
        for r in results:
            row = " | ".join(f"{str(r.get(k) or ''):<{widths[k]}}" for k in keys)
            print(row)
            
        print(f"\nTotal rows returned: {len(results)}")
    except Exception as e:
        print(f"Query execution failed: {e}")
        sys.exit(1)

def _run_worker(args):
    """Executes standalone worker operations."""
    import sys
    if args.worker_command == "analyze-run":
        print(f"Starting standalone worker to analyze run {args.run_id}...")
        from src.observability.anomaly.worker import ExternalAnomalyWorker
        worker = ExternalAnomalyWorker(mode="artifact")
        result = worker.analyze_run(args.run_id, allow_partial=True)
        
        print(f"\nAnalysis Status: {result.status}")
        print(f"Anomalies Found: {result.anomaly_count}")
        print(f"Health Score: {result.health_score}")
        if result.errors:
            print("Errors encountered:")
            for err in result.errors:
                print(f"  - {err}")
            sys.exit(1)
        else:
            print("Analysis complete. Worker status updated successfully.")
            sys.exit(0)

def _run_retention(args):
    """Executes data retention operations."""
    import sys
    from src.observability.reporting.retention import RetentionManager
    manager = RetentionManager()
    
    if args.retention_command == "plan":
        print("Scanning simulation runs for expired or redundant files (Dry Run)...")
        plan = manager.generate_cleanup_plan()
        print(f"\nTotal eligible runs scanned: {plan.get('scanned_runs_count', 0)}")
        print(f"Prunable runs classified: {len(plan.get('eligible_runs', []))}")
        print(f"Protected runs classified: {len(plan.get('protected_runs', []))}")
        print("\nPruning Plan details:")
        for r_id, details in plan.get("eligible_runs", []):
            print(f"  - Run {r_id}: reason={details.get('reason')}, files={details.get('files')}")
        print("\nProtected Runs:")
        for r_id, details in plan.get("protected_runs", []):
            print(f"  - Run {r_id}: reason={details.get('reason')}")
        print("\nDry run completed. Run with 'retention clean --confirm' to prune files.")
        sys.exit(0)
        
    elif args.retention_command == "clean":
        if not args.confirm:
            print("ERROR: --confirm flag is required to execute deletion.")
            sys.exit(1)
        print("Executing cleanup of expired observability artifacts...")
        logs = manager.execute_cleanup()
        print(f"\nCleanup successfully completed.")
        print(f"Total files pruned: {logs.get('deleted_files_count', 0)}")
        print(f"Purged run directories: {logs.get('purged_runs_count', 0)}")
        sys.exit(0)

def _run_warehouse(args):
    """Executes database warehouse operations."""
    import sys
    from src.observability.warehouse.factory import get_warehouse_adapter
    adapter = get_warehouse_adapter()
    
    if args.warehouse_command == "init":
        print("Initializing database warehouse schema...")
        try:
            if hasattr(adapter, "init_schema"):
                adapter.init_schema()
                print("Schema initialization completed successfully.")
            else:
                print("Schema initialization not supported by the active warehouse backend.")
            sys.exit(0)
        except Exception as e:
            print(f"Schema initialization failed: {e}")
            sys.exit(1)
            
    elif args.warehouse_command == "ingest-run":
        print(f"Ingesting run {args.run_id} (dry_run={args.dry_run}, force={args.force})...")
        result = adapter.ingest_run(args.run_id, dry_run=args.dry_run, force=args.force)
        
    elif args.warehouse_command == "ingest-sweep":
        print(f"Ingesting sweep {args.sweep_id} (dry_run={args.dry_run}, force={args.force})...")
        result = adapter.ingest_sweep(args.sweep_id, dry_run=args.dry_run, force=args.force)
        
    elif args.warehouse_command == "query":
        try:
            if args.query_command == "worst-runs":
                print(f"Querying worst runs by health score (limit={args.limit})...")
                results = adapter.query_runs({"sort": "health_score_asc", "limit": args.limit})
                if not results:
                    print("Query returned 0 records.")
                    sys.exit(0)
                print(f"{'Run ID':<40} | {'Scenario Name':<25} | {'Health Score':<12}")
                print("-" * 85)
                for r in results:
                    print(f"{r.run_id:<40} | {r.scenario_name:<25} | {r.health_score:<12.2f}")
                sys.exit(0)
                
            elif args.query_command == "entity-events":
                print(f"Querying events for entity {args.entity_id} (limit={args.limit})...")
                results = adapter.query_events({"entity_id": args.entity_id, "limit": args.limit})
                if not results:
                    print("Query returned 0 records.")
                    sys.exit(0)
                print(f"{'Tick':<6} | {'Event Type':<25} | {'Severity':<8} | {'Message':<60}")
                print("-" * 105)
                for ev in results:
                    print(f"{ev.tick:<6} | {ev.event_type:<25} | {ev.severity:<8} | {ev.message[:60]:<60}")
                sys.exit(0)
                
            else:
                print(f"Unknown query command: {args.query_command}")
                sys.exit(1)
        except Exception as e:
            print(f"Query execution failed: {e}")
            sys.exit(1)
            
    else:
        print(f"Unknown warehouse command: {args.warehouse_command}")
        sys.exit(1)
        
    print(f"\nIngestion Status: {result.status}")
    print(f"Ingestion ID: {result.ingestion_id}")
    print(f"Duration: {result.duration_ms:.2f}ms")
    print("\nRecords Processed:")
    for k, v in result.records_ingested.items():
        print(f"  - {k}: {v}")
        
    if result.errors:
        print("\nErrors encountered:")
        for err in result.errors:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print("\nIngestion complete successfully.")
        sys.exit(0)

def _run_cognition(args):
    from src.observability.reporting.history_query import HistoricalRunQueryService, sanitize_id
    import sys
    import json
    
    query_service = HistoricalRunQueryService()
    
    try:
        if hasattr(args, "run_id") and args.run_id:
            sanitize_id(args.run_id)
        if hasattr(args, "entity_id") and args.entity_id:
            sanitize_id(args.entity_id)
    except ValueError as e:
        print(f"Security Error: {e}", file=sys.stderr)
        sys.exit(1)
        
    try:
        if args.cognition_command == "snapshot":
            print(f"Querying cognition snapshots for run {args.run_id}, entity {args.entity_id} (page={args.page}, page_size={args.page_size}, full_graph={args.full_graph})...")
            result = query_service.get_entity_snapshots(
                run_id=args.run_id,
                entity_id=args.entity_id,
                page=args.page,
                page_size=args.page_size,
                full_graph=args.full_graph
            )
            print(f"Total Snapshots Matching: {result['total']}")
            print(json.dumps(result["snapshots"], indent=2))
            sys.exit(0)
            
        elif args.cognition_command == "diff":
            print(f"Querying cognition graph diffs for run {args.run_id}, entity {args.entity_id}...")
            result = query_service.get_entity_diffs(
                run_id=args.run_id,
                entity_id=args.entity_id
            )
            print(f"Total Diffs Found: {len(result)}")
            print(json.dumps(result, indent=2))
            sys.exit(0)
            
        elif args.cognition_command == "features":
            print(f"Querying cognition features for run {args.run_id}, entity {args.entity_id}...")
            result = query_service.get_entity_features(
                run_id=args.run_id,
                entity_id=args.entity_id
            )
            print(f"Total Feature Records: {len(result)}")
            print(json.dumps(result, indent=2))
            sys.exit(0)
            
        elif args.cognition_command == "patterns":
            print(f"Querying strategic failure patterns for run {args.run_id}...")
            result = query_service.get_run_patterns(
                run_id=args.run_id
            )
            print(f"Total Patterns Found: {len(result)}")
            print(json.dumps(result, indent=2))
            sys.exit(0)
            
        else:
            print(f"Unknown cognition command: {args.cognition_command}", file=sys.stderr)
            sys.exit(1)
            
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected Error: {e}", file=sys.stderr)
        sys.exit(1)

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
    elif args.command == "export":
        _run_export(args)
    elif args.command == "export-sweep":
        _run_export_sweep(args)
    elif args.command == "build-dataset":
        _run_build_dataset(args)
    elif args.command == "query-dataset":
        _run_query_dataset(args)
    elif args.command == "worker":
        _run_worker(args)
    elif args.command == "retention":
        _run_retention(args)
    elif args.command == "warehouse":
        _run_warehouse(args)
    elif args.command == "cognition":
        _run_cognition(args)
    elif args.command == "diagnostics":
        from src.cli.diagnostics import run_diagnostics_resources
        exit_code = run_diagnostics_resources(
            fmt=getattr(args, "fmt", "table"),
            run_id=getattr(args, "run_id", None),
        )
        sys.exit(exit_code)
    elif args.command == "inspect":
        print("V2 Inspect mode not yet fully implemented. Entity state inspection logic pending M4.")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
