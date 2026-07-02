"""
src/domains/cooperation/phase.py
───────────────────────────────────────────────────────────────────────────────
Phase 7 — CooperationPhase bounded execution.
"""

from __future__ import annotations
import time
from dataclasses import replace
from src.core.state import AuthoritativeState
from src.core.updates import StateUpdate, EntityUpdate, StrategicUpdate, SocialUpdate, SocialBondUpdate
from src.domains.cooperation.evaluators import HelpNeedEvaluator, PartnerFitEvaluator
from src.domains.cooperation.providers import PartnerCandidateProvider, CandidateBudget
from src.domains.cooperation.services import (
    CooperationDecisionService,
    CooperationIntentBridge,
    PartyObjectiveAlignmentService,
    PartyCohesionService,
    CooperationLearningService
)
from src.domains.cooperation.events import (
    HelpNeedDetectedEvent,
    PartnerSelectedEvent,
    PartnerRejectedEvent,
    CooperationDecisionSelectedEvent
)

class CooperationPhase:
    """
    The main execution boundary of the Phase 7 Social Cooperation loop.
    Cooperation evaluated efficiently under a set strategic ticks budget.
    """

    @staticmethod
    def execute(
        state: AuthoritativeState,
        update: StateUpdate,
    ) -> StateUpdate:
        # Respect feature flag or custom state parameters
        flag = getattr(state, "social_cooperation_enabled", True)
        # Avoid direct state attribute mutations causing TypeError by using state.beliefs or state.periodic_due_ticks
        if hasattr(state, "periodic_due_ticks") and "social_cooperation_disabled" in state.periodic_due_ticks:
            flag = False
        if not flag:
            return update

        new_entity_updates = dict(update.entity_updates)
        budget = CandidateBudget(max_candidates=5, spatial_radius=15.0)
        
        evaluation_count = 0
        t_start = time.perf_counter_ns()
        
        # Scoped evaluation per tick
        for entity_id, entity in state.entities.items():
            if not entity.lifecycle.active or not entity.combat.alive:
                continue

            # Emit events only if state.tick % 10 == 0 or timeline length is within limits
            if len(entity.timeline) < 150:
                # 1. Evaluate help needs
                help_needs = HelpNeedEvaluator.evaluate(entity, state)
                
                # Emit help need events
                for need in help_needs:
                    entity.timeline.append(HelpNeedDetectedEvent(
                        entity_id=entity_id,
                        tick=state.tick,
                        need_key=need.key,
                        severity=need.severity,
                        reason=need.reason
                    ))
            else:
                help_needs = HelpNeedEvaluator.evaluate(entity, state)

            # Skip provider scanning if no help needs detected and no active party logic to process
            if not help_needs and entity.identity.group_id is None:
                continue
                
            evaluation_count += 1
            
            # 2. Get scoped partner candidates
            candidates = PartnerCandidateProvider.get_candidates(entity, state, help_needs, budget)
            
            # 3. Evaluate fit reports for candidates
            fit_reports = []
            for cand_p in candidates:
                cand_ent = state.entities.get(cand_p.entity_id)
                if cand_ent:
                    rep = PartnerFitEvaluator.evaluate(entity, cand_ent, help_needs, state)
                    fit_reports.append(rep)
                    
            # 4. Choose cooperation posture
            decision = CooperationDecisionService.select(entity, help_needs, candidates, tuple(fit_reports), state)
            
            # Emit decision select events only when timeline budget permits
            if len(entity.timeline) < 150:
                entity.timeline.append(CooperationDecisionSelectedEvent(
                    entity_id=entity_id,
                    tick=state.tick,
                    posture=decision.selected_posture,
                    partner_id=decision.selected_partner_id,
                    reason=decision.trace.get("reason", "Cooperation strategy chosen")
                ))
                
                if decision.selected_partner_id:
                    entity.timeline.append(PartnerSelectedEvent(
                        entity_id=entity_id,
                        tick=state.tick,
                        partner_id=decision.selected_partner_id,
                        posture=decision.selected_posture,
                        fit_score=decision.fit_score,
                        reason="Best fit score among candidates"
                    ))
                
                for rej_id, rej_reason in decision.rejected_partners.items():
                    entity.timeline.append(PartnerRejectedEvent(
                        entity_id=entity_id,
                        tick=state.tick,
                        candidate_id=rej_id,
                        reason=rej_reason,
                        fit_score=0.0,
                        trust_score=0.0
                    ))

            # 5. Map cooperation posture to safe contract intent / blockers
            resolved_up = CooperationIntentBridge.map_decision(entity, decision, state)
            
            # Retrieve or create EntityUpdate
            entity_up = new_entity_updates.get(entity_id, EntityUpdate(entity_id=entity_id))
            merged_up = entity_up.merge(resolved_up)
            
            # Feed property updates.
            # Store a JSON-serializable sentinel (the posture string) rather than the raw
            # CooperationDecisionResult object, which would break canonical state hashing
            # when property_updates are merged into entity.identity.properties.
            # EventExtractor only checks `is not None` on this key (line 302), so any
            # truthy value is sufficient to trigger cooperation_event emission.
            prop_up = dict(merged_up.property_updates)
            prop_up["last_cooperation_decision"] = decision.selected_posture.value if hasattr(decision.selected_posture, "value") else str(decision.selected_posture)

            new_entity_updates[entity_id] = replace(merged_up, property_updates=prop_up)

        # 6. Evaluate party cohesion for active groups in this tick
        new_groups_add = list(update.groups_add_or_update)
        for g_id, g_rec in state.groups.items():
            rep = PartyCohesionService.evaluate(g_id, state)
            if rep.status in ("MEMBER_ABANDONING", "LEADER_LOST"):
                # Handle group cohesion collapse: dissolve or signal retreat
                # Map to updates by decrementing trust or updating state
                for mb_id in g_rec.member_ids:
                    mb = state.entities.get(mb_id)
                    if mb and mb_id != g_rec.leader_id:
                        mb_up = new_entity_updates.get(mb_id, EntityUpdate(entity_id=mb_id))
                        # Decrease trust due to party abandonment or leader loss
                        soc_up = mb_up.social or SocialUpdate()
                        new_trust = dict(soc_up.trust_delta)
                        new_trust[g_rec.leader_id] = new_trust.get(g_rec.leader_id, 0.0) - 0.25
                        
                        mb_up = replace(mb_up, social=replace(soc_up, trust_delta=new_trust))
                        new_entity_updates[mb_id] = mb_up
                        
        t_duration_ms = (time.perf_counter_ns() - t_start) / 1e6
        
        # Safe metric reporting
        metric_counters = dict(update.metric_counters) if getattr(update, "metric_counters", None) is not None else {}
        metric_counters["cooperation_evaluations"] = evaluation_count
        metric_counters["cooperation_phase_ms"] = t_duration_ms

        return replace(
            update,
            entity_updates=new_entity_updates,
            metric_counters=metric_counters
        )
