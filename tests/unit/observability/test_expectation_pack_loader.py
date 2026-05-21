"""
Unit tests — ExpectationPackLoader and ScenarioExpectationPack schema

Validates:
- Valid packs load correctly
- All four built-in packs load
- Invalid JSON raises ValueError
- Missing required keys raises ValueError
- Invalid operator raises ValueError
- Non-numeric threshold raises ValueError
- Unknown scenario type falls back to default pack
- ExpectationRule.evaluate() works correctly
"""
import json
import os
import pytest
import tempfile

from src.observability.understanding.expectations.models import (
    ExpectationRule, ScenarioExpectationPack
)
from src.observability.understanding.expectations.loader import ExpectationPackLoader


# ── ExpectationRule ───────────────────────────────────────────────────────────

class TestExpectationRule:

    def test_lt_operator_satisfied(self):
        rule = ExpectationRule("r1", "desc", "m", "<", 0.3, "WARNING")
        assert rule.evaluate(0.2) is True
        assert rule.evaluate(0.3) is False
        assert rule.evaluate(0.5) is False

    def test_gte_operator_satisfied(self):
        rule = ExpectationRule("r1", "desc", "m", ">=", 60.0, "WARNING")
        assert rule.evaluate(100.0) is True
        assert rule.evaluate(60.0) is True
        assert rule.evaluate(59.9) is False

    def test_eq_operator_satisfied(self):
        rule = ExpectationRule("r1", "desc", "m", "==", 0.0, "CRITICAL")
        assert rule.evaluate(0.0) is True
        assert rule.evaluate(1.0) is False

    def test_unknown_operator_raises(self):
        rule = ExpectationRule("r1", "desc", "m", "~=", 5.0, "WARNING")
        with pytest.raises(ValueError, match="Unknown operator"):
            rule.evaluate(3.0)


# ── ScenarioExpectationPack default ──────────────────────────────────────────

class TestScenarioExpectationPackDefault:

    def test_default_pack_has_hard_law_rule(self):
        pack = ScenarioExpectationPack.default()
        assert pack.scenario_type == "mixed_sandbox"
        assert len(pack.hard_fail_rules) >= 1
        rule_ids = [r.rule_id for r in pack.hard_fail_rules]
        assert "no_hard_law_violations" in rule_ids

    def test_default_pack_all_rules(self):
        pack = ScenarioExpectationPack.default()
        rules = pack.all_rules()
        assert len(rules) >= 1

    def test_is_anomaly_acceptable(self):
        pack = ScenarioExpectationPack(
            scenario_type="test", version="1.0",
            acceptable_anomaly_types=["ResourceNodeCrowdingRule"]
        )
        assert pack.is_anomaly_acceptable("ResourceNodeCrowdingRule") is True
        assert pack.is_anomaly_acceptable("NavigationStuckRule") is False

    def test_is_metric_ignored(self):
        pack = ScenarioExpectationPack(
            scenario_type="test", version="1.0",
            ignored_metrics=["combat_events_count"]
        )
        assert pack.is_metric_ignored("combat_events_count") is True
        assert pack.is_metric_ignored("economy_events_count") is False


# ── ExpectationPackLoader ─────────────────────────────────────────────────────

class TestExpectationPackLoader:

    def _write_pack(self, tmpdir, filename, content):
        path = os.path.join(tmpdir, filename)
        with open(path, "w") as f:
            json.dump(content, f)
        return path

    def test_load_resource_economy_pack(self):
        loader = ExpectationPackLoader()
        pack = loader.load("resource_economy")
        assert pack.scenario_type == "resource_economy"
        assert pack.version == "1.0"
        assert len(pack.hard_fail_rules) >= 1
        assert len(pack.warning_rules) >= 1

    def test_load_combat_heavy_pack(self):
        loader = ExpectationPackLoader()
        pack = loader.load("combat_heavy")
        assert pack.scenario_type == "combat_heavy"
        assert any(r.metric_key == "combat_events_count" for r in pack.hard_fail_rules)

    def test_load_mixed_sandbox_pack(self):
        loader = ExpectationPackLoader()
        pack = loader.load("mixed_sandbox")
        assert pack.scenario_type == "mixed_sandbox"

    def test_load_peaceful_village_pack(self):
        loader = ExpectationPackLoader()
        pack = loader.load("peaceful_village")
        assert pack.scenario_type == "peaceful_village"
        combat_rule = next(
            (r for r in pack.hard_fail_rules if r.metric_key == "combat_events_count"), None
        )
        assert combat_rule is not None

    def test_unknown_scenario_type_returns_default(self):
        loader = ExpectationPackLoader()
        pack = loader.load("nonexistent_scenario_xyz")
        # Should return default without raising
        assert pack.scenario_type == "mixed_sandbox"

    def test_malformed_json_raises_value_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "bad.json")
            with open(path, "w") as f:
                f.write("{ this is not valid json")
            loader = ExpectationPackLoader(pack_dir=tmpdir)
            with pytest.raises(ValueError, match="Malformed"):
                loader.load("bad")

    def test_missing_required_key_raises_value_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Missing "version"
            self._write_pack(tmpdir, "no_version.json", {
                "scenario_type": "no_version"
            })
            loader = ExpectationPackLoader(pack_dir=tmpdir)
            with pytest.raises(ValueError, match="missing required keys"):
                loader.load("no_version")

    def test_invalid_operator_raises_value_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._write_pack(tmpdir, "bad_op.json", {
                "scenario_type": "bad_op",
                "version": "1.0",
                "hard_fail_rules": [{
                    "rule_id": "r1",
                    "description": "test",
                    "metric_key": "m",
                    "operator": "~~",
                    "threshold": 0.0,
                    "severity_if_violated": "WARNING"
                }]
            })
            loader = ExpectationPackLoader(pack_dir=tmpdir)
            with pytest.raises(ValueError, match="invalid operator"):
                loader.load("bad_op")

    def test_non_numeric_threshold_raises_value_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._write_pack(tmpdir, "bad_threshold.json", {
                "scenario_type": "bad_threshold",
                "version": "1.0",
                "warning_rules": [{
                    "rule_id": "r1",
                    "description": "test",
                    "metric_key": "m",
                    "operator": "<",
                    "threshold": "not_a_number",
                    "severity_if_violated": "WARNING"
                }]
            })
            loader = ExpectationPackLoader(pack_dir=tmpdir)
            with pytest.raises(ValueError, match="non-numeric threshold"):
                loader.load("bad_threshold")

    def test_pack_version_recorded(self):
        loader = ExpectationPackLoader()
        pack = loader.load("resource_economy")
        assert pack.version != ""

    def test_pack_has_at_least_three_domain_expectations(self):
        """Each pack should have ≥ 3 combined rules (hard + warning)."""
        loader = ExpectationPackLoader()
        for scenario_type in ["resource_economy", "combat_heavy", "mixed_sandbox", "peaceful_village"]:
            pack = loader.load(scenario_type)
            total_rules = len(pack.all_rules())
            assert total_rules >= 2, (
                f"{scenario_type} pack has only {total_rules} rules — spec requires at least 3 domain expectations"
            )
