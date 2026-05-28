from dataclasses import dataclass
from typing import List, Dict, Optional, Any

@dataclass(frozen=True, slots=True)
class TraceEvent:
    event_id: str
    category: str
    severity: str
    message: str
    entity_id: Optional[int] = None

class TraceVolumeGovernor:
    """Manages and limits debug/observability log & trace volume."""
    def __init__(self, max_events_per_tick: int = 1000, repeated_summary_threshold: int = 5) -> None:
        self.max_events_per_tick = max_events_per_tick
        self.repeated_summary_threshold = repeated_summary_threshold
        self.dropped_count = 0
        self.summarized_count = 0

    def process_events(self, events: List[TraceEvent]) -> List[TraceEvent]:
        # Filter: keep hard_law and high severity events always, process others
        hard_laws = [e for e in events if e.category == "hard_law" or e.severity == "ERROR"]
        evidence = [e for e in events if e.category in ("campaign_semantic", "scenario_evidence") or e.severity == "WARNING"]
        others = [e for e in events if e not in hard_laws and e not in evidence]

        # Summarize repeated others
        summarized_others = []
        counts: Dict[str, List[TraceEvent]] = {}
        for e in others:
            key = f"{e.category}:{e.message}:{e.entity_id}"
            if key not in counts:
                counts[key] = []
            counts[key].append(e)

        for key, group in counts.items():
            if len(group) >= self.repeated_summary_threshold:
                self.summarized_count += len(group) - 1
                rep_event = TraceEvent(
                    event_id=group[0].event_id,
                    category=group[0].category,
                    severity=group[0].severity,
                    message=f"{group[0].message} (Repeated message summarized, count={len(group)})",
                    entity_id=group[0].entity_id
                )
                summarized_others.append(rep_event)
            else:
                summarized_others.extend(group)

        # Enforce max events cap
        available_slots = self.max_events_per_tick - len(hard_laws) - len(evidence)
        if available_slots < 0:
            # Budget heavily exhausted, drop only from others, keep hard_laws and evidence
            self.dropped_count += len(summarized_others)
            return hard_laws + evidence

        if len(summarized_others) > available_slots:
            self.dropped_count += len(summarized_others) - available_slots
            summarized_others = summarized_others[:available_slots]

        return hard_laws + evidence + summarized_others

    def generate_report(self) -> Dict[str, int]:
        return {
            "dropped_total": self.dropped_count,
            "summarized_total": self.summarized_count
        }
