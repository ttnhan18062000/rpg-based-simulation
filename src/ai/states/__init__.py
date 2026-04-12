from src.core.models.enums import AIState
from src.ai.states.base import AIContext, StateHandler
from src.ai.states.navigation import (
    IdleHandler, WanderHandler, ReturnToTownHandler, 
    ReturnToCampHandler, GuardCampHandler, ExhaustedHandler,
    InvestigateHandler
)
from src.ai.states.combat import (
    HuntHandler, CombatHandler, FleeHandler, AlertHandler
)
from src.ai.states.interaction import (
    LootingHandler, HarvestingHandler, CorpseRunHandler
)
from src.ai.states.town import (
    RestingInTownHandler, VisitShopHandler, VisitBlacksmithHandler,
    VisitGuildHandler, VisitClassHallHandler, VisitInnHandler,
    VisitHomeHandler
)
from src.ai.states.routine import SleepingHandler, EatingHandler

STATE_HANDLERS: dict[AIState, StateHandler] = {
    AIState.IDLE: IdleHandler(),
    AIState.WANDER: WanderHandler(),
    AIState.HUNT: HuntHandler(),
    AIState.COMBAT: CombatHandler(),
    AIState.FLEE: FleeHandler(),
    AIState.RETURN_TO_TOWN: ReturnToTownHandler(),
    AIState.RESTING_IN_TOWN: RestingInTownHandler(),
    AIState.RETURN_TO_CAMP: ReturnToCampHandler(),
    AIState.GUARD_CAMP: GuardCampHandler(),
    AIState.LOOTING: LootingHandler(),
    AIState.ALERT: AlertHandler(),
    AIState.VISIT_SHOP: VisitShopHandler(),
    AIState.VISIT_BLACKSMITH: VisitBlacksmithHandler(),
    AIState.VISIT_GUILD: VisitGuildHandler(),
    AIState.HARVESTING: HarvestingHandler(),
    AIState.VISIT_CLASS_HALL: VisitClassHallHandler(),
    AIState.VISIT_INN: VisitInnHandler(),
    AIState.VISIT_HOME: VisitHomeHandler(),
    AIState.SLEEPING: SleepingHandler(),
    AIState.EATING: EatingHandler(),
    AIState.EXHAUSTED: ExhaustedHandler(),
    AIState.INVESTIGATING: InvestigateHandler(),
}

__all__ = [
    # Core types
    "AIContext",
    "StateHandler",
    "STATE_HANDLERS",
    
    # Handlers
    "IdleHandler",
    "WanderHandler",
    "HuntHandler",
    "CombatHandler",
    "FleeHandler",
    "ReturnToTownHandler",
    "RestingInTownHandler",
    "ReturnToCampHandler",
    "GuardCampHandler",
    "LootingHandler",
    "AlertHandler",
    "VisitShopHandler",
    "VisitBlacksmithHandler",
    "VisitGuildHandler",
    "HarvestingHandler",
    "VisitClassHallHandler",
    "VisitInnHandler",
    "VisitHomeHandler",
    "ExhaustedHandler",
    "CorpseRunHandler",
    
    # Shared Helpers (from base.py)
    "is_tile_passable",
    "propose_move_toward",
    "propose_move_away",
    "propose_retreat_home",
    "get_perception_cleanup_update",
    "beyond_leash",
    "should_flee",
    "is_in_hostile_town",
    "is_on_home_territory",
    "is_on_enemy_territory",
    
    # Navigation/Combat Specific Helpers
    "get_weapon_range",
    "best_ready_skill",
    "can_use_potion",
    
    # Town/Interaction Helpers
    "find_building",
    "can_use_buildings",
    "hero_wants_to_buy",
    "hero_has_sellable_items",
    "hero_should_visit_blacksmith",
    "hero_should_visit_guild",
    "hero_should_visit_class_hall",
    "hero_should_visit_inn",
    "hero_should_visit_home",
    "find_nearby_resource",
]

# Re-export key helpers for backward compatibility
from src.ai.states.base import (
    is_tile_passable,
    propose_move_toward,
    propose_move_away,
    propose_retreat_home,
    get_perception_cleanup_update,
    beyond_leash,
    should_flee,
    is_in_hostile_town,
    is_on_home_territory,
    is_on_enemy_territory,
)

from src.ai.states.combat import (
    get_weapon_range,
    best_ready_skill,
    can_use_potion,
)

from src.ai.states.town import (
    find_building,
    can_use_buildings,
    hero_wants_to_buy,
    hero_has_sellable_items,
    hero_should_visit_blacksmith,
    hero_should_visit_guild,
    hero_should_visit_class_hall,
    hero_should_visit_inn,
    hero_should_visit_home,
)

from src.ai.states.interaction import (
    find_nearby_resource,
)
