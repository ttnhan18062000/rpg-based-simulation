# Compliance IDs: WORLD-GEN-005
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from src.worldgeneration.schema import GenerationIntentSpec
from src.worldmodules.schema import WorldModuleSpec


@dataclass(frozen=True)
class ModuleScore:
    """Scored fitness of a WorldModuleSpec against a GenerationIntentSpec."""

    module_id: str
    score: float  # normalized 0.0–1.0
    reasons: list[str]  # human-readable explanation of why this score was assigned
    dimensions: dict[str, float]  # per-dimension raw scores before normalization


class ModuleScorer:
    """
    Pure scoring utility that evaluates how well each WorldModuleSpec candidate
    fits a GenerationIntentSpec.  No I/O, no side effects.
    """

    _DANGER_TAGS: frozenset[str] = frozenset({"hostile", "conflict", "danger_zone"})
    _DANGER_TYPES: frozenset[str] = frozenset({"conflict", "danger_zone"})
    _DANGER_MAX: float = 5.0

    @staticmethod
    def score(
        intent: GenerationIntentSpec,
        modules: List[WorldModuleSpec],
    ) -> Dict[str, ModuleScore]:
        """
        Score every module in *modules* against *intent*.

        Returns
        -------
        Dict[str, ModuleScore]
            One entry per module keyed by module_id.
            Required modules always receive score=1.0.
        """
        result: Dict[str, ModuleScore] = {}
        required: set[str] = set(intent.required_modules or [])

        for module in modules:
            # Required modules bypass dimension scoring entirely
            if module.module_id in required:
                result[module.module_id] = ModuleScore(
                    module_id=module.module_id,
                    score=1.0,
                    reasons=["required by intent"],
                    dimensions={"required": 1.0},
                )
                continue

            dimensions: dict[str, float] = {}
            reasons: list[str] = []

            # --- Dimension 1: module_type vs settlement_style ---
            # Settlements lose fitness when danger is high (less survivable).
            # Danger-aligned types (by module_type or observability_tags) gain fitness.
            _danger_ratio: float = intent.danger_level / ModuleScorer._DANGER_MAX
            # Compute danger tags early — needed for module_type scoring too
            obs_tags: set[str] = set(module.observability_tags or [])
            has_danger_tags = bool(obs_tags & ModuleScorer._DANGER_TAGS)
            has_danger_type = module.module_type in ModuleScorer._DANGER_TYPES

            if module.module_type == "settlement":
                if intent.settlement_style == "none":
                    dimensions["module_type"] = 0.0
                    reasons.append(
                        "settlement_style=none penalises settlement type"
                    )
                else:
                    # Penalise settlements proportionally to danger: full at 0,
                    # 50% at max danger. Settlements become less fitting as danger rises.
                    dim = max(0.0, 1.0 - _danger_ratio * 0.5)
                    dimensions["module_type"] = dim
                    reasons.append(
                        f"settlement type matches settlement_style={intent.settlement_style}"
                        f" (danger penalty={round(_danger_ratio * 0.5, 2)})"
                    )
            elif module.module_type == "terrain":
                dimensions["module_type"] = 1.0
                reasons.append("terrain type always scores high")
            elif has_danger_type or has_danger_tags:
                # Modules with danger-aligned type OR danger tags gain fitness as danger rises.
                dim = min(1.0, _danger_ratio * 2.0)
                label = (
                    f"module_type={module.module_type} danger-aligned"
                    if has_danger_type
                    else "danger observability_tags"
                )
                dimensions["module_type"] = dim
                reasons.append(
                    f"{label} gains fitness at danger_level={intent.danger_level}"
                )
            elif module.module_type in {"ecology", "population", "economy"}:
                dimensions["module_type"] = 0.5
                reasons.append(f"module_type={module.module_type} is a recognized support type")
            else:
                dimensions["module_type"] = 0.3
                reasons.append(f"module_type={module.module_type} is neutral")

            # --- Dimension 2: danger_level ---
            if has_danger_tags or has_danger_type:
                dim = min(1.0, intent.danger_level / ModuleScorer._DANGER_MAX)
                label = (
                    "conflict type"
                    if has_danger_type
                    else "danger tags"
                )
                reasons.append(
                    f"danger_level={intent.danger_level} matches {label}"
                )
                dimensions["danger_level"] = dim
            else:
                dimensions["danger_level"] = max(
                    0.0, 1.0 - intent.danger_level / ModuleScorer._DANGER_MAX
                )

            # --- Dimension 3: resource_density ---
            resource_count = len(module.resource_recipes or [])
            if resource_count > 0 or module.module_type == "economy":
                dim = min(1.0, float(intent.resource_density))
                label = (
                    "economy type"
                    if module.module_type == "economy"
                    else f"{resource_count} resource recipes"
                )
                reasons.append(
                    f"resource_density={intent.resource_density} matches {label}"
                )
                dimensions["resource_density"] = dim
            else:
                dimensions["resource_density"] = 0.1

            # --- Dimension 4: population_scale ---
            # Normalize so default 1.0 → 0.5 and high 2.0+ → 1.0.
            # A population_scale of 1.0 is neutral intent, not maximum.
            _POPULATION_SCALE_MAX: float = 2.0
            if module.module_type in {"settlement", "population"}:
                dim = min(1.0, float(intent.population_scale) / _POPULATION_SCALE_MAX)
                reasons.append(
                    f"population_scale={intent.population_scale} matches"
                    f" {module.module_type} type"
                )
                dimensions["population_scale"] = dim
            else:
                dimensions["population_scale"] = 0.1

            # --- Normalize: average of dimensions, clamped to [0.0, 1.0] ---
            raw = sum(dimensions.values()) / len(dimensions)
            normalized = min(1.0, max(0.0, raw))

            # Guarantee non-empty reasons (fallback — should never trigger given
            # the four dimensions above always append at least one reason each)
            if not reasons:
                reasons.append(
                    f"module_type={module.module_type}, no strong intent match"
                )

            result[module.module_id] = ModuleScore(
                module_id=module.module_id,
                score=round(normalized, 4),
                reasons=reasons,
                dimensions=dimensions,
            )

        return result
