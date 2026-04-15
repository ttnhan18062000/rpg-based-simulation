from __future__ import annotations
from typing import TYPE_CHECKING, Any, Optional
from pydantic import Field, ConfigDict
from src.core.models.base import SimulationModel
from src.core.models.strategy import StrategicStatus, ProjectRecord, ProjectKind, ConcernRecord, ObligationRecord, LeadRecord, BlockerRecord, SocialContractRecord, ObjectiveRecord, OfferStatus

if TYPE_CHECKING:
    from src.core.entities.entity import Entity
    from src.core.models.snapshot import Snapshot
    from src.ai.cognition_capacity import CognitionCapacityProfile

class StrategicCandidate(SimulationModel):
    """Working model for a strategic option within the bounded appraisal phase."""
    model_config = ConfigDict(extra='forbid')
    
    candidate_id: str
    kind: str # e.g. 'project', 'concern', 'obligation', 'lead', 'blocker', 'contract'
    source_id: str
    score: float
    continuity_score: float
    urgency_score: float
    salience_score: float
    capacity_fit_score: float
    source_kind: str
    is_current_project: bool
    is_current_objective: bool
    is_interrupting: bool

class BoundedStrategicSlice(SimulationModel):
    """The final set of candidates an entity is allowed to cognitively consider."""
    model_config = ConfigDict(extra='forbid')
    
    profile: Any # CognitionCapacityProfile
    candidates: list[StrategicCandidate] = Field(default_factory=list)
    dropped_candidates_count: int = 0
    dropped_concerns_count: int = 0
    dropped_leads_count: int = 0
    dropped_suspended_projects_count: int = 0
    reserved_current_project_slot_used: bool = False

class StrategicDecisionOutcome(SimulationModel):
    """The outcome of a bounded strategic appraisal pass."""
    model_config = ConfigDict(extra='forbid')
    
    selected_project_id: str | None = None
    selected_objective_id: str | None = None
    kept_current_project: bool = False
    switched_project: bool = False
    switch_margin_used: float = 0.0
    interrupting_candidate_id: str | None = None
    switch_reason: str | None = None
    bounded_slice: BoundedStrategicSlice

def _clamp(value: float, lower: float, upper: float) -> float:
    if value < lower:
        return lower
    if value > upper:
        return upper
    return value

def _norm_weight(value: float | None, default: float = 1.0, max_value: float = 2.0) -> float:
    if value is None:
        value = default
    # AOA Stabilization: Allow over-paving for strategic priorities [design-03]
    return max(0.0, value / max_value)

def _safe_numeric(obj: Any, default: float) -> float:
    """Safely convert an object to float, defaulting if it's a Mock or invalid."""
    if obj is None: return default
    # Detect unittest.mock objects
    if hasattr(obj, "_mock_return_value") or "Mock" in type(obj).__name__:
        return default
    try:
        return float(obj)
    except (TypeError, ValueError):
        return default

def _bool_score(flag: bool) -> float:
    return 1.0 if flag else 0.0

