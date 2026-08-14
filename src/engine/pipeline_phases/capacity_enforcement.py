
from __future__ import annotations
from typing import TYPE_CHECKING, Dict, List
from dataclasses import replace

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState, EntityState
    from src.core.updates import StateUpdate, StrategicUpdate

from src.strategy.capacity import CapacityService
from src.core.updates import EntityUpdate, StrategicUpdate

class CapacityEnforcementPhase:
    """
    Authoritative phase to ensure entities do not exceed cognitive bandwidth.
    Logic ID: STRAT-185 (Strategic state retention is bounded)
    """

    @staticmethod
    def enforce(state: AuthoritativeState, update: StateUpdate) -> StateUpdate:
        refined_entity_updates = dict(update.entity_updates)
        
        # Milestone 5 Optimization: Only enforce on strategic-dirty entities
        # Logic ID: PERF-007 (O(Dirty) enforcement)
        from src.core.dirty import get_relevant_entity_ids
        relevant_ids = get_relevant_entity_ids(state, update, "capacity")

        for e_id in relevant_ids:
            entity = state.entities.get(e_id)
            if not entity:
                continue
            
            ent_upd = refined_entity_updates.get(e_id)
            if not ent_upd or not ent_upd.strategic:
                continue
            
            # We must enforce on the PREDICTED state after this update
            # But for simplicity and safety, we can just enforce on the 
            # current state + the proposed update's additions.
            
            strat_upd = ent_upd.strategic
            profile = entity.strategic.profile
            
            # 1. Enforce Leads
            lead_removals = []
            if len(entity.strategic.leads) + len(strat_upd.leads_add_or_update) > profile.max_leads:
                all_leads = dict(entity.strategic.leads)
                for lead in strat_upd.leads_add_or_update:
                    all_leads[lead.id] = lead
                for l_id in strat_upd.leads_remove:
                    all_leads.pop(l_id, None)
                    
                lead_removals = CapacityService.trim_dict(
                    all_leads, 
                    profile.max_leads,
                    lambda l: CapacityEnforcementPhase._score_lead(l)
                )
            
            # 2. Enforce Concerns
            concern_removals = []
            if len(entity.strategic.concerns) + len(strat_upd.concerns_add_or_update) > profile.max_concerns:
                all_concerns = dict(entity.strategic.concerns)
                for concern in strat_upd.concerns_add_or_update:
                    all_concerns[concern.id] = concern
                for c_id in strat_upd.concerns_remove:
                    all_concerns.pop(c_id, None)
                    
                concern_removals = CapacityService.trim_dict(
                    all_concerns,
                    profile.max_concerns,
                    lambda c: c.urgency
                )
            
            # 3. Enforce Turning Points (History)
            all_tps = entity.strategic.turning_points
            max_tps = getattr(profile, "max_turning_points", 20)
            trimmed_tps = all_tps
            if len(all_tps) + len(strat_upd.turning_points_add) > max_tps:
                combined_tps = list(all_tps)
                combined_tps.extend(strat_upd.turning_points_add)
                trimmed_tps = CapacityService.trim_list(
                    combined_tps,
                    max_tps,
                    lambda tp: tp.salience
                )
            
            # 4. Enforce Projects
            project_removals = []
            if len(entity.strategic.projects) + len(strat_upd.projects_add_or_update) > profile.max_active_projects:
                all_projects = dict(entity.strategic.projects)
                for proj in strat_upd.projects_add_or_update:
                    all_projects[proj.id] = proj
                for p_id in strat_upd.projects_remove:
                    all_projects.pop(p_id, None)
                    
                project_removals = CapacityService.trim_dict(
                    all_projects,
                    profile.max_active_projects,
                    lambda p: p.score
                )
            
            # 5. Enforce Hypotheses
            hypo_removals = []
            if len(entity.strategic.hypotheses) + len(strat_upd.hypotheses_add_or_update) > profile.max_hypotheses:
                all_hypotheses = dict(entity.strategic.hypotheses)
                for hypo in strat_upd.hypotheses_add_or_update:
                    all_hypotheses[hypo.id] = hypo
                for h_id in strat_upd.hypotheses_remove:
                    all_hypotheses.pop(h_id, None)
                    
                hypo_removals = CapacityService.trim_dict(
                    all_hypotheses,
                    profile.max_hypotheses,
                    lambda h: h.confidence
                )
            
            # 6. Enforce Candidate Zones
            zone_removals = []
            if len(entity.strategic.candidate_zones) + len(strat_upd.candidate_zones_add_or_update) > profile.max_candidate_zones:
                all_zones = dict(entity.strategic.candidate_zones)
                for zone in strat_upd.candidate_zones_add_or_update:
                    all_zones[zone.id] = zone
                for z_id in strat_upd.candidate_zones_remove:
                    all_zones.pop(z_id, None)
                    
                zone_removals = CapacityService.trim_dict(
                    all_zones,
                    profile.max_candidate_zones,
                    lambda z: z.score
                )

            # 7. Enforce Committed Intentions (ordered by sequence_index -- NOT score-based, unlike 1-6 above)
            ci_removals = []
            if len(entity.strategic.committed_intentions) + len(strat_upd.committed_intentions_add_or_update) > profile.max_committed_intentions:
                by_id = {ci.intention_id: ci for ci in entity.strategic.committed_intentions}
                for ci in strat_upd.committed_intentions_add_or_update:
                    by_id[ci.intention_id] = ci
                for ci_id in strat_upd.committed_intentions_remove:
                    by_id.pop(ci_id, None)
                combined = list(by_id.values())
                survivors = CapacityService.trim_list(combined, profile.max_committed_intentions, score_func=lambda ci: -ci.sequence_index)
                survivor_ids = {ci.intention_id for ci in survivors}
                ci_removals = [ci.intention_id for ci in combined if ci.intention_id not in survivor_ids]

            # If nothing changed, continue
            any_removals = lead_removals or concern_removals or project_removals or hypo_removals or zone_removals or ci_removals
            if not any_removals and len(trimmed_tps) == len(all_tps):
                continue

            # Update the strategic update with removals
            new_leads_remove = list(set(strat_upd.leads_remove) | set(lead_removals))
            new_concerns_remove = list(set(strat_upd.concerns_remove) | set(concern_removals))
            new_projects_remove = list(set(strat_upd.projects_remove) | set(project_removals))
            new_hypotheses_remove = list(set(strat_upd.hypotheses_remove) | set(hypo_removals))
            new_zones_remove = list(set(strat_upd.candidate_zones_remove) | set(zone_removals))
            new_committed_intentions_remove = list(set(strat_upd.committed_intentions_remove) | set(ci_removals))

            refined_entity_updates[e_id] = replace(
                ent_upd,
                strategic=replace(
                    strat_upd,
                    leads_remove=new_leads_remove,
                    concerns_remove=new_concerns_remove,
                    projects_remove=new_projects_remove,
                    hypotheses_remove=new_hypotheses_remove,
                    candidate_zones_remove=new_zones_remove,
                    committed_intentions_remove=new_committed_intentions_remove
                )
            )

            if lead_removals or concern_removals or project_removals or hypo_removals or zone_removals or ci_removals:
                # Audit rejections due to capacity
                reason = "STRATEGIC_CAPACITY_TRIM"
                new_rejections_delta = dict(update.rejections_delta)
                new_rejections_delta[reason] = new_rejections_delta.get(reason, 0) + 1
                update = replace(update, rejections_delta=new_rejections_delta)

                # Mark as overloaded if we had to drop leads
                if lead_removals:
                    refined_entity_updates[e_id] = replace(
                        refined_entity_updates[e_id],
                        strategic=replace(
                            refined_entity_updates[e_id].strategic,
                            overload_source_set="bandwidth",
                            overload_tick_set=state.tick
                        )
                    )

        return replace(update, entity_updates=refined_entity_updates)

    @staticmethod
    def _score_lead(lead) -> float:
        from src.core.strategic import LeadCertainty
        certainty_map = {
            LeadCertainty.PRECISE: 1.0,
            LeadCertainty.APPROXIMATE: 0.7,
            LeadCertainty.VAGUE: 0.3,
            LeadCertainty.EXHAUSTED: 0.0
        }
        return certainty_map.get(lead.certainty, 0.0)
