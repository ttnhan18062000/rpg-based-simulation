"""
behavior_scorecard — Phase 26 semantic behavior scorecards.
Provides structured metrics evaluating entity and population changes.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class EntityBehaviorScorecard:
    """
    Immutable representation of an individual entity's behavioral outcomes.
    """
    run_id: str
    entity_id: int
    ticks_observed: int
    route_families_used: Mapping[str, int]
    behavior_categories_used: Mapping[str, int]
    episodes_started: int
    episodes_completed: int
    episodes_failed: int
    repeated_failure_count: int
    adaptation_proof_count: int
    stagnation_score: float
    progression_score: float
    cooperation_score: float
    information_usage_score: float
    behavior_diversity_score: float
    verdict: str

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dict."""
        return {
            "run_id": self.run_id,
            "entity_id": self.entity_id,
            "ticks_observed": self.ticks_observed,
            "route_families_used": dict(self.route_families_used),
            "behavior_categories_used": dict(self.behavior_categories_used),
            "episodes_started": self.episodes_started,
            "episodes_completed": self.episodes_completed,
            "episodes_failed": self.episodes_failed,
            "repeated_failure_count": self.repeated_failure_count,
            "adaptation_proof_count": self.adaptation_proof_count,
            "stagnation_score": self.stagnation_score,
            "progression_score": self.progression_score,
            "cooperation_score": self.cooperation_score,
            "information_usage_score": self.information_usage_score,
            "behavior_diversity_score": self.behavior_diversity_score,
            "verdict": self.verdict,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EntityBehaviorScorecard:
        """Deserialize from a JSON-compatible dict."""
        return cls(
            run_id=data["run_id"],
            entity_id=data["entity_id"],
            ticks_observed=data["ticks_observed"],
            route_families_used=data.get("route_families_used") or {},
            behavior_categories_used=data.get("behavior_categories_used") or {},
            episodes_started=data["episodes_started"],
            episodes_completed=data["episodes_completed"],
            episodes_failed=data["episodes_failed"],
            repeated_failure_count=data["repeated_failure_count"],
            adaptation_proof_count=data["adaptation_proof_count"],
            stagnation_score=data["stagnation_score"],
            progression_score=data["progression_score"],
            cooperation_score=data["cooperation_score"],
            information_usage_score=data["information_usage_score"],
            behavior_diversity_score=data["behavior_diversity_score"],
            verdict=data["verdict"],
        )


@dataclass(frozen=True)
class RunBehaviorScorecard:
    """
    Immutable representation of population-level run behavior outcomes.
    """
    run_id: str
    entity_count: int
    route_diversity_score: float
    action_entropy: float
    episode_success_rate: float
    stagnation_ratio: float
    repeated_failure_loop_count: int
    adaptation_proof_count: int
    hidden_knowledge_suspicion_count: int
    cognition_impact_score: float
    observability_overhead_ms_avg: float
    runtime_cost_delta_percent: float
    verdict: str

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dict."""
        return {
            "run_id": self.run_id,
            "entity_count": self.entity_count,
            "route_diversity_score": self.route_diversity_score,
            "action_entropy": self.action_entropy,
            "episode_success_rate": self.episode_success_rate,
            "stagnation_ratio": self.stagnation_ratio,
            "repeated_failure_loop_count": self.repeated_failure_loop_count,
            "adaptation_proof_count": self.adaptation_proof_count,
            "hidden_knowledge_suspicion_count": self.hidden_knowledge_suspicion_count,
            "cognition_impact_score": self.cognition_impact_score,
            "observability_overhead_ms_avg": self.observability_overhead_ms_avg,
            "runtime_cost_delta_percent": self.runtime_cost_delta_percent,
            "verdict": self.verdict,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RunBehaviorScorecard:
        """Deserialize from a JSON-compatible dict."""
        return cls(
            run_id=data["run_id"],
            entity_count=data["entity_count"],
            route_diversity_score=data["route_diversity_score"],
            action_entropy=data["action_entropy"],
            episode_success_rate=data["episode_success_rate"],
            stagnation_ratio=data["stagnation_ratio"],
            repeated_failure_loop_count=data["repeated_failure_loop_count"],
            adaptation_proof_count=data["adaptation_proof_count"],
            hidden_knowledge_suspicion_count=data["hidden_knowledge_suspicion_count"],
            cognition_impact_score=data["cognition_impact_score"],
            observability_overhead_ms_avg=data["observability_overhead_ms_avg"],
            runtime_cost_delta_percent=data["runtime_cost_delta_percent"],
            verdict=data["verdict"],
        )
