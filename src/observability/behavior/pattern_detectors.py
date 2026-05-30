"""
pattern_detectors — Phase 25 pattern matching algorithms.
Processes events and episodes to isolate behavioral anomalies.
"""
from __future__ import annotations
import uuid
from typing import List, Sequence
from src.observability.behavior.behavior_event import BehaviorEvent
from src.observability.behavior.behavior_episode import BehaviorEpisode
from src.observability.behavior.behavior_finding import BehaviorFinding


class RepeatedFailureLoopDetector:
    """Detects when an entity enters a repeated loop of route or quest failures without adapting."""
    def detect(
        self,
        entity_id: int,
        events: Sequence[BehaviorEvent],
        episodes: Sequence[BehaviorEpisode]
    ) -> List[BehaviorFinding]:
        findings = []
        failure_episodes = [ep for ep in episodes if ep.entity_id == entity_id and ep.outcome == "failure"]
        
        if len(failure_episodes) >= 3:
            evidence_eps = tuple(ep.episode_id for ep in failure_episodes)
            findings.append(BehaviorFinding(
                finding_id=str(uuid.uuid4()),
                finding_type="repeated_failure_loop",
                severity="WARNING",
                summary=f"Entity {entity_id} experienced {len(failure_episodes)} consecutive failures without adapting",
                affected_entities=(entity_id,),
                tick_range=(failure_episodes[0].start_tick, failure_episodes[-1].end_tick or failure_episodes[-1].start_tick),
                evidence_event_ids=(),
                evidence_episode_ids=evidence_eps,
                suggested_systems=("locomotion_system", "navigation_system"),
                recommendation="Introduce dynamic route-avoidance or cooldown backoff after consecutive failures."
            ))
        return findings


class BehaviorChangeProofDetector:
    """Verifies adaptation proofs: e.g. a failure followed by successful route adaptation."""
    def detect(
        self,
        entity_id: int,
        events: Sequence[BehaviorEvent],
        episodes: Sequence[BehaviorEpisode]
    ) -> List[BehaviorFinding]:
        findings = []
        resolved_episodes = [ep for ep in episodes if ep.entity_id == entity_id and ep.outcome == "resolved"]
        
        for ep in resolved_episodes:
            findings.append(BehaviorFinding(
                finding_id=str(uuid.uuid4()),
                finding_type="successful_adaptation",
                severity="INFO",
                summary=f"Entity {entity_id} adapted route successfully following blockage at tick {ep.start_tick}",
                affected_entities=(entity_id,),
                tick_range=(ep.start_tick, ep.end_tick or ep.start_tick),
                evidence_event_ids=(),
                evidence_episode_ids=(ep.episode_id,),
                suggested_systems=("navigation_system",),
                recommendation="Maintain active goal weight modifiers since adaptation is working."
            ))
        return findings


class HiddenKnowledgeSuspicionDetector:
    """Identifies potential omniscience leaks where entities route perfectly around unseen threats."""
    def detect(
        self,
        entity_id: int,
        events: Sequence[BehaviorEvent],
        episodes: Sequence[BehaviorEpisode]
    ) -> List[BehaviorFinding]:
        findings = []
        queries = [ev for ev in events if ev.entity_id == entity_id and ev.behavior_category == "information_seeking" and ev.behavior_family == "query"]
        avoidances = [ev for ev in events if ev.entity_id == entity_id and ev.behavior_category == "avoidance"]
        
        if len(avoidances) >= 3 and len(queries) == 0:
            findings.append(BehaviorFinding(
                finding_id=str(uuid.uuid4()),
                finding_type="hidden_knowledge_suspicion",
                severity="ERROR",
                summary=f"Entity {entity_id} demonstrated high avoidance behavior without any queries; possible omniscience leak",
                affected_entities=(entity_id,),
                tick_range=None,
                evidence_event_ids=tuple(ev.source_event_ids[0] for ev in avoidances if ev.source_event_ids),
                evidence_episode_ids=(),
                suggested_systems=("perception_system", "intelligence_system"),
                recommendation="Enforce strict salience capacity limits and clear ignore lists."
            ))
        return findings
