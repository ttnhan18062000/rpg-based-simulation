"""
src/domains/campaigns/behavior_change.py
───────────────────────────────────────────────────────────────────────────────
Phase 9 — Behavior-Change Proof Detector.
"""

from typing import List, Tuple
from src.domains.campaigns.schema import CampaignEvent, BehaviorChangeProof


class BehaviorChangeProofDetector:
    def detect(self, events: List[CampaignEvent]) -> Tuple[BehaviorChangeProof, ...]:
        """Analyzes campaign events and returns behavior change proofs with temporal order checks."""
        proofs: List[BehaviorChangeProof] = []

        # Group events by entity
        entity_events_map = {}
        for event in events:
            if event.entity_id is not None:
                entity_events_map.setdefault(event.entity_id, []).append(event)

        for entity_id, entity_events in entity_events_map.items():
            # Sort events temporally by tick and event_id order
            sorted_events = sorted(entity_events, key=lambda e: (e.tick, e.event_id))

            for i, cause in enumerate(sorted_events):
                # 1. Combat Loss -> Later Avoidance or Seeking Help (party)
                if cause.event_type == "combat_loss":
                    # Look for subsequent avoidance or party forming
                    for later in sorted_events[i + 1:]:
                        if later.event_type == "avoided_danger" or (later.event_type == "route_changed" and "avoid" in str(later.details.get("reason", ""))):
                            proofs.append(BehaviorChangeProof(
                                entity_id=entity_id,
                                cause_event_id=cause.event_id,
                                later_event_id=later.event_id,
                                change_kind="avoidance",
                                explanation="Entity avoided the danger region or route after experiencing a combat loss.",
                                confidence=0.9
                            ))
                            break
                        if later.event_type == "party_formed" or later.event_type == "requested_party":
                            proofs.append(BehaviorChangeProof(
                                entity_id=entity_id,
                                cause_event_id=cause.event_id,
                                later_event_id=later.event_id,
                                change_kind="social_cooperation",
                                explanation="Entity formed or joined a party after experiencing a combat loss.",
                                confidence=0.85
                            ))
                            break

                # 2. Info Learned -> Later Route Change
                elif cause.event_type in ["rumor_heard", "recipe_learned", "information_learned", "asked_guide"]:
                    # Look for route changes or crafting actions corresponding to the info
                    for later in sorted_events[i + 1:]:
                        if later.event_type == "route_changed" or later.event_type == "item_crafted" or (later.event_type == "quest_completed" and "easy" in str(later.details.get("difficulty", ""))):
                            proofs.append(BehaviorChangeProof(
                                entity_id=entity_id,
                                cause_event_id=cause.event_id,
                                later_event_id=later.event_id,
                                change_kind="route_adaptation",
                                explanation="Entity changed active route or crafted upgrade after acquiring critical knowledge.",
                                confidence=0.8
                            ))
                            break

                # 3. Upgrade -> Later Harder Objective
                elif cause.event_type in ["item_crafted", "level_up", "crafted_iron_sword"]:
                    for later in sorted_events[i + 1:]:
                        if later.event_type == "quest_completed" and later.details.get("difficulty") == "hard":
                            proofs.append(BehaviorChangeProof(
                                entity_id=entity_id,
                                cause_event_id=cause.event_id,
                                later_event_id=later.event_id,
                                change_kind="combat_progression",
                                explanation="Entity took on or completed a hard quest after obtaining an equipment or level upgrade.",
                                confidence=0.95
                            ))
                            break

                # 4. Betrayal -> Later Partner Rejection
                elif cause.event_type == "betrayed_by_partner":
                    betrayed_partner = cause.details.get("partner_id")
                    for later in sorted_events[i + 1:]:
                        if later.event_type == "partner_rejected" and later.details.get("partner_id") == betrayed_partner:
                            proofs.append(BehaviorChangeProof(
                                entity_id=entity_id,
                                cause_event_id=cause.event_id,
                                later_event_id=later.event_id,
                                change_kind="cooperation_rejection",
                                explanation=f"Entity rejected working with partner {betrayed_partner} after prior betrayal.",
                                confidence=0.98
                            ))
                            break

                # 5. World Warning / Depletion -> Later Route Avoidance
                elif cause.event_type == "resource_depleted":
                    depleted_resource = cause.details.get("resource")
                    for later in sorted_events[i + 1:]:
                        if later.event_type == "route_changed" and depleted_resource in str(later.details.get("reason", "")):
                            proofs.append(BehaviorChangeProof(
                                entity_id=entity_id,
                                cause_event_id=cause.event_id,
                                later_event_id=later.event_id,
                                change_kind="scarcity_avoidance",
                                explanation="Entity changed route to seek alternative resources after original resource depletion.",
                                confidence=0.88
                            ))
                            break

        return tuple(proofs)
