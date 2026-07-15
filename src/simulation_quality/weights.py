from __future__ import annotations
import os
from typing import Any, Optional, Union
import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.simulation_quality.pillars import PillarId


class DetectionParams(BaseModel):
    model_config = ConfigDict(frozen=True)

    loop_threshold: float
    window_size: int
    max_worst_events: int
    time_gates: dict[str, int]


class ScoringWeights(BaseModel):
    model_config = ConfigDict(frozen=True)

    pillar_rules: dict[str, dict[str, float]]
    grade_thresholds: dict[str, float]
    detection: DetectionParams
    _pillar_weights: dict[str, float] = {}
    _flat_rules: dict[str, float] = {}
    _ambiguous_keys: set[str] = set()

    @model_validator(mode="after")
    def _build_flat_index(self) -> "ScoringWeights":
        flat: dict[str, float] = {}
        seen_in: dict[str, set[str]] = {}
        for pillar_id, pillar_section in self.pillar_rules.items():
            for key, value in pillar_section.items():
                flat[key] = value
                seen_in.setdefault(key, set()).add(pillar_id)
        ambiguous = {key for key, pillars in seen_in.items() if len(pillars) > 1}
        object.__setattr__(self, "_flat_rules", flat)
        object.__setattr__(self, "_ambiguous_keys", ambiguous)
        return self

    def for_pillar(self, pillar_id: Union[str, PillarId]) -> "PillarWeightsView":
        # `PillarId` mixes in `str`, but its `Enum.__str__` override means bare
        # `str(pillar_id)` renders as "PillarId.WORLD", not "WORLD" — `.value` is
        # required to normalize an enum member to its plain pillar-name string.
        key = pillar_id.value if isinstance(pillar_id, PillarId) else str(pillar_id)
        rules = self.pillar_rules.get(key)
        if rules is None:
            raise KeyError(
                f"ScoringWeights.for_pillar: unknown pillar '{key}'. "
                f"Available pillars: {sorted(self.pillar_rules.keys())}"
            )
        return PillarWeightsView(key, rules, self)

    @classmethod
    def load(
        cls,
        weights_path: str,
        grade_path: str,
        detection_path: str,
        profile: str = "default",
    ) -> "ScoringWeights":
        with open(weights_path, "r", encoding="utf-8") as fh:
            raw_weights: dict[str, Any] = yaml.safe_load(fh)

        with open(grade_path, "r", encoding="utf-8") as fh:
            raw_grades: dict[str, Any] = yaml.safe_load(fh)

        with open(detection_path, "r", encoding="utf-8") as fh:
            raw_detection: dict[str, Any] = yaml.safe_load(fh)

        pillar_rules: dict[str, dict[str, float]] = {}
        for pillar_key, rules in raw_weights.items():
            if not isinstance(rules, dict):
                raise ValueError(
                    f"scoring_weights.yaml: pillar '{pillar_key}' must be a mapping of rule_key -> float"
                )
            pillar_rules[str(pillar_key)] = {str(k): float(v) for k, v in rules.items()}

        grade_thresholds: dict[str, float] = {str(k): float(v) for k, v in raw_grades.items()}

        detection = DetectionParams(
            loop_threshold=float(raw_detection["loop_threshold"]),
            window_size=int(raw_detection["window_size"]),
            max_worst_events=int(raw_detection["max_worst_events"]),
            time_gates={str(k): int(v) for k, v in raw_detection.get("time_gates", {}).items()},
        )

        instance = cls(
            pillar_rules=pillar_rules,
            grade_thresholds=grade_thresholds,
            detection=detection,
        )

        profile_weights = cls._load_profile_weights(weights_path, profile)
        object.__setattr__(instance, "_pillar_weights", profile_weights)

        return instance

    @staticmethod
    def _load_profile_weights(weights_path: str, profile: str) -> dict[str, float]:
        profiles_dir = os.path.join(os.path.dirname(weights_path), "profiles")
        profile_path = os.path.join(profiles_dir, f"{profile}.yaml")
        if not os.path.exists(profile_path):
            return {}
        with open(profile_path, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        overrides = data.get("pillar_weights", {}) if data else {}
        return {str(k): float(v) for k, v in overrides.items()}

    def __getitem__(self, key: str) -> float:
        if key in self._ambiguous_keys:
            owning_pillars = sorted(
                pillar_id
                for pillar_id, rules in self.pillar_rules.items()
                if key in rules
            )
            raise KeyError(
                f"ScoringWeights: rule key '{key}' is declared in multiple pillars "
                f"({owning_pillars}) — use ScoringWeights.for_pillar(pillar_id)['{key}'] "
                f"instead of a bare top-level lookup for this key."
            )
        value = self._flat_rules.get(key)
        if value is None:
            raise KeyError(
                f"ScoringWeights: rule key '{key}' not found in any pillar section. "
                f"Available keys: {sorted(self._flat_rules.keys())}"
            )
        return value

    def int_param(self, key: str) -> int:
        try:
            return self.detection.time_gates[key]
        except KeyError:
            raise KeyError(
                f"ScoringWeights.int_param: time gate '{key}' not found in detection_params. "
                f"Available keys: {sorted(self.detection.time_gates.keys())}"
            )

    def pillar_weight(self, pillar_id: str) -> float:
        return self._pillar_weights.get(str(pillar_id), 1.0)


class PillarWeightsView:
    """A pillar-scoped read window onto a `ScoringWeights` instance.

    Returned by `ScoringWeights.for_pillar(pillar_id)`. Reads only from that pillar's own
    `pillar_rules` section, so a rule key declared in more than one pillar section resolves
    to the calling pillar's own declared value rather than colliding with another pillar's.
    """

    def __init__(self, pillar_id: str, rules: dict[str, float], parent: "ScoringWeights") -> None:
        self._pillar_id = pillar_id
        self._rules = rules
        self._parent = parent

    def __getitem__(self, key: str) -> float:
        try:
            return self._rules[key]
        except KeyError:
            raise KeyError(
                f"ScoringWeights: rule key '{key}' not found in pillar '{self._pillar_id}'. "
                f"Available keys for this pillar: {sorted(self._rules.keys())}"
            )

    def int_param(self, key: str) -> int:
        return self._parent.int_param(key)

    def pillar_weight(self, pillar_id: str) -> float:
        return self._parent.pillar_weight(pillar_id)
