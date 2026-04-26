import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))


import pytest
from unittest.mock import MagicMock, patch
from src_legacy.core.entities.entity import Entity
from src_legacy.core.models.vectors import Vector2
from src_legacy.core.gameplay.effects import EffectType, StatusEffect
from src_legacy.systems.gameplay.action_system import ActionSystem
from src_legacy.core.models.enums import SkillType, DamageType, ActionType, Element, HeroClass
from src_legacy.core.models.world_state import WorldState

def test_shatter_combo():
    # Setup with REAL World and Entities [AOA STABILIZATION: Entity-First Mocking]
    grid = MagicMock()
    grid.width = 10
    grid.height = 10
    from src_legacy.platform.spatial_hash import SpatialHash
    world = WorldState(seed=42, grid=grid, spatial_index=SpatialHash(cell_size=8))
    
    attacker = Entity(id=1, kind="hero", faction=0)
    attacker.combat.atk_base = 10
    from src_legacy.core.gameplay.classes import SkillInstance
    attacker.progression.skills = [SkillInstance(skill_id="Heavy Strike")]
    
    defender = Entity(id=2, kind="monster", faction="monsters")
    defender.combat.max_hp = 100
    defender.combat.hp = 100
    
    # Add Frozen effect
    frozen = StatusEffect(effect_type=EffectType.FROZEN, remaining_ticks=5)
    defender.combat.effects = [frozen]
    
    # Register in world
    world.entities[1] = attacker
    world.entities[2] = defender
    
    config = MagicMock()
    config.min_commitment_ticks = 1
    config.damage_variance = 0.0
    config.threat_damage_mult = 1.0
    
    # Mock Skill Definition
    sdef = MagicMock()
    sdef.name = "Heavy Strike"
    sdef.skill_type = SkillType.ACTIVE
    sdef.damage_type = DamageType.PHYSICAL
    sdef.power = 1.0
    sdef.radius = 0
    sdef.stamina_cost = 0
    sdef.cooldown = 0
    sdef.element = Element.NONE
    
    # Mock Damage Calculator to return 10 base damage (so raw_damage = 9 after armor formula)
    calc_ctx = MagicMock()
    calc_ctx.atk_power = 10
    calc_ctx.atk_mult = 1.0
    calc_ctx.def_power = 0
    calc_ctx.def_mult = 1.0
    calc_ctx.damage = 10
    calc_ctx.is_crit = False
    
    with patch('src.actions.damage.get_damage_calculator') as mock_get_calc:
        mock_calc = MagicMock()
        mock_calc.resolve.return_value = calc_ctx
        mock_get_calc.return_value = mock_calc
        
        # Using REAL RNG for authoritative damage calculation [AOA STABILIZATION]
        from src_legacy.platform.rng import DeterministicRNG
        rng = DeterministicRNG(seed=42)
        
        # Patch SKILL_DEFS to find our mock skill
        from src_legacy.systems.gameplay.action_system import SKILL_DEFS
        with patch.dict(SKILL_DEFS, {"Heavy Strike": sdef}):
            # Explicit mock proposal to capture updates
            from src_legacy.actions.base import ActionProposal
            proposal = ActionProposal(actor_id=attacker.id, verb=ActionType.USE_SKILL, target=("Heavy Strike", defender.id))
            updates = ActionSystem._get_use_skill_updates(
                world, config, rng, None, 
                attacker, sdef.name, defender.id, proposal=proposal
            )
                
            # Apply updates using the authoritative pipeline
            ActionSystem._apply_updates(world, attacker, updates, rng)
            
            # Base damage = 9. Shatter = 1.5x -> 13.
            # 100 - 13 = 87
            assert defender.combat.hp == 87
            # Frozen should be expired (ticks=0)
            assert any(e.effect_type == EffectType.FROZEN and e.remaining_ticks == 0 for e in defender.combat.effects)
