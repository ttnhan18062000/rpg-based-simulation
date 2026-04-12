from __future__ import annotations
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))


import pytest
import hashlib
import pickle


from src.config import SimulationConfig
from src.api.engine_manager import EngineManager
from src.core.models.enums import ActionType, Domain

def _state_fingerprint(mgr: EngineManager) -> str:
    snap = mgr.get_snapshot()
    if not snap: return ""
    parts: list[str] = [f"tick={snap.tick}", f"seed={snap.seed}"]
    for eid in sorted(snap.entities):
        e = snap.entities[eid]
        # Core stats (AOA authorative paths)
        hp = e.combat.hp
        mhp = e.combat.max_hp
        parts.append(f"e{eid}:{e.kind}@{e.spatial.pos.x:.2f},{e.spatial.pos.y:.2f}|hp={hp}/{mhp}")
        # Epic 17 / Genetic Pillar
        parts.append(f"e{eid}:gen={e.identity.generation}|deaths={e.identity.death_count}")
        # Social Registry Bonds (Authoritative social state)
        for target_id, bond in sorted(mgr.world.social_registry.bonds.get(eid, {}).items()):
            parts.append(f"e{eid}:bond={target_id}:{bond.familiarity:.4f}")
    return hashlib.sha256("\n".join(parts).encode()).hexdigest()

def test_chaos_mode_resilience():
    """Verify simulation can survive 40% AI result dropout."""
    cfg = SimulationConfig(
        num_workers=1,
        chaos_enabled=True,
        chaos_drop_rate=0.4,
        max_ticks=50,
        initial_entity_count=10,
        grid_width=64,
        grid_height=64,
        town_center_x=32,
        town_center_y=32,
        camp_min_distance_from_town=10,
    )
    mgr = EngineManager(cfg)
    loop = mgr._loop
    for _ in range(50):
        if not loop.tick_once(): break
    assert loop.world.tick >= 50
    mgr.stop()

def test_chaos_determinism():
    """Verify that even with chaos drops, the simulation remains deterministic."""
    cfg = SimulationConfig(
        world_seed=88,
        num_workers=1,
        chaos_enabled=True,
        chaos_drop_rate=0.2,
        max_ticks=20,
        initial_entity_count=5,
        grid_width=64,
        grid_height=64,
        town_center_x=32,
        town_center_y=32,
        camp_min_distance_from_town=10,
    )
    
    fps = []
    for _ in range(2):
        mgr = EngineManager(cfg)
        loop = mgr._loop
        tick_fps = []
        for _ in range(20):
            loop.tick_once()
            tick_fps.append(_state_fingerprint(mgr))
        fps.append(tick_fps)
        mgr.stop()
        
    assert fps[0] == fps[1], "Chaos mode diverged between identical runs!"

if __name__ == "__main__":
    print("Running chaos mode resilience test...")
    test_chaos_mode_resilience()
    print("Running chaos determinism test...")
    test_chaos_determinism()
    print("All tests passed!")
