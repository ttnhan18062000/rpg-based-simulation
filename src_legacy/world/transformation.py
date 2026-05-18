from __future__ import annotations
from typing import Dict, Any, List, Optional
from src_legacy.core.state import RegionState

class TransformationService:
    """
    Authoritative service for regional type shifting (Transformations).
    """

    TRANSFORMATION_THRESHOLDS = {
        "FOREST": {
            "BURNT_FOREST": {"trauma": 50.0},
            "WASTELAND": {"trauma": 100.0, "calamity": 0.5}
        },
        "PLAINS": {
            "DESERT": {"trauma": 80.0},
            "WASTELAND": {"trauma": 150.0}
        },
        "MOUNTAIN": {
            "VOLCANIC": {"calamity": 0.8},
            "FROZEN_PEAKS": {"modifiers": ["FROST"]}
        }
    }

    @staticmethod
    def get_potential_transformation(region: RegionState) -> Optional[str]:
        """
        Determines if the region should transform based on its current state.
        Returns the new kind name if a threshold is met.
        """
        possible_shifts = TransformationService.TRANSFORMATION_THRESHOLDS.get(region.kind, {})
        
        # Sort potential transformations by the number of requirements (most complex first)
        # to ensure we pick the most 'advanced' state if multiple are met.
        sorted_shifts = sorted(
            possible_shifts.items(), 
            key=lambda item: len(item[1]), 
            reverse=True
        )
        
        for next_kind, requirements in sorted_shifts:
            met = True
            
            if "trauma" in requirements and region.trauma_score < requirements["trauma"]:
                met = False
            if "calamity" in requirements and region.calamity_intensity < requirements["calamity"]:
                met = False
            if "modifiers" in requirements:
                for mod in requirements["modifiers"]:
                    if mod not in region.active_modifiers:
                        met = False
                        break
            
            if met:
                return next_kind
                
        return None

    @staticmethod
    def apply_transformation(region: RegionState) -> RegionState:
        """
        Checks for and applies regional transformations.
        """
        next_kind = TransformationService.get_potential_transformation(region)
        if next_kind and next_kind != region.kind:
            from dataclasses import replace
            return replace(region, kind=next_kind)
        return region
