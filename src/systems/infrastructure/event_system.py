import logging
from typing import Callable, Type, Dict, List, Any

from src.core.data.events import (
    DomainEvent, CombatEvent, DeathEvent, LootEvent, LevelUpEvent, TradeEvent, CraftEvent, QuestEvent
)
from src.core.models.world_state import WorldState

logger = logging.getLogger(__name__)
EventHandler = Callable[[DomainEvent], None]

class EventBus:
    """Simple synchronous pub/sub event bus for domain events."""
    def __init__(self):
        self._subscribers: Dict[Type[DomainEvent], List[EventHandler]] = {}
        self._global_subscribers: List[EventHandler] = []

    def subscribe(self, event_type: Type[DomainEvent], handler: EventHandler) -> None:
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    def subscribe_all(self, handler: EventHandler) -> None:
        self._global_subscribers.append(handler)

    def unsubscribe(self, event_type: Type[DomainEvent], handler: EventHandler) -> None:
        """Remove a subscriber for a specific event type."""
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(handler)
                if not self._subscribers[event_type]:
                    del self._subscribers[event_type]
            except ValueError:
                pass

    def unsubscribe_all(self, handler: EventHandler) -> None:
        """Remove a subscriber from all event types and global subscriptions."""
        for handlers in self._subscribers.values():
            try:
                handlers.remove(handler)
            except ValueError:
                pass
        
        # Clean up empty lists
        self._subscribers = {k: v for k, v in self._subscribers.items() if v}
        
        try:
            self._global_subscribers.remove(handler)
        except ValueError:
            pass

    def publish(self, event: DomainEvent) -> None:
        evt_type = type(event)
        if evt_type in self._subscribers:
            for handler in self._subscribers[evt_type]:
                try:
                    handler(event)
                except Exception as e:
                    logger.error("EventBus handler error for %s: %s", evt_type.__name__, e, exc_info=True)
        
        for handler in self._global_subscribers:
            try:
                handler(event)
            except Exception as e:
                logger.error("EventBus global handler error: %s", e, exc_info=True)


class TelemetryBridge:
    """Translates strongly typed DomainEvents into the legacy REST SimEvent ring buffer."""
    def __init__(self, world: WorldState, emit_func: Callable):
        self._world = world
        self._emit = emit_func

    def attach(self, bus: EventBus) -> None:
        bus.subscribe(CombatEvent, self.handle_combat)
        bus.subscribe(DeathEvent, self.handle_death)
        bus.subscribe(LootEvent, self.handle_loot)
        bus.subscribe(LevelUpEvent, self.handle_level_up)
        bus.subscribe(TradeEvent, self.handle_trade)
        bus.subscribe(CraftEvent, self.handle_craft)
        bus.subscribe(QuestEvent, self.handle_quest)

    def detach(self, bus: EventBus) -> None:
        """Detach all handlers from the bus to break circular references."""
        bus.unsubscribe(CombatEvent, self.handle_combat)
        bus.unsubscribe(DeathEvent, self.handle_death)
        bus.unsubscribe(LootEvent, self.handle_loot)
        bus.unsubscribe(LevelUpEvent, self.handle_level_up)
        bus.unsubscribe(TradeEvent, self.handle_trade)
        bus.unsubscribe(CraftEvent, self.handle_craft)
        bus.unsubscribe(QuestEvent, self.handle_quest)
        self._world = None
        self._emit = None

    def _get_name(self, entity_id: int) -> str:
        ent = self._world.entities.get(entity_id)
        if ent:
            return ent.identity.display_name or f"#{entity_id}"
        return f"#{entity_id}"

    def handle_combat(self, event: CombatEvent) -> None:
        att_name = self._get_name(event.attacker_id)
        dfd_name = self._get_name(event.defender_id)
        
        if event.is_evasion:
            msg = f"{att_name}'s attack was EVADED by {dfd_name}"
        else:
            crit_str = " (CRIT!)" if event.is_crit else ""
            msg = f"{att_name} hit {dfd_name} for {event.damage} damage{crit_str}"

        metadata = event.__dict__.copy()
        metadata["verb"] = event.skill_used # Standardize for legacy E2E
        self._emit("combat", msg, entity_ids=(event.attacker_id, event.defender_id), metadata=metadata)

    def handle_death(self, event: DeathEvent) -> None:
        name = self._get_name(event.entity_id)
        if event.is_permadeath:
            msg = f"{name} DIED PERMANENTLY at level {event.level_at_death}."
        else:
            msg = f"{name} died at level {event.level_at_death}."
        
        # killer_id can be None
        e_ids = [event.entity_id]
        if event.killer_id is not None:
            e_ids.append(event.killer_id)
            
        self._emit("death", msg, entity_ids=tuple(e_ids), metadata=event.__dict__)

    def handle_loot(self, event: LootEvent) -> None:
        name = self._get_name(event.entity_id)
        msg = f"{name} looted {event.item_name} from {event.source}"
        self._emit("loot", msg, entity_ids=(event.entity_id,), metadata=event.__dict__)

    def handle_level_up(self, event: LevelUpEvent) -> None:
        name = self._get_name(event.entity_id)
        msg = f"{name} leveled up! ({event.old_level} -> {event.new_level})"
        self._emit("level_up", msg, entity_ids=(event.entity_id,), metadata=event.__dict__)

    def handle_trade(self, event: TradeEvent) -> None:
        name = self._get_name(event.entity_id)
        action_word = "bought" if event.action == "buy" else "sold"
        cost_word = "for" if event.action == "buy" else "earning"
        msg = f"{name} {action_word} {event.item_id} {cost_word} {event.gold_change}g"
        self._emit("trade", msg, entity_ids=(event.entity_id,), metadata=event.__dict__)

    def handle_craft(self, event: CraftEvent) -> None:
        name = self._get_name(event.entity_id)
        msg = f"{name} crafted {event.output_item} (Recipe: {event.recipe_id})"
        self._emit("craft", msg, entity_ids=(event.entity_id,), metadata=event.__dict__)

    def handle_quest(self, event: QuestEvent) -> None:
        name = self._get_name(event.entity_id)
        msg = f"{name} {event.status} quest '{event.quest_title}'"
        if event.status == "completed":
            msg += f" (+{event.gold_reward}g, +{event.xp_reward}xp)"
        self._emit("quest", msg, entity_ids=(event.entity_id,), metadata=event.__dict__)
