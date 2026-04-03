import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

"""Tests for Narrative Memory System (TCK-20260326-NARRATIVE).

Verifies:
  1. MindAspect helpers: total_glory(), total_trauma(), prune_memories()
  2. MemoryModifier: biases goal scores based on accumulated memories
  3. SURVIVAL events: recorded on near-death survival
  4. DISCOVERY events: recorded on first region visit
"""

import pytest
from unittest.mock import MagicMock

from src.ai.goals.base import GoalScore, MemoryModifier
from src.core.aspects.mind import MindAspect
from src.core.models.enums import AIState


# ===========================================================================
# MindAspect Helpers
# ===========================================================================

class TestMindAspectMemoryHelpers:
    """MindAspect should provide query methods for memory_log."""

    def test_total_glory_sums_positive_impact(self):
        """total_glory() returns sum of all positive-impact entries."""
        mind = MindAspect()
        mind.memory_log = [
            {"tick": 10, "type": "GLORY", "desc": "Killed goblin", "impact": 5.0},
            {"tick": 20, "type": "GLORY", "desc": "Killed boss", "impact": 50.0},
            {"tick": 30, "type": "TRAUMA", "desc": "Saw ally die", "impact": -10.0},
        ]
        assert mind.total_glory() == 55.0

    def test_total_trauma_sums_negative_impact(self):
        """total_trauma() returns sum of all negative-impact entries (negative value)."""
        mind = MindAspect()
        mind.memory_log = [
            {"tick": 10, "type": "TRAUMA", "desc": "Saw ally die", "impact": -10.0},
            {"tick": 20, "type": "SURVIVAL", "desc": "Near death", "impact": -3.0},
            {"tick": 30, "type": "GLORY", "desc": "Killed goblin", "impact": 5.0},
        ]
        assert mind.total_trauma() == -13.0

    def test_total_glory_returns_zero_when_empty(self):
        """total_glory() returns 0 when memory_log is empty."""
        mind = MindAspect()
        assert mind.total_glory() == 0.0

    def test_total_trauma_returns_zero_when_empty(self):
        """total_trauma() returns 0 when memory_log is empty."""
        mind = MindAspect()
        assert mind.total_trauma() == 0.0

    def test_prune_keeps_highest_impact(self):
        """prune_memories() caps at max_entries, keeping highest abs(impact)."""
        mind = MindAspect()
        # Create 60 entries with varying impact
        mind.memory_log = [
            {"tick": i, "type": "GLORY", "desc": f"Event {i}", "impact": float(i)}
            for i in range(60)
        ]
        mind.prune_memories(max_entries=50)
        assert len(mind.memory_log) == 50
        # The 10 lowest-impact entries (0-9) should be pruned
        impacts = [e["impact"] for e in mind.memory_log]
        assert min(impacts) >= 10.0

    def test_prune_noop_under_limit(self):
        """prune_memories() does nothing if under max_entries."""
        mind = MindAspect()
        mind.memory_log = [
            {"tick": i, "type": "GLORY", "desc": f"Event {i}", "impact": 5.0}
            for i in range(10)
        ]
        mind.prune_memories(max_entries=50)
        assert len(mind.memory_log) == 10


# ===========================================================================
# MemoryModifier
# ===========================================================================

