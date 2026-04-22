# tests_v2/parity/test_movement_parity.py
import json
import os
import pytest
from dataclasses import make_dataclass
from typing import Tuple, Dict, Any

from src_v2.core.state import AuthoritativeState, EntityState
from src_v2.engine.movement import MovementSystem

# Constants
RESULTS_PATH = "tests_v2/parity/movement_oracle/results.json"

def load_oracle_results():
    if not os.path.exists(RESULTS_PATH):
        pytest.skip(f"Oracle results not found at {RESULTS_PATH}. Run capture script first.")
    with open(RESULTS_PATH, "r") as f:
        return json.load(f)

# Scenario mapping (matching verify_v2_movement.py)
SCENARIOS = {
    "success_move": {"actor_pos": (5, 5), "target_pos": (5, 6), "blocked": [], "others": {}, "active": True},
    "blocked_terrain": {"actor_pos": (5, 5), "target_pos": (5, 6), "blocked": [(5, 6)], "others": {}, "active": True},
    "occupied_tile": {"actor_pos": (5, 5), "target_pos": (5, 6), "blocked": [], "others": {(5, 6): 2}, "active": True},
    "actor_dead": {"actor_pos": (5, 5), "target_pos": (5, 6), "blocked": [], "others": {}, "active": False},
    "double_claim": {"actor_pos": (5, 5), "target_pos": (5, 6), "blocked": [], "others": {}, "active": True, "occupied_context": [(5, 6)]},
}

@pytest.mark.parametrize("oracle", load_oracle_results(), ids=lambda o: o["scenario"])
def test_movement_parity_with_oracle(oracle):
    """
    Verifies that V2 MovementSystem logic matches the captured original behavior (oracle).
    """
    name = oracle["scenario"]
    s = SCENARIOS.get(name)
    assert s is not None, f"Scenario {name} not found in test mapping"

    # 1. Setup V2 state
    entities = {
        1: EntityState(id=1, kind="actor", position=s["actor_pos"], active=s["active"])
    }
    for pos, eid in s["others"].items():
        entities[eid] = EntityState(id=eid, kind="other", position=pos, active=True)

    state = AuthoritativeState(
        tick=1, 
        seed=42, 
        entities=entities, 
        blocked_tiles=set(s["blocked"])
    )

    # 2. Execute V2 logic
    # Handle double_claim scenario (Requires special context with transient_claims)
    if name == "double_claim":
        Context = make_dataclass("Context", [("blocked_tiles", list), ("transient_claims", list), ("entities", dict)])
        ctx = Context(
            blocked_tiles=list(s["blocked"]), 
            transient_claims=s.get("occupied_context", []), 
            entities=entities
        )
        update = MovementSystem.resolve_move(ctx, entities[1], oracle["target"])
    else:
        update = MovementSystem.resolve_move(state, entities[1], oracle["target"])

    # 3. Extract V2 results
    v2_valid = update.moved_this_tick == True
    v2_reason = "ADVANCING"
    if update.navigation and update.navigation.failure_reason:
        v2_reason = update.navigation.failure_reason

    # 4. Parity Assertions
    # Special case: actor_dead in src returns False/None. In V2 it returns False/ADVANCING (No-Op).
    if name == "actor_dead":
        assert v2_valid == False, f"Scenario {name}: V2 should be invalid for dead actor"
        # In V2, dead actor skip is a no-op, so we don't strictly assert the reason if it's default
    else:
        assert v2_valid == oracle["is_valid"], (
            f"Scenario {name}: Validity mismatch. Oracle={oracle['is_valid']}, V2={v2_valid}"
        )
        if oracle["reason_code"] is not None:
             assert v2_reason == oracle["reason_code"], (
                 f"Scenario {name}: Reason code mismatch. Oracle={oracle['reason_code']}, V2={v2_reason}"
             )
