"""Tests for mob roaming leash mechanic (enhance-04).

Covers:
- WanderHandler returns home when beyond leash radius
- HuntHandler abandons chase when beyond leash × 1.5
- HuntHandler abandons chase after give-up ticks
- HuntHandler resets chase_ticks on combat engagement
- ReturnToCampHandler heals while returning
- No leash enforcement for entities with leash_radius=0
- beyond_leash helper function
"""



from src.actions.base import ActionProposal
from src.ai.states import (
    AIContext, HuntHandler, WanderHandler, ReturnToCampHandler, beyond_leash,
)
from src.config import SimulationConfig
from src.core.models.enums import ActionType, AIState
from src.core.gameplay.faction import Faction, FactionRegistry
from src.core.world.grid import Grid
from src.core.gameplay.items.items import Inventory
from src.core.entities.entity import Entity, Vector2
from src.core.models.snapshot import Snapshot
from src.core.models.world_state import WorldState
from src.platform.rng import DeterministicRNG
from src.platform.spatial_hash import SpatialHash


def _make_world(width: int = 64, height: int = 64, camp_pos: Vector2 | None = None) -> WorldState:
    grid = Grid(width, height)
    spatial = SpatialHash(8)
    w = WorldState(seed=42, grid=grid, spatial_index=spatial)
    if camp_pos is not None:
        w.camps.append(camp_pos)
    return w


def _make_mob(
    eid: int, x: int, y: int,
    home_x: int = 5, home_y: int = 5,
    leash_radius: int = 15,
    chase_ticks: int = 0,
    hp: int = 50, max_hp: int = 50,
    ai_state: AIState = AIState.WANDER,
) -> Entity:
    e = Entity(id=eid, kind="goblin")
    e.identity.faction = Faction.GOBLIN_HORDE
    e.spatial.pos = Vector2(x, y)
    from src.core.aspects.inventory import InventoryAspect
    e.inventory = InventoryAspect(items=[], max_slots=12, max_weight=30.0)
    e.spatial.home_pos = Vector2(home_x, home_y)
    e.spatial.leash_radius = leash_radius
    e.combat.hp = hp
    e.combat.max_hp = max_hp
    e.combat.atk_base = 10
    e.combat.def_base = 5
    e.combat.spd_base = 10
    e.mind.decision.ai_state = ai_state
    e.mind.navigation.chase_ticks = chase_ticks
    return e


def _make_hero(eid: int, x: int, y: int) -> Entity:
    hero = Entity(id=eid, kind="hero")
    hero.identity.faction = Faction.HERO_GUILD
    hero.spatial.pos = Vector2(x, y)
    from src.core.aspects.inventory import InventoryAspect
    hero.inventory = InventoryAspect(items=[], max_slots=36, max_weight=90.0)
    hero.combat.hp = 100
    hero.combat.max_hp = 100
    hero.combat.atk_base = 15
    hero.combat.def_base = 5
    hero.combat.spd_base = 10
    return hero


def _make_ctx(actor: Entity, world: WorldState) -> AIContext:
    cfg = SimulationConfig()
    rng = DeterministicRNG(42)
    faction_reg = FactionRegistry.default()
    snapshot = Snapshot.from_world(world)
    return AIContext(
        actor=snapshot.entities[actor.id],
        snapshot=snapshot,
        config=cfg,
        rng=rng,
        faction_reg=faction_reg,
    )


# -----------------------------------------------------------------------
# beyond_leash helper
# -----------------------------------------------------------------------

class TestBeyondLeash:
    """Unit tests for the beyond_leash() helper."""

    def test_no_leash_returns_false(self):
        mob = _make_mob(1, x=50, y=50, leash_radius=0)
        assert beyond_leash(mob) is False

    def test_no_home_returns_false(self):
        e = Entity(id=1, kind="goblin")
        e.identity.faction = Faction.GOBLIN_HORDE
        e.spatial.pos = Vector2(50, 50)
        e.spatial.home_pos = None
        e.spatial.leash_radius = 15
        assert beyond_leash(e) is False

    def test_within_radius_returns_false(self):
        mob = _make_mob(1, x=15, y=5, leash_radius=15)  # distance 10
        assert beyond_leash(mob) is False

    def test_beyond_radius_returns_true(self):
        mob = _make_mob(1, x=25, y=5, leash_radius=15)  # distance 20
        assert beyond_leash(mob) is True

    def test_multiplier_extends_range(self):
        mob = _make_mob(1, x=25, y=5, leash_radius=15)  # distance 20
        assert beyond_leash(mob, multiplier=1.0) is True
        assert beyond_leash(mob, multiplier=1.5) is False  # 15*1.5=22 > 20


