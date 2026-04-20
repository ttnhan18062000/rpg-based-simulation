import sys
import os
import json
from unittest.mock import MagicMock, PropertyMock

# Add src to path
sys.path.append(os.path.abspath("."))

from src.ai.states.interaction import LootingHandler, HarvestingHandler
from src.ai.states.base import AIContext
from src.core.models.enums import ActionType, AIState, GoalType
from src.core.models.vectors import Vector2

def run_oracle():
    results = []
    
    # Mock resources
    node_wood = MagicMock()
    node_wood.spatial.pos = Vector2(1, 1)
    node_wood.is_available = True
    node_wood.name = "Timber"
    node_wood.harvest_ticks = 3
    
    # --- Scenario 1: Harvesting Progress ---
    actor = MagicMock()
    actor.id = 1
    actor.spatial.pos = Vector2(1, 1)
    actor.interaction.loot_progress = 0
    actor.inventory.is_effectively_full = False
    
    # Mock combat
    type(actor.combat).hp_ratio = PropertyMock(return_value=1.0)
    type(actor.combat).hp = PropertyMock(return_value=100)
    type(actor.combat).max_hp = PropertyMock(return_value=100)
    type(actor.combat).alive = PropertyMock(return_value=True)
    
    # Mock mind/decision/personality/emotion for should_flee
    actor.mind.decision.ai_state = AIState.IDLE
    actor.mind.decision.last_goal = GoalType.EXPLORE
    actor.mind.decision.personality.caution = 0.5
    actor.mind.emotion.mood = 0.5
    actor.mind.emotion.panic = 0.0
    actor.mind.emotion.grudges = {}
    actor.mind.perception.entity_memory = {}
    actor.identity.hero_class = None
    
    snapshot = MagicMock()
    snapshot.resource_nodes = [node_wood]
    snapshot.ground_items = {}
    snapshot.entities = {1: actor}
    
    # Mock config
    config = MagicMock()
    config.flee_hp_threshold = 0.2
    config.flee_exit_threshold = 0.4
    config.low_hp_threshold = 0.2
    config.crit_hp_threshold = 0.1
    config.base_bravery = 0.5
    
    # AIContext(actor, snapshot, config, rng, faction_reg)
    ctx = AIContext(
        actor=actor, 
        snapshot=snapshot, 
        config=config,
        rng=MagicMock(),
        faction_reg=MagicMock()
    )
    
    # Tick 1
    handler = HarvestingHandler()
    state, proposal = handler.handle(ctx)
    results.append({
        "scenario": "harvest_tick_1",
        "state": state.name,
        "verb": proposal.verb.name if hasattr(proposal.verb, "name") else str(proposal.verb),
        "progress_delta": next((u.loot_progress_delta for u in (proposal.updates or []) if hasattr(u, "loot_progress_delta")), 0)
    })
    
    # Tick 4 (Completion)
    actor.interaction.loot_progress = 3
    state, proposal = handler.handle(ctx)
    results.append({
        "scenario": "harvest_done",
        "state": state.name,
        "verb": proposal.verb.name if hasattr(proposal.verb, "name") else str(proposal.verb),
        "target": [proposal.target.x, proposal.target.y] if hasattr(proposal.target, "x") else proposal.target
    })
    
    # --- Scenario 2: Looting Progress ---
    actor.interaction.loot_progress = 0
    snapshot.ground_items = {(1, 1): ["wood"]}
    config.loot_duration = 5
    
    handler = LootingHandler()
    state, proposal = handler.handle(ctx)
    results.append({
        "scenario": "loot_tick_1",
        "state": state.name,
        "verb": proposal.verb.name if hasattr(proposal.verb, "name") else str(proposal.verb),
        "progress_delta": next((u.loot_progress_delta for u in (proposal.updates or []) if hasattr(u, "loot_progress_delta")), 0)
    })
    
    # --- Scenario 3: Inventory Full ---
    actor.inventory.is_effectively_full = True
    state, proposal = handler.handle(ctx)
    results.append({
        "scenario": "loot_full_inventory",
        "state": state.name,
        "verb": proposal.verb.name if hasattr(proposal.verb, "name") else str(proposal.verb),
        "progress_set": next((u.loot_progress_set for u in (proposal.updates or []) if hasattr(u, "loot_progress_set")), -1)
    })

    output_path = "tests_v2/parity/interaction_oracle/results.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Captured {len(results)} interaction scenarios to {output_path}")

if __name__ == "__main__":
    run_oracle()
