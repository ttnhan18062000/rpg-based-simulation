import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

"""Tests for Narrative Memory System (TCK-20260405-CONVERGENCE).

Verifies:
  1. MindAspect helpers: total_glory(), total_trauma(), prune_memories()
  2. MemoryModifier: biases goal scores based on accumulated memories
  3. SURVIVAL events: recorded on near-death survival
  4. DISCOVERY events: recorded on first region visit
"""

import pytest
from unittest.mock import MagicMock

from src.ai.goals.base import GoalScore, MemoryModifier
from src.core.aspects.mind import MindAspect, MemoryLogEntry, DiscoveryNarrative
from src.core.models.enums import AIState, GoalType


# ===========================================================================
# MindAspect Helpers
# ===========================================================================

class TestMindAspectMemoryHelpers:
    """MindAspect should provide query methods for memory_log."""

    def test_total_glory_sums_positive_impact(self):
        """total_glory() returns sum of all positive-impact entries."""
        mind = MindAspect()
        mind.narrative.memory_log = [
            MemoryLogEntry(tick=10, type="glory", impact=5.0),
            MemoryLogEntry(tick=20, type="glory", impact=50.0),
            MemoryLogEntry(tick=30, type="trauma", impact=-10.0),
        ]
        assert mind.total_glory() == 55.0

    def test_total_trauma_sums_negative_impact(self):
        """total_trauma() returns sum of all negative-impact entries (including survival)."""
        mind = MindAspect()
        mind.narrative.memory_log = [
            MemoryLogEntry(tick=10, type="trauma", impact=-10.0),
            MemoryLogEntry(tick=20, type="survival", impact=-3.0),
            MemoryLogEntry(tick=30, type="glory", impact=5.0),
        ]
        # MindAspect.total_trauma() includes "trauma" AND "survival"
        assert mind.total_trauma() == -13.0

    def test_prune_keeps_highest_impact(self):
        """prune_memories() caps at max_entries, keeping highest abs(impact)."""
        mind = MindAspect()
        # Create 60 entries with varying impact
        mind.narrative.memory_log = [
            MemoryLogEntry(tick=i, type="glory", impact=float(i))
            for i in range(60)
        ]
        mind.prune_memories(max_entries=50)
        assert len(mind.narrative.memory_log) == 50
        # The 10 lowest-impact entries (0-9) should be pruned
        impacts = [e.impact for e in mind.narrative.memory_log]
        assert min(impacts) >= 10.0


# ===========================================================================
# MemoryModifier
# ===========================================================================

class TestMemoryModifier:
    """MemoryModifier biases goal scores based on accumulated memories."""

    def _make_ctx_with_memory(self, memory_log: list[MemoryLogEntry]) -> MagicMock:
        ctx = MagicMock()
        mind = MindAspect()
        mind.narrative.memory_log = memory_log
        ctx.actor.mind = mind
        return ctx

    def test_combat_boosted_by_glory(self):
        """High glory → combat score boosted."""
        ctx = self._make_ctx_with_memory([
            MemoryLogEntry(tick=10, type="glory", impact=100.0),
        ])
        modifier = MemoryModifier()
        score = GoalScore(goal=GoalType.COMBAT, score=1.0, target_state=AIState.HUNT)
        modifier.modify(score, ctx)
        # glory=100 → score *= 1 + 100/100 = 2.0
        assert score.score == pytest.approx(2.0)

    def test_flee_boosted_by_trauma(self):
        """High trauma → flee score boosted."""
        ctx = self._make_ctx_with_memory([
            MemoryLogEntry(tick=10, type="trauma", impact=-20.0),
            MemoryLogEntry(tick=20, type="survival", impact=-3.0),
        ])
        modifier = MemoryModifier()
        score = GoalScore(goal=GoalType.FLEE, score=1.0, target_state=AIState.FLEE)
        modifier.modify(score, ctx)
        # |trauma|=23 → score *= 1 + 23/100 = 1.23
        assert score.score == pytest.approx(1.23)

    def test_explore_boosted_by_discovery(self):
        """Discoveries → explore score boosted."""
        ctx = self._make_ctx_with_memory([
            MemoryLogEntry(tick=10, type="discovery", impact=2.0),
            MemoryLogEntry(tick=20, type="discovery", impact=2.0),
        ])
        modifier = MemoryModifier()
        score = GoalScore(goal=GoalType.EXPLORE, score=1.0, target_state=AIState.WANDER)
        modifier.modify(score, ctx)
        # 2 discoveries → score *= 1 + 2/20 = 1.1
        assert score.score == pytest.approx(1.1)


# ===========================================================================
# Event Recording (SURVIVAL & DISCOVERY)
# ===========================================================================

