from __future__ import annotations
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from src_legacy.core.state import AuthoritativeState
from src_legacy.core.serialization import StateDeserializer
from src_legacy.engine.apply import ApplyPath
from src_legacy.engine.checkpoint import CanonicalStateHasher

logger = logging.getLogger(__name__)

class ReplayPlayer:
    """
    Authoritative re-execution engine for simulation replays.
    Enforces the "Determinism Law": Replay must result in bit-identical hashes.
    """

    def __init__(self, run_dir: Path):
        self.run_dir = run_dir
        self.manifest = self._load_json(run_dir / "manifest.json")
        self._state: Optional[AuthoritativeState] = None

    def _load_json(self, path: Path) -> Dict[str, Any]:
        with open(path, "r") as f:
            return json.load(f)

    def load_initial_state(self, initial_state_data: Optional[Dict[str, Any]] = None) -> AuthoritativeState:
        """
        Prepare the player with the starting state of the simulation.
        If initial_state_data is None, we attempt to reconstruct it from manifest metadata
        (Note: In a production system, this would load from a baseline snapshot).
        """
        if initial_state_data:
            self._state = StateDeserializer.deserialize_state(initial_state_data)
        else:
            # Fallback: Create a blank state from manifest metadata
            # This is only useful if the replay starts at tick 0 with a known seed.
            self._state = AuthoritativeState(
                tick=self.manifest.get("start_tick", 0),
                seed=self.manifest.get("seed", 0),
                world_time=self.manifest.get("start_world_time", 0)
            )
        return self._state

    def replay_all(self, stop_at_tick: Optional[int] = None) -> Dict[str, Any]:
        """
        Execute the entire replay sequence found in the run directory.
        Verifies hashes at each tick boundary.
        """
        if self._state is None:
            raise RuntimeError("Initial state must be loaded before replaying.")

        results = {
            "ticks_replayed": 0,
            "verification_failures": [],
            "final_hash": None
        }

        # Load and sort chunks
        chunks = sorted(self.run_dir.glob("chunk_*.json"))
        
        for chunk_path in chunks:
            events = self._load_json(chunk_path)
            for event in events:
                tick = event.get("tick")
                if stop_at_tick is not None and tick > stop_at_tick:
                    break

                if event.get("event_type") == "REFINED_UPDATE":
                    payload = event.get("payload")
                    update_data = payload.get("update")
                    
                    # Deserialize the update
                    update = StateDeserializer.deserialize_update(update_data)
                    
                    # Authoritative Application
                    self._state = ApplyPath.apply_generation(
                        self._state,
                        update,
                        next_tick=self._state.tick + 1,
                        next_world_time=payload.get("world_time") + 1 if "world_time" in payload else self._state.world_time + 1
                    )
                    results["ticks_replayed"] += 1

                if event.get("event_type") == "TICK_END":
                    # Verify Hash Parity
                    if self._state.tick == 9:
                        results["replayed_state_9"] = CanonicalStateHasher.to_canonical_json(self._state, pretty=True)
                        
                    recorded_hash = event.get("payload", {}).get("hash")
                    current_hash = CanonicalStateHasher.get_hash(self._state)
                    
                    if recorded_hash and current_hash != recorded_hash:
                        failure = {
                            "tick": tick,
                            "expected": recorded_hash,
                            "actual": current_hash
                        }
                        results["verification_failures"].append(failure)
                        logger.error(f"Fidelity Breach at tick {tick}: {failure}")
                        # Depending on policy, we might stop here or continue
        
        results["final_hash"] = CanonicalStateHasher.get_hash(self._state)
        return results

    @property
    def current_state(self) -> Optional[AuthoritativeState]:
        return self._state