class TestMemoryModifier:
    """MemoryModifier biases goal scores based on accumulated memories."""

    def _make_ctx_with_memory(self, memory_log: list[dict]) -> MagicMock:
        ctx = MagicMock()
        mind = MindAspect()
        mind.memory_log = memory_log
        ctx.actor.mind = mind
        return ctx

    def test_combat_boosted_by_glory(self):
        """High glory → combat score boosted."""
        ctx = self._make_ctx_with_memory([
            {"tick": 10, "type": "GLORY", "desc": "kill", "impact": 50.0},
            {"tick": 20, "type": "GLORY", "desc": "kill", "impact": 50.0},
        ])
        modifier = MemoryModifier()
        score = GoalScore(goal="combat", score=1.0, target_state=AIState.HUNT)
        modifier.modify(score, ctx)
        # glory=100 → score *= 1 + 100/100 = 2.0
        assert score.score > 1.5, f"High glory should boost combat, got {score.score}"

    def test_flee_boosted_by_trauma(self):
        """High trauma → flee score boosted."""
        ctx = self._make_ctx_with_memory([
            {"tick": 10, "type": "TRAUMA", "desc": "saw death", "impact": -10.0},
            {"tick": 20, "type": "TRAUMA", "desc": "saw death", "impact": -10.0},
            {"tick": 30, "type": "SURVIVAL", "desc": "near death", "impact": -3.0},
        ])
        modifier = MemoryModifier()
        score = GoalScore(goal="flee", score=1.0, target_state=AIState.FLEE)
        modifier.modify(score, ctx)
        # |trauma|=23 → score *= 1 + 23/100 = 1.23
        assert score.score > 1.1, f"High trauma should boost flee, got {score.score}"

    def test_explore_boosted_by_discovery(self):
        """Discoveries → explore score boosted."""
        ctx = self._make_ctx_with_memory([
            {"tick": 10, "type": "DISCOVERY", "desc": "found region", "impact": 2.0},
            {"tick": 20, "type": "DISCOVERY", "desc": "found region", "impact": 2.0},
            {"tick": 30, "type": "DISCOVERY", "desc": "found region", "impact": 2.0},
        ])
        modifier = MemoryModifier()
        score = GoalScore(goal="explore", score=1.0, target_state=AIState.WANDER)
        modifier.modify(score, ctx)
        # 3 discoveries → score *= 1 + 3/20 = 1.15
        assert score.score > 1.1, f"Discoveries should boost explore, got {score.score}"

    def test_no_memory_no_change(self):
        """Empty memory_log should leave all scores unchanged."""
        ctx = self._make_ctx_with_memory([])
        modifier = MemoryModifier()
        score = GoalScore(goal="combat", score=1.0, target_state=AIState.HUNT)
        modifier.modify(score, ctx)
        assert score.score == 1.0

    def test_unrelated_goal_not_affected(self):
        """Goals without memory-based rules should be unchanged."""
        ctx = self._make_ctx_with_memory([
            {"tick": 10, "type": "GLORY", "desc": "kill", "impact": 50.0},
        ])
        modifier = MemoryModifier()
        score = GoalScore(goal="rest", score=1.0, target_state=AIState.RESTING_IN_TOWN)
        modifier.modify(score, ctx)
        assert score.score == 1.0


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

        # Setup
        config = MagicMock()
        rng = MagicMock()
        system = ActionSystem(config, rng)
        context = MagicMock()
        context.world.tick = 100
        context.config.threat_damage_mult = 1.0
        context.config.threat_tank_class_mult = 1.5

        attacker = Entity(
            id=1, kind="hero",
            spatial=SpatialAspect(pos=Vector2(0,0)),
            combat=CombatAspect(hp=100, max_hp=100),
            identity=IdentityAspect(faction=Faction.HERO_GUILD)
        )
        defender = Entity(
            id=2, kind="goblin",
            spatial=SpatialAspect(pos=Vector2(1,1)),
            combat=CombatAspect(hp=20, max_hp=100),
            identity=IdentityAspect(faction=Faction.GOBLIN_HORDE)
        )
        # mind is already initialized by model_post_init

        from src.core.models.enums import SkillType, DamageType
        sdef = MagicMock()
        sdef.skill_id = "test_skill"
        sdef.name = "Test Skill"
        sdef.power = 1.0
        sdef.damage_type = DamageType.PHYSICAL
        sdef.radius = 0
        sdef.skill_type = SkillType.ACTIVE
        instance = MagicMock()
        instance.effective_power.return_value = 1.0

        # Simulate damage that leaves defender alive but low
        # _apply_skill_effect is where the logic lives
        with MagicMock() as mock_calc:
            mock_calc.resolve.return_value = MagicMock(atk_power=10, atk_mult=1.0, def_power=10, def_mult=1.0)
            with pytest.MonkeyPatch().context() as mp:
                mp.setattr("src.actions.damage.get_damage_calculator", lambda x: mock_calc)
                system._apply_skill_effect(context, attacker, defender, sdef, instance)

        # Defender HP was 20, raw dmg = (10*1 - 10*1//2) = 5. HP becomes 15.
        # 15/100 = 15% < 20% threshold.
        survival_entries = [e for e in defender.mind.memory_log if e["type"] == "SURVIVAL"]
        assert len(survival_entries) == 1
        assert survival_entries[0]["impact"] == -3.0

    def test_discovery_event_recorded_on_new_region(self):
        """AIBrain should record DISCOVERY when entering a brand new region."""
        from src.ai.brain import AIBrain
        from src.ai.states import AIContext
        from src.core.entities.entity import Entity, Vector2
        from src.core.aspects.combat import CombatAspect
        from src.core.aspects.spatial import SpatialAspect
        from src.core.aspects.identity import IdentityAspect
        from src.core.gameplay.faction import Faction

        # Setup
        config = MagicMock()
        rng = MagicMock()
        brain = AIBrain(config, rng)

        actor = Entity(
            id=1, kind="hero",
            spatial=SpatialAspect(pos=Vector2(0,0)),
            combat=CombatAspect(hp=100, max_hp=100),
            identity=IdentityAspect(faction=Faction.HERO_GUILD)
        )
        actor.spatial.current_region_id = "region_1"
        # mind is already initialized

        snapshot = MagicMock()
        snapshot.tick = 200
        ctx = AIContext(actor=actor, snapshot=snapshot, config=config, rng=rng, faction_reg=MagicMock())

        # Calling _memory_appraisal_phase directly
        brain._memory_appraisal_phase(ctx)

        discovery_entries = [e for e in actor.mind.memory_log if e["type"] == "DISCOVERY"]
        assert len(discovery_entries) == 1
        assert discovery_entries[0]["impact"] == 2.0
        assert "region_1" in actor.mind.memory_locations

    def test_memory_decay_prunes_on_appraisal(self):
        """AIBrain should trigger prune_memories during appraisal."""
        from src.ai.brain import AIBrain
        from src.ai.states import AIContext
        from src.core.entities.entity import Entity, Vector2
        from src.core.aspects.combat import CombatAspect
        from src.core.aspects.spatial import SpatialAspect
        from src.core.aspects.identity import IdentityAspect
        from src.core.gameplay.faction import Faction

        config = MagicMock()
        rng = MagicMock()
        brain = AIBrain(config, rng)

        actor = Entity(
            id=1, kind="hero",
            spatial=SpatialAspect(pos=Vector2(0,0)),
            combat=CombatAspect(hp=100, max_hp=100),
            identity=IdentityAspect(faction=Faction.HERO_GUILD)
        )
        # Add 60 entries
        actor.mind.memory_log = [{"tick":1, "type":"GLORY", "impact":1.0}] * 60

        snapshot = MagicMock()
        snapshot.tick = 200
        actor.combat.hp = actor.combat.max_hp
        ctx = AIContext(actor=actor, snapshot=snapshot, config=config, rng=rng, faction_reg=MagicMock())

        brain._memory_appraisal_phase(ctx)

        assert len(actor.mind.memory_log) == 50
