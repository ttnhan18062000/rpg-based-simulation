"""
src/domains/feature_packs/balance_spec.py
───────────────────────────────────────────────────────────────────────────────
BalanceExperimentSpec + BalanceExperimentRunner — declarative balance harness
for feature pack acceptance testing (E63D).

The runner is intentionally pure: it accepts a pre-computed metric snapshot dict
rather than executing a live simulation run.  CI cost stays near-zero.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class BalanceExperimentSpec(BaseModel):
    """Declarative specification for a balance acceptance experiment.

    Fields
    ------
    metric_path:
        Dot-separated path into the metric snapshot dict.
        Example: ``"route_distribution.ESCORT_DIGNITARY"``
    baseline_pack:
        Name of the pack whose presence defines the baseline being evaluated.
        Used only for labelling and reporting — does not affect the numerical check.
    threshold:
        The value the resolved metric must meet or exceed for the experiment to pass.
    tolerance:
        Maximum absolute deviation below *threshold* that still counts as a pass.
        Effective pass condition: ``measured >= threshold - tolerance``.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    metric_path: str = Field(..., min_length=1)
    baseline_pack: str = Field(..., min_length=1)
    threshold: float = Field(..., ge=0.0)
    tolerance: float = Field(0.0, ge=0.0)

    def to_dict(self) -> dict:
        return {
            "metric_path": self.metric_path,
            "baseline_pack": self.baseline_pack,
            "threshold": self.threshold,
            "tolerance": self.tolerance,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "BalanceExperimentSpec":
        return cls(**d)


@dataclass(frozen=True, slots=True)
class ExperimentResult:
    """Outcome of a single balance experiment run.

    Attributes
    ----------
    passed:   Whether the measured value satisfied the spec.
    measured: The value resolved from the metric snapshot.
    spec:     The spec that was evaluated.
    """

    passed: bool
    measured: float
    spec: BalanceExperimentSpec


class BalanceExperimentRunner:
    """Pure evaluator for BalanceExperimentSpec against a metric snapshot.

    Usage
    -----
    snapshot = {"route_distribution": {"ESCORT_DIGNITARY": 0.25}}
    spec = BalanceExperimentSpec(
        metric_path="route_distribution.ESCORT_DIGNITARY",
        baseline_pack="demo_escort_pack",
        threshold=0.1,
    )
    result = BalanceExperimentRunner.run(spec, snapshot)
    assert result.passed
    """

    @staticmethod
    def run(spec: BalanceExperimentSpec, snapshot: dict[str, Any]) -> ExperimentResult:
        """Evaluate *spec* against *snapshot*.

        Parameters
        ----------
        spec:
            The balance experiment to evaluate.
        snapshot:
            A nested dict of pre-computed metrics.  Values must be numeric at
            the resolved leaf path.

        Returns
        -------
        ExperimentResult
            Contains pass/fail, measured value, and the originating spec.

        Raises
        ------
        KeyError
            If *metric_path* does not resolve within *snapshot*.
        TypeError
            If the resolved value is not numeric.
        """
        value: Any = snapshot
        for key in spec.metric_path.split("."):
            if not isinstance(value, dict):
                raise KeyError(
                    f"metric_path '{spec.metric_path}': expected dict at '{key}', got {type(value).__name__}"
                )
            value = value[key]

        if not isinstance(value, (int, float)):
            raise TypeError(
                f"metric_path '{spec.metric_path}' resolved to {type(value).__name__}, expected numeric"
            )

        measured = float(value)
        passed = measured >= (spec.threshold - spec.tolerance)
        return ExperimentResult(passed=passed, measured=measured, spec=spec)
