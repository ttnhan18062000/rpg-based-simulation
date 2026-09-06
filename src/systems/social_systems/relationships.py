# Compliance IDs: SOC-193, SOC-194, SOC-195, SOC-196, SOC-217
from __future__ import annotations
from typing import Dict, Any, TYPE_CHECKING
from src.core.state import SocialComponent

if TYPE_CHECKING:
    from src.core.updates import SocialUpdate

class RelationshipService:
    """
    Authoritative service for directed social bonds between entities.
    In V2, these are stored in each entity's SocialComponent.
    """

    @staticmethod
    def process_update(social: SocialComponent, update: SocialUpdate) -> SocialComponent:
        """
        Authoritatively apply deltas to social histories.
        Logic ID: SOC-217 (Social updates are authoritative / not direct mutation)
        """
        from dataclasses import replace
        
        new_trust = dict(social.trust_history)
        new_fam = dict(social.familiarity_history)
        new_debt = dict(social.debt_history)
        new_fear = dict(social.fear_history)
        new_grudge = dict(social.grudge_history)
        new_salience = dict(social.salience_history)
        
        # Apply deltas with clamping (-1.0 to 1.0 or 0.0 to 1.0)
        for eid, delta in update.trust_delta.items():
            # Logic ID: SOC-196 (Trust/sentiment changes through interaction evidence)
            new_trust[eid] = max(-1.0, min(1.0, new_trust.get(eid, 0.0) + delta))
            
        for eid, delta in update.familiarity_delta.items():
            # Logic ID: SOC-195 (Familiarity changes through interaction evidence)
            new_fam[eid] = max(0.0, min(1.0, new_fam.get(eid, 0.0) + delta))
            
        for eid, delta in update.debt_delta.items():
            new_debt[eid] = max(-1.0, min(1.0, new_debt.get(eid, 0.0) + delta))
            
        for eid, delta in update.fear_delta.items():
            new_fear[eid] = max(0.0, min(1.0, new_fear.get(eid, 0.0) + delta))
            
        for eid, delta in update.grudge_delta.items():
            new_grudge[eid] = max(0.0, min(5.0, new_grudge.get(eid, 0.0) + delta))
            
        for eid, delta in update.salience_delta.items():
            new_salience[eid] = max(0.0, min(1.0, new_salience.get(eid, 0.0) + delta))

        from src.core.state import SocialBond
        new_bonds = dict(social.bonds)
        for b_upd in update.bond_updates:
            tid = b_upd.target_id
            bond = new_bonds.get(tid, SocialBond(target_id=tid))
            new_bonds[tid] = replace(
                bond,
                familiarity=max(0.0, min(1.0, bond.familiarity + b_upd.familiarity_delta)),
                sentiment=max(-1.0, min(1.0, bond.sentiment + b_upd.sentiment_delta)),
                last_interaction_tick=b_upd.last_interaction_tick_set if b_upd.last_interaction_tick_set is not None else bond.last_interaction_tick,
                role=b_upd.role_set if b_upd.role_set is not None else bond.role
            )

        new_betrayals = list(social.betrayal_records)
        new_betrayals.extend(update.betrayal_records_add)

        new_nemesis = set(social.nemesis_ids)
        new_nemesis.update(update.nemesis_promotion)

        new_places = dict(social.place_attachment)
        for rid, delta in update.place_attachment_delta.items():
            new_places[rid] = max(0.0, min(1.0, new_places.get(rid, 0.0) + delta))

        new_regional_rep = dict(social.regional_reputation)
        for rid, delta in update.regional_reputation_delta.items():
            new_regional_rep[rid] = max(0.0, min(2.0, new_regional_rep.get(rid, 0.0) + delta))

        new_combat_loss = dict(social.combat_loss_counts)
        for eid, count in update.combat_loss_delta.items():
            new_combat_loss[eid] = new_combat_loss.get(eid, 0) + count

        return replace(
            social,
            trust_history=new_trust,
            familiarity_history=new_fam,
            debt_history=new_debt,
            fear_history=new_fear,
            grudge_history=new_grudge,
            salience_history=new_salience,
            bonds=new_bonds,
            nemesis_ids=new_nemesis,
            place_attachment=new_places,
            regional_reputation=new_regional_rep,
            combat_loss_counts=new_combat_loss,
            betrayal_count=social.betrayal_count + update.betrayal_increment,
            betrayal_records=new_betrayals,
            # Logic ID: SOC-193 (Public reputation and private relationship are separate)
            public_reputation=update.reputation_set if update.reputation_set is not None else (
                max(0.0, min(2.0, social.public_reputation + update.heroism_delta - update.notoriety_delta))
            ),
            heroism_score=social.heroism_score + update.heroism_delta,
            notoriety_score=social.notoriety_score + update.notoriety_delta,
            last_offer_tick=update.last_offer_tick_set if update.last_offer_tick_set is not None else social.last_offer_tick,
            rejection_count={k: social.rejection_count.get(k, 0) + v for k, v in update.rejection_increment.items()}
        )

    @staticmethod
    def prune_low_salience(social: SocialComponent, threshold: float = 0.05) -> SocialComponent:
        """
        Prunes social records for entities with low salience to keep state lean.
        """
        from dataclasses import replace
        
        valid_eids = {eid for eid, sal in social.salience_history.items() if sal >= threshold}
        
        return replace(
            social,
            trust_history={k: v for k, v in social.trust_history.items() if k in valid_eids},
            familiarity_history={k: v for k, v in social.familiarity_history.items() if k in valid_eids},
            debt_history={k: v for k, v in social.debt_history.items() if k in valid_eids},
            fear_history={k: v for k, v in social.fear_history.items() if k in valid_eids},
            grudge_history={k: v for k, v in social.grudge_history.items() if k in valid_eids},
            salience_history={k: v for k, v in social.salience_history.items() if k in valid_eids}
        )
