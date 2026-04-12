"""Headless Regression Runner. [MILESTONE 7]

Provides a reusable, deterministic, and isolated way to execute the 
simulation engine for regression testing and artifact generation.
"""

import os
import time
import json
import logging
import dataclasses
from typing import Any, Dict, List, Optional
from pathlib import Path

from src.config import SimulationConfig
from src.api.engine_manager import EngineManager
from src.core.logic.cognition_graph_exporter import EntityCognitionExporter
from src.api.adapters.cytoscape_adapter import CytoscapeAdapter
from src.utils.replay import ReplayRecorder

logger = logging.getLogger(__name__)

@dataclasses.dataclass
class RunResult:
    """Structured result of a headless simulation run."""
    seed: int
    ticks: int
    duration: float
    replay_path: Path
    cognition_paths: Dict[int, Path] # entity_id -> path
    manifest_path: Path
    success: bool = True
    error: Optional[str] = None

class HeadlessRunner:
    """Authoritative runner for headless simulation regression."""
    
    def __init__(self, output_root: str = "logs/regression", max_runs: int = 10):
        self.output_root = Path(output_root)
        self.output_root.mkdir(parents=True, exist_ok=True)
        self.max_runs = max_runs
        
    def _isolate_environment(self):
        """Disable external infrastructure for clean regression."""
        os.environ["LOKI_URL"] = ""
        os.environ["DISABLE_KAFKA"] = "1"
        os.environ["REDIS_URL"] = ""
        os.environ["DISABLE_REDIS"] = "1"
        os.environ["METRICS_PORT"] = "0"

    def _rotate_logs(self):
        """Prune oldest runs if total count exceeds max_runs."""
        if self.max_runs <= 0:
            return

        # Find all run directories
        runs = [d for d in self.output_root.iterdir() if d.is_dir() and d.name.startswith("run_")]
        if len(runs) <= self.max_runs:
            return

        # Sort by name (which includes timestamp run_seed_time) or ctime
        # Since our run_id format is run_{seed}_{timestamp}, simple sort works if seeds are stable.
        # But sorting by ctime is more robust for generic rotation.
        runs.sort(key=lambda x: x.stat().st_ctime)

        to_delete = runs[:len(runs) - self.max_runs]
        for d in to_delete:
            import shutil
            try:
                shutil.rmtree(d)
                logger.info("Rotated old regression run: %s", d.name)
            except Exception as e:
                logger.error("Failed to rotate run %s: %s", d.name, e)

    def run(
        self, 
        seed: int, 
        ticks: int, 
        config_overrides: Optional[Dict[str, Any]] = None,
        track_entities: Optional[List[int]] = None
    ) -> RunResult:
        """Execute a deterministic simulation run and capture artifacts."""
        self._isolate_environment()
        
        run_id = f"run_{seed}_{int(time.time())}"
        run_dir = self.output_root / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        
        # Prune old logs before generating new ones
        self._rotate_logs()
        
        replay_path = run_dir / "replay.json"
        
        # 1. Setup Config
        sim_params = {
            "world_seed": seed,
            "max_ticks": ticks + 1,
            "num_workers": 1, # Strict determinism
            "grid_width": 64,  # Reduced for regression speed
            "grid_height": 64, # Reduced for regression speed
            "initial_entity_count": 10,
            "hero_count": 2,
            "replay_file": str(replay_path)
        }
        if config_overrides:
            sim_params.update(config_overrides)
            
        config = SimulationConfig(**sim_params)
        
        # 2. Bootstrap Engine
        mgr = EngineManager(config)
        loop = mgr._loop
        if not loop:
            return RunResult(seed, ticks, 0, replay_path, {}, run_dir / "manifest.json", False, "Loop init failed")
            
        recorder = ReplayRecorder(str(replay_path), seed)
        cognition_paths = {}
        
        start_time = time.perf_counter()
        
        # 3. Execution Phase
        try:
            for _ in range(ticks):
                prev_tick = loop.world.tick
                # ActionSystem authoritative transitions happen inside tick_once
                if not loop.tick_once():
                    break
                
                # Record state for replay
                recorder.record_tick(prev_tick, loop.last_applied, loop.world)
                
            duration = time.perf_counter() - start_time
            
            # 4. Artifact Generation Phase (Cognition Graphs)
            if track_entities is None:
                # Default: track first heroes if available
                track_entities = [e.id for e in loop.world.entities.values() if e.identity.role == 0]
            
            for eid in track_entities:
                entity = loop.world.entities.get(eid)
                if entity:
                    graph = EntityCognitionExporter.export(entity, loop.world.tick)
                    cyto = CytoscapeAdapter.to_cytoscape_json(graph)
                    
                    cpath = run_dir / f"cognition_e{eid}.json"
                    with open(cpath, 'w', encoding='utf-8') as f:
                        json.dump(cyto, f, indent=2)
                    cognition_paths[eid] = cpath
                    
            recorder.flush()
            
            # 5. Manifest
            manifest = {
                "seed": seed,
                "ticks": loop.world.tick,
                "duration": duration,
                "replay": str(replay_path),
                "cognition_graphs": {str(k): str(v) for k, v in cognition_paths.items()},
                "config": sim_params
            }
            manifest_path = run_dir / "manifest.json"
            with open(manifest_path, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=2)
                
            return RunResult(seed, loop.world.tick, duration, replay_path, cognition_paths, manifest_path)
            
        except Exception as e:
            logger.exception("Headless run failed")
            return RunResult(seed, loop.world.tick, 0, replay_path, cognition_paths, run_dir / "manifest.json", False, str(e))
        finally:
            mgr.stop()
