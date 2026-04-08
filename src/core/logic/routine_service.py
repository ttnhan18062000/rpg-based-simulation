from typing import TYPE_CHECKING, Any
from src.core.models.enums import GoalType

if TYPE_CHECKING:
    from src.core.entities.entity import Entity

class RoutineService:
    """Calculates biological and routine utility biases for AI decision making. [PHASE 3]
    
    Pillar: Biological Realism. This service provides stateless utility adjustments 
    that drive entities toward survival behaviors based on their authoritative needs.
    """

    @staticmethod
    def calculate_routine_biases(entity: 'Entity', current_hour: int) -> dict[GoalType, float]:
        """Returns utility multipliers for goals based on biological debt and schedule.
        
        Args:
            entity: The entity to evaluate.
            current_hour: The current world hour (0-23).
            
        Returns:
            A dictionary mapping GoalType to a utility multiplier (1.0 = no bias).
        """
        biases = {}
        routine = entity.mind.routine
        
        # 1. Sleep Need (Aggressive scaling as debt approaches 1.0)
        # We start biasing after 50% debt.
        if routine.sleep_debt > 0.5:
            # Linear scaling from 0.5 (1.0x) to 1.0 (6.0x)
            debt_factor = (routine.sleep_debt - 0.5) / 0.5 
            biases[GoalType.SLEEP] = 1.0 + (debt_factor * 5.0)
            
        # 2. Hunger Need
        # We start biasing after 30% hunger.
        if routine.hunger_level > 0.3:
            # Linear scaling from 0.3 (1.0x) to 1.0 (4.0x)
            hunger_factor = (routine.hunger_level - 0.3) / 0.7 
            biases[GoalType.EAT] = 1.0 + (hunger_factor * 3.0)
            
            # Hunger also drives opportunistic looting for food
            current_loot_bias = biases.get(GoalType.LOOT, 1.0)
            biases[GoalType.LOOT] = current_loot_bias * (1.0 + (hunger_factor * 1.5))

        # 3. Daily Cycles (Circadian Rhythm)
        # Determine if the entity SHOULD be active based on their individual schedule
        is_active_time = routine.active_start_hour <= current_hour < routine.active_end_hour
        
        if not is_active_time:
            # Night time (or off-hours): Strong bias toward sleep and safety
            biases[GoalType.SLEEP] = biases.get(GoalType.SLEEP, 1.0) * 2.5
            biases[GoalType.REST] = biases.get(GoalType.REST, 1.0) * 1.8
            
            # Significant penalties to high-energy/risky activities during off-hours
            biases[GoalType.COMBAT] = 0.4
            biases[GoalType.EXPLORE] = 0.2
            biases[GoalType.TRADE] = 0.1 # Shops are likely closed anyway
        else:
            # Active time: Slight penalty to sleeping unless sleep_debt is very high
            if routine.sleep_debt < 0.8:
                biases[GoalType.SLEEP] = biases.get(GoalType.SLEEP, 1.0) * 0.1
                biases[GoalType.REST] = biases.get(GoalType.REST, 1.0) * 0.5
            
        return biases
