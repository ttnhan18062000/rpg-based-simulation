import pytest
from unittest.mock import MagicMock, patch
from src.core.entities.entity import Entity
from src.core.models.enums import ActionType, SkillType, SkillTarget, DamageType
from src.core.gameplay.effects import EffectType, StatusEffect
from src.systems.gameplay.action_system import ActionSystem

def test_shatter_combo():
    system = ActionSystem(MagicMock(), MagicMock())
    context = MagicMock()
    context.world.entities = {}
    
    attacker = MagicMock(spec=Entity)
    attacker.id = 1
    attacker.combat.hp = 100
    
    defender = MagicMock(spec=Entity)
    defender.id = 2
    defender.combat.hp = 100
    defender.stats.combat.hp_ratio = 1.0
    defender.combat.alive = True
    # Add Frozen effect
    frozen = StatusEffect(effect_type=EffectType.FROZEN, remaining_ticks=5)
    defender.combat.effects = [frozen]
    
    sdef = MagicMock()
    sdef.name = "Heavy Strike"
    sdef.skill_type = SkillType.ACTIVE
    sdef.damage_type = DamageType.PHYSICAL
    sdef.power = 1.0
    sdef.radius = 0
    
    instance = MagicMock()
    instance.effective_power.return_value = 1.0
    
    # Mock Damage Calculator to return 10 base damage
    calc_ctx = MagicMock()
    calc_ctx.combat.atk_power = 10
    calc_ctx.combat.atk_mult = 1.0
    calc_ctx.combat.def_power = 0
    calc_ctx.combat.def_mult = 1.0
    
    with patch('src.actions.damage.get_damage_calculator') as mock_get_calc:
        mock_calc = MagicMock()
        mock_calc.resolve.return_value = calc_ctx
        mock_get_calc.return_value = mock_calc
        
        system._apply_skill_effect(context, attacker, defender, sdef, instance)
        
        # Base damage = 10. Shatter = 1.5x -> 15.
        # 100 - 15 = 85
        assert defender.combat.hp == 85
        # Frozen should be expired (ticks=0)
        assert frozen.remaining_ticks == 0
