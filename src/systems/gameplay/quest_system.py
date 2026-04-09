"""QuestSystem handles quest progression and rewards."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.systems.infrastructure.base import System

if TYPE_CHECKING:
    from src.systems.infrastructure.base import SystemContext

logger = logging.getLogger(__name__)


class QuestSystem(System):
    """System for managing entity quests and rewards."""

    def on_tick(self, context: SystemContext, tick: int) -> None:
        """Check quest completion and prune finished quests."""
        from src.core.gameplay.quests import QuestType
        
        world = context.world
        for entity in world.entities.values():
            if not entity.combat.alive or entity.kind == "generator" or not entity.progression.quests:
                continue
                
            for q in entity.progression.quests:
                if q.completed:
                    continue
                    
                # EXPLORE: complete when hero is within 2 tiles of target
                if q.quest_type == QuestType.EXPLORE and q.target_pos is not None:
                    if entity.spatial.pos.manhattan(q.target_pos) <= 2:
                        q.advance()
                        from src.utils.metrics import SIM_QUEST_STATUS_TOTAL
                        SIM_QUEST_STATUS_TOTAL.labels(type="explore", status="completed").inc()
                        
                        # Use Aspects for rewards
                        prog = entity.progression
                        if prog:
                            prog.gold += q.gold_reward
                            prog.xp += q.xp_reward
                            entity.identity.reputation += 5.0
                            
                        logger.info(
                            "Tick %d: Entity %d completed quest '%s' → +%d gold, +%d XP",
                            tick, entity.id, q.title, q.gold_reward, q.xp_reward,
                        )
                        if hasattr(world, "event_bus") and world.event_bus:
                            from src.core.data.events import QuestEvent
                            world.event_bus.publish(QuestEvent(
                                entity_id=entity.id,
                                quest_title=q.title,
                                quest_type=q.quest_type.name,
                                status="completed",
                                gold_reward=q.gold_reward,
                                xp_reward=q.xp_reward
                            ))
            
            # Prune completed quests older than 50 ticks (keep for display briefly)
            entity.progression.quests = [q for q in entity.progression.quests if not q.completed or tick % 50 != 0]
