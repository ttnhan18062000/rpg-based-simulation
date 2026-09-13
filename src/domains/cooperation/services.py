"""
src/domains/cooperation/services.py
───────────────────────────────────────────────────────────────────────────────
Phase 7 — Cooperation Decision, Intent Bridge, Alignment/Cohesion and Learning Services.
"""

from __future__ import annotations
from dataclasses import dataclass, field, replace
from typing import Tuple, Dict, Any, List, Optional, Mapping
from src.core.state import EntityState, AuthoritativeState
from src.core.updates import EntityUpdate, StrategicUpdate, SocialUpdate, SocialBondUpdate
from src.core.strategic import ContractState, ContractKind, ContractStatus, RiskLevel
from src.domains.cooperation.postures import CooperationPosture
from src.domains.cooperation.evaluators import HelpNeed, PartnerFitReport
from src.domains.cooperation.providers import PartnerCandidate

@dataclass(frozen=True, slots=True)
class CooperationDecisionResult:
    entity_id: int
    selected_posture: CooperationPosture
    selected_partner_id: Optional[int]
    fit_score: float
    rejected_partners: Dict[int, str]
    trace: Dict[str, Any]

class CooperationDecisionService:
    @staticmethod
    def find_pending_incoming_offer(
        entity: EntityState,
        state: AuthoritativeState,
    ) -> Optional[Tuple[int, str]]:
        """
        TCK-20260912-PARTY-FORMATION-REACHABILITY-INVESTIGATION: the accept-side counterpart to
        CooperationIntentBridge.map_decision()'s REQUEST_HELP/HIRE_SUPPORT offer creation.
        Contracts are only ever stored on the OFFERING entity's own strategic.contracts (never
        mirrored to the target), so the receiving entity has to scan for offers addressed to it.

        Returns (offering_entity_id, contract_id) for the first live, unexpired OFFERED
        RECRUITMENT contract targeting `entity`, deterministically ordered (by offering entity ID,
        then contract ID), or None. Minimal acceptance precondition per this ticket's own scope
        (a pending offer exists and there's no disqualifying reason) -- the offering entity must be
        alive and active, and `entity` itself must not already be in a group. Richer acceptance
        criteria (trust, need matching, faction, existing commitments) are explicitly deferred --
        see docs/plans/deferred_tuning_decisions_register.md.
        """
        if entity.identity.group_id is not None:
            return None
        for offerer_id in sorted(state.entities.keys()):
            if offerer_id == entity.id:
                continue
            offerer = state.entities[offerer_id]
            if not offerer.lifecycle.active or not offerer.combat.alive:
                continue
            for c_id in sorted(offerer.strategic.contracts.keys()):
                contract = offerer.strategic.contracts[c_id]
                if (
                    contract.kind == ContractKind.RECRUITMENT
                    and contract.status == ContractStatus.OFFERED
                    and contract.target_id == entity.id
                    and (contract.expiry_tick <= 0 or contract.expiry_tick > state.tick)
                ):
                    return offerer_id, c_id
        return None

    @staticmethod
    def select(
        entity: EntityState,
        help_needs: Tuple[HelpNeed, ...],
        candidates: Tuple[PartnerCandidate, ...],
        fit_reports: Tuple[PartnerFitReport, ...],
        state: AuthoritativeState,
    ) -> CooperationDecisionResult:
        trace = {}
        rejected = {}

        # 0. Pending incoming recruitment offer takes priority over pursuing (or deferring) this
        # entity's own help needs -- responding to another entity's request is a distinct decision
        # from "do I need help for my own objective."
        pending_offer = CooperationDecisionService.find_pending_incoming_offer(entity, state)
        if pending_offer is not None:
            offerer_id, contract_id = pending_offer
            return CooperationDecisionResult(
                entity_id=entity.id,
                selected_posture=CooperationPosture.JOIN_PARTY,
                selected_partner_id=offerer_id,
                fit_score=1.0,
                rejected_partners={},
                trace={"accepted_contract_id": contract_id, "reason": "Accepting pending recruitment offer"},
            )

        # 1. Easy objective / no needs selects SOLO
        if not help_needs:
            return CooperationDecisionResult(
                entity_id=entity.id,
                selected_posture=CooperationPosture.SOLO,
                selected_partner_id=None,
                fit_score=1.0,
                rejected_partners={},
                trace={"reason": "No help needs detected."}
            )

        on_offer_cooldown = state.tick < entity.identity.cooldowns.get("cooperation_offer_retry", 0)

        # TCK-20260830-COOPERATION-OFFER-CONCURRENT-DUPLICATE-BURST: gate offer creation itself
        # on an already-pending, unexpired RECRUITMENT offer — without this, the same entity can
        # create several simultaneous duplicate offers on consecutive ticks before the first one
        # ever expires (the retry cooldown above only throttles re-offering *after* an expiry).
        has_pending_recruitment_offer = any(
            c.kind == ContractKind.RECRUITMENT
            and c.status == ContractStatus.OFFERED
            and (c.expiry_tick <= 0 or c.expiry_tick > state.tick)
            for c in entity.strategic.contracts.values()
        )

        # personality effects
        pers = entity.identity.personality
        sociability = pers.sociability
        bravery = pers.bravery
        caution = getattr(pers, "caution", 0.0) # Caution fallback
        greed = pers.greed
        
        # Determine dominant help need severity
        max_sev_need = max(help_needs, key=lambda x: x.severity)
        trace["dominant_need"] = max_sev_need.key
        trace["need_severity"] = max_sev_need.severity

        # 2. Score cooperation vs going solo
        # Base solo score drops as need severity rises, boosted by bravery
        solo_score = max(0.0, 1.0 - max_sev_need.severity + bravery * 0.4)
        coop_score = max_sev_need.severity + sociability * 0.3
        
        trace["solo_score_base"] = solo_score
        trace["coop_score_base"] = coop_score

        # Find best partner by fit report
        best_report = None
        for rep in fit_reports:
            # Check rejection bounds (e.g. low trust)
            if rep.trust_score < 0.2:
                rejected[rep.candidate_id] = f"low trust ({rep.trust_score:.2f}) from prior history"
                continue
            if rep.fit_score < 0.3:
                rejected[rep.candidate_id] = f"poor role fit or high risk ({rep.fit_score:.2f})"
                continue
                
            # If greedy entity, check if partner costs too much
            cand_cost = next((c.cost_gold for c in candidates if c.entity_id == rep.candidate_id), 0)
            if greed > 0.6 and cand_cost > entity.inventory.gold * 0.1:
                rejected[rep.candidate_id] = f"high partner cost ({cand_cost} gold)"
                continue
                
            if best_report is None or rep.fit_score > best_report.fit_score:
                best_report = rep

        # 3. Select posture based on scores
        if best_report and not on_offer_cooldown and not has_pending_recruitment_offer:
            # Good partner exists
            best_cand = next(c for c in candidates if c.entity_id == best_report.candidate_id)
            trace["best_partner"] = best_report.candidate_id
            trace["partner_fit_score"] = best_report.fit_score
            
            # Weighted decision comparison
            final_coop_score = coop_score + best_report.fit_score * 0.5
            if final_coop_score > solo_score:
                # Hire vs Request depending on partner cost and role
                if best_cand.cost_gold > 0:
                    chosen_posture = CooperationPosture.HIRE_SUPPORT
                else:
                    chosen_posture = CooperationPosture.REQUEST_HELP
                    
                return CooperationDecisionResult(
                    entity_id=entity.id,
                    selected_posture=chosen_posture,
                    selected_partner_id=best_report.candidate_id,
                    fit_score=best_report.fit_score,
                    rejected_partners=rejected,
                    trace=trace
                )
        
        # No suitable partner or solo preferred
        if solo_score >= 0.5:
            return CooperationDecisionResult(
                entity_id=entity.id,
                selected_posture=CooperationPosture.SOLO,
                selected_partner_id=None,
                fit_score=0.0,
                rejected_partners=rejected,
                trace=trace
            )
        else:
            # Need is too severe to solo, but no partner exists
            return CooperationDecisionResult(
                entity_id=entity.id,
                selected_posture=CooperationPosture.DEFER_NO_PARTNER,
                selected_partner_id=None,
                fit_score=0.0,
                rejected_partners=rejected,
                trace=trace
            )


