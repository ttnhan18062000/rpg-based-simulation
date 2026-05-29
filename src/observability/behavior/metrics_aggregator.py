"""
BehaviorMetricsAggregator — Phase 24 semantic behavior metrics aggregator.
Compiles behavior counts, failure occurrences, and adaptation ticks outside simulation loop.
"""
from __future__ import annotations
from typing import Sequence, Any
from src.observability.behavior.behavior_event import BehaviorEvent
from src.observability.behavior.behavior_metric_window import BehaviorMetricWindow


class BehaviorMetricsAggregator:
    """
    Groups and aggregates normalized BehaviorEvents into BehaviorMetricWindows.
    Designed for async execution or post-run analysis.
    """
    def aggregate(
        self,
        run_id: str,
        window_start: int,
        window_end: int,
        behavior_events: Sequence[BehaviorEvent],
        episodes: Sequence[Any] = (),
    ) -> BehaviorMetricWindow:
        behavior_counts = {}
        route_family_counts = {}
        episode_counts = {}
        episode_outcomes = {}
        failure_counts = {}
        adaptation_counts = {}
        entity_activity_counts = {}

        # 1. Filter events falling within [window_start, window_end]
        filtered_events = [
            e for e in behavior_events
            if window_start <= e.tick <= window_end
        ]

        # 2. Extract counts from filtered behavior events
        for ev in filtered_events:
            # Map category & family: category/family
            key = f"{ev.behavior_category}/{ev.behavior_family}"
            behavior_counts[key] = behavior_counts.get(key, 0) + 1

            if ev.route_family:
                route_family_counts[ev.route_family] = route_family_counts.get(ev.route_family, 0) + 1

            if ev.behavior_category == "failure_response":
                f_type = ev.behavior_family or "unknown"
                failure_counts[f_type] = failure_counts.get(f_type, 0) + 1
                
                # Check for adaptation indicators
                if ev.outcome == "adapted" or "adaptation" in (ev.reason or "").lower():
                    adaptation_counts["successful_adaptation"] = adaptation_counts.get("successful_adaptation", 0) + 1

            if ev.entity_id is not None:
                ent_key = f"entity_{ev.entity_id}"
                entity_activity_counts[ent_key] = entity_activity_counts.get(ent_key, 0) + 1

        # 3. Process episodes (placeholder/compatibility for Phase 23)
        for ep in episodes:
            start_t = getattr(ep, "start_tick", None)
            if start_t is not None and not (window_start <= start_t <= window_end):
                continue
            
            ep_type = getattr(ep, "episode_type", "unknown")
            episode_counts[ep_type] = episode_counts.get(ep_type, 0) + 1
            
            outcome = getattr(ep, "outcome", "unknown")
            outcome_key = f"{ep_type}/{outcome}"
            episode_outcomes[outcome_key] = episode_outcomes.get(outcome_key, 0) + 1

        return BehaviorMetricWindow(
            run_id=run_id,
            window_start_tick=window_start,
            window_end_tick=window_end,
            behavior_counts=behavior_counts,
            route_family_counts=route_family_counts,
            episode_counts=episode_counts,
            episode_outcomes=episode_outcomes,
            failure_counts=failure_counts,
            adaptation_counts=adaptation_counts,
            entity_activity_counts=entity_activity_counts
        )
