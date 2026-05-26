# Compliance IDs: OBS-071, OBS-072, OBS-073
from __future__ import annotations
import os
import json
from typing import Optional, Dict
from pydantic import BaseModel, Field, field_validator, model_validator


class ExpectationValue(BaseModel):
    """
    Defines allowed limits and severity if those limits are breached.
    """
    min: Optional[float] = None
    max: Optional[float] = None
    equals: Optional[float] = None
    max_multiplier_from_baseline: Optional[float] = None
    min_multiplier_from_baseline: Optional[float] = None
    severity: str = "WARNING"  # "PASS" | "WARNING" | "FAIL"

    @model_validator(mode="after")
    def validate_bounds(self) -> ExpectationValue:
        fields = [self.min, self.max, self.equals, self.max_multiplier_from_baseline, self.min_multiplier_from_baseline]
        if all(x is None for x in fields):
            raise ValueError(
                "Expectation must define at least one limit (min, max, equals, max_multiplier_from_baseline, min_multiplier_from_baseline)"
            )
        if self.severity not in ("PASS", "WARNING", "FAIL"):
            raise ValueError(f"Invalid severity: {self.severity}")
        return self


class BalanceEnvelope(BaseModel):
    """
    Defines scenario-specific metrics expectations to evaluate against runs and sweeps.
    """
    scenario_name: str
    scenario_type: str
    expectations: Dict[str, ExpectationValue] = Field(default_factory=dict)
    schema_version: str = "1.0"

    @field_validator("scenario_name", "scenario_type")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Must not be empty")
        return v


class BalanceEnvelopeLoader:
    """
    Utility to load, parse, and validate scenario balance envelopes.
    """
    @classmethod
    def load_from_file(cls, path: str) -> BalanceEnvelope:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Balance envelope file not found: {path}")
        with open(path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except Exception as e:
                raise ValueError(f"Invalid JSON in balance envelope: {e}")
        return BalanceEnvelope.model_validate(data)