# -----------------------------------------------------------------------
# WanderHandler leash
# -----------------------------------------------------------------------

class TestWanderLeash:
    """WanderHandler should return mobs home when beyond leash."""

    def test_mob_beyond_leash_returns_to_camp(self):
        world = _make_world(camp_pos=Vector2(5, 5))
        mob = _make_mob(1, x=30, y=5, leash_radius=15)  # 25 tiles from home (5,5)
        mob.mind.decision.ai_state = AIState.WANDER
        world.add_entity(mob)

        ctx = _make_ctx(mob, world)
        handler = WanderHandler()
        state, proposal = handler.handle(ctx)

        assert state == AIState.RETURN_TO_CAMP, (
            f"Mob beyond leash should return to camp, got {state}")
        assert "leash" in proposal.reason.lower() or "returning" in proposal.reason.lower()

    def test_mob_within_leash_wanders_normally(self):
        world = _make_world()
        mob = _make_mob(1, x=10, y=5, leash_radius=15)  # 5 tiles from home
        mob.mind.decision.ai_state = AIState.WANDER
        world.add_entity(mob)

        ctx = _make_ctx(mob, world)
        handler = WanderHandler()
        state, proposal = handler.handle(ctx)

        assert state == AIState.WANDER, (
            f"Mob within leash should continue wandering, got {state}")

    def test_no_leash_mob_wanders_freely(self):
        world = _make_world()
        mob = _make_mob(1, x=50, y=50, leash_radius=0)  # no leash
        mob.mind.decision.ai_state = AIState.WANDER
        world.add_entity(mob)

        ctx = _make_ctx(mob, world)
        handler = WanderHandler()
        state, proposal = handler.handle(ctx)

        assert state == AIState.WANDER, (
            f"Mob without leash should wander freely, got {state}")


# -----------------------------------------------------------------------
# HuntHandler leash
# -----------------------------------------------------------------------