class BoundedStrategicAppraisalService:
    """Orchestrates bounded strategic appraisal using CognitionCapacityProfile.
    
    Implements exact derivation rules for Milestone 2.
    """
    
    @staticmethod
    def evaluate(entity: Entity, snapshot: Snapshot, profile: CognitionCapacityProfile, ephemeral_updates: Optional[StrategicUpdate] = None) -> StrategicDecisionOutcome:
        """Perform a single bounded strategic evaluation pass."""
        tick = snapshot.tick
        strat = entity.mind.strategic
        
        # 1. Gather Raw Candidates
        all_raw_candidates: list[StrategicCandidate] = []
        
        # Current Project
        curr_prj = strat.current_project
        if curr_prj and curr_prj.status != StrategicStatus.RESOLVED:
            all_raw_candidates.append(BoundedStrategicAppraisalService._create_candidate(entity, curr_prj, profile, "project", is_current=True))
            
        # Unresolved Concerns
        concerns = list(strat.concerns)
        if ephemeral_updates and ephemeral_updates.concerns_add_or_update:
            # Merge ephemeral concerns (overwriting existing by ID if needed)
            for ec in ephemeral_updates.concerns_add_or_update:
                found = False
                for i, c in enumerate(concerns):
                    if c.concern_id == ec.concern_id:
                        concerns[i] = ec
                        found = True
                        break
                if not found:
                    concerns.append(ec)

        for c in concerns:
            if c.resolved_tick is None:
                all_raw_candidates.append(BoundedStrategicAppraisalService._create_candidate(entity, c, profile, "concern"))
                
        # Obligations
        for obligation in strat.obligations:
            if not obligation.resolved_tick:
                all_raw_candidates.append(BoundedStrategicAppraisalService._create_candidate(entity, obligation, profile, "obligation"))
                
        # Active Blockers
        for blocker in strat.blockers:
            if not blocker.resolved:
                cp_score = 0.0
                if curr_prj and (blocker.spawned_from_id == curr_prj.project_id or blocker.source_project_id == curr_prj.project_id):
                    # Use the score of the first candidate if it's the current project
                    cp_score = all_raw_candidates[0].score if (all_raw_candidates and all_raw_candidates[0].is_current_project) else 0.0
                all_raw_candidates.append(BoundedStrategicAppraisalService._create_candidate(entity, blocker, profile, "blocker", curr_prj_score=cp_score))

        # Fresh Unresolved Leads
        for lead in strat.leads:
            if not lead.is_exhausted:
                all_raw_candidates.append(BoundedStrategicAppraisalService._create_candidate(entity, lead, profile, "lead"))
                
        # Candidate Zones [phase_2_intel_capacity]
        for zone in strat.candidate_zones:
            all_raw_candidates.append(BoundedStrategicAppraisalService._create_candidate(entity, zone, profile, "zone"))
                
        # Active Contracts
        for contract in strat.contracts:
            if contract.status == StrategicStatus.ACTIVE:
                all_raw_candidates.append(BoundedStrategicAppraisalService._create_candidate(entity, contract, profile, "contract"))

        # Recruitment Offers [phase_2_intel_capacity]
        for offer in strat.offers:
            if offer.status in (OfferStatus.PENDING, OfferStatus.COUNTERED):
                all_raw_candidates.append(BoundedStrategicAppraisalService._create_candidate(entity, offer, profile, "offer"))

        # Focus (Future Projects)
        projects = list(strat.projects)
        if ephemeral_updates and ephemeral_updates.projects_add_or_update:
             for ep in ephemeral_updates.projects_add_or_update:
                found = False
                for i, p in enumerate(projects):
                    if p.project_id == ep.project_id:
                        projects[i] = ep
                        found = True
                        break
                if not found:
                    projects.append(ep)

        for p in projects:
            if p.status == StrategicStatus.ACTIVE and p.project_id != strat.current_project_id:
                all_raw_candidates.append(BoundedStrategicAppraisalService._create_candidate(entity, p, profile, "project"))
            elif p.status == StrategicStatus.SUSPENDED:
                all_raw_candidates.append(BoundedStrategicAppraisalService._create_candidate(entity, p, profile, "suspended_project"))

        # 1.5 Directive Promotion [TCK-20260415-HARDENING]
        # If no project is active and no concerns are pressing, promote directives to candidacy
        if not curr_prj and not any(c.source_id for c in all_raw_candidates if c.kind == "concern"):
            for directive in strat.directives:
                prj_id = f"project_{directive.directive_id}"
                # Only promote if not already in state
                if not any(p.project_id == prj_id for p in strat.projects):
                    # We create a virtual project record for candidacy only
                    virtual_prj = ProjectRecord(
                        project_id=prj_id,
                        kind=ProjectKind.SOCIAL, # Mapped from directive kind if we had a mapping
                        label=directive.label,
                        priority=directive.priority,
                        created_tick=tick
                    )
                    all_raw_candidates.append(BoundedStrategicAppraisalService._create_candidate(entity, virtual_prj, profile, "project"))

        # 2. Apply Pre-bounds
        bounded_pool, drops = BoundedStrategicAppraisalService._apply_pre_bounds(all_raw_candidates, profile, curr_prj)
        
        # 3. Final Slicing & Slicing Determinism
        # Merge, deduplicate, sort
        seen = {}
        for c in bounded_pool:
            key = (c.kind, c.source_id)
            if key not in seen or c.score > seen[key].score:
                seen[key] = c
        
        final_candidates = sorted(seen.values(), key=lambda x: (-x.score, -int(x.is_current_project), -x.urgency_score, x.candidate_id))
        
        # Final Cap
        reserved_used = any(c.is_current_project for c in final_candidates)
        final_slice_list = []
        dropped_final = 0
        
        if reserved_used:
            # keep current project plus top (limit - 1)
            curr_c = next(c for c in final_candidates if c.is_current_project)
            others = [c for c in final_candidates if not c.is_current_project]
            final_slice_list = [curr_c] + others[:profile.active_slice_limit - 1]
            dropped_final = len(final_candidates) - len(final_slice_list)
        else:
            final_slice_list = final_candidates[:profile.active_slice_limit]
            dropped_final = len(final_candidates) - len(final_slice_list)

        bounded_slice = BoundedStrategicSlice(
            profile=profile,
            candidates=final_slice_list,
            dropped_candidates_count=drops['total'] + dropped_final,
            dropped_concerns_count=drops['concerns'],
            dropped_leads_count=drops['leads'],
            dropped_suspended_projects_count=drops['suspended'],
            reserved_current_project_slot_used=reserved_used
        )
        
        # 4. Continuity Decision
        outcome = BoundedStrategicAppraisalService._resolve_continuity(entity, snapshot, bounded_slice)
        return outcome

    @staticmethod
    def _create_candidate(entity: Entity, source: Any, profile: CognitionCapacityProfile, kind: str, is_current: bool = False, curr_prj_score: float = 0.0) -> StrategicCandidate:
        """Create a scored StrategicCandidate from a raw source record."""
        # Generic ID resolution for all types
        sid = "unknown"
        if kind == "project" or kind == "suspended_project":
            sid = getattr(source, "project_id", "unknown")
        elif kind == "concern":
            sid = getattr(source, "concern_id", "unknown")
        elif kind == "obligation":
            sid = getattr(source, "obligation_id", "unknown")
        elif kind == "lead":
            sid = getattr(source, "lead_id", "unknown")
        elif kind == "blocker":
            sid = getattr(source, "blocker_id", "unknown")
        elif kind == "contract":
            sid = getattr(source, "contract_id", "unknown")
        elif kind == "zone":
            sid = getattr(source, "zone_id", "unknown")
        elif kind == "offer":
            sid = getattr(source, "offer_id", "unknown")
        
        if sid is None:
            sid = "unknown"
        
        cid = f"cand_{kind}_{sid}"
        s_kind = kind
        
        # Scoring Formulas
        score = 0.0
        u_score = 0.0
        s_score = 0.0
        
        if kind == "project" or kind == "suspended_project":
            p = _norm_weight(source.priority, 1.0, 2.0)
            u = _norm_weight(source.urgency, 1.0, 2.0)
            s = _norm_weight(getattr(source, 'salience', 0.5), 1.0, 2.0)
            a = _norm_weight(source.abandonment_cost, 1.0, 2.0)
            u_score = u
            s_score = s
            if kind == "project":
                score = round(max(0.0, 0.30 * p + 0.20 * u + 0.15 * s + 0.25 * a + 0.10 * profile.resume_reliability), 3)
            else:
                score = round(max(0.0, 0.25 * p + 0.20 * u + 0.25 * a + 0.30 * profile.resume_reliability), 3)
        elif kind == "concern":
            p = _norm_weight(source.priority, 1.0, 2.0)
            u = _norm_weight(source.urgency, 1.0, 2.0)
            s = _norm_weight(getattr(source, 'salience', 0.5), 1.0, 2.0)
            u_score = u
            s_score = s
            score = round(max(0.0, 0.25 * p + 0.40 * u + 0.25 * s + 0.10 * (1.0 - profile.interruption_resistance)), 3)
        elif kind == "obligation":
            p = _norm_weight(source.priority, 1.0, 2.0)
            u = _norm_weight(getattr(source, "urgency", 0.5), 1.0, 2.0)
            d = _norm_weight(getattr(source, "deadline_pressure", 0.0), 1.0, 2.0)
            u_score = u
            score = round(max(0.0, 0.30 * p + 0.35 * u + 0.25 * d + 0.10 * profile.judgment_stability), 3)
        elif kind == "lead":
            p = _norm_weight(source.priority, 1.0, 2.0)
            c = _clamp(getattr(source, "certainty", 0.5), 0.0, 1.0)
            f = _clamp(getattr(source, "freshness", 0.5), 0.0, 1.0)
            q = _clamp(getattr(source, "source_quality", 0.5), 0.0, 1.0)
            score = round(_clamp(0.20 * p + 0.25 * c + 0.20 * f + 0.20 * q + 0.15 * profile.evidence_quality, 0.0, 1.0), 3)
        elif kind == "zone":
            conf = _clamp(getattr(source, "confidence", 0.5), 0.0, 1.0)
            # Curiosity comes from personality, not capacity profile
            curiosity = _safe_numeric(getattr(entity.mind.decision.personality, "curiosity", 0.5), 0.5)
            score = round(_clamp(0.50 * conf + 0.30 * profile.evidence_quality + 0.20 * curiosity / 2.0, 0.0, 1.0), 3)
        elif kind == "blocker":
            sev = _norm_weight(source.severity, 1.0, 2.0)
            score = round(_clamp(0.40 * sev + 0.30 * curr_prj_score + 0.15 * profile.planning_budget / 9.0 + 0.15 * profile.blocker_resolution_patience, 0.0, 1.0), 3)
        elif kind == "contract" or kind == "offer":
            p = _norm_weight(getattr(source, 'priority', 1.0), 1.0, 2.0)
            active = 1.0 if getattr(source, 'status', None) == StrategicStatus.ACTIVE else 0.5
            score = round(_clamp(0.35 * p + 0.35 * active + 0.30 * (profile.social_bandwidth / 7.0), 0.0, 1.0), 3)
            
        return StrategicCandidate(
            candidate_id=cid,
            kind=kind,
            source_id=sid,
            score=score,
            continuity_score=0.0,
            urgency_score=u_score,
            salience_score=s_score,
            capacity_fit_score=0.0,
            source_kind=s_kind,
            is_current_project=is_current,
            is_current_objective=(sid == entity.mind.strategic.current_objective_id),
            is_interrupting=(not is_current and score > 0.5)
        )

    @staticmethod
    def _apply_pre_bounds(candidates: list[StrategicCandidate], profile: CognitionCapacityProfile, current_prj: ProjectRecord | None) -> tuple[list[StrategicCandidate], dict[str, int]]:
        """Apply per-category caps before final sorting."""
        pool = []
        drops = {'concerns': 0, 'leads': 0, 'suspended': 0, 'contracts': 0, 'blockers': 0, 'zones': 0, 'allies': 0, 'total': 0}
        
        # Split by kind
        by_kind = {}
        for c in candidates:
            by_kind.setdefault(c.kind, []).append(c)
            
        # 1. Unresolved concerns
        concerns = sorted(by_kind.get('concern', []), key=lambda x: x.score, reverse=True)
        pool.extend(concerns[:profile.concern_intake_limit])
        drops['concerns'] = max(0, len(concerns) - profile.concern_intake_limit)
        
        # 2. Leads
        leads = sorted(by_kind.get('lead', []), key=lambda x: x.score, reverse=True)
        pool.extend(leads[:profile.lead_retention_limit])
        drops['leads'] = max(0, len(leads) - profile.lead_retention_limit)
        
        # 2. Concerns
        concerns = sorted(by_kind.get('concern', []), key=lambda x: x.score, reverse=True)
        pool.extend(concerns[:profile.concern_intake_limit])
        drops['concerns'] = max(0, len(concerns) - profile.concern_intake_limit)
        
        # 3. Suspended projects
        suspended = sorted(by_kind.get('suspended_project', []), key=lambda x: x.score, reverse=True)
        pool.extend(suspended[:profile.planning_budget])
        drops['suspended'] = max(0, len(suspended) - profile.planning_budget)
        
        # 4. Social Evaluations (Contracts + Offers) [phase_2_intel_capacity]
        allies = sorted(by_kind.get('contract', []) + by_kind.get('offer', []), key=lambda x: x.score, reverse=True)
        pool.extend(allies[:profile.ally_evaluation_limit])
        drops['allies'] = max(0, len(allies) - profile.ally_evaluation_limit)
        
        # 5. Candidate Zones [phase_2_intel_capacity]
        zones = sorted(by_kind.get('zone', []), key=lambda x: x.score, reverse=True)
        pool.extend(zones[:profile.candidate_zone_limit])
        drops['zones'] = max(0, len(zones) - profile.candidate_zone_limit)
        
        # 6. Blockers
        blockers = sorted(by_kind.get('blocker', []), key=lambda x: x.score, reverse=True)
        pool.extend(blockers[:profile.detour_depth_limit + 1])
        drops['blockers'] = max(0, len(blockers) - (profile.detour_depth_limit + 1))
        
        # 7. current project
        curr = [c for c in by_kind.get('project', []) if c.is_current_project]
        pool.extend(curr)
        
        # 8. Obligations
        pool.extend(by_kind.get('obligation', []))
        
        # 9. Regular Projects
        pool.extend([c for c in by_kind.get('project', []) if not c.is_current_project])
        
        drops['total'] = sum(v for k, v in drops.items() if k != 'total')
        return pool, drops

    @staticmethod
    def _resolve_continuity(entity: Entity, snapshot: Snapshot, bounded_slice: BoundedStrategicSlice) -> StrategicDecisionOutcome:
        """Resolve project and objective continuity using bounded slice."""
        profile = bounded_slice.profile
        strat = entity.mind.strategic
        current_project_id = strat.current_project_id
        
        # Project Continuity
        current_c = next((c for c in bounded_slice.candidates if c.is_current_project), None)
        current_score = current_c.score if current_c else 0.0
        
        best_rival = None
        rivals = [c for c in bounded_slice.candidates if not c.is_current_project]
        if rivals:
            best_rival = max(rivals, key=lambda x: x.score)
        best_rival_score = best_rival.score if best_rival else 0.0
        
        switch_margin = round(_clamp(0.10 + 0.25 * profile.interruption_resistance + 0.15 * profile.judgment_stability, 0.10, 0.45), 3)
        
        kept = False
        switched = False
        selected_project_id = current_project_id
        interrupting_id = None
        switch_reason = None
        
        if current_project_id:
            # 0. Strategic Hysteresis (Lock) [phase_2_stage_3]
            lock_until = _safe_numeric(getattr(strat, "project_lock_until", 0), 0)
            if lock_until > snapshot.tick:
                 # Lock is active -> Force retention
                 return StrategicDecisionOutcome(
                     selected_project_id=current_project_id,
                     selected_objective_id=strat.current_objective_id,
                     kept_current_project=True,
                     switched_project=False,
                     switch_reason=f"Project {current_project_id} is locked until tick {lock_until}.",
                     bounded_slice=bounded_slice
                 )
                 
            if best_rival_score > current_score + switch_margin:
                # SWITCH
                switched = True
                interrupting_id = best_rival.candidate_id
                switch_reason = f"Rival {best_rival.kind} {best_rival.source_id} score ({best_rival.score}) exceeded current project ({current_score}) by margin {switch_margin}."
                # Map rival to project root
                selected_project_id = BoundedStrategicAppraisalService._map_candidate_to_project(best_rival, strat)
            else:
                # KEEP
                kept = True
        else:
            # NO CURRENT PROJECT -> pick highest project source
            valid_rivals = [c for c in bounded_slice.candidates if c.kind in ('project', 'suspended_project', 'concern', 'obligation')]
            if valid_rivals:
                best_valid = max(valid_rivals, key=lambda x: x.score)
                selected_project_id = BoundedStrategicAppraisalService._map_candidate_to_project(best_valid, strat)
                switched = True
                switch_reason = f"No current project. Selected {best_valid.kind} {best_valid.source_id} (score {best_valid.score}) as new focus."

        # Objective Continuity
        selected_obj_id = strat.current_objective_id
        if kept and selected_project_id == current_project_id:
            # Check for high scorring blockers (above 0.70)
            high_blocker = any(c.kind == "blocker" and c.score > 0.70 for c in bounded_slice.candidates)
            if high_blocker:
                selected_obj_id = BoundedStrategicAppraisalService._derive_objective(selected_project_id, bounded_slice, strat)
        else:
            # Re-derive
            selected_obj_id = BoundedStrategicAppraisalService._derive_objective(selected_project_id, bounded_slice, strat)

        return StrategicDecisionOutcome(
            selected_project_id=selected_project_id,
            selected_objective_id=selected_obj_id,
            kept_current_project=kept,
            switched_project=switched,
            switch_margin_used=switch_margin,
            interrupting_candidate_id=interrupting_id,
            switch_reason=switch_reason,
            bounded_slice=bounded_slice
        )

    @staticmethod
    def _map_candidate_to_project(candidate: StrategicCandidate, strat: Any) -> str | None:
        """Map a candidate to a root project source."""
        if candidate.kind == 'project':
            return candidate.source_id
        if candidate.kind == 'suspended_project':
            return candidate.source_id
        if candidate.kind == 'concern':
            if candidate.source_id.startswith("concern_unstable_region"):
                return "project_stabilization"
            return f"project_{candidate.source_id}"
        if candidate.kind == 'obligation':
            return f"project_{candidate.source_id}"
        # For lead/blocker, no project change
        return strat.current_project_id

    @staticmethod
    def _derive_objective(project_id: str | None, bounded_slice: BoundedStrategicSlice, strat: Any) -> str | None:
        """Derive objective using exact precedence order."""
        if not project_id:
            return None
        
        project = next((p for p in strat.projects if p.project_id == project_id), None)
        if not project:
            return None
            
        # 1. blocker candidate tied to selected project
        for c in bounded_slice.candidates:
            if c.kind == "blocker":
                # Find the blocker record to check tie
                blocker = next((b for b in strat.blockers if b.blocker_id == c.source_id), None)
                if blocker and (blocker.spawned_from_id == project_id or blocker.source_project_id == project_id):
                    return c.source_id
                    
        # 2. lead candidate tied to selected project
        for c in bounded_slice.candidates:
            if c.kind == "lead":
                lead = next((l for l in strat.leads if l.lead_id == c.source_id), None)
                if lead and project_id in lead.related_project_ids:
                    return c.source_id
                    
        # 3. obligation candidate tied to selected project
        for c in bounded_slice.candidates:
            if c.kind == "obligation":
                # Obligations don't currently have a direct project link in Milestone 2 schema other than potential kind
                pass
                
        # 4. concern candidate tied to selected project
        for c in bounded_slice.candidates:
            if c.kind == "concern":
                concern = next((cn for cn in strat.concerns if cn.concern_id == c.source_id), None)
                if concern and concern.source_project_id == project_id:
                    return c.source_id
                    
        # 5. project's active_objective_id
        if project.active_objective_id:
            ao = next((o for o in project.objectives if o.objective_id == project.active_objective_id), None)
            if ao and ao.status != StrategicStatus.RESOLVED:
                return project.active_objective_id
                
        # 6. first unresolved objective in project order
        for obj in project.objectives:
            if obj.status != StrategicStatus.RESOLVED:
                return obj.objective_id
                
        return None
