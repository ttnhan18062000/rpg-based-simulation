from __future__ import annotations
import datetime
from datetime import timezone
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from src.simulation_quality.pillar_accumulator import PillarAccumulator
from src.simulation_quality.pillars import PillarId
from src.simulation_quality.score_record import ScoreRecord
from src.simulation_quality.weights import ScoringWeights


@dataclass
class PillarSnapshot:
    pillar_id: str
    raw_score: float
    normalized_score: float
    grade: str
    event_count: int
    negative_count: int
    loop_detected: bool
    loop_flags: frozenset[str]
    worst_events: tuple[ScoreRecord, ...]


@dataclass
class QualityReport:
    run_id: str
    tick_count: int
    overall_score: float
    overall_grade: str
    generated_at: str
    pillars: Mapping[str, PillarSnapshot]

    def to_dict(self) -> dict[str, Any]:
        pillars_out: dict[str, Any] = {}
        for pillar_id, snap in self.pillars.items():
            worst_out = []
            for rec in snap.worst_events:
                worst_out.append({
                    "tick": rec.tick,
                    "event_id": rec.event_id,
                    "pillar": rec.pillar.value,
                    "delta": rec.delta,
                    "reason": rec.reason,
                    "event_type": rec.event_type,
                    "entity_id": rec.entity_id,
                    "region_id": rec.region_id,
                    "tags": list(rec.tags),
                })
            pillars_out[pillar_id] = {
                "raw_score": snap.raw_score,
                "normalized_score": snap.normalized_score,
                "grade": snap.grade,
                "event_count": snap.event_count,
                "negative_count": snap.negative_count,
                "loop_detected": snap.loop_detected,
                "loop_flags": sorted(snap.loop_flags),
                "worst_events": worst_out,
            }
        return {
            "run_id": self.run_id,
            "tick_count": self.tick_count,
            "overall_score": self.overall_score,
            "overall_grade": self.overall_grade,
            "generated_at": self.generated_at,
            "pillars": pillars_out,
        }


def _assign_grade(normalized_score: float, grade_thresholds: dict[str, float]) -> str:
    if normalized_score > grade_thresholds["S"]:
        return "S"
    if normalized_score > grade_thresholds["A"]:
        return "A"
    if normalized_score > grade_thresholds["B"]:
        return "B"
    if normalized_score > grade_thresholds["C"]:
        return "C"
    if normalized_score > grade_thresholds["D"]:
        return "D"
    return "F"


class QualityReportBuilder:
    @staticmethod
    def build(
        accumulators: Mapping[PillarId, PillarAccumulator],
        current_tick: int,
        run_id: str,
        weights: ScoringWeights,
    ) -> QualityReport:
        effective_tick = max(1, current_tick)
        pillar_snapshots: dict[str, PillarSnapshot] = {}
        weighted_sum = 0.0
        weight_total = 0.0

        for pillar_id, acc in accumulators.items():
            snap = acc.snapshot()
            last_event_tick = snap.get("last_event_tick", 0)
            floor_tick = max(1, effective_tick // 4)
            effective_denominator = max(floor_tick, last_event_tick) if last_event_tick > 0 else effective_tick
            normalized_score = snap["raw_score"] / effective_denominator
            grade = _assign_grade(normalized_score, weights.grade_thresholds)
            pillar_weight = weights.pillar_weight(pillar_id.value)

            pillar_snapshots[pillar_id.value] = PillarSnapshot(
                pillar_id=pillar_id.value,
                raw_score=snap["raw_score"],
                normalized_score=normalized_score,
                grade=grade,
                event_count=snap["event_count"],
                negative_count=snap["negative_count"],
                loop_detected=len(snap["loop_flags"]) > 0,
                loop_flags=snap["loop_flags"],
                worst_events=snap["worst_events"],
            )
            weighted_sum += normalized_score * pillar_weight
            weight_total += pillar_weight

        overall_score = weighted_sum / weight_total if weight_total > 0 else 0.0
        overall_grade = _assign_grade(overall_score, weights.grade_thresholds)

        return QualityReport(
            run_id=run_id,
            tick_count=current_tick,
            overall_score=overall_score,
            overall_grade=overall_grade,
            generated_at=datetime.datetime.now(timezone.utc).isoformat(),
            pillars=pillar_snapshots,
        )
