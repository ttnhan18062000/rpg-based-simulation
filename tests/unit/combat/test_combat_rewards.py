from unittest.mock import MagicMock
import pytest
from src.actions.combat import CombatAction, KillRewardService
from src.actions.base import ActionProposal, ProgressionUpdate, WorldUpdate
from src.core.entities.entity import Entity
from src.core.models.vectors import Vector2
from src.core.models.enums import DamageType, Element, HeroClass, Faction
from src.platform.rng import DeterministicRNG
from src.core.aspects.identity import IdentityAspect
from src.core.aspects.combat import CombatAspect
from src.core.aspects.progression import ProgressionAspect
from src.core.aspects.spatial import SpatialAspect

@pytest.fixture
def reward_setup():
    config = MagicMock()
    config.damage_variance = 0.0 # No variance for predictable rewards
    config.threat_damage_mult = 1.0
    rng = DeterministicRNG(0)
    
    # Killer (Hero)
    killer = MagicMock(spec=Entity)
    killer.id = 1
    killer.kind = "hero"
    killer.identity = IdentityAspect(display_name="Hero", kind="hero", faction=Faction.HERO_GUILD)
    killer.combat = CombatAspect(hp=100, max_hp=100, atk_base=100, def_base=10)
    killer.progression = ProgressionAspect(level=1, hero_class=HeroClass.WARRIOR)
    killer.spatial = SpatialAspect(pos=Vector2(10, 10))
    killer.inventory = MagicMock()
    killer.inventory.weapon = None
    killer.mind = MagicMock()
    
    # Victim (Hero)
    victim = MagicMock(spec=Entity)
    victim.id = 2
    victim.kind = "boss"
    victim.identity = IdentityAspect(display_name="Boss", kind="boss", faction=Faction.HERO_GUILD, is_world_boss=True)
    victim.combat = CombatAspect(hp=10, max_hp=500, atk_base=20, def_base=20)
    victim.progression = ProgressionAspect(level=5, gold=100)
    victim.spatial = SpatialAspect(pos=Vector2(11, 10))
    victim.inventory = MagicMock()
    victim.inventory.items = ["magic_orc_axe"]
    victim.mind = MagicMock()
    
    world = MagicMock()
    world.entities = {1: killer, 2: victim}
    world.tick = 100
    world.grid = MagicMock()
    world.grid.has_line_of_sight.return_value = True
    
    return CombatAction(config, rng), killer, victim, world

def test_kill_reward_emission_in_apply(reward_setup):
    action, killer, victim, world = reward_setup
    
    # Proposal for a lethal blow
    proposal = ActionProposal(actor_id=1, verb=2, target=2)
    
    # Apply should now trigger KillRewardService.resolve_kill internally 
    # because damage (predicted ~80+) > victim.hp (10)
    action.apply(proposal, world)
    
    # 1. Verify ProgressionUpdate for rewards was added
    prog_updates = [u for u in proposal.updates if isinstance(u, ProgressionUpdate)]
    assert len(prog_updates) >= 2 # Hit veterancy + Kill rewards
    
    # Check kill rewards (Gold, XP from KillRewardService)
    # XP for higher level victim should be 10
    kill_rewards = next(u for u in prog_updates if u.xp_delta == 10)
    assert kill_rewards.gold_delta == 100 # full gold initially
    assert kill_rewards.veterancy_points_delta == 5
    
    # 2. Verify WorldBoss Rewards (Fame, Titles)
    boss_rewards = next(u for u in prog_updates if u.fame_delta == 100)
    assert "Slayer of Boss" in boss_rewards.titles_add
    
    # 3. Verify Corpse Creation (WorldUpdate)
    world_updates = [u for u in proposal.updates if isinstance(u, WorldUpdate)]
    assert len(world_updates) == 1
    assert world_updates[0].new_corpse is not None
    assert world_updates[0].new_corpse.entity_id == 2
    assert world_updates[0].new_corpse.gold == 80 # 80% for Hero Guild corpse
    
    # 4. Verify Killer gold adjustment (compensating for corpse portion)
    gold_adj = next(u for u in prog_updates if u.gold_delta == -80)
    assert gold_adj is not None

def test_no_reward_on_non_lethal_hit(reward_setup):
    action, killer, victim, world = reward_setup
    victim.combat.hp = 500 # Full health, won't die
    
    proposal = ActionProposal(actor_id=1, verb=2, target=2)
    action.apply(proposal, world)
    
    # No WorldUpdates (corpses) should be emitted
    world_updates = [u for u in proposal.updates if isinstance(u, WorldUpdate)]
    assert len(world_updates) == 0
    
    # No gold/XP/fame rewards
    prog_updates = [u for u in proposal.updates if isinstance(u, ProgressionUpdate)]
    # Should only have hit veterancy (+1)
    assert all(u.xp_delta == 0 and u.fame_delta == 0 for u in prog_updates)
