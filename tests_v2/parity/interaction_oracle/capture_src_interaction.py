import sys
import os
import json
from unittest.mock import MagicMock, PropertyMock

# Add src to path
sys.path.append(os.path.abspath("."))

from src.ai.states.interaction import LootingHandler, HarvestingHandler
from src.ai.states.base import AIContext
from src.core.models.enums import ActionType, AIState, GoalType, Faction, MovementIntention
from src.core.models.vectors import Vector2
from src.core.entities.entity import Entity
from src.core.models.snapshot import Snapshot
from src.config import SimulationConfig

def run_oracle():
    results = []
    
    # Mock resources
    node_wood = MagicMock()
    node_wood.id = 500
    node_wood.spatial.pos = Vector2(1, 1)
    node_wood.is_available = True
    node_wood.name = "Timber"
    node_wood.harvest_ticks = 2
    
    # --- Real Entity Setup ---
    actor = Entity(id=1, kind="hero")
    actor.spatial.pos = Vector2(1, 1)
    actor.spatial.vision_range = 10
    actor.interaction.loot_progress = 0
    from src.core.aspects.inventory import InventoryAspect
    actor.inventory = InventoryAspect()
    actor.identity.faction = Faction.HERO_GUILD
    actor.next_act_at = 100
    actor.combat.hp = 100
    actor.combat.max_hp = 100
    
    actor.mind.decision.ai_state = AIState.IDLE
    actor.mind.decision.last_goal = GoalType.EXPLORE
    actor.mind.decision.personality.caution = 0.5
    actor.mind.decision.personality.aggression = 0.5
    actor.mind.emotion.mood = 0.5
    actor.mind.emotion.panic = 0.0
    actor.mind.emotion.grudges = {}
    actor.mind.perception.entity_memory = {}
    actor.identity.hero_class = None
    
    # Snapshot
    snapshot = MagicMock()
    snapshot.resource_nodes = [node_wood]
    snapshot.ground_items = {}
    snapshot.entities = {1: actor}
    snapshot.grid.is_walkable.return_value = True
    
    # Real Config
    config = SimulationConfig(
        flee_hp_threshold=0.2,
        flee_exit_threshold=0.4,
        overhaul_features={"use_movement_model_v2": False}
    )
    
    # Mock faction_reg
    faction_reg = MagicMock()
    faction_reg.is_hostile.return_value = False 
    
    ctx = AIContext(
        actor=actor, 
        snapshot=snapshot, 
        config=config,
        rng=MagicMock(),
        faction_reg=faction_reg
    )
    ctx._visible_override = []
    
    def capture(name, state, proposal):
        res = {
            "scenario": name,
            "state": state.name,
            "verb": proposal.verb.name if hasattr(proposal.verb, "name") else str(proposal.verb)
        }
        if hasattr(proposal, "target") and proposal.target:
             res["target"] = [proposal.target.x, proposal.target.y] if hasattr(proposal.target, "x") else proposal.target
        
        for u in (proposal.updates or []):
            if hasattr(u, "loot_progress_delta"):
                res["progress_delta"] = u.loot_progress_delta
            if hasattr(u, "loot_progress_set"):
                res["progress_set"] = u.loot_progress_set
        results.append(res)

    # --- Scenario 1: Harvesting Progress ---
    handler = HarvestingHandler()
    state, proposal = handler.handle(ctx)
    capture("harvest_tick_1", state, proposal)
    
    # --- Scenario 2: Harvesting Done ---
    actor.interaction.loot_progress = 2 
    state, proposal = handler.handle(ctx)
    capture("harvest_done", state, proposal)
    
    # --- Scenario 3: Looting Progress ---
    actor.interaction.loot_progress = 0
    snapshot.ground_items = {(1, 1): ["wood"]}
    
    handler = LootingHandler()
    state, proposal = handler.handle(ctx)
    capture("loot_tick_1", state, proposal)
    
    # --- Scenario 4: Inventory Full ---
    actor.inventory.max_slots = 5
    actor.inventory.items = ["wood"] * 5
    
    state, proposal = handler.handle(ctx)
    capture("loot_full_inventory", state, proposal)

    # --- Scenario 5: Interruption by Enemy (Reset) ---
    actor.inventory.items = []
    actor.interaction.loot_progress = 1
    
    enemy = Entity(id=999, kind="monster")
    enemy.spatial.pos = Vector2(2, 2)
    enemy.combat.hp = 100
    enemy.identity.faction = Faction.GOBLIN_HORDE
    
    def is_hostile_mock(f1, f2):
        return (f1 == Faction.HERO_GUILD and f2 == Faction.GOBLIN_HORDE)
    faction_reg.is_hostile.side_effect = is_hostile_mock
    
    ctx._visible_override = [enemy]
    
    handler = HarvestingHandler()
    state, proposal = handler.handle(ctx)
    capture("harvest_interrupted_enemy", state, proposal)

    # --- Scenario 6: Interruption by HP (Reset/Flee) ---
    ctx._visible_override = [] 
    actor.combat.hp = 10 
    
    state, proposal = handler.handle(ctx)
    capture("harvest_interrupted_hp", state, proposal)

    output_path = "tests_v2/parity/interaction_oracle/results.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Captured {len(results)} interaction scenarios to {output_path}")

if __name__ == "__main__":
    run_oracle()