class CooperationIntentBridge:
    @staticmethod
    def map_decision(
        entity: EntityState,
        decision: CooperationDecisionResult,
        state: AuthoritativeState,
    ) -> EntityUpdate:
        from src.core.strategic import BlockerState, BlockerKind, ContractState, ContractKind, ContractStatus, ProjectState, ProjectKind, ProjectStatus, ObjectiveState, ObjectiveKind, ObjectiveStatus
        
        prop_upd = {}
        strat_upd = StrategicUpdate()
        
        posture = decision.selected_posture
        partner_id = decision.selected_partner_id
        
        # 1. Map Defer to BlockerState
        if posture == CooperationPosture.DEFER_NO_PARTNER:
            blocker = BlockerState(
                id=f"block_no_partner_{entity.id}_{state.tick}",
                kind=BlockerKind.SOCIAL,
                subject="suitable_partner",
                severity=decision.trace.get("need_severity", 0.7),
                resolved=False
            )
            strat_upd = StrategicUpdate(
                blockers_add_or_update=[blocker]
            )
            prop_upd["cooperation_blocker"] = blocker.id
            
        # 2. Map REQUEST_HELP or HIRE_SUPPORT to recruitment ContractState offer
        elif posture in (CooperationPosture.REQUEST_HELP, CooperationPosture.HIRE_SUPPORT) and partner_id:
            c_id = f"cnt_recruit_{entity.id}_{partner_id}_{state.tick}"
            cost = 20 if posture == CooperationPosture.HIRE_SUPPORT else 0
            
            from src.systems.social_systems.contracts import ContractService
            contract = ContractService.create_recruitment_contract(
                contract_id=c_id,
                source_id=entity.id,
                target_id=partner_id,
                daily_pay=cost,
                duration_ticks=100,
                risk_level=RiskLevel.NORMAL,
                tick=state.tick
            )
            
            # Bridge through strategic contracts add
            strat_upd = StrategicUpdate(
                contracts_add_or_update=[contract]
            )
            prop_upd["proposed_cooperation_contract"] = c_id

        # 3. Handle FOLLOW_LEADER and active recruitment contract
        elif posture == CooperationPosture.FOLLOW_LEADER and partner_id:
            # Active leader influences scorer weights
            prop_upd["leader_influence_boost"] = 0.4
            
        return EntityUpdate(
            entity_id=entity.id,
            strategic=strat_upd,
            property_updates=prop_upd
        )


