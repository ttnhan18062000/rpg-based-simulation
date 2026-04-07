import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))


import pytest
from unittest.mock import MagicMock, patch
from src.ai.brain import AIBrain, AIContext
from src.core.models.enums import AIState, EmotionType
from src.core.entities.entity import Entity
from src.actions.base import MindUpdate

def test_appraisal_phase_triggers_panic_on_low_hp():
    # Setup with REAL Entity [AOA STABILIZATION: Entity-First Mocking]
    config = MagicMock()
    config.flee_hp_threshold = 0.3
    rng = MagicMock()
    brain = AIBrain(config, rng)
    
    actor = Entity(id=1, kind="hero", faction="player")
    actor.combat.max_hp = 100
    actor.combat.hp = 20 # 0.2 ratio, below 30% threshold
    actor.identity.display_name = "PanicAgent"
    
    # Mock context with proper fields [AOA STABILIZATION]
    snapshot = MagicMock()
    snapshot.tick = 100 # Ensure appraisal throttle is bypassed
    ctx = AIContext(
        actor=actor,
        snapshot=snapshot,
        config=config,
        rng=rng,
        faction_reg=brain._faction_reg,
        _visible_override=[]
    )
    
    # Run finalization directly to get updates — ensuring 100% convergence
    updates = []
    # Appraisal logic currently lives in deliberation/brain helper, 
    # but the style check is in finalization. 
    # Actually, brain._memory_appraisal_phase appends to updates.
    brain._memory_appraisal_phase(ctx, updates)
    
    # In AOA Brain, appraisal might project into MindUpdate
    # Check if panic delta exists in any MindUpdate
    panic_delta = 0.0
    for u in updates:
        if isinstance(u, MindUpdate) and u.emotion_delta:
            panic_delta += u.emotion_delta.get(EmotionType.PANIC, 0.0)
    
    # Low HP should trigger panic increment
    assert panic_delta > 0.0
