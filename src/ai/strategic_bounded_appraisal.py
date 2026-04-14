from __future__ import annotations
from typing import TYPE_CHECKING, Any, Optional
from pydantic import Field, ConfigDict
from src.core.models.base import SimulationModel
from src.core.models.strategy import StrategicStatus, ProjectRecord, ConcernRecord, ObligationRecord, LeadRecord, BlockerRecord, SocialContractRecord, ObjectiveRecord

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
    return _clamp(value / max_value, 0.0, 1.0)

def _bool_score(flag: bool) -> float:
    return 1.0 if flag else 0.0

class BoundedStrategicAppraisalService:
    """Orchestrates bounded strategic appraisal using CognitionCapacityProfile.
    
    Implements exact derivation rules for Milestone 2.
    """
    
    @staticmethod
    def evaluate(entity: Entity, snapshot: Snapshot, profile: CognitionCapacityProfile) -> StrategicDecisionOutcome:
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
        for concern in strat.concerns:
            if not concern.resolved_tick:
                all_raw_candidates.append(BoundedStrategicAppraisalService._create_candidate(entity, concern, profile, "concern"))
                
        # Obligations
        for obligation in strat.obligations:
            if not obligation.resolved_tick:
                all_raw_candidates.append(BoundedStrategicAppraisalService._create_candidate(entity, obligation, profile, "obligation"))
                
        # Suspended Projects
        for sp in strat.projects:
            if sp.status == StrategicStatus.SUSPENDED:
                all_raw_candidates.append(BoundedStrategicAppraisalService._create_candidate(entity, sp, profile, "suspended_project"))
                
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
                
        # Active Contracts
        for contract in strat.contracts:
            if contract.status == StrategicStatus.ACTIVE:
                all_raw_candidates.append(BoundedStrategicAppraisalService._create_candidate(entity, contract, profile, "contract"))

        # Active Projects (that are not current)
        for p in strat.projects:
            if p.status == StrategicStatus.ACTIVE:
                is_curr = (p.project_id == strat.current_project_id)
                if not is_curr:
                    all_raw_candidates.append(BoundedStrategicAppraisalService._create_candidate(entity, p, profile, "project"))

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
        cid = f"cand_{kind}_{getattr(source, 'project_id', getattr(source, 'concern_id', getattr(source, 'obligation_id', getattr(source, 'lead_id', getattr(source, 'blocker_id', getattr(source, 'contract_id', 'unknown'))))))}"
        sid = getattr(source, 'project_id', getattr(source, 'concern_id', getattr(source, 'obligation_id', getattr(source, 'lead_id', getattr(source, 'blocker_id', getattr(source, 'contract_id', 'unknown'))))))
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
                score = round(_clamp(0.30 * p + 0.20 * u + 0.15 * s + 0.25 * a + 0.10 * profile.resume_reliability, 0.0, 1.0), 3)
            else:
                score = round(_clamp(0.25 * p + 0.20 * u + 0.25 * a + 0.30 * profile.resume_reliability, 0.0, 1.0), 3)
        elif kind == "concern":
            p = _norm_weight(source.priority, 1.0, 2.0)
            u = _norm_weight(source.urgency, 1.0, 2.0)
            s = _norm_weight(getattr(source, 'salience', 0.5), 1.0, 2.0)
            u_score = u
            s_score = s
            score = round(_clamp(0.25 * p + 0.40 * u + 0.25 * s + 0.10 * (1.0 - profile.interruption_resistance), 0.0, 1.0), 3)
        elif kind == "obligation":
            p = _norm_weight(source.priority, 1.0, 2.0)
            u = _norm_weight(getattr(source, "urgency", 0.5), 1.0, 2.0)
            d = _norm_weight(getattr(source, "deadline_pressure", 0.0), 1.0, 2.0)
            u_score = u
            score = round(_clamp(0.30 * p + 0.35 * u + 0.25 * d + 0.10 * profile.judgment_stability, 0.0, 1.0), 3)
        elif kind == "lead":
            p = _norm_weight(source.priority, 1.0, 2.0)
            c = _clamp(getattr(source, "confidence", 0.5), 0.0, 1.0)
            f = _clamp(getattr(source, "freshness", 0.5), 0.0, 1.0)
            q = _clamp(getattr(source, "source_quality", 0.5), 0.0, 1.0)
            score = round(_clamp(0.20 * p + 0.25 * c + 0.20 * f + 0.20 * q + 0.15 * profile.evidence_quality, 0.0, 1.0), 3)
        elif kind == "blocker":
            sev = _norm_weight(source.severity, 1.0, 2.0)
            score = round(_clamp(0.40 * sev + 0.30 * curr_prj_score + 0.15 * profile.planning_budget / 9.0 + 0.15 * profile.blocker_resolution_patience, 0.0, 1.0), 3)
        elif kind == "contract":
            p = _norm_weight(source.priority, 1.0, 2.0)
            active = 1.0 if source.status == StrategicStatus.ACTIVE else 0.5
            score = round(_clamp(0.35 * p + 0.35 * active + 0.30 * (profile.social_bandwidth / 7.0), 0.0, 1.0), 3)
            
        return StrategicCandidate(
            candidate_id=cid,
            kind=kind,
            source_id=sid,
            score=score,
            continuity_score=0.0, # Not explicitly used for scoring but field required
            urgency_score=u_score,
            salience_score=s_score,
            capacity_fit_score=0.0, # Optional but field required
            source_kind=s_kind,
            is_current_project=is_current,
            is_current_objective=(sid == entity.mind.strategic.current_objective_id),
            is_interrupting=(not is_current and score > 0.5) # heuristic for is_interrupting flag
        )

    @staticmethod
    def _apply_pre_bounds(candidates: list[StrategicCandidate], profile: CognitionCapacityProfile, current_prj: ProjectRecord | None) -> tuple[list[StrategicCandidate], dict[str, int]]:
        """Apply per-category caps before final sorting."""
        pool = []
        drops = {'concerns': 0, 'leads': 0, 'suspended': 0, 'contracts': 0, 'blockers': 0, 'total': 0}
        
        # Split by kind
        by_kind = {}
        for c in candidates:
            by_kind.setdefault(c.kind, []).append(c)
            
        # 1. Unresolved concerns
        concerns = sorted(by_kind.get('concern', []), key=lambda x: x.score, reverse=True)
        pool.extend(concerns[:profile.concern_intake_limit])
        drops['concerns'] = len(concerns) - profile.concern_intake_limit if len(concerns) > profile.concern_intake_limit else 0
        
        # 2. Leads
        leads = sorted(by_kind.get('lead', []), key=lambda x: x.score, reverse=True)
        pool.extend(leads[:profile.lead_retention_limit])
        drops['leads'] = len(leads) - profile.lead_retention_limit if len(leads) > profile.lead_retention_limit else 0
        
        # 3. Suspended projects
        suspended = sorted(by_kind.get('suspended_project', []), key=lambda x: x.score, reverse=True)
        pool.extend(suspended[:profile.planning_budget])
        drops['suspended'] = len(suspended) - profile.planning_budget if len(suspended) > profile.planning_budget else 0
        
        # 4. Active contracts
        contracts = sorted(by_kind.get('contract', []), key=lambda x: x.score, reverse=True)
        pool.extend(contracts[:profile.social_bandwidth])
        drops['contracts'] = len(contracts) - profile.social_bandwidth if len(contracts) > profile.social_bandwidth else 0
        
        # 5. Blockers
        blockers = sorted(by_kind.get('blocker', []), key=lambda x: x.score, reverse=True)
        pool.extend(blockers[:profile.detour_depth_limit + 1])
        drops['blockers'] = len(blockers) - (profile.detour_depth_limit + 1) if len(blockers) > (profile.detour_depth_limit + 1) else 0
        
        # 6. current project (mandatory slot handled here by ensuring it's in the pool if it exists)
        curr = [c for c in by_kind.get('project', []) if c.is_current_project]
        pool.extend(curr)
        
        # 7. Obligations (not explicitly capped in pre-bounds specs)
        pool.extend(by_kind.get('obligation', []))
        
        # 8. Regular Projects (capped in final slice)
        pool.extend([c for c in by_kind.get('project', []) if not c.is_current_project])
        
        drops['total'] = drops['concerns'] + drops['leads'] + drops['suspended'] + drops['contracts'] + drops['blockers']
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
        
        if current_project_id:
            if best_rival_score > current_score + switch_margin:
                # SWITCH
                switched = True
                interrupting_id = best_rival.candidate_id
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
            # Milestone 2: mapped to potential concern shell, but for outcome return same project or create dummy
            # For this phase, return None to trigger shell logic later if needed
            return None
        if candidate.kind == 'obligation':
            return None
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
