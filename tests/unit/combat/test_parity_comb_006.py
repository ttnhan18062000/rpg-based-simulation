"""
tests/unit/combat/test_parity_comb_006.py

COMB-006: AoE radius application legality — splash damage must not affect
dead or inactive entities even if they are within the splash radius.
"""

from dataclasses import replace
from src.core.state import AuthoritativeState
from src.core.builder import V2EntityBuilder
from src.core.enums import Faction
from src.engine.combat import CombatResolutionSystem


def _attacker(entity_id=1, pos=(0, 0), atk=50, hp=100):
    return (V2EntityBuilder(entity_id)
        .kind("human")
        .location(*pos)
        .identity(faction=Faction.HERO_GUILD)
        .combat(hp=hp, atk=atk, readiness=100.0, max_hp=100, attack_range=10)
        .build()
    )


def _target(entity_id, pos, hp=100, alive=True, active=True):
    ent = (V2EntityBuilder(entity_id)
        .kind("monster")
        .location(*pos)
        .identity(faction=Faction.MONSTER_HORDE)
        .combat(hp=hp, readiness=0.0, max_hp=100)
        .build()
    )
    ent = replace(ent, combat=replace(ent.combat, alive=alive))
    ent = replace(ent, lifecycle=replace(ent.lifecycle, active=active))
    return ent


class TestAoERadiusLegality:
    def test_aoe_splash_skips_dead_entities(self):
        """COMB-006: dead entities (alive=False) inside radius must not receive splash damage."""
        attacker = _attacker(1, pos=(0, 0), atk=50)
        dead_enemy = _target(2, pos=(1, 0), alive=False)

        state = AuthoritativeState(
            entities={1: attacker, 2: dead_enemy}, tick=1, seed=1
        )

        updates = CombatResolutionSystem.resolve_aoe_attack(attacker, (1, 0), radius=3, state=state)

        assert attacker.id in updates
        assert updates[attacker.id].outcome_kind == "SUCCESS"
        assert 2 not in updates, "Dead entity inside AoE radius must not receive splash damage"

    def test_aoe_splash_skips_inactive_entities(self):
        """COMB-006: inactive entities inside radius must not receive splash damage."""
        attacker = _attacker(1, pos=(0, 0), atk=50)
        inactive_enemy = _target(3, pos=(1, 0), active=False)

        state = AuthoritativeState(
            entities={1: attacker, 3: inactive_enemy}, tick=1, seed=1
        )

        updates = CombatResolutionSystem.resolve_aoe_attack(attacker, (1, 0), radius=3, state=state)

        assert attacker.id in updates
        assert 3 not in updates, "Inactive entity inside AoE radius must not receive splash damage"

    def test_aoe_splash_hits_living_active_enemy(self):
        """Control: living active enemies inside radius DO receive splash damage."""
        attacker = _attacker(1, pos=(0, 0), atk=50)
        live_enemy = _target(4, pos=(1, 0), alive=True, active=True)

        state = AuthoritativeState(
            entities={1: attacker, 4: live_enemy}, tick=1, seed=1
        )

        updates = CombatResolutionSystem.resolve_aoe_attack(attacker, (1, 0), radius=3, state=state)

        assert 4 in updates, "Living active enemy inside AoE radius must receive splash damage"
        assert updates[4].damage_taken > 0