class TestMemoryRecording:
    """Verifies that SURVIVAL and DISCOVERY events are recorded correctly."""

    def test_survival_event_recorded_on_near_death(self):
        """ActionSystem should record SURVIVAL when defender has < 20% HP."""
        from src.systems.gameplay.action_system import ActionSystem
        from src.core.entities.entity import Entity, Vector2
        from src.core.aspects.combat import CombatAspect
        from src.core.aspects.spatial import SpatialAspect
        from src.core.aspects.identity import IdentityAspect
        from src.core.gameplay.faction import Faction
        from src.core.models.world_state import WorldState
        from src.actions.base import ActionProposal, CombatTraceUpdate, CombatTraceRecord

        # Setup
        config = MagicMock()
        config.flee_hp_threshold = 0.2 # Prevent MagicMock comparison TypeError
        rng = MagicMock()
        system = ActionSystem(config, rng)
        
        from src.core.world.grid import Grid
        from src.platform.spatial_hash import SpatialHash
        world = WorldState(seed=42, grid=Grid(10, 10), spatial_index=SpatialHash(cell_size=8))
        
        attacker = Entity(
            id=1, kind="hero",
            spatial=SpatialAspect(pos=Vector2(0,0)),
            combat=CombatAspect(hp=100, max_hp=100),
            identity=IdentityAspect(faction=Faction.HERO_GUILD)
        )
        defender = Entity(
            id=2, kind="goblin",
            spatial=SpatialAspect(pos=Vector2(1,1)),
            combat=CombatAspect(hp=21, max_hp=100), # Just above threshold
            identity=IdentityAspect(faction=Faction.GOBLIN_HORDE)
        )
        world.add_entity(attacker)
        world.add_entity(defender)

        # Trigger authoritative update application through a proposal
        # ActionSystem._apply_updates will handle the CombatTraceUpdate
        proposal = ActionProposal(
            actor_id=attacker.id,
            verb=GoalType.COMBAT,
            updates=[
                CombatTraceUpdate(result=CombatTraceRecord(
                    tick=100, attacker_id=attacker.id, defender_id=defender.id,
                    damage=5 # Leaves defender at 16 HP (16%)
                ))
            ]
        )
        
        from src.platform.rng import DeterministicRNG
        system.apply_action_state_transitions(world, config, [proposal], rng=DeterministicRNG(42))
        
        # Defender HP was 21, took 5 dmg -> 16. 16/100 = 16% < 20% threshold.
        survival_entries = [e for e in defender.mind.narrative.memory_log if e.type == "survival"]
        assert len(survival_entries) == 1
        assert survival_entries[0].impact == -3.0

    def test_discovery_event_recorded_on_new_region(self):
        """AIBrain should record DISCOVERY when entering a brand new region."""
        from src.ai.brain import AIBrain
        from src.ai.states import AIContext
        from src.core.entities.entity import Entity, Vector2
        from src.core.aspects.spatial import SpatialAspect
        from src.core.aspects.identity import IdentityAspect
        from src.core.gameplay.faction import Faction

        # Setup
        config = MagicMock()
        config.flee_hp_threshold = 0.2
        rng = MagicMock()
        brain = AIBrain(config, rng)

        actor = Entity(
            id=1, kind="hero",
            spatial=SpatialAspect(pos=Vector2(0,0), current_region_id="region_1"),
            identity=IdentityAspect(faction=Faction.HERO_GUILD)
        )
        
        snapshot = MagicMock()
        snapshot.tick = 200
        ctx = AIContext(actor=actor, snapshot=snapshot, config=config, rng=rng, faction_reg=MagicMock())

        # Calling _memory_appraisal_phase directly
        updates = []
        brain._memory_appraisal_phase(ctx, updates)

        # Check for PerceptionUpdate with DISCOVERY
        from src.actions.base import PerceptionUpdate
        up = next((u for u in updates if isinstance(u, PerceptionUpdate) and u.memory_log_add), None)
        assert up is not None
        assert any(e.type == "discovery" for e in up.memory_log_add)
        assert up.memory_locations_set["region_1"] == 2.0

    def test_memory_decay_prunes_on_appraisal(self):
        """AIBrain should trigger prune_memories during appraisal."""
        from src.ai.brain import AIBrain
        from src.ai.states import AIContext
        from src.core.entities.entity import Entity, Vector2
        from src.core.aspects.spatial import SpatialAspect
        from src.core.aspects.identity import IdentityAspect
        from src.core.gameplay.faction import Faction

        config = MagicMock()
        config.flee_hp_threshold = 0.2
        rng = MagicMock()
        brain = AIBrain(config, rng)

        actor = Entity(
            id=1, kind="hero",
            spatial=SpatialAspect(pos=Vector2(0,0)),
            identity=IdentityAspect(faction=Faction.HERO_GUILD)
        )
        # Add 60 entries (MindAspect.narrative.memory_log)
        actor.mind.narrative.memory_log = [MemoryLogEntry(tick=1, type="glory", impact=1.0)] * 60

        snapshot = MagicMock()
        snapshot.tick = 200
        ctx = AIContext(actor=actor, snapshot=snapshot, config=config, rng=rng, faction_reg=MagicMock())

        brain._memory_appraisal_phase(ctx, [])

        # Pruning should happen in-place on actor.mind
        assert len(actor.mind.narrative.memory_log) == 50
