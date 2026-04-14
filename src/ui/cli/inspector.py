from typing import TYPE_CHECKING, Any
import json
from src.core.models.enums import AIState, StrategicStatus
from src.core.models.vectors import Vector2

if TYPE_CHECKING:
    from src.core.entities.entity import Entity
    from src.core.models.social import SocialRegistry

class EntityInspector:
    """Terminal-based visualizer for Macro-Interest entity data."""

    @staticmethod
    def print_header(text: str):
        print(f"\n\033[95m=== {text} ===\033[0m")

    @staticmethod
    def print_field(label: str, value: Any, color: str = "\033[94m"):
        print(f"{color}{label:15}\033[0m: {value}")

    @staticmethod
    def render_biological_needs(entity: "Entity"):
        """Display sleep, hunger, and schedule data."""
        routine = entity.mind.routine
        EntityInspector.print_header("BIOLOGICAL NEEDS")
        
        # Simple text-based status bars
        try:
            # AOA Stabilization: Robust check for MagicMock [design-03]
            s_debt = float(routine.sleep_debt)
            h_level = float(routine.hunger_level)
            sleep_pct = int(min(100, s_debt * 100))
            hunger_pct = int(min(100, h_level * 100))
            
            sleep_bar = f"[{'#' * (sleep_pct // 5)}{'-' * (20 - sleep_pct // 5)}]"
            hunger_bar = f"[{'#' * (hunger_pct // 5)}{'-' * (20 - hunger_pct // 5)}]"
            
            sleep_color = "\033[91m" if s_debt > 0.8 else "\033[92m"
            hunger_color = "\033[93m" if h_level > 0.7 else "\033[92m"
            
            print(f"Sleep Debt:   {sleep_color}{sleep_bar}\033[0m {s_debt:.2f}")
            print(f"Hunger Level: {hunger_color}{hunger_bar}\033[0m {h_level:.2f}")
        except (TypeError, ValueError):
            pass
        
        state = "\033[96mSLEEPING\033[0m" if routine.is_sleeping else "\033[92mAWAKE\033[0m"
        EntityInspector.print_field("Current State", state)
        EntityInspector.print_field("Active Hours", f"{routine.active_start_hour:02d}:00 - {routine.active_end_hour:02d}:00")

    @staticmethod
    def render_personality(entity: "Entity"):
        """Display curated personality labels from OCEAN traits. [PHASE 0 FIX]"""
        identity = entity.identity
        EntityInspector.print_header("WHO IS THIS?")
        
        EntityInspector.print_field("Archetype", f"\033[93m{identity.archetype.name}\033[0m")
        EntityInspector.print_field("Faction", f"\033[96m{identity.faction}\033[0m")
        
        def get_label(val: float, high: str, low: str) -> str:
            try:
                # AOA Stabilization: Robust numeric check to avoid MagicMock comparison errors [design-03]
                f_val = float(val) 
                if f_val > 0.7: return f"\033[92m{high}\033[0m"
                if f_val < 0.3: return f"\033[91m{low}\033[0m"
            except (TypeError, ValueError):
                # Fallback for MagicMock or non-numeric types
                pass
            return "Average"

        # Show curated labels based on RPG traits [PHASE 1 UPDATED]
        pers = entity.mind.decision.personality
        print(f"  ◈ Combat: {get_label(pers.aggression, 'Aggressive', 'Passive')}")
        print(f"  ◈ Wealth: {get_label(pers.greed, 'Greedy', 'Generous')}")
        print(f"  ◈ Safety: {get_label(pers.caution, 'Cautious', 'Reckless')}")
        print(f"  ◈ Drive:  {get_label(pers.ambition, 'Ambitious', 'Content')}")
        print(f"  ◈ Sight:  {get_label(pers.curiosity, 'Curious', 'Incurious')}")

    @staticmethod
    def render_likely_choices(entity: "Entity"):
        """Display predictive goal scores explaining 'What do they want?'. [PHASE 0 FIX]"""
        motives = entity.mind.decision.goal_scores
        if not motives:
            return

        EntityInspector.print_header("LIKELY NEXT CHOICES")
        
        # Sort by utility weight
        sorted_motives = sorted(motives.items(), key=lambda x: x[1], reverse=True)
        top_3 = sorted_motives[:3]
        
        for i, (goal_type, weight) in enumerate(top_3):
            pct = int(min(100, weight * 50)) 
            bar = f"[{'#' * (pct // 5)}{'-' * (20 - pct // 5)}]"
            
            # Descriptive motive label based on goal type and archetype
            motive_label = "Satisfying Motive"
            if weight > 1.2: motive_label = "\033[91mDominant Drive\033[0m"
            elif weight > 0.8: motive_label = "\033[93mActive Pursuit\033[0m"
            
            print(f"{i+1}. {goal_type.name:<13} \033[96m{bar}\033[0m {weight:.2f} | {motive_label}")

    @staticmethod
    def render_social_bonds(entity: "Entity", registry: "SocialRegistry"):
        """Display relationships with other entities."""
        EntityInspector.print_header("SOCIAL BONDS")
        
        bonds = []
        for key, bond in registry.bonds.items():
            if bond.source_id == entity.id:
                bonds.append(bond)
        
        if not bonds:
            print("No established social bonds.")
            return

        # Sort by total emotional intensity
        bonds.sort(key=lambda b: (abs(b.trust) + abs(b.fear) + abs(b.rivalry)), reverse=True)
        
        print(f"{'Target ID':<10} | {'Trust':<6} | {'Loyalty':<7} | {'Resent':<6} | {'Dynamics'}")
        print("-" * 65)
        for b in bonds:
            dynamics = []
            if b.trust > 0.5: dynamics.append("Ally")
            if b.loyalty > 0.6: dynamics.append("Devoted")
            if b.resentment > 0.6: dynamics.append("Bitter")
            if b.fear > 0.5: dynamics.append("Intimidated")
            if b.rivalry > 0.5: dynamics.append("Rival")
            if not dynamics: dynamics.append("Neutral")
            
            trust_color = "\033[92m" if b.trust > 0 else "\033[91m"
            loyalty_color = "\033[96m" if b.loyalty > 0.4 else "\033[0m"
            resent_color = "\033[91m" if b.resentment > 0.4 else "\033[0m"
            
            print(f"{b.target_id:<10} | "
                  f"{trust_color}{b.trust:>6.2f}\033[0m | "
                  f"{loyalty_color}{b.loyalty:>7.2f}\033[0m | "
                  f"{resent_color}{b.resentment:>6.2f}\033[0m | "
                  f"{', '.join(dynamics)}")

    @staticmethod
    def render_ongoing_arc(entity: "Entity", current_tick: int):
        """Display high-salience chronological events (Storytelling lens). [PHASE 0 FIX]"""
        EntityInspector.print_header("ONGOING ARC (RECENT STORY)")
        
        logs = entity.mind.narrative.memory_log
        if not logs:
            print("The character's story is just beginning.")
            return

        from src.core.logic.memory_salience import MemorySalienceService
        
        # Filter for high salience memories (Option A)
        salient_events = [
            e for e in logs 
            if MemorySalienceService.calculate_weighted_impact(e, current_tick) > 0.4
        ]
        
        # Thematic summary (Option B)
        themes = {}
        for e in logs[-20:]: # Last 20 for theme trend
            themes[e.type] = themes.get(e.type, 0) + 1
        
        if themes:
            top_theme = max(themes.items(), key=lambda x: x[1])[0]
            theme_label = f"\033[95m{top_theme.upper()} FOCUS\033[0m"
            print(f"Current trajectory: {theme_label}")
            print("-" * 60)

        if not salient_events:
            print("No major turning points recently.")
            return

        # Show last 5 SALIENT events in chronological order
        print(f"{'Tick':<6} | {'Narrative Tag':<15} | {'Impact':<6} | {'Event'}")
        print("-" * 60)
        for log in salient_events[-5:]:
            impact_color = "\033[91m" if log.impact < -0.5 else "\033[92m" if log.impact > 0.5 else "\033[0m"
            
            # Narrative tag logic
            tag = log.type.upper()
            if log.impact > 1.0: tag = "MAJOR VICTORY"
            elif log.impact < -1.0: tag = "TRAUMATIC LOSS"
            
            # Simple message extraction
            message = log.details.get("desc", log.type) if isinstance(log.details, dict) else log.type
            print(f"{log.tick:<6} | {tag:<15} | {impact_color}{log.impact:>6.2f}\033[0m | {message}")

    @staticmethod
    def render_public_reputation(entity: "Entity"):
        """Display the public-facing reputation profile. [PHASE 2]"""
        rep = entity.identity.reputation
        EntityInspector.print_header("PUBLIC REPUTATION")
        
        # Tags with colorized chips
        tags_str = ", ".join([f"\033[95m[{t}]\033[0m" for t in rep.reputation_tags])
        EntityInspector.print_field("Titles/Tags", tags_str if tags_str else "None")
        
        # Multi-dimensional scores
        # AOA Stabilization: Robust check for MagicMock [design-03]
        try:
            d_score = float(rep.defender_score)
            h_score = float(rep.heroism_score)
            t_score = float(rep.trustworthiness)
            g_score = float(rep.greed_score)
            th_score = float(rep.threat_notoriety)
            c_score = float(rep.cowardice_score)
            print(f"  ◈ Defender: {d_score:>5.1f} | Heroism: {h_score:>5.1f}")
            print(f"  ◈ Trust:    {t_score:>5.1f} | Greed:   {g_score:>5.1f}")
            print(f"  ◈ Threat:   {th_score:>5.1f} | Coward:  {c_score:>5.1f}")
        except (TypeError, ValueError):
            pass

    @staticmethod
    def render_turning_points(entity: "Entity"):
        """Display high-salience durable memories (The Soul). [PHASE 2]"""
        EntityInspector.print_header("DURABLE TURNING POINTS")
        
        tps = entity.mind.narrative.turning_points
        if not tps:
            print("No life-defining events recorded yet.")
            return
            
        # Top 5 by salience
        sorted_tps = sorted(tps, key=lambda x: x.salience_score, reverse=True)[:5]
        
        print(f"{'Tick':<6} | {'Kind':<15} | {'Salience':<8} | {'Impact'}")
        print("-" * 60)
        for tp in sorted_tps:
            kind_name = tp.kind.name if hasattr(tp.kind, "name") else str(tp.kind)
            print(f"{tp.tick:<6} | {kind_name:<15} | {tp.salience_score:>8.2f} | {tp.emotional_impact:>6.2f}")

    @staticmethod
    def render_uncertainty_layer(entity: "Entity"):
        """Display leads, zones, and hypotheses (The Fog of War). [phase_3_task_1]"""
        strat = entity.mind.strategic
        if not (strat.leads or strat.candidate_zones or strat.hypotheses):
            return

        EntityInspector.print_header("STRATEGIC UNCERTAINTY")
        
        # 1. Hypotheses
        if strat.hypotheses:
            print(f"  \033[95m◈ Hypotheses ({len(strat.hypotheses)})\033[0m")
            for h in strat.hypotheses:
                status = "ACTIVE" if h.is_active else "RESOLVED"
                print(f"    - {h.label:25} | Conf: {h.confidence:.2f} | {status}")

        # 2. Candidate Zones
        if strat.candidate_zones:
            print(f"\n  \033[96m◈ Candidate Zones ({len(strat.candidate_zones)})\033[0m")
            for z in strat.candidate_zones:
                search_prefix = "\033[93m[SEARCHED]\033[0m" if z.last_search_tick > 0 else "          "
                outcome = f" | {z.search_outcome}" if z.search_outcome else ""
                print(f"    {search_prefix} {z.zone_id:20} | Conf: {z.confidence:.2f}{outcome}")

        # 3. Leads (Top 5)
        if strat.leads:
            print(f"\n  \033[92m◈ Leads (Top 5/{len(strat.leads)})\033[0m")
            sorted_leads = sorted(strat.leads, key=lambda l: l.certainty, reverse=True)[:5]
            for l in sorted_leads:
                exhaustion = " \033[91m(EXHAUSTED)\033[0m" if l.is_exhausted else ""
                print(f"    - {l.label:25} | cert: {l.certainty:.2f} | subject: {l.subject}{exhaustion}")

    @staticmethod
    def render_social_contracts(entity: "Entity"):
        """Display active contracts and pending offers. [PHASE 4]"""
        strat = entity.mind.strategic
        if not (strat.contracts or strat.offers or strat.obligations):
            return

        EntityInspector.print_header("SOCIAL CONTRACTS & OBLIGATIONS")
        
        # 1. Active Contracts
        if strat.contracts:
            print(f"  \033[92m◈ Active Contracts ({len(strat.contracts)})\033[0m")
            for c in strat.contracts:
                member_count = len(c.member_ids) + 1
                role = c.member_roles.get(entity.id, "Member")
                print(f"    - {c.purpose:25} | {c.kind.name} | {member_count} members | Role: {role}")

        # 2. Pending Offers
        if strat.offers:
            print(f"\n  \033[93m◈ Pending Offers ({len(strat.offers)})\033[0m")
            for o in strat.offers:
                dir_icon = "⬅️" if o.candidate_id == entity.id else "➡️"
                other_party = o.recruiter_id if o.candidate_id == entity.id else o.candidate_id
                print(f"    {dir_icon} {o.contract_kind.name:15} | From/To: {other_party:<5} | {o.status.name}")

        # 3. Obligations
        if strat.obligations:
            print(f"\n  \033[94m◈ Unilateral Obligations ({len(strat.obligations)})\033[0m")
            for o in strat.obligations:
                deadline = f" | Due: T{o.deadline_tick}" if o.deadline_tick else ""
                print(f"    - {o.label:25} | To: {o.target_id:<5} | Pri: {o.priority:.1f}{deadline}")

    @staticmethod
    def render_strategic_domain(entity: "Entity", current_tick: int = 0):
        """Display long-term intent, directives, and ongoing projects. [PHASE 1-2 UPDATED]"""
        strat = entity.mind.strategic
        EntityInspector.print_header("STRATEGIC DOMAIN (PLAN & COMMITMENT)")
        
        # 1. Active Objective (The Bridge)
        obj_id = strat.current_objective_id or "NONE"
        obj_color = "\033[92m" # Default Green
        interruption_tag = ""
        
        # Heuristic for interruption (Phase 2)
        if strat.interrupted_project_id:
            obj_color = "\033[91m" # Red for interruption
            interruption_tag = f" \033[1;91m[REPLACING {strat.interrupted_project_id}]\033[0m"
        
        print(f"  \033[1mCurrent Objective\033[0m: {obj_color}{obj_id}\033[0m{interruption_tag}")
        
        # 2. Commitment & Continuity [PHASE 2]
        current_prj = strat.current_project
        if current_prj:
            # We use 'committed_at' to show duration
            duration = int(current_tick) - int(current_prj.committed_at)
            try:
                # AOA Stabilization: Robust numeric check for MagicMock [design-03]
                lock_val = int(strat.project_lock_until)
                lock_rem = max(0, lock_val - int(current_tick))
                lock_str = f" \033[93m(LOCKED {lock_rem}t)\033[0m" if lock_rem > 0 else ""
                
                engaged = int(strat.engaged_ticks)
                engaged_str = f" | \033[96mEngaged: {engaged}t\033[0m" if engaged > 0 else ""
            except (TypeError, ValueError, AttributeError):
                lock_str = ""
                engaged_str = ""
            print(f"  \033[1mCommitted\033[0m: {duration} ticks ago{lock_str}{engaged_str}")
            try:
                # AOA Stabilization: Robust numeric check for MagicMock [design-03]
                thresh = float(current_prj.interruption_threshold)
                cost = float(current_prj.abandonment_cost)
                print(f"  \033[1mThreshold\033[0m: {thresh:.2f} | Cost: {cost:.2f}")
            except (TypeError, ValueError):
                pass

        # 3. Drivers [PHASE 2]
        if strat.recent_drivers:
            print(f"\n  \033[94m◈ Strategic Reasoning\033[0m")
            for d in strat.recent_drivers:
                print(f"    - {d.label:25} | {d.description}")

        # 4. Projects
        if strat.projects:
            print(f"\n  \033[96m◈ Active Projects ({len(strat.projects)})\033[0m")
            current_id = strat.current_project_id
            for p in strat.projects:
                status_color = "\033[92m" if p.status == StrategicStatus.ACTIVE else "\033[93m" if p.status == StrategicStatus.SUSPENDED else "\033[90m"
                status_chip = f"{status_color}[{p.status.name}]\033[0m"
                if p.project_id == current_id:
                     status_chip = f"\033[1;92m[CURRENT]\033[0m"
                
                project_name = f"\033[1m{p.label}\033[0m"
                reason = p.metadata.get("reason", "")
                reason_str = f" \033[90m({reason})\033[0m" if reason else ""
                
                suspension_str = ""
                if p.status == StrategicStatus.SUSPENDED:
                    suspension_str = f" \033[93m| Reason: {p.suspension_reason}\033[0m"
                
                print(f"    {status_chip} {p.project_id:20} | {project_name}{reason_str}{suspension_str}")
                if p.project_id == current_id:
                    # Find the active objective label
                    obj_label = "No labeled objective"
                    for obj in p.objectives:
                        if obj.objective_id == strat.current_objective_id:
                            obj_label = obj.label
                            break
                    print(f"      \033[90m↳ Objective: {strat.current_objective_id} ({obj_label})\033[0m")
        else:
            print("\n  - No active projects.")
            
        # 3. Directives
        if strat.directives:
            print(f"\n  \033[93m◈ Directives ({len(strat.directives)})\033[0m")
            for d in strat.directives:
                kind_str = f"[{d.kind.name}]"
                print(f"    - {kind_str:15} | {d.label}")
        else:
            print("\n  - No active directives.")
            
        # 4. Concerns/Blockers
        if strat.concerns:
            print(f"\n  \033[91m◈ Active Concerns ({len(strat.concerns)})\033[0m")
            for c in strat.concerns:
                urgency_mark = "\033[91m(!)\033[0m" if c.priority > 4.0 or c.urgency > 0.8 else "   "
                vis_icon = "👁" if c.visibility == "public" else "🔒" if c.visibility == "private" else "👥"
                print(f"    {urgency_mark} {c.label:30} | Pri: {c.priority:.1f} | Urg: {c.urgency:.1f} | {vis_icon} {c.visibility}")
                if c.source_event_id:
                    print(f"       \033[90m↳ Cause: {c.cause_type} ({c.source_event_id})\033[0m")

        # 5. Uncertainty & Social [PHASE 4]
        EntityInspector.render_uncertainty_layer(entity)
        EntityInspector.render_social_contracts(entity)
        EntityInspector.render_cognition_capacity(entity)

    @staticmethod
    def render_cognition_capacity(entity: "Entity"):
        """Display cognitive budgets and overload status. [phase_2_intel_capacity]"""
        strat = entity.mind.strategic
        profile = strat.last_capacity_profile
        if not profile:
            return

        EntityInspector.print_header("COGNITION & CAPACITY")
        
        # 1. Capacity Profile Summary
        print(f"  \033[95m◈ Cognitive Profile\033[0m")
        print(f"    Planning:  {profile.planning_budget:>3} | Stability: {profile.judgment_stability:.2f}")
        print(f"    Evidence:  {profile.evidence_quality:.2f} | Social BW: {profile.social_bandwidth:>3}")
        print(f"    Detour:     {profile.detour_depth_limit:>2} | Leads:    {profile.lead_retention_limit:>3}")

        # 2. Budget Usage Bars
        print(f"\n  \033[96m◈ Active Budgets\033[0m")
        
        def print_budget_bar(label: str, used: int, limit: int, color: str = "\033[96m"):
            pct = int(min(100, (used / max(1, limit)) * 100))
            bar_len = 20
            filled = int((pct / 100) * bar_len)
            
            bar_color = color
            if pct > 90: bar_color = "\033[91m" # Red
            elif pct > 70: bar_color = "\033[93m" # Yellow
            
            bar = f"[{'#' * filled}{'-' * (bar_len - filled)}]"
            print(f"    {label:12} {bar_color}{bar}\033[0m {used}/{limit}")

        print_budget_bar("Candidates", strat.active_slice_used, profile.active_slice_limit)
        print_budget_bar("Concerns", strat.active_concerns_used, profile.concern_intake_limit, "\033[91m")
        print_budget_bar("Leads", strat.retained_leads_used, profile.lead_retention_limit, "\033[92m")
        print_budget_bar("Zones", strat.candidate_zones_used, profile.candidate_zone_limit, "\033[94m")
        print_budget_bar("Allies", strat.ally_evaluations_used, profile.ally_evaluation_limit, "\033[95m")

        # 3. Overload Status
        if strat.is_overloaded:
            print(f"\n  \033[1;91m[!] COGNITIVE OVERLOAD ALERT\033[0m")
            print(f"    Score: {strat.overload_score:.2f} | Dropped: {strat.dropped_candidates_count} candidates")
            print(f"    Latent Concerns: {strat.latent_concerns_count} (ignored this tick)")
        else:
            print(f"\n  \033[90mStrategic pressure: {strat.overload_score:.2f} (Stable)\033[0m")

    @staticmethod
    def inspect_full(entity: "Entity", registry: "SocialRegistry"):
        """Run all inspection modules."""
        print("\033[1m" + "="*80)
        print(f"ENTITY INSPECTION: {entity.identity.display_name} (ID: {entity.id})")
        print("="*80 + "\033[0m")
        
        EntityInspector.print_header("GENERAL INFO")
        EntityInspector.print_field("Level", f"{entity.progression.level} {entity.identity.tier}")
        EntityInspector.print_field("Position", f"X:{entity.spatial.pos.x:.1f}, Y:{entity.spatial.pos.y:.1f}")
        EntityInspector.print_field("HP", f"{entity.combat.hp}/{entity.combat.max_hp}")
        EntityInspector.print_field("AI State", f"{entity.mind.decision.ai_state.name} \033[90m({entity.mind.strategic.current_objective_id or 'No Objective'})\033[0m")
        
        EntityInspector.render_biological_needs(entity)
        EntityInspector.render_personality(entity)
        EntityInspector.render_strategic_domain(entity, getattr(registry, "_current_tick", 0))
        EntityInspector.render_public_reputation(entity)
        EntityInspector.render_likely_choices(entity)
        EntityInspector.render_social_bonds(entity, registry)
        EntityInspector.render_turning_points(entity)
        EntityInspector.render_ongoing_arc(entity, getattr(registry, "_current_tick", 0))
        print("\n" + "="*80)
