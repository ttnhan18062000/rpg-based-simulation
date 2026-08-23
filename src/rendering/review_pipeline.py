"""Tiered Tier 0 (pure data) -> Tier 1 (JSON digest) -> Tier 2 (annotated image,
fetched only on escalation) agent-review pipeline.

TCK-20260821-VISUAL-AGENT-REVIEW. Composes the four already-shipped sibling metric
modules (`connectivity.py`, `density.py`, `shape.py` — `variants.py` is multi-seed/
multi-spec and out of scope for a single-state digest) plus `grading.py`'s hard/soft
rule evaluation and grade assignment into one orchestrating entry point,
`run_tier0_tier1_pipeline`. `should_escalate` is the single call site for the D/F
escalation cutoff. `Tier1Digest`/`digest_to_json` define the compact, deterministic
JSON payload a reviewing agent reads first, before ever considering an image. The
annotated/gridlined render (`render_annotated.py`) is written to disk only when
`should_escalate(...)` returns `True` — this is the structural mechanism (not just an
agent-prompt instruction) behind this ticket's "zero image is ever fetched when Tier 0
does not flag an anomaly" acceptance criterion.
"""
from __future__ import annotations

import dataclasses
import json
import os
from dataclasses import dataclass

from src.core.state import AuthoritativeState
from src.rendering.connectivity import analyze_connectivity
from src.rendering.density import compute_density_cv, compute_terrain_histogram
from src.rendering.grading import (
    GradeConfig,
    HardRuleResult,
    assign_grade,
    combine_rule_deltas,
    evaluate_hard_rule,
    evaluate_soft_rule,
    load_grade_config,
)
from src.rendering.render import render_output_path
from src.rendering.render_annotated import render_annotated
from src.rendering.shape import connected_components


def should_escalate(hard_results: list[HardRuleResult], grade: str) -> bool:
    return any(not r.passed for r in hard_results) or grade in ("D", "F")


@dataclass(frozen=True)
class Tier1Digest:
    world_id: str
    seed: int
    tick: int
    grade: str
    combined_score: float
    hard_rule_results: tuple[dict, ...]
    soft_rule_results: tuple[dict, ...]
    terrain_histogram: dict[str, int]
    entity_count: int
    connectivity_component_count: int
    connectivity_percent_reachable: float
    flagged_shape_components: tuple[dict, ...]
    escalate: bool
    plain_render_path: str
    annotated_render_path: str | None


def digest_to_json(digest: Tier1Digest) -> str:
    return json.dumps(dataclasses.asdict(digest), sort_keys=True)


def run_tier0_tier1_pipeline(
    state: AuthoritativeState,
    world_id: str,
    base_dir: str,
    run_id: str,
    grade_config: GradeConfig | None = None,
) -> Tier1Digest:
    config = grade_config if grade_config is not None else load_grade_config()

    connectivity_result = analyze_connectivity(state.terrain, state.blocked_tiles)
    density_result = compute_density_cv(state.entities)
    terrain_histogram = compute_terrain_histogram(state.terrain)
    shape_components = connected_components(state.terrain)

    hard_result = evaluate_hard_rule(
        "fully_connected", connectivity_result.component_count == 1, config
    )
    hard_results = [hard_result]

    soft_results = []
    if shape_components:
        soft_results.append(
            evaluate_soft_rule(
                "fill_ratio_healthy_band", shape_components[0].fill_ratio, config
            )
        )

    combined_score = combine_rule_deltas(hard_results, soft_results)
    grade = assign_grade(combined_score, config.grade_thresholds)
    escalate = should_escalate(hard_results, grade)

    band = config.soft_rules["fill_ratio_healthy_band"]
    flagged_shape_components = tuple(
        sorted(
            (
                {"terrain_type": sc.terrain_type, "bbox": sc.bbox, "fill_ratio": sc.fill_ratio}
                for sc in shape_components
                if sc.fill_ratio < band.healthy_low or sc.fill_ratio > band.healthy_high
            ),
            key=lambda d: (d["terrain_type"], d["bbox"]),
        )
    )

    plain_render_path = render_output_path(base_dir, run_id, f"{world_id}_tick{state.tick}.png")
    annotated_render_path = None
    if escalate:
        annotated_render_path = render_output_path(
            base_dir, run_id, f"{world_id}_tick{state.tick}_annotated.png"
        )
        os.makedirs(os.path.dirname(annotated_render_path), exist_ok=True)
        render_annotated(state, annotated_render_path)

    return Tier1Digest(
        world_id=world_id,
        seed=state.seed,
        tick=state.tick,
        grade=grade,
        combined_score=combined_score,
        hard_rule_results=tuple(dataclasses.asdict(r) for r in hard_results),
        soft_rule_results=tuple(dataclasses.asdict(r) for r in soft_results),
        terrain_histogram=terrain_histogram,
        entity_count=density_result.entity_count,
        connectivity_component_count=connectivity_result.component_count,
        connectivity_percent_reachable=connectivity_result.percent_reachable,
        flagged_shape_components=flagged_shape_components,
        escalate=escalate,
        plain_render_path=plain_render_path,
        annotated_render_path=annotated_render_path,
    )
