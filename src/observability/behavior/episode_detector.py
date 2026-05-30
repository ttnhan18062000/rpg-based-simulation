"""
EpisodeDetector — Phase 23 semantic behavior episode reconstruction analyzer.
Scans chronological BehaviorEvent sequences to reconstruct distinct episodes.
"""
from __future__ import annotations
import uuid
from typing import List, Optional
from src.observability.behavior.behavior_timeline_store import EntityBehaviorTimeline
from src.observability.behavior.behavior_episode import BehaviorEpisode


class EpisodeDetector:
    """
    State-free post-run analyzer grouping behavior histories into semantic episodes.
    """
    def detect(self, timeline: EntityBehaviorTimeline) -> List[BehaviorEpisode]:
        episodes: List[BehaviorEpisode] = []
        events = sorted(timeline.events, key=lambda x: x.tick)
        
        # 1. Combat episodes: combat/engage -> combat/kill_or_defeat or recovery/recover
        active_combat_start: Optional[int] = None
        combat_event_ids: List[str] = []
        combat_steps: List[str] = []
        
        # 2. Quest episodes: quest/accept -> quest/complete or failure_response/quest_failure
        active_quest_start: Optional[int] = None
        active_quest_id: Optional[str] = None
        quest_event_ids: List[str] = []
        quest_steps: List[str] = []

        # 3. Info episodes: information_seeking/query -> information_seeking/learned
        active_info_start: Optional[int] = None
        info_event_ids: List[str] = []
        info_steps: List[str] = []

        # 4. Failure-response episodes: failure_response/blocked_route -> movement/travel (success)
        active_fail_start: Optional[int] = None
        fail_event_ids: List[str] = []
        fail_steps: List[str] = []

        for ev in events:
            # --- Combat Episode logic ---
            if ev.behavior_category == "combat" and ev.behavior_family == "engage":
                if active_combat_start is None:
                    active_combat_start = ev.tick
                    combat_event_ids = []
                    combat_steps = []
                combat_event_ids.extend(ev.source_event_ids)
                combat_steps.append(f"engage_tick_{ev.tick}")
            elif active_combat_start is not None and (
                (ev.behavior_category == "combat" and ev.behavior_family in ("kill_or_defeat", "defeat")) or
                (ev.behavior_category == "recovery" and ev.behavior_family == "recover")
            ):
                combat_event_ids.extend(ev.source_event_ids)
                combat_steps.append(f"{ev.behavior_family}_tick_{ev.tick}")
                outcome = "success" if ev.behavior_family == "kill_or_defeat" else "escaped"
                episodes.append(BehaviorEpisode(
                    episode_id=str(uuid.uuid4()),
                    run_id=timeline.run_id,
                    entity_id=timeline.entity_id,
                    episode_type="combat_episode",
                    start_tick=active_combat_start,
                    end_tick=ev.tick,
                    trigger="combat_engagement",
                    steps=tuple(combat_steps),
                    outcome=outcome,
                    source_behavior_event_ids=tuple(combat_event_ids),
                    summary=f"Combat episode from tick {active_combat_start} to {ev.tick} with outcome: {outcome}"
                ))
                active_combat_start = None

            # --- Quest Episode logic ---
            if ev.behavior_category == "quest" and ev.behavior_family == "accept":
                active_quest_start = ev.tick
                active_quest_id = ev.target_id or "unknown"
                quest_event_ids = list(ev.source_event_ids)
                quest_steps = [f"accept_tick_{ev.tick}"]
            elif active_quest_start is not None and ev.behavior_category == "quest" and ev.target_id == active_quest_id:
                quest_event_ids.extend(ev.source_event_ids)
                quest_steps.append(f"{ev.behavior_family}_tick_{ev.tick}")
                if ev.behavior_family == "complete":
                    episodes.append(BehaviorEpisode(
                        episode_id=str(uuid.uuid4()),
                        run_id=timeline.run_id,
                        entity_id=timeline.entity_id,
                        episode_type="quest_episode",
                        start_tick=active_quest_start,
                        end_tick=ev.tick,
                        trigger=f"quest_{active_quest_id}",
                        steps=tuple(quest_steps),
                        outcome="success",
                        source_behavior_event_ids=tuple(quest_event_ids),
                        summary=f"Quest {active_quest_id} completed successfully"
                    ))
                    active_quest_start = None
            elif active_quest_start is not None and ev.behavior_category == "failure_response" and ev.behavior_family == "quest_failure":
                quest_event_ids.extend(ev.source_event_ids)
                quest_steps.append(f"failure_tick_{ev.tick}")
                episodes.append(BehaviorEpisode(
                    episode_id=str(uuid.uuid4()),
                    run_id=timeline.run_id,
                    entity_id=timeline.entity_id,
                    episode_type="quest_episode",
                    start_tick=active_quest_start,
                    end_tick=ev.tick,
                    trigger=f"quest_{active_quest_id}",
                    steps=tuple(quest_steps),
                    outcome="failure",
                    source_behavior_event_ids=tuple(quest_event_ids),
                    summary=f"Quest {active_quest_id} failed"
                ))
                active_quest_start = None

            # --- Info Episode logic ---
            if ev.behavior_category == "information_seeking" and ev.behavior_family == "query":
                active_info_start = ev.tick
                info_event_ids = list(ev.source_event_ids)
                info_steps = [f"query_tick_{ev.tick}"]
            elif active_info_start is not None and ev.behavior_category == "information_seeking" and ev.behavior_family == "learned":
                info_event_ids.extend(ev.source_event_ids)
                info_steps.append(f"learned_tick_{ev.tick}")
                episodes.append(BehaviorEpisode(
                    episode_id=str(uuid.uuid4()),
                    run_id=timeline.run_id,
                    entity_id=timeline.entity_id,
                    episode_type="information_episode",
                    start_tick=active_info_start,
                    end_tick=ev.tick,
                    trigger="information_inquiry",
                    steps=tuple(info_steps),
                    outcome="success",
                    source_behavior_event_ids=tuple(info_event_ids),
                    summary="Information sought and successfully acquired"
                ))
                active_info_start = None

            # --- Failure Response logic ---
            if ev.behavior_category == "failure_response" and ev.behavior_family == "blocked_route":
                active_fail_start = ev.tick
                fail_event_ids = list(ev.source_event_ids)
                fail_steps = [f"blocked_tick_{ev.tick}"]
            elif active_fail_start is not None and ev.behavior_category == "movement" and ev.behavior_family == "travel" and ev.outcome == "success":
                fail_event_ids.extend(ev.source_event_ids)
                fail_steps.append(f"resolved_travel_tick_{ev.tick}")
                episodes.append(BehaviorEpisode(
                    episode_id=str(uuid.uuid4()),
                    run_id=timeline.run_id,
                    entity_id=timeline.entity_id,
                    episode_type="failure_response_episode",
                    start_tick=active_fail_start,
                    end_tick=ev.tick,
                    trigger="route_blockage",
                    steps=tuple(fail_steps),
                    outcome="resolved",
                    source_behavior_event_ids=tuple(fail_event_ids),
                    summary="Route blockage resolved and travel resumed"
                ))
                active_fail_start = None

        # Clean up any unresolved ongoing/stuck episodes
        if active_combat_start is not None:
            episodes.append(BehaviorEpisode(
                episode_id=str(uuid.uuid4()),
                run_id=timeline.run_id,
                entity_id=timeline.entity_id,
                episode_type="combat_episode",
                start_tick=active_combat_start,
                end_tick=None,
                trigger="combat_engagement",
                steps=tuple(combat_steps),
                outcome="ongoing",
                source_behavior_event_ids=tuple(combat_event_ids),
                summary="Combat engagement started but unresolved"
            ))

        if active_quest_start is not None:
            episodes.append(BehaviorEpisode(
                episode_id=str(uuid.uuid4()),
                run_id=timeline.run_id,
                entity_id=timeline.entity_id,
                episode_type="quest_episode",
                start_tick=active_quest_start,
                end_tick=None,
                trigger=f"quest_{active_quest_id}",
                steps=tuple(quest_steps),
                outcome="stuck",
                source_behavior_event_ids=tuple(quest_event_ids),
                summary=f"Quest {active_quest_id} in stuck or abandoned state"
            ))

        return episodes
