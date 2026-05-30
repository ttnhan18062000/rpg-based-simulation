"""
src/domains/campaigns/classifier.py
───────────────────────────────────────────────────────────────────────────────
Phase 9 — Life-Arc Classifier for classifying entity traces.
"""

from typing import List, Tuple, Dict, Any
from src.domains.campaigns.schema import EntityArcReport, CampaignEvent, BehaviorChangeProof


class LifeArcClassifier:
    def classify(
        self,
        entity_id: int,
        events: List[CampaignEvent],
        behavior_change_proofs: Tuple[BehaviorChangeProof, ...]
    ) -> EntityArcReport:
        """Classifies the life trace events of an entity into arc families."""
        arc_types: List[str] = []
        major_events: List[Dict[str, Any]] = []
        evidence_event_ids: List[str] = []

        # Filter events for this entity
        entity_events = [e for e in events if e.entity_id == entity_id]
        
        # Track event types and categories
        event_types = {e.event_type for e in entity_events}
        categories = {e.category for e in entity_events}

        # Identify major events
        for e in entity_events:
            if e.event_type in ["combat_loss", "quest_completed", "recipe_learned", "item_crafted", "party_formed", "died", "rumor_heard"]:
                major_events.append({
                    "tick": e.tick,
                    "event_type": e.event_type,
                    "details": e.details
                })
                evidence_event_ids.append(e.event_id)

        # 1. Cautious Growth Arc
        # Evidenced by taking a combat loss or warning, avoiding wolf/danger, recovering, or selecting easy quests
        has_loss = "combat_loss" in event_types
        has_recovery = any(e.event_type == "quest_completed" and "inn" in str(e.details.get("quest_type", "")) for e in entity_events) or "recovered_at_inn" in event_types
        has_easy_quest = any(e.event_type == "quest_completed" and e.details.get("difficulty") == "easy" for e in entity_events)
        
        # Check behavior change proof for avoidance
        has_avoidance = any(p.change_kind == "avoidance" for p in behavior_change_proofs if p.entity_id == entity_id)
        if (has_loss or has_avoidance) and (has_recovery or has_easy_quest):
            arc_types.append("cautious_growth")

        # 2. Craft Growth Arc
        has_recipe = "recipe_learned" in event_types
        has_craft = "item_crafted" in event_types or "crafted_iron_sword" in event_types
        if has_recipe or has_craft:
            arc_types.append("craft_growth")

        # 3. Information Growth Arc
        has_rumor = "rumor_heard" in event_types or "asked_guide" in event_types
        has_exploration = "location_scouted" in event_types or "route_changed" in event_types
        if has_rumor or has_exploration:
            arc_types.append("information_growth")

        # 4. Party / Cooperation Growth
        has_party = "party_formed" in event_types or "requested_party" in event_types
        if has_party:
            arc_types.append("party_growth")

        # 5. Risky Growth / Combat Growth
        has_hard_quest = any(e.event_type == "quest_completed" and e.details.get("difficulty") == "hard" for e in entity_events)
        has_combat_win = "combat_win" in event_types
        if has_hard_quest and has_combat_win:
            arc_types.append("risky_growth")

        # 6. Failed Adventurer / Death Arc
        has_death = "died" in event_types
        if has_death:
            arc_types.append("failed_adventurer")
            arc_types.append("death_arc")

        # 7. Stagnant Arc
        # If very few events or no quest completions or progression changes
        if len(entity_events) < 5 or (not any(e.event_type in ["quest_completed", "item_crafted", "party_formed"] for e in entity_events)):
            arc_types.append("stagnant")

        if not arc_types:
            arc_types.append("cautious_growth")  # Default baseline

        return EntityArcReport(
            entity_id=entity_id,
            arc_types=tuple(arc_types),
            major_events=tuple(major_events),
            behavior_change_proofs=tuple(p for p in behavior_change_proofs if p.entity_id == entity_id),
            evidence_event_ids=tuple(evidence_event_ids)
        )
