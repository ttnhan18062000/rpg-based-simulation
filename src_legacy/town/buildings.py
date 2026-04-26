from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional
from src_legacy.core.state import BuildingState

class BuildingRegistry:
    """Registry for static building data and service templates."""
    
    # Building Types
    INN = "INN"
    GUILD = "GUILD"
    SHOP = "SHOP"
    BLACKSMITH = "BLACKSMITH"
    HOME = "HOME"
    CHURCH = "CHURCH"
    
    _templates = {
        INN: {"max_hp": 1000, "services": ["REST", "HEAL_DEBT"]},
        GUILD: {"max_hp": 2000, "services": ["QUEST", "INTEL"]},
        SHOP: {"max_hp": 800, "services": ["TRADE"]},
        BLACKSMITH: {"max_hp": 1200, "services": ["CRAFT", "REPAIR"]},
        HOME: {"max_hp": 500, "services": ["STORAGE", "PRIVATE_REST"]},
        CHURCH: {"max_hp": 1500, "services": ["BLESSING", "RESURRECTION"]},
    }
    
    @staticmethod
    def get_template(kind: str) -> Optional[dict]:
        return BuildingRegistry._templates.get(kind)

    @staticmethod
    def get_services(kind: str) -> List[str]:
        template = BuildingRegistry.get_template(kind)
        return template["services"] if template else []
