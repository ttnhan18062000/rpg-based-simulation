"""
ExpectationPackLoader — Loads scenario expectation packs from JSON files.

Pack files live in `data/expectation_packs/{scenario_type}.json`.
Falls back to the default pack if the requested scenario type is not found.
"""
from __future__ import annotations
import json
import logging
import os
from typing import Optional

from src.observability.understanding.expectations.models import (
    ExpectationRule, ScenarioExpectationPack
)

logger = logging.getLogger(__name__)

# Default search path relative to the project root
DEFAULT_PACK_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "..", "..", "data", "expectation_packs"
)


class ExpectationPackLoader:
    """
    Loads and validates scenario expectation packs from JSON files.

    Usage:
        pack = ExpectationPackLoader().load("resource_economy")
    """

    def __init__(self, pack_dir: Optional[str] = None) -> None:
        self.pack_dir = pack_dir or self._find_pack_dir()

    def _find_pack_dir(self) -> str:
        """Locate data/expectation_packs/ relative to the project root."""
        # Walk up from this file until we find a directory containing data/
        cur = os.path.dirname(os.path.abspath(__file__))
        for _ in range(8):
            candidate = os.path.join(cur, "data", "expectation_packs")
            if os.path.isdir(candidate):
                return candidate
            cur = os.path.dirname(cur)
        # Fallback: return expected path even if it doesn't exist yet
        return os.path.join(os.getcwd(), "data", "expectation_packs")

    def load(self, scenario_type: str) -> ScenarioExpectationPack:
        """
        Load a pack for the given scenario type.
        Falls back to the default pack if not found, logging a warning.
        Raises ValueError if the JSON is malformed.
        """
        pack_path = os.path.join(self.pack_dir, f"{scenario_type}.json")
        if not os.path.exists(pack_path):
            known_scenarios = {"resource_economy", "combat_heavy", "mixed_sandbox", "peaceful_village"}
            if scenario_type in known_scenarios:
                raise FileNotFoundError(
                    f"Required expectation pack not found for known scenario_type={scenario_type!r} "
                    f"at {pack_path}."
                )
            logger.warning(
                f"Expectation pack not found for scenario_type={scenario_type!r} "
                f"at {pack_path}. Using default pack."
            )
            return ScenarioExpectationPack.default()

        try:
            with open(pack_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Malformed expectation pack JSON at {pack_path}: {e}") from e

        return self._parse(data, pack_path)

    def _parse(self, data: dict, source: str) -> ScenarioExpectationPack:
        """Parse and validate a pack dict into a ScenarioExpectationPack."""
        required_keys = {"scenario_type", "version"}
        missing = required_keys - set(data.keys())
        if missing:
            raise ValueError(f"Expectation pack at {source} missing required keys: {missing}")

        hard_fail_rules = [
            self._parse_rule(r, "hard_fail_rules", source)
            for r in data.get("hard_fail_rules", [])
        ]
        warning_rules = [
            self._parse_rule(r, "warning_rules", source)
            for r in data.get("warning_rules", [])
        ]

        return ScenarioExpectationPack(
            scenario_type=data["scenario_type"],
            version=data["version"],
            description=data.get("description", ""),
            hard_fail_rules=hard_fail_rules,
            warning_rules=warning_rules,
            acceptable_anomaly_types=data.get("acceptable_anomaly_types", []),
            ignored_metrics=data.get("ignored_metrics", []),
            required_signals=data.get("required_signals", []),
        )

    def _parse_rule(self, rule_data: dict, section: str, source: str) -> ExpectationRule:
        """Parse and validate a single rule dict."""
        required = {"rule_id", "description", "metric_key", "operator", "threshold", "severity_if_violated"}
        missing = required - set(rule_data.keys())
        if missing:
            raise ValueError(
                f"Expectation rule in {section} at {source} missing keys: {missing}"
            )
        valid_ops = {"<", "<=", ">", ">=", "==", "!="}
        op = rule_data["operator"]
        if op not in valid_ops:
            raise ValueError(
                f"Expectation rule {rule_data['rule_id']!r} has invalid operator {op!r}. "
                f"Must be one of {valid_ops}."
            )
        try:
            threshold = float(rule_data["threshold"])
        except (TypeError, ValueError) as e:
            raise ValueError(
                f"Expectation rule {rule_data['rule_id']!r} has non-numeric threshold: {e}"
            ) from e

        return ExpectationRule(
            rule_id=rule_data["rule_id"],
            description=rule_data["description"],
            metric_key=rule_data["metric_key"],
            operator=op,
            threshold=threshold,
            severity_if_violated=rule_data["severity_if_violated"],
        )
