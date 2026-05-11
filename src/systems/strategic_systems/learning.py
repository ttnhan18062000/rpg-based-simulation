# Compliance IDs: SOC-135, SOC-138, SOC-139, SOC-140, STRAT-044, STRAT-049, STRAT-051, STRAT-052, STRAT-069, STRAT-075, STRAT-076, STRAT-142, STRAT-195
# Compliance IDs: SOC-135, SOC-138, SOC-139, SOC-140, STRAT-044, STRAT-049, STRAT-051, STRAT-052, STRAT-069, STRAT-075, STRAT-076, STRAT-142
from __future__ import annotations
from typing import Dict, List
from src.core.strategic import TurningPointState

class StrategicLearningService:
    """
    Translates historical turning points into utility biases.
    """

    @staticmethod
    def get_goal_biases(turning_points: List[TurningPointState]) -> Dict[str, float]:
        """
        Returns a map of GoalKind -> utility_delta.
        """
        biases = {}
        
        for tp in turning_points:
            # Impact scales by salience (0.0 to 1.0)
            weight = tp.salience * 10.0 # Up to 10 points bias
            
            if tp.kind == 'great_victory' or tp.kind == 'victory':
                # Victories increase confidence in similar activities
                if 'victory' in tp.id: # ID usually contains the kind (e.g. victory_combat_...)
                    if 'combat' in tp.id:
                        biases['combat'] = biases.get('combat', 0.0) + weight
                    elif 'exploration' in tp.id:
                        biases['exploration'] = biases.get('exploration', 0.0) + weight
                        
            elif tp.kind == 'loss' or tp.kind == 'near_death':
                # Losses/Danger decrease desire for those activities (fear)
                if 'combat' in tp.id or tp.kind == 'near_death':
                    biases['combat'] = biases.get('combat', 0.0) - (weight * 2.0)
                elif 'exploration' in tp.id:
                    biases['exploration'] = biases.get('exploration', 0.0) - weight
                    
            elif tp.kind == 'first_kill':
                # First kill might unlock bloodlust/confidence
                biases['combat'] = biases.get('combat', 0.0) + 5.0
                
            elif tp.kind == 'betrayal':
                # Betrayal reduces social utility
                biases['social'] = biases.get('social', 0.0) - weight
                
        return biases
