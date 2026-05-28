"""
src/domains/campaigns/forbidden.py
───────────────────────────────────────────────────────────────────────────────
Phase 9 — Forbidden Behavior Detector.
"""

from typing import Tuple, List, Dict
from src.domains.campaigns.schema import CampaignEvent, ForbiddenBehaviorReport


class ForbiddenBehaviorDetector:
    def detect(self, events: List[CampaignEvent]) -> Tuple[ForbiddenBehaviorReport, ...]:
        """Scans the campaign trace events and identifies illegal transitions/behaviors."""
        reports: List[ForbiddenBehaviorReport] = []

        # Group events by entity
        entity_events_map = {}
        for event in events:
            if event.entity_id is not None:
                entity_events_map.setdefault(event.entity_id, []).append(event)

        for entity_id, entity_events in entity_events_map.items():
            # Sort events by tick
            sorted_events = sorted(entity_events, key=lambda e: (e.tick, e.event_id))

            dead = False
            death_tick = -1
            death_event_id = ""

            failed_actions: Dict[str, List[int]] = {}  # action_type -> list of ticks

            for i, event in enumerate(sorted_events):
                # 1. Action after death
                if dead:
                    reports.append(ForbiddenBehaviorReport(
                        rule_violated="action_after_death",
                        entity_id=entity_id,
                        tick=event.tick,
                        evidence_event_ids=(death_event_id, event.event_id),
                        explanation=f"Entity {entity_id} performed action '{event.event_type}' after dying at tick {death_tick}."
                    ))
                
                if event.event_type == "died":
                    dead = True
                    death_tick = event.tick
                    death_event_id = event.event_id

                # 2. Hidden knowledge / omniscience usage
                if event.event_type == "use_hidden_knowledge" or (event.event_type == "scout_location" and event.details.get("omniscient") is True):
                    reports.append(ForbiddenBehaviorReport(
                        rule_violated="omniscient_hidden_knowledge",
                        entity_id=entity_id,
                        tick=event.tick,
                        evidence_event_ids=(event.event_id,),
                        explanation=f"Entity {entity_id} accessed unknown resources or regions without prior sensory/information exposure."
                    ))

                # 3. Repeated failed action loop
                if event.event_type == "failed_action":
                    action_key = event.details.get("action_name", "generic_action")
                    failed_actions.setdefault(action_key, []).append(event.tick)
                    # If failed same action 4+ consecutive times within a short duration
                    ticks = failed_actions[action_key]
                    if len(ticks) >= 4 and (ticks[-1] - ticks[-4] < 20):
                        reports.append(ForbiddenBehaviorReport(
                            rule_violated="repeated_same_failed_action_forever",
                            entity_id=entity_id,
                            tick=event.tick,
                            evidence_event_ids=tuple(
                                [e.event_id for e in sorted_events if e.event_type == "failed_action" and e.details.get("action_name") == action_key][-4:]
                            ),
                            explanation=f"Entity {entity_id} trapped in infinite failure loop for action '{action_key}'."
                        ))

                # 4. Ignored critical survival need
                if event.event_type == "ignored_critical_need":
                    reports.append(ForbiddenBehaviorReport(
                        rule_violated="ignored_critical_need",
                        entity_id=entity_id,
                        tick=event.tick,
                        evidence_event_ids=(event.event_id,),
                        explanation=f"Entity {entity_id} ignored warning indicators or critical survival needs until death/stagnation."
                    ))

                # 5. Missing trace for major decision
                if event.event_type == "major_decision_without_trace":
                    reports.append(ForbiddenBehaviorReport(
                        rule_violated="no_trace_for_major_decision",
                        entity_id=entity_id,
                        tick=event.tick,
                        evidence_event_ids=(event.event_id,),
                        explanation=f"Entity {entity_id} executed a major decision with empty decision trace."
                    ))

        return tuple(reports)
