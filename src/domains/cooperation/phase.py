"""
src/domains/cooperation/phase.py
───────────────────────────────────────────────────────────────────────────────
Phase 7 — CooperationPhase bounded execution.
"""

from __future__ import annotations
import time
from dataclasses import replace
from src.core.state import AuthoritativeState
from src.core.strategic import ContractStatus
from src.core.updates import StateUpdate, EntityUpdate, StrategicUpdate, SocialUpdate, SocialBondUpdate
from src.domains.cooperation.evaluators import HelpNeedEvaluator, PartnerFitEvaluator
from src.domains.cooperation.providers import PartnerCandidateProvider, CandidateBudget
from src.domains.cooperation.postures import CooperationPosture
from src.domains.cooperation.services import (
    CooperationDecisionService,
    CooperationIntentBridge,
    PartyObjectiveAlignmentService,
    PartyCohesionService,
    CooperationLearningService,
    CooperationOutcomeEvent
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

            # TCK-20260912-PARTY-FORMATION-REACHABILITY-INVESTIGATION: an entity with no help
            # need of its own must still be evaluated when another entity has a pending
            # recruitment offer addressed to it -- otherwise it would never get the chance to
            # accept regardless of what CooperationDecisionService.select() would decide.
            pending_offer = CooperationDecisionService.find_pending_incoming_offer(entity, state)

            # Skip provider scanning if no help needs detected and no active party logic to process
            if not help_needs and entity.identity.group_id is None and pending_offer is None:
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

            # TCK-20260912-PARTY-FORMATION-REACHABILITY-INVESTIGATION: JOIN_PARTY promotes the
            # accepted offer on the OFFERING entity's own strategic.contracts to ACTIVE --
            # contracts are only ever stored on the offering entity's own record (never mirrored
            # to the target), so this writes an EntityUpdate for decision.selected_partner_id,
            # not for `entity` itself. map_decision() has no branch for JOIN_PARTY since its
            # single-entity-return signature can't target a different entity_id; handled here
            # instead, mirroring the party-cohesion-collapse block below, which writes updates for
            # entities other than the loop's own current entity for the same structural reason.
            # Once ACTIVE, GroupSystem.update_groups() (a later phase) forms the real group from
            # this contract on its own -- this block's only job is the status promotion.
            if decision.selected_posture == CooperationPosture.JOIN_PARTY and decision.selected_partner_id is not None:
                offerer_id = decision.selected_partner_id
                contract_id = decision.trace.get("accepted_contract_id")
                offerer = state.entities.get(offerer_id)
                if offerer is not None and contract_id is not None:
                    contract = offerer.strategic.contracts.get(contract_id)
                    if contract is not None and contract.status == ContractStatus.OFFERED:
                        # Use the already-correct, previously-dead ContractService.accept_contract()
                        # (src/systems/social_systems/contracts.py) rather than a raw
                        # dataclasses.replace() -- it also resets expiry_tick to
                        # tick + contract.terms["duration"] via SocialContractSystem
                        # .transition_contract(), which a naive status-only replace would miss,
                        # leaving the promoted contract carrying its original ~10-tick OFFER
                        # expiry and causing GroupSystem.update_groups() to immediately treat it
                        # as invalid and dissolve the just-formed group.
                        from src.systems.social_systems.contracts import ContractService
                        promote_strat_up = ContractService.accept_contract(offerer, contract_id, state.tick)
                        offerer_up = new_entity_updates.get(offerer_id, EntityUpdate(entity_id=offerer_id))
                        offerer_up = offerer_up.merge(EntityUpdate(
                            entity_id=offerer_id,
                            strategic=promote_strat_up,
                        ))
                        new_entity_updates[offerer_id] = offerer_up

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
                # Handle group cohesion collapse: dissolve or signal retreat.
                #
                # TCK-20260911-COOPERATION-TRUST-HISTORY-ZERO-ACCUMULATION-INVESTIGATION: this
                # branch used to hardcode `trust_delta = -0.25` inline instead of calling the
                # real, tested CooperationLearningService.learn() -- the exact same number
                # learn()'s own "abandoned" outcome_type computes, which is not a coincidence:
                # this was a hand-copied shortcut for a call that should have been made. Routing
                # through the real service also picks up grudge_delta (0.3 for "abandoned"),
                # which the old inline version silently dropped. learn()'s own
                # future_preference_modifier is NOT wired here -- there is no existing
                # SocialUpdate/SocialComponent field for a persistent per-partner preference
                # signal (Phase 7's own "future partner preference"/"cooperation memory" design
                # intent was never built as a real field anywhere in this codebase); this is a
                # disclosed gap, not a silent drop, and out of this fix's own narrow scope.
                for mb_id in g_rec.member_ids:
                    mb = state.entities.get(mb_id)
                    if mb and mb_id != g_rec.leader_id:
                        mb_up = new_entity_updates.get(mb_id, EntityUpdate(entity_id=mb_id))
                        outcome = CooperationOutcomeEvent(
                            tick=state.tick,
                            partner_id=g_rec.leader_id,
                            outcome_type="abandoned",
                            description=f"Party cohesion collapse ({rep.status})",
                        )
                        learn_result = CooperationLearningService.learn(mb, outcome, state)

                        soc_up = mb_up.social or SocialUpdate()
                        new_trust = dict(soc_up.trust_delta)
                        new_trust[g_rec.leader_id] = (
                            new_trust.get(g_rec.leader_id, 0.0) + learn_result.trust_delta
                        )
                        new_grudge = dict(soc_up.grudge_delta)
                        new_grudge[g_rec.leader_id] = (
                            new_grudge.get(g_rec.leader_id, 0.0) + learn_result.grudge_delta
                        )

                        mb_up = replace(
                            mb_up,
                            social=replace(soc_up, trust_delta=new_trust, grudge_delta=new_grudge),
                        )
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