@dataclass(frozen=True, slots=True)
class PartyAlignmentReport:
    aligned_member_ids: Tuple[int, ...]
    drifting_member_ids: Tuple[int, ...]
    blocked_member_ids: Tuple[int, ...]
    reasons: Mapping[int, str]

class PartyObjectiveAlignmentService:
    @staticmethod
    def evaluate(
        leader: EntityState,
        members: Tuple[EntityState, ...],
        state: AuthoritativeState,
    ) -> PartyAlignmentReport:
        aligned = []
        drifting = []
        blocked = []
        reasons = {}
        
        lead_target = leader.navigation.target
        lead_obj = leader.strategic.current_objective_id
        
        for mb in members:
            # Survival priority check: Critical health overrides
            if mb.combat.hp < mb.combat.max_hp * 0.35:
                blocked.append(mb.id)
                reasons[mb.id] = "Low HP survival override of leader objective"
                continue
                
            # Trust check: low trust leads to drift
            trust = mb.social.trust_history.get(leader.id, 0.5)
            if trust < 0.35:
                drifting.append(mb.id)
                reasons[mb.id] = "Low trust in leader objective target"
                continue
                
            # Distance regroup check
            l_pos = leader.navigation.position
            m_pos = mb.navigation.position
            dist = ((l_pos[0] - m_pos[0])**2 + (l_pos[1] - m_pos[1])**2)**0.5
            if dist > 20.0:
                drifting.append(mb.id)
                reasons[mb.id] = "Regroup required (distance too high)"
                continue
                
            aligned.append(mb.id)
            reasons[mb.id] = "Aligned with leader active objective"
            
        return PartyAlignmentReport(
            aligned_member_ids=tuple(aligned),
            drifting_member_ids=tuple(drifting),
            blocked_member_ids=tuple(blocked),
            reasons=reasons
        )