class TestHuntLeash:
    """HuntHandler should abandon chase when leash exceeded or chase times out."""

    def test_chase_beyond_leash_abandons(self):
        """Mob chasing beyond 1.5× leash radius should abandon."""
        world = _make_world(camp_pos=Vector2(5, 5))
        # Mob far from home, chasing a hero even farther away
        mob = _make_mob(1, x=30, y=5, leash_radius=15)  # 25 from home > 15*1.5=22
        mob.mind.decision.ai_state = AIState.HUNT
        hero = _make_hero(2, x=32, y=5)
        world.add_entity(mob)
        world.add_entity(hero)

        ctx = _make_ctx(mob, world)
        handler = HuntHandler()
        state, proposal = handler.handle(ctx)

        assert state == AIState.RETURN_TO_CAMP, (
            f"Mob beyond chase leash should return, got {state}")

    def test_chase_within_leash_continues(self):
        """Mob chasing within 1.5× leash should keep hunting."""
        world = _make_world(camp_pos=Vector2(0, 0))
        mob = _make_mob(1, x=15, y=5, leash_radius=15)  # 10 from home < 22
        mob.mind.decision.ai_state = AIState.HUNT
        hero = _make_hero(2, x=18, y=5)
        world.add_entity(mob)
        world.add_entity(hero)

        ctx = _make_ctx(mob, world)
        handler = HuntHandler()
        state, proposal = handler.handle(ctx)

        assert state == AIState.HUNT, (
            f"Mob within chase leash should keep hunting, got {state}")

    def test_chase_give_up_after_timeout(self):
        """Mob should abandon chase after mob_chase_give_up_ticks."""
        world = _make_world(camp_pos=Vector2(5, 5))
        mob = _make_mob(1, x=10, y=5, leash_radius=15, chase_ticks=20)
        mob.mind.decision.ai_state = AIState.HUNT
        hero = _make_hero(2, x=14, y=5)
        world.add_entity(mob)
        world.add_entity(hero)

        ctx = _make_ctx(mob, world)
        handler = HuntHandler()
        state, proposal = handler.handle(ctx)

        assert state == AIState.RETURN_TO_CAMP, (
            f"Mob after chase timeout should return, got {state}")
        assert "timed out" in proposal.reason.lower()

    def test_chase_ticks_increments(self):
        """chase_ticks should increment each time mob moves toward enemy."""
        world = _make_world()
        mob = _make_mob(1, x=10, y=5, leash_radius=15, chase_ticks=5)
        mob.mind.decision.ai_state = AIState.HUNT
        hero = _make_hero(2, x=14, y=5)
        world.add_entity(mob)
        world.add_entity(hero)

        ctx = _make_ctx(mob, world)
        handler = HuntHandler()
        state, proposal = handler.handle(ctx)

        assert state == AIState.HUNT
        assert proposal.intent_metadata.get("chase_ticks") == 6, (
            f"chase_ticks should increment to 6 in metadata, got {proposal.intent_metadata.get('chase_ticks')}")

    def test_chase_ticks_resets_on_combat(self):
        """chase_ticks should reset when mob engages in combat."""
        world = _make_world()
        mob = _make_mob(1, x=10, y=5, leash_radius=15, chase_ticks=15)
        mob.mind.decision.ai_state = AIState.HUNT
        hero = _make_hero(2, x=10, y=6)  # adjacent
        world.add_entity(mob)
        world.add_entity(hero)

        ctx = _make_ctx(mob, world)
        handler = HuntHandler()
        state, proposal = handler.handle(ctx)

        assert state == AIState.COMBAT
        assert proposal.intent_metadata.get("chase_ticks") == 0, (
            f"chase_ticks should reset on combat, got {proposal.intent_metadata.get('chase_ticks')}")

    def test_no_leash_mob_hunts_freely(self):
        """Mob without leash should hunt without restrictions."""
        world = _make_world()
        mob = _make_mob(1, x=50, y=50, leash_radius=0, chase_ticks=100)
        mob.mind.decision.ai_state = AIState.HUNT
        hero = _make_hero(2, x=53, y=50)
        world.add_entity(mob)
        world.add_entity(hero)

        ctx = _make_ctx(mob, world)
        handler = HuntHandler()
        state, proposal = handler.handle(ctx)

        assert state == AIState.HUNT, (
            f"Mob without leash should keep hunting, got {state}")


# -----------------------------------------------------------------------
# ReturnToCampHandler heal-on-return
# -----------------------------------------------------------------------

class TestReturnToCampHeal:
    """ReturnToCampHandler should heal mobs while they walk home."""

    def test_heals_while_returning(self):
        """Mob should regen HP each tick while returning to camp."""
        world = _make_world(camp_pos=Vector2(0, 0))
        mob = _make_mob(1, x=20, y=5, hp=30, max_hp=100)
        mob.mind.decision.ai_state = AIState.RETURN_TO_CAMP
        world.add_entity(mob)

        ctx = _make_ctx(mob, world)
        handler = ReturnToCampHandler()
        state, proposal = handler.handle(ctx)
        # 5% of 100 max_hp = 5 hp healed
        assert proposal.intent_metadata.get("hp_add") == 5, (
            f"Heal intent should be 5, got {proposal.intent_metadata.get('hp_add')}")

    def test_does_not_overheal(self):
        """Healing should not exceed max HP."""
        world = _make_world(camp_pos=Vector2(0, 0))
        mob = _make_mob(1, x=20, y=5, hp=98, max_hp=100)
        mob.mind.decision.ai_state = AIState.RETURN_TO_CAMP
        world.add_entity(mob)

        ctx = _make_ctx(mob, world)
        handler = ReturnToCampHandler()
        state, proposal = handler.handle(ctx)
 
        assert proposal.intent_metadata.get("hp_add") == 2, (
            f"Should heal only 2 to hit cap, got {proposal.intent_metadata.get('hp_add')}")

    def test_full_hp_no_change(self):
        """Already full HP should not change."""
        world = _make_world(camp_pos=Vector2(0, 0))
        mob = _make_mob(1, x=20, y=5, hp=100, max_hp=100)
        mob.mind.decision.ai_state = AIState.RETURN_TO_CAMP
        world.add_entity(mob)

        ctx = _make_ctx(mob, world)
        handler = ReturnToCampHandler()
        state, proposal = handler.handle(ctx)
 
        assert proposal.intent_metadata.get("hp_add") is None, (
            "Mob should NOT heal when at full HP")
