from __future__ import annotations
from typing import Optional, Dict, Any

class EvolutionService:
    """
    Handles entity transformation (e.g. Goblin -> Goblin Elite).
    """
    
    EVOLUTION_MAP = {
        "goblin_0": {"target": "goblin_1", "required_level": 10},
        "goblin_1": {"target": "goblin_2", "required_level": 20},
    }

    @staticmethod
    def check_evolution(kind: str, level: int) -> Optional[str]:
        """Returns the new kind if evolution is possible."""
        config = EvolutionService.EVOLUTION_MAP.get(kind)
        if config and level >= config["required_level"]:
            return config["target"]
        return None

    @staticmethod
    def get_evolution_gear(new_kind: str) -> Dict[str, str]:
        """Returns equipment for the new form."""
        if new_kind == "goblin_1":
            return {"MAIN_HAND": "iron_sword", "TORSO": "leather_armor"}
        if new_kind == "goblin_2":
            return {"MAIN_HAND": "iron_sword", "TORSO": "leather_armor", "HEAD": "iron_helmet"}
        return {}
