from __future__ import annotations
import argparse
import sys
import logging
import time
import random
from pathlib import Path

from src.config.profiles import RuntimeProfile, HardwareClass
from src.engine.kernel import Kernel
from src.core.state import AuthoritativeState
from src.platform.rng import DeterministicRNG
from src.systems.generator import EntityGenerator

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
    
    # Use deterministic random for positions
    pos_rng = random.Random(seed)
    
    entities = {}
    # Spawn hero at center
    hero = gen.spawn_hero((64.0, 64.0))
    entities[hero.id] = hero
    
    # Spawn monsters
    for _ in range(entities_count - 1):
        monster = gen.spawn_goblin((
            64.0 + pos_rng.uniform(-20, 20), 
            64.0 + pos_rng.uniform(-20, 20)
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
    elif args.command == "inspect":
        print("V2 Inspect mode not yet fully implemented. Entity state inspection logic pending M4.")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
