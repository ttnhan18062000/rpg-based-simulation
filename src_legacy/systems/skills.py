from __future__ import annotations
from typing import TYPE_CHECKING, Dict, Set
from dataclasses import replace

if TYPE_CHECKING:
    from src_legacy.core.state import AuthoritativeState, EntityState
    from src_legacy.core.updates import StateUpdate

class SkillSystem:
    """
    Authoritative logic for skill unlocks and cooldown management.
    Law: Entities cannot use skills they have not unlocked or that are on cooldown.
    """

    @staticmethod
    def process_skill_unlocks(state: AuthoritativeState, update: StateUpdate) -> StateUpdate:
        """
        Check if any entity has leveled up or changed class and unlock eligible skills.
        """
        from src_legacy.core.registry import Registry
        from src_legacy.core.updates import IdentityUpdate
        
        refined_entity_updates = dict(update.entity_updates)
        
        for e_id, ent_upd in update.entity_updates.items():
            if not ent_upd.identity:
                continue
                
            entity = state.entities.get(e_id)
            if not entity:
                continue
                
            # If level or class changed, re-evaluate skills
            level = ent_upd.identity.evolution_level_set if ent_upd.identity.evolution_level_set is not None else entity.identity.evolution_level
            # In PH8, we haven't implemented full class changing via IdentityUpdate yet, 
            # but we assume entity.identity.class_id has the class.
            current_class = entity.identity.class_id
            
            new_skills: Set[str] = set()
            for skill_id, skill_data in Registry.SKILLS.items():
                if skill_id in entity.identity.learned_skills:
                    continue
                    
                if level >= skill_data.required_level:
                    if skill_data.required_class is None or skill_data.required_class == current_class:
                        new_skills.add(skill_id)
                        
            if new_skills:
                # Merge into IdentityUpdate
                current_learned = list(ent_upd.identity.skills_learned) if ent_upd.identity and hasattr(ent_upd.identity, 'skills_learned') else []
                for s in new_skills:
                    if s not in current_learned:
                        current_learned.append(s)
                
                id_upd = ent_upd.identity or IdentityUpdate()
                id_upd = replace(id_upd, skills_learned=current_learned)
                
                refined_entity_updates[e_id] = replace(ent_upd, identity=id_upd)
                
        return replace(update, entity_updates=refined_entity_updates)
