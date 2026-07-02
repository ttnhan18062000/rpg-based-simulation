from __future__ import annotations
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from src.observability.events import SimulationEvent

class EntityInspectionSnapshot(BaseModel):
    entity_id: int
    exists: bool
    alive: bool = False
    position: Optional[tuple[float, float]] = None
    faction_id: Optional[int] = None
    region_id: Optional[str] = None
    current_goal: Optional[str] = None
    current_target: Optional[str] = None
    current_action: Optional[str] = None
    combat_summary: Dict[str, Any] = Field(default_factory=dict)
    inventory_summary: Dict[str, Any] = Field(default_factory=dict)
    quest_summary: List[Dict[str, Any]] = Field(default_factory=list)
    strategic_summary: Dict[str, Any] = Field(default_factory=dict)
    recent_timeline_events: List[Dict[str, Any]] = Field(default_factory=list)
    latest_rejection_reason: Optional[str] = None
    latest_anomaly_flags: List[str] = Field(default_factory=list)
    role: Optional[int] = None
    class_id: Optional[str] = None
    personality: Dict[str, Any] = Field(default_factory=dict)
    # Top-3 goal scores from the last adventure routing decision (winner + runner-ups).
    # Each entry: {"goal_id": str, "score": float, "rank": int}.
    # Empty when no decision trace writer is active or no tick has run yet.
    goal_scores: List[Dict[str, Any]] = Field(default_factory=list)
    # Narrative modifier summary extracted from runtime strategic state (E43H).
    # {"grief_concerns": [{"concern_id", "dead_ally_id", "urgency"},...],
    #  "nemesis_blockers": [{"blocker_id", "antagonist_id", "severity"},...]}.
    # Populated from entity.strategic.concerns/blockers by NarrativeModifierExtractor.
    narrative_modifiers: Dict[str, Any] = Field(default_factory=dict)

