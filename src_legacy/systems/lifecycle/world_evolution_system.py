"""WorldEvolutionSystem manages global difficulty scaling and faction aggression."""

from __future__ import annotations
from src_legacy.systems.infrastructure.base import System, SystemContext

class WorldEvolutionSystem(System):
    """System for managing simulation-wide difficulty and aggressive scaling."""

    def on_tick(self, ctx: SystemContext, tick: int) -> None:
        """Advance world age and update global modifiers."""
        world = ctx.world
        world.world_age += 1
        
        # Difficulty increases every 10k ticks
        world.difficulty_modifier = 1.0 + (world.world_age // 10000) * 0.1
        
        from src_legacy.utils.metrics import SIM_WORLD_DIFFICULTY_MULT
        SIM_WORLD_DIFFICULTY_MULT.set(world.difficulty_modifier)
        
        # Faction slow-creep aggression
        for f in [1, 2, 3]: # Faction enums or hardcoded indices
            agg = world.faction_aggression.get(f, 0.0)
            world.faction_aggression[f] = min(100.0, agg + 0.001)
