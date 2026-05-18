# src/engine/cognition.py
from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Tuple, Dict

if TYPE_CHECKING:
    from src_legacy.core.state import EntityState, AuthoritativeState

@dataclass(frozen=True)
class EmotionalProfile:
    panic_level: float = 0.0  # 0.0 to 1.0
    aggression_mod: float = 1.0
    is_fleeing: bool = False

class SensoryFilter:
    """
    Pillar 1.2: Selective Attention.
    Filters the viewport based on saliency to simulate cognitive limits.
    """
    
    @staticmethod
    def filter_saliency(
        subject: EntityState,
        neighbors: List[Tuple[int, EntityState]],
        max_targets: int = 5
    ) -> List[EntityState]:
        """
        Scores neighbors and returns the most salient ones.
        """
        scored: List[Tuple[float, EntityState]] = []
        sx, sy = subject.position
        
        current_target_id = subject.task.payload.get("target_id")
        
        for _, ent in neighbors:
            score = 0.0
            
            # 1. Proximity (Inverse Distance)
            dist = max(1.0, abs(ent.position[0] - sx) + abs(ent.position[1] - sy))
            score += 100.0 / dist
            
            # 2. Hostility
            if ent.identity.faction != subject.identity.faction:
                score += 200.0
                # Grudge modifier (if damaged by them recently)
                # TODO: Implement relationship/grudge check
            
            # 3. Focus (Current Target)
            if ent.id == current_target_id:
                score += 300.0
                
            # 4. State
            if not ent.combat.alive:
                score *= 0.1 # Corpses are low saliency
            
            scored.append((score, ent))
            
        # Sort by score descending
        scored.sort(key=lambda x: x[0], reverse=True)
        
        return [ent for _, ent in scored[:max_targets]]

class AppraisalSystem:
    """
    Pillar 1.1: Emotional Spikes.
    Calculates emotional modifiers based on environment and personal state.
    """
    
    @staticmethod
    def evaluate_emotional_state(
        subject: EntityState,
        neighbors: List[EntityState],
        region_trauma: float = 0.0,
        social_context: Optional[SocialComponent] = None
    ) -> EmotionalProfile:
        """
        Calculates Panic and Aggression levels.
        """
        panic = 0.0
        aggression = 0.0
        
        # 0. Regional Dread (Pillar 4.2)
        panic += region_trauma * 0.5
        
        # 0.5 Social Context (Pillar 4.1 Nemesis System)
        if social_context:
            for neighbor in neighbors:
                grudge = social_context.grudge_history.get(neighbor.id, 0.0)
                if grudge > 0.5:
                    # Nemesis detected!
                    if subject.combat.hp > subject.combat.max_hp * 0.5:
                        aggression += grudge * 0.5
                    else:
                        panic += grudge * 0.3
        
        # 1. Personal Safety (HP check)
        hp_percent = subject.combat.hp / max(1, subject.combat.max_hp)
        if hp_percent < 0.2:
            panic += 0.5
        elif hp_percent < 0.1:
            panic += 0.8
            
        # 2. Faction Ratio (Outnumbered)
        allies = 1 # Subject is their own ally
        hostiles = 0
        for ent in neighbors:
            if ent.identity.faction == subject.identity.faction:
                allies += 1
            else:
                hostiles += 1
                
        if hostiles > allies * 2:
            panic += 0.3
            
        # 3. Decision
        is_fleeing = panic > 0.4
        
        return EmotionalProfile(
            panic_level=min(1.0, panic),
            aggression_mod=1.5 if hp_percent > 0.8 else 0.5 if is_fleeing else 1.0,
            is_fleeing=is_fleeing
        )
