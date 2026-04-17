
import pytest
from src.core.models.vectors import Vector2
from src.core.models.enums import MovementIntention, ActionType
from src.core.logic.movement_model import MovementModel
from src.ai.states.base import AIContext
from src.core.entities.entity_builder import EntityBuilder
from src.core.models.world_state import WorldState
from src.core.models.snapshot import Snapshot
from src.core.world.grid import Grid
from src.platform.rng import DeterministicRNG
from src.platform.spatial_hash import SpatialHash

def test_diag():
    rng = DeterministicRNG(42)
    grid = Grid(10, 10)
    spatial = SpatialHash(4)
    world = WorldState(seed=42, grid=grid, spatial_index=spatial)
    
    # Actor at (1,1)
    actor = EntityBuilder(rng, 1).kind("hero").at(Vector2(1, 1)).build()
    world.add_entity(actor)
    
    # Blockers everywhere so actor must wait
    for pos in [Vector2(2,1), Vector2(0,1), Vector2(1,2), Vector2(1,0)]:
        eid = world.allocate_entity_id()
        blocker = EntityBuilder(rng, eid).kind("hero").at(pos).build()
        world.add_entity(blocker)
        print(f"Added blocker {eid} at {pos}")
    
    snapshot = Snapshot.from_world(world)
    ctx = AIContext(actor=snapshot.entities[1], snapshot=snapshot, config=None, rng=rng, faction_reg=None)
    
    # Verify snapshot content
    print(f"Entities in snapshot: {list(snapshot.entities.keys())}")
    for eid, e in snapshot.entities.items():
        print(f"Entity {eid}: pos={e.spatial.pos}, hp={e.combat.hp}, alive={e.combat.alive}")
        
    nearby = snapshot.nearby_entity_ids(2, 1, 0)
    print(f"Nearby (2,1): {nearby}")
    
    from src.core.logic.legality_service import LegalityService
    occ = LegalityService.check_occupancy(Vector2(2,1), world)
    print(f"Occupancy at (2,1) in WORLD: {occ}")
    
    proposal = MovementModel.plan_or_step(ctx, Vector2(5, 1), MovementIntention.PURSUIT, "Advancing")
    print(f"Proposal: verb={proposal.verb}, target={proposal.target}, reason='{proposal.reason}'")

if __name__ == "__main__":
    test_diag()
