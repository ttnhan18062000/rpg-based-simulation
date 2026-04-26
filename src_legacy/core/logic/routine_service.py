from typing import TYPE_CHECKING, Any
from src_legacy.core.models.enums import GoalType

if TYPE_CHECKING:
    from src_legacy.core.entities.entity import Entity

class RoutineService:
    """Calculates biological and routine utility biases for AI decision making. [PHASE 3]
    
    Pillar: Biological Realism. This service provides stateless utility adjustments 
    that drive entities toward survival behaviors based on their authoritative needs.
    """

    @staticmethod
    def calculate_routine_biases(entity: 'Entity', current_hour: int, current_tick: int) -> dict[GoalType, float]:
        """Returns utility multipliers for goals based on biological debt, schedule, and attachments."""
        # AOA Stabilization: Robust numeric check to avoid MagicMock comparison errors [design-03]
        try:
            current_hour = int(current_hour)
        except (TypeError, ValueError):
            current_hour = 0
            
        biases = {g: 1.0 for g in GoalType}
        routine_state = entity.mind.routine
        
        # 1. Suppression Logic (Disruption and Panic)
        # Disruption can come from recent events (handled by RoutineService updates)
        is_disrupted = current_tick < routine_state.disrupted_until_tick
        is_panicked = entity.mind.emotion.panic > 0.4
        
        # If disrupted or panicked, routines are totally suppressed
        routine_active = not (is_disrupted or is_panicked)

        # 2. Biological Needs (Baseline "Hard" Biases - always active)
        # Sleep Need (Aggressive scaling as debt approaches 1.0)
        if routine_state.sleep_debt > 0.5:
            # Linear scaling from 0.5 (1.0x) to 1.0 (6.0x)
            debt_factor = (routine_state.sleep_debt - 0.5) / 0.5 
            biases[GoalType.SLEEP] *= 1.0 + (debt_factor * 5.0)
            
        # Hunger Need
        if routine_state.hunger_level > 0.3:
            # Linear scaling from 0.3 (1.0x) to 1.0 (4.0x)
            hunger_factor = (routine_state.hunger_level - 0.3) / 0.7 
            biases[GoalType.EAT] = biases.get(GoalType.EAT, 1.0) * (1.0 + (hunger_factor * 3.0))
            
            # Hunger also drives opportunistic looting for food
            biases[GoalType.LOOT] = biases.get(GoalType.LOOT, 1.0) * (1.0 + (hunger_factor * 1.5))

        # 3. Routine Profiles (Phased Social Patterns)
        if routine_active:
            for profile in entity.mind.routine_profiles:
                start, end = profile.schedule_window
                # Handle wrapping window (e.g. 22 to 6)
                in_window = False
                if start < end:
                    in_window = start <= current_hour < end
                else:
                    in_window = current_hour >= start or current_hour < end
                
                if in_window:
                    # Apply bias based on goal and priority
                    # Scale priority (1.0 to 5.0) to multiplier (1.5x up to ~4.0x)
                    multiplier = 1.0 + (profile.priority * 0.6)
                    biases[profile.ideal_goal] = biases.get(profile.ideal_goal, 1.0) * multiplier
                    
                    # Also boost related goals (e.g. WORK boosts REST slightly as preparation)
                    if profile.ideal_goal == GoalType.CRAFT:
                        biases[GoalType.REST] = biases.get(GoalType.REST, 1.0) * 1.1

        # 4. Place Attachment Biases (Spatial Preference)
        # If the entity has a HOME or WORKPLACE, bias relevant goals when they are prioritized
        if routine_active:
            from src_legacy.core.models.enums import AttachmentKind
            for attachment in entity.mind.place_attachments:
                if attachment.kind == AttachmentKind.HOME:
                    # Home increases SLEEP/REST priority
                    if biases.get(GoalType.SLEEP, 1.0) > 1.2 or biases.get(GoalType.REST, 1.0) > 1.2:
                        biases[GoalType.SLEEP] *= (1.0 + attachment.importance * 0.5)
                        biases[GoalType.REST] *= (1.0 + attachment.importance * 0.3)
                
                elif attachment.kind == AttachmentKind.WORKPLACE:
                    # Workplace increases WORK related goals
                    work_goals = (GoalType.CRAFT, GoalType.TRADE, GoalType.GUARD, GoalType.PATROL)
                    for g in work_goals:
                        if biases.get(g, 1.0) > 1.1:
                            biases[g] *= (1.0 + attachment.importance * 0.4)

        # 5. Night/Day Circadian Baseline (for entities without specific profiles)
        # AOA Stabilization: Robust check for non-numeric current_hour from Mocks [design-03]
        safe_hour = current_hour if isinstance(current_hour, (int, float)) else 12
        is_active_window = 6 <= safe_hour < 22
        if not is_active_window and not entity.mind.routine_profiles:
            # Night time baseline: Strong bias toward sleep and safety
            biases[GoalType.SLEEP] = biases.get(GoalType.SLEEP, 1.0) * 2.0
            biases[GoalType.REST] = biases.get(GoalType.REST, 1.0) * 1.5
            
            # Penalties to risky activities
            biases[GoalType.COMBAT] *= 0.6
            biases[GoalType.EXPLORE] *= 0.3
            
        return biases