@dataclass(frozen=True, slots=True)
class PartyCohesionReport:
    status: str  # "STABLE", "NEEDS_REGROUP", "MEMBER_DRIFTING", "MEMBER_ABANDONING", "LEADER_LOST"
    issue_member_ids: Tuple[int, ...]
    issue_reasons: Tuple[str, ...]

class PartyCohesionService:
    @staticmethod
    def evaluate(
        group_id: int,
        state: AuthoritativeState,
    ) -> PartyCohesionReport:
        group_rec = state.groups.get(group_id)
        if not group_rec:
            return PartyCohesionReport("LEADER_LOST", (), ("Group record missing",))
            
        leader = state.entities.get(group_rec.leader_id)
        if not leader or not leader.combat.alive or not leader.lifecycle.active:
            return PartyCohesionReport("LEADER_LOST", (group_rec.leader_id,), ("Leader dead or inactive",))
            
        drifting_members = []
        abandoning_members = []
        reasons = []
        
        l_pos = leader.navigation.position
        
        for m_id in group_rec.member_ids:
            if m_id == leader.id:
                continue
            mb = state.entities.get(m_id)
            if not mb or not mb.combat.alive:
                continue
                
            # HP check for retreat abandonment
            if mb.combat.hp < mb.combat.max_hp * 0.25:
                abandoning_members.append(m_id)
                reasons.append(f"Member {m_id} critical low HP triggers abandonment")
                continue
                
            # Trust collapse
            trust = mb.social.trust_history.get(leader.id, 0.5)
            if trust < 0.2:
                abandoning_members.append(m_id)
                reasons.append(f"Member {m_id} trust collapsed under threshold")
                continue

            # Distance drift
            m_pos = mb.navigation.position
            dist = ((l_pos[0] - m_pos[0])**2 + (l_pos[1] - m_pos[1])**2)**0.5
            if dist > 15.0:
                drifting_members.append(m_id)
                reasons.append(f"Member {m_id} drifted far from leader")
                
        if abandoning_members:
            return PartyCohesionReport("MEMBER_ABANDONING", tuple(abandoning_members), tuple(reasons))
        if drifting_members:
            return PartyCohesionReport("NEEDS_REGROUP", tuple(drifting_members), tuple(reasons))
            
        return PartyCohesionReport("STABLE", (), ("Party remains stable and cohesive",))


@dataclass(frozen=True, slots=True)
class CooperationOutcomeEvent:
    tick: int
    partner_id: int
    outcome_type: str  # "success" | "rescue" | "abandoned" | "betrayal"
    description: str

@dataclass(frozen=True, slots=True)
class CooperationLearningResult:
    trust_delta: float
    grudge_delta: float
    future_preference_modifier: float

class CooperationLearningService:
    @staticmethod
    def learn(
        entity: EntityState,
        outcome: CooperationOutcomeEvent,
        state: AuthoritativeState,
    ) -> CooperationLearningResult:
        # One learning event is bounded; does not swing trust extremely unless betrayal
        trust_delta = 0.0
        grudge_delta = 0.0
        pref_mod = 1.0
        
        out_type = outcome.outcome_type
        if out_type == "success":
            trust_delta = 0.08
            pref_mod = 1.2
        elif out_type == "rescue":
            trust_delta = 0.22
            pref_mod = 1.5
        elif out_type == "abandoned":
            trust_delta = -0.25
            grudge_delta = 0.3
            pref_mod = 0.4
        elif out_type == "betrayal":
            trust_delta = -0.75
            grudge_delta = 0.9
            pref_mod = 0.0
            
        # Bounds checking: ensure delta is strictly capped
        return CooperationLearningResult(
            trust_delta=trust_delta,
            grudge_delta=grudge_delta,
            future_preference_modifier=pref_mod
        )
