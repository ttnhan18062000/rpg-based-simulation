"""Grade-band scorer consuming the four shipped sibling metric modules' raw outputs.

TCK-20260821-VISUAL-GRADE-SCORER. This module is the intended grading consumer
connectivity.py/shape.py/density.py/variants.py already name in their own docstrings
(each of those returns raw structural facts only -- never a grade/S-A-B-C-D-F band --
and explicitly defers grading to this ticket). It turns ConnectivityResult,
ShapeComponent, DensityResult, and variants.py's primitives into an S/A/B/C/D/F grade
via: a config-sourced GradeConfig (fail-loud loader, config/rendering/
grade_thresholds.toml); binary hard-rule evaluation (fixed pass/fail delta, no
gradient); non-monotonic healthy-band soft-rule evaluation (trapezoidal function of a
raw metric -- positive inside the band, negative at both extremes); an additive
combination of all hard+soft deltas into one score; grade assignment reusing SimQ's
exact threshold values and exact strict-`>` ladder semantics (copied by value, not
imported, from config/simulation_quality/grade_thresholds.yaml -- see
config/rendering/grade_thresholds.toml's header for the architectural-independence
rationale); and multi-seed averaging via a plain arithmetic mean, not special-cased for
N=1 (staging_artifacts/TCK-20260821-VISUAL-GRADE-SCORER/plan.md Decision 4).

This module is architecturally independent from src.simulation_quality: it does not
import src.simulation_quality.* or src.observability.events, does not subclass
src.simulation_quality.scorers.base.PillarScorer, and does not register a new
src.simulation_quality.pillars.PillarId member (plan.md's Scope Guards). Uses stdlib
tomllib, never PyYAML, to parse its config -- src/rendering/ is guarded stdlib-only by
tests/architecture/test_rendering_zero_new_dependency_guard.py (plan.md Decision 2).
"""
from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

_DEFAULT_CONFIG_PATH = (
    Path(__file__).resolve().parents[2] / "config" / "rendering" / "grade_thresholds.toml"
)

_REQUIRED_GRADE_KEYS = ("S", "A", "B", "C", "D")
_REQUIRED_HARD_RULE_KEYS = ("pass_delta", "fail_delta")
_REQUIRED_SOFT_RULE_KEYS = ("low", "healthy_low", "healthy_high", "high", "peak_delta", "min_delta")


@dataclass(frozen=True)
class HardRuleConfig:
    pass_delta: float
    fail_delta: float


@dataclass(frozen=True)
class SoftRuleConfig:
    low: float
    healthy_low: float
    healthy_high: float
    high: float
    peak_delta: float
    min_delta: float


@dataclass(frozen=True)
class GradeConfig:
    grade_thresholds: dict[str, float]
    hard_rules: dict[str, HardRuleConfig]
    soft_rules: dict[str, SoftRuleConfig]


def _require_numeric(container: dict, key: str, context: str) -> float:
    if key not in container:
        raise KeyError(f"{context} is missing required key {key!r}")
    value = container[key]
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{context}[{key!r}] must be numeric, got {value!r}")
    return float(value)


def load_grade_config(path: str | Path = _DEFAULT_CONFIG_PATH) -> GradeConfig:
    with open(path, "rb") as f:
        raw = tomllib.load(f)

    raw_grade_thresholds = raw["grade_thresholds"]
    grade_thresholds = {
        key: _require_numeric(raw_grade_thresholds, key, "grade_thresholds")
        for key in _REQUIRED_GRADE_KEYS
    }

    hard_rules: dict[str, HardRuleConfig] = {}
    for name, rule in raw.get("hard_rules", {}).items():
        hard_rules[name] = HardRuleConfig(
            pass_delta=_require_numeric(rule, "pass_delta", f"hard_rules.{name}"),
            fail_delta=_require_numeric(rule, "fail_delta", f"hard_rules.{name}"),
        )

    soft_rules: dict[str, SoftRuleConfig] = {}
    for name, rule in raw.get("soft_rules", {}).items():
        soft_rules[name] = SoftRuleConfig(
            low=_require_numeric(rule, "low", f"soft_rules.{name}"),
            healthy_low=_require_numeric(rule, "healthy_low", f"soft_rules.{name}"),
            healthy_high=_require_numeric(rule, "healthy_high", f"soft_rules.{name}"),
            high=_require_numeric(rule, "high", f"soft_rules.{name}"),
            peak_delta=_require_numeric(rule, "peak_delta", f"soft_rules.{name}"),
            min_delta=_require_numeric(rule, "min_delta", f"soft_rules.{name}"),
        )

    return GradeConfig(
        grade_thresholds=grade_thresholds,
        hard_rules=hard_rules,
        soft_rules=soft_rules,
    )


@dataclass(frozen=True)
class HardRuleResult:
    name: str
    passed: bool
    delta: float


def evaluate_hard_rule(name: str, passed: bool, config: GradeConfig) -> HardRuleResult:
    rule = config.hard_rules[name]
    delta = rule.pass_delta if passed else rule.fail_delta
    return HardRuleResult(name=name, passed=passed, delta=delta)


@dataclass(frozen=True)
class SoftRuleResult:
    name: str
    raw_value: float
    delta: float


def _trapezoidal_delta(raw_value: float, rule: SoftRuleConfig) -> float:
    if raw_value <= rule.low or raw_value >= rule.high:
        return rule.min_delta
    if raw_value < rule.healthy_low:
        span = rule.healthy_low - rule.low
        frac = (raw_value - rule.low) / span
        return rule.min_delta + frac * (rule.peak_delta - rule.min_delta)
    if raw_value > rule.healthy_high:
        span = rule.high - rule.healthy_high
        frac = (rule.high - raw_value) / span
        return rule.min_delta + frac * (rule.peak_delta - rule.min_delta)
    return rule.peak_delta


def evaluate_soft_rule(name: str, raw_value: float, config: GradeConfig) -> SoftRuleResult:
    rule = config.soft_rules[name]
    delta = _trapezoidal_delta(raw_value, rule)
    return SoftRuleResult(name=name, raw_value=raw_value, delta=delta)


def combine_rule_deltas(
    hard_results: list[HardRuleResult],
    soft_results: list[SoftRuleResult],
) -> float:
    return sum(r.delta for r in hard_results) + sum(r.delta for r in soft_results)


def assign_grade(combined_score: float, grade_thresholds: dict[str, float]) -> str:
    if combined_score > grade_thresholds["S"]:
        return "S"
    if combined_score > grade_thresholds["A"]:
        return "A"
    if combined_score > grade_thresholds["B"]:
        return "B"
    if combined_score > grade_thresholds["C"]:
        return "C"
    if combined_score > grade_thresholds["D"]:
        return "D"
    return "F"


def average_scores(per_seed_scores: list[float]) -> float:
    return sum(per_seed_scores) / len(per_seed_scores)
