from typing import TYPE_CHECKING, Any
import json
from src.core.models.enums import AIState
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
        sleep_pct = int(min(100, routine.sleep_debt * 100))
        hunger_pct = int(min(100, routine.hunger_level * 100))
        
        sleep_bar = f"[{'#' * (sleep_pct // 5)}{'-' * (20 - sleep_pct // 5)}]"
        hunger_bar = f"[{'#' * (hunger_pct // 5)}{'-' * (20 - hunger_pct // 5)}]"
        
        sleep_color = "\033[91m" if routine.sleep_debt > 0.8 else "\033[92m"
        hunger_color = "\033[93m" if routine.hunger_level > 0.7 else "\033[92m"
        
        print(f"Sleep Debt:   {sleep_color}{sleep_bar}\033[0m {routine.sleep_debt:.2f}")
        print(f"Hunger Level: {hunger_color}{hunger_bar}\033[0m {routine.hunger_level:.2f}")
        
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
            if val > 0.7: return f"\033[92m{high}\033[0m"
            if val < 0.3: return f"\033[91m{low}\033[0m"
            return "Average"

        # Show curated labels with thematic icons
        print(f"  ◈ Mind: {get_label(identity.openness, 'Creative', 'Traditional')}")
        print(f"  ◈ Will: {get_label(identity.conscientiousness, 'Disciplined', 'Easygoing')}")
        print(f"  ◈ Social: {get_label(identity.extraversion, 'Outgoing', 'Reserved')}")
        print(f"  ◈ Heart: {get_label(identity.agreeableness, 'Compassionate', 'Competitive')}")
        print(f"  ◈ Temper: {get_label(identity.neuroticism, 'Sensitive', 'Resilient')}")

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
        rep = entity.reputation
        EntityInspector.print_header("PUBLIC REPUTATION")
        
        # Tags with colorized chips
        tags_str = ", ".join([f"\033[95m[{t}]\033[0m" for t in rep.reputation_tags])
        EntityInspector.print_field("Titles/Tags", tags_str if tags_str else "None")
        
        # Multi-dimensional scores
        print(f"  ◈ Defender: {rep.defender_score:>5.1f} | Heroism: {rep.heroism_score:>5.1f}")
        print(f"  ◈ Trust:    {rep.trustworthiness:>5.1f} | Greed:   {rep.greed_score:>5.1f}")
        print(f"  ◈ Threat:   {rep.threat_notoriety:>5.1f} | Coward:  {rep.cowardice_score:>5.1f}")

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
    def render_strategic_domain(entity: "Entity"):
        """Display long-term intent, directives, and ongoing projects. [PHASE 1-2 UPDATED]"""
        strat = entity.mind.strategic
        EntityInspector.print_header("STRATEGIC DOMAIN (PLAN & COMMITMENT)")
        
        # 1. Active Objective (The Bridge)
        obj_id = strat.current_objective_id or "NONE"
        obj_color = "\033[92m" # Default Green
        interruption_tag = ""
        
        # Heuristic for interruption (Phase 2)
        if obj_id == "obj_satisfy_needs":
            obj_color = "\033[91m" # Red for interruption
            interruption_tag = " \033[1;91m[INTERRUPTION]\033[0m"
        
        print(f"  \033[1mCurrent Objective\033[0m: {obj_color}{obj_id}\033[0m{interruption_tag}")
        
        # 2. Projects
        if strat.projects:
            print(f"\n  \033[96m◈ Active Projects ({len(strat.projects)})\033[0m")
            current_id = strat.current_project_id
            for p in strat.projects:
                status_chip = "\033[92m[ACTIVE]\033[0m" if p.project_id == current_id else "[IDLE]"
                project_name = f"\033[1m{p.label}\033[0m"
                reason = p.metadata.get("reason", "")
                reason_str = f" \033[90m({reason})\033[0m" if reason else ""
                print(f"    {status_chip} {p.project_id:20} | {project_name}{reason_str}")
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
                urgency = "\033[91m(!)\033[0m" if c.priority > 4.0 else "   "
                print(f"    {urgency} {c.label:30} | Priority: {c.priority:.2f}")
        
        # 5. Obligations/Contracts (Summary)
        total_obs = len(strat.obligations) + len(strat.contracts)
        if total_obs > 0:
            print(f"\n  ◈ Obligations: {len(strat.obligations)} | Contracts: {len(strat.contracts)}")

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
        EntityInspector.render_strategic_domain(entity)
        EntityInspector.render_public_reputation(entity)
        EntityInspector.render_likely_choices(entity)
        EntityInspector.render_social_bonds(entity, registry)
        EntityInspector.render_turning_points(entity)
        EntityInspector.render_ongoing_arc(entity, getattr(registry, "_current_tick", 0))
        print("\n" + "="*80)