class EntityInspector:
    """Thread-safe inspector of single entities for real-time observability."""
    
    @staticmethod
    def inspect_entity(manager: Optional[Any], entity_id: int, timeline_limit: int = 20) -> EntityInspectionSnapshot:
        """Resolves a compact inspection snapshot for the given entity ID."""
        if manager is None:
            return EntityInspectionSnapshot(entity_id=entity_id, exists=False)
            
        latest_state = None
        if hasattr(manager, "latest_state"):
            latest_state = manager.latest_state
            
        if not latest_state:
            return EntityInspectionSnapshot(entity_id=entity_id, exists=False)
            
        entity = latest_state.entities.get(entity_id)
        if not entity:
            return EntityInspectionSnapshot(entity_id=entity_id, exists=False)
            
        # 1. Combat Summary
        combat_sum = {
            "hp": entity.combat.hp,
            "max_hp": entity.combat.max_hp,
            "tactical_role": entity.combat.tactical_role,
        }
        
        # 2. Inventory Summary
        inventory_sum = {
            "gold": entity.inventory.gold,
            "item_count": len(entity.inventory.items),
            "max_slots": entity.inventory.max_slots,
        }
        
        # 3. Quest Summary
        from src.core.quests import QuestState
        quests = []
        for q in entity.strategic.projects.values():
            if isinstance(q, QuestState):
                quests.append({
                    "id": q.id,
                    "name": q.name,
                    "status": q.quest_status.name if hasattr(q.quest_status, 'name') else str(q.quest_status),
                    "progress": q.progress_ratio
                })
                
        # 4. Strategic Summary
        strategic_sum = {
            "current_project_id": entity.strategic.current_project_id,
            "blockers_count": len(entity.strategic.blockers),
            "contracts_count": len(entity.strategic.contracts),
            "leads_count": len(entity.strategic.leads),
            "boredom": entity.strategic.boredom.copy() if hasattr(entity.strategic.boredom, "copy") else entity.strategic.boredom
        }
        
        # 5. Timeline Events
        events = []
        kernel = manager.kernel
        if kernel and getattr(kernel, "entity_timeline_store", None):
            timeline = kernel.entity_timeline_store.get_entity_timeline(entity_id)
            sorted_events = sorted(timeline, key=lambda e: e.tick, reverse=True)
            for ev in sorted_events[:timeline_limit]:
                events.append({
                    "type": ev.event_type,
                    "severity": ev.severity.name if hasattr(ev.severity, "name") else str(ev.severity),
                    "message": ev.message,
                    "tick": ev.tick
                })
                
        # 6. Rejection / Failure Reason
        rejection_reason = None
        for r in reversed(entity.identity.latest_intent_results):
            if not r.accepted:
                rejection_reason = str(r.reason)
                break
        if not rejection_reason:
            rejection_reason = entity.navigation.last_failure_reason
            
        # 7. Anomaly Flags
        anomaly_flags = []
        if entity.navigation.oscillation_count > 3:
            anomaly_flags.append("HIGH_OSCILLATION")
        if entity.navigation.wait_count > 5:
            anomaly_flags.append("HIGH_WAIT_COUNT")
        if any(v > 50 for v in entity.strategic.boredom.values()):
            anomaly_flags.append("HIGH_BOREDOM")
            
        # Current Goal, target, action
        current_goal = entity.strategic.current_objective_id
        current_target = str(entity.navigation.target) if entity.navigation.target else None
        current_action = entity.task.work_kind

        # 8. Identity extension: role, class_id, personality
        identity_role = entity.identity.role
        identity_class_id = entity.identity.class_id
        personality_dict = entity.identity.personality.to_canonical_dict()

        # 9. Goal scores — top-3 from the last adventure routing tick (winner + runner-ups).
        # Pulled from the run-scoped DecisionTraceWriter cache; empty if no writer is active.
        goal_scores: List[Dict[str, Any]] = []
        try:
            from src.observability.cognition.decision_trace_writer import get_active_writer
            _writer = get_active_writer()
            if _writer is not None:
                goal_scores = _writer.get_latest_goal_scores(entity_id)
        except Exception:
            pass

        # 10. Narrative modifiers (E43H) — grief urgency concerns and nemesis blockers.
        # Extracted from runtime strategic state (injected by GriefUrgencyImporter /
        # NemesisRelationImporter at episode start).
        narrative_modifiers: Dict[str, Any] = EntityInspector._extract_narrative_modifiers(entity)

        return EntityInspectionSnapshot(
            entity_id=entity_id,
            exists=True,
            alive=entity.combat.alive,
            position=entity.navigation.position,
            faction_id=entity.identity.faction,
            region_id=entity.navigation.region_id,
            current_goal=current_goal,
            current_target=current_target,
            current_action=current_action,
            combat_summary=combat_sum,
            inventory_summary=inventory_sum,
            quest_summary=quests,
            strategic_summary=strategic_sum,
            recent_timeline_events=events,
            latest_rejection_reason=rejection_reason,
            latest_anomaly_flags=anomaly_flags,
            role=identity_role,
            class_id=identity_class_id,
            personality=personality_dict,
            goal_scores=goal_scores,
            narrative_modifiers=narrative_modifiers,
        )

    @staticmethod
    def _extract_narrative_modifiers(entity: Any) -> Dict[str, Any]:
        """Extract grief urgency concerns and nemesis blockers from runtime strategic state."""
        grief_concerns: List[Dict[str, Any]] = []
        nemesis_blockers: List[Dict[str, Any]] = []
        try:
            from src.core.strategic import ConcernKind, BlockerKind
            strat = getattr(entity, "strategic", None)
            if strat is None:
                return {"grief_concerns": [], "nemesis_blockers": []}
            for concern_id, concern in strat.concerns.items():
                if (
                    concern_id.startswith("grief_ally_")
                    and getattr(concern, "kind", None) == ConcernKind.SOCIAL_THREAT
                ):
                    try:
                        dead_ally_id = int(concern_id.removeprefix("grief_ally_"))
                    except ValueError:
                        dead_ally_id = -1
                    grief_concerns.append({
                        "concern_id": concern_id,
                        "dead_ally_id": dead_ally_id,
                        "urgency": round(getattr(concern, "urgency", 0.0), 4),
                    })
            for blocker_id, blocker in strat.blockers.items():
                if (
                    getattr(blocker, "kind", None) == BlockerKind.SOCIAL
                    and getattr(blocker, "subject", "").isdigit()
                ):
                    nemesis_blockers.append({
                        "blocker_id": blocker_id,
                        "antagonist_id": int(blocker.subject),
                        "severity": round(getattr(blocker, "severity", 0.0), 4),
                    })
        except Exception:
            pass
        return {"grief_concerns": grief_concerns, "nemesis_blockers": nemesis_blockers}
