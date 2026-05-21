"""
StaleBaselineDetector — warns when a baseline may no longer be valid
because the engine version, scenario config, or schema version changed.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class StalenessWarning:
    field_name: str
    baseline_value: str
    current_value: str
    message: str


@dataclass
class StalenessResult:
    is_stale: bool
    warnings: List[StalenessWarning] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "is_stale": self.is_stale,
            "warnings": [
                {
                    "field": w.field_name,
                    "baseline_value": w.baseline_value,
                    "current_value": w.current_value,
                    "message": w.message,
                }
                for w in self.warnings
            ],
        }


class StaleBaselineDetector:
    """
    Compares metadata from an active baseline against a current run's metadata
    to detect version mismatches that could make the baseline invalid.

    Checks:
    - artifact_schema_version
    - scenario_type
    - engine_version (if present in both)
    """

    def check(
        self,
        baseline_meta: dict,
        current_run_meta: dict,
    ) -> StalenessResult:
        """
        baseline_meta: dict from BaselineConfig (or its model_dump())
        current_run_meta: dict from the current run's metadata (e.g. run_report.json metadata section)
        """
        warnings: List[StalenessWarning] = []

        # Schema version mismatch
        b_schema = baseline_meta.get("artifact_schema_version", "baseline_v1")
        c_schema = current_run_meta.get("artifact_schema_version", "baseline_v1")
        if b_schema != c_schema:
            warnings.append(StalenessWarning(
                field_name="artifact_schema_version",
                baseline_value=b_schema,
                current_value=c_schema,
                message=(
                    f"Baseline uses schema '{b_schema}' but current run uses '{c_schema}'. "
                    "Comparison metrics may be incompatible."
                ),
            ))

        # Scenario type mismatch
        b_scenario = baseline_meta.get("scenario_type", "")
        c_scenario = current_run_meta.get("scenario_type", "")
        if b_scenario and c_scenario and b_scenario != c_scenario:
            warnings.append(StalenessWarning(
                field_name="scenario_type",
                baseline_value=b_scenario,
                current_value=c_scenario,
                message=(
                    f"Baseline was built for scenario '{b_scenario}' but current run is '{c_scenario}'. "
                    "Baseline thresholds may not apply."
                ),
            ))

        # Engine version mismatch (optional field)
        b_ver = baseline_meta.get("engine_version")
        c_ver = current_run_meta.get("engine_version")
        if b_ver and c_ver and b_ver != c_ver:
            warnings.append(StalenessWarning(
                field_name="engine_version",
                baseline_value=b_ver,
                current_value=c_ver,
                message=(
                    f"Engine version changed from '{b_ver}' (baseline) to '{c_ver}' (current). "
                    "Baseline should be regenerated after engine changes."
                ),
            ))

        return StalenessResult(is_stale=len(warnings) > 0, warnings=warnings)
