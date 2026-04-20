import sys
import os
import json
from dataclasses import asdict

# Add src to path
sys.path.append(os.path.abspath("."))

from src.actions.move import MoveAction
from src.actions.base import ActionProposal
from src.core.models.enums import ActionType, Material
from src.core.models.vectors import Vector2
from src.core.models.world_state import WorldState

class MockGrid:
    def __init__(self, blocked_tiles):
        self.blocked_tiles = blocked_tiles
    def is_walkable(self, pos):
        return (pos.x, pos.y) not in self.blocked_tiles

class MockSpatialHash:
    def __init__(self, entities_at):
        self.entities_at = entities_at
    def query_cell(self, pos):
        return self.entities_at.get((pos.x, pos.y), [])
    def insert(self, eid, pos): pass
    def remove(self, eid, pos): pass
    def move(self, eid, old, new): pass

def run_oracle():
    # Setup scenarios
    scenarios = [
        {"name": "success_move", "actor_pos": (5, 5), "target_pos": (5, 6), "blocked": [], "others": {}, "alive": True},
        {"name": "blocked_terrain", "actor_pos": (5, 5), "target_pos": (5, 6), "blocked": [(5, 6)], "others": {}, "alive": True},
        {"name": "occupied_tile", "actor_pos": (5, 5), "target_pos": (5, 6), "blocked": [], "others": {(5, 6): [2]}, "alive": True},
        {"name": "actor_dead", "actor_pos": (5, 5), "target_pos": (5, 6), "blocked": [], "others": {}, "alive": False},
        {"name": "double_claim", "actor_pos": (5, 5), "target_pos": (5, 6), "blocked": [], "others": {}, "alive": True, "occupied_this_tick": [(5, 6)]},
    ]

    results = []

    for s in scenarios:
        grid = MockGrid(s["blocked"])
        spatial = MockSpatialHash(s["others"])
        world = WorldState(seed=42, grid=grid, spatial_index=spatial)
        
        # Add actor
        from unittest.mock import MagicMock
        actor = MagicMock()
        actor.id = 1
        actor.combat.alive = s["alive"]
        actor.spatial.pos = Vector2(*s["actor_pos"])
        world.entities[1] = actor

        # Add others
        for pos, ids in s["others"].items():
            for eid in ids:
                other = MagicMock()
                other.id = eid
                other.combat.alive = True
                other.spatial.pos = Vector2(*pos)
                world.entities[eid] = other

        proposal = ActionProposal(actor_id=1, verb=ActionType.MOVE, target=Vector2(*s["target_pos"]))
        occupied = set(s.get("occupied_this_tick", []))
        
        is_valid = MoveAction.validate(proposal, world, occupied)
        
        results.append({
            "scenario": s["name"],
            "is_valid": is_valid,
            "reason_code": proposal.reason.code.name if proposal.reason else None,
            "target": s["target_pos"]
        })

    output_path = "tests_v2/parity/movement_oracle/results.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Captured {len(results)} scenarios to {output_path}")

if __name__ == "__main__":
    run_oracle()
