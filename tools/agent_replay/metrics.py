"""3-tier metrics computation for the filtered replay eval pilot
(TCK-20260907-FILTERED-REPLAY-EVAL-PILOT, Step 6).

Computes exactly the 3 tiers the frozen spec (`agent_evaluation_foundation_experiment.md`)
defines — Primary (per-defect-class flag-rate agreement across 2 runs), Safety (contamination-
check pass/fail, sourced from `pilot_isolation.IsolationEvidence`), Efficiency (wall-clock +
tool-call volume, informative only) — and nothing else. Never derives or claims a "false-pass"/
"false-block" rate for anything beyond the 2 named defect classes (M2, M3), per the frozen spec's
own Terminology discipline clause and this ticket's Scope Guards.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class RepeatabilityResult:
    repeatable: bool
    per_defect_class_agreement: dict
    disagreements: list


def compare_repeatability(run1_flags: dict, run2_flags: dict) -> RepeatabilityResult:
    """`run1_flags`/`run2_flags`: `{ticket_id: {"M2": bool, ...}}` (M3 is evaluated only against
    its own synthetic/clean fixtures, never against real sampled tickets — see
    defect_detectors.py's module docstring — so a caller may key M3 under a synthetic fixture id
    rather than a real ticket_id; this function makes no assumption about what the keys mean)."""
    disagreements: list = []
    per_class_disagreement: dict = {}

    for ticket_id, flags1 in run1_flags.items():
        flags2 = run2_flags.get(ticket_id, {})
        for defect_class, value1 in flags1.items():
            value2 = flags2.get(defect_class)
            if value1 != value2:
                disagreements.append(f"{ticket_id}:{defect_class}")
                per_class_disagreement[defect_class] = True

    all_classes = {dc for flags in run1_flags.values() for dc in flags} | {
        dc for flags in run2_flags.values() for dc in flags
    }
    per_class_agreement = {dc: not per_class_disagreement.get(dc, False) for dc in sorted(all_classes)}

    return RepeatabilityResult(
        repeatable=not disagreements,
        per_defect_class_agreement=per_class_agreement,
        disagreements=sorted(disagreements),
    )


@dataclass(frozen=True)
class PilotMetrics:
    primary_repeatability_pct: float
    primary_per_class_agreement: dict
    primary_disagreements: list
    safety_isolation_held: bool
    safety_evidence: str
    efficiency_wall_clock_s: dict = field(default_factory=dict)
    efficiency_work_volume: dict = field(default_factory=dict)


def compute_metrics(
    run1_flags: dict,
    run2_flags: dict,
    isolation_evidence,
    timing_data: dict,
) -> PilotMetrics:
    repeatability = compare_repeatability(run1_flags, run2_flags)

    total_checks = sum(len(flags) for flags in run1_flags.values())
    agreements = total_checks - len(repeatability.disagreements)
    pct = (agreements / total_checks * 100.0) if total_checks else 100.0

    safety_evidence = (
        isolation_evidence.violation
        if not isolation_evidence.held
        else (
            f"pre-porcelain={isolation_evidence.pre_porcelain!r}, "
            f"post-porcelain={isolation_evidence.post_porcelain!r} — no pilot-attributed write "
            "detected under agent-monitoring/*.jsonl, unscoped sidecar unchanged"
        )
    )

    return PilotMetrics(
        primary_repeatability_pct=pct,
        primary_per_class_agreement=repeatability.per_defect_class_agreement,
        primary_disagreements=repeatability.disagreements,
        safety_isolation_held=isolation_evidence.held,
        safety_evidence=safety_evidence,
        efficiency_wall_clock_s=dict(timing_data.get("wall_clock_s", {})),
        efficiency_work_volume=dict(timing_data.get("work_volume", {})),
    )
