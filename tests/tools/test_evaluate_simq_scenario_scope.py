"""
Tests for tools/evaluate_simq.py's scenario-scoping logic.

TCK-20260810-SIMQ-EVALUATE-SLOW-TIER-SCOPE-LEAK: `make simq-full-audit-full` chronically timed
out because the default (no --scenario) engine re-run mode ignored tier scoping and re-ran every
key in grade_anchors.json, including the much more expensive SLOW tier (1000t/2000t) --
contradicting the Makefile target's own documented "fast (<=500t) scenarios only" contract.

Groups:
  1. Default (no --scenario, no --dry-run, no --include-slow) excludes >500t keys
  2. --include-slow restores the full key list
  3. --dry-run is never tier-filtered (cheap regardless of tier)
  4. --scenario always wins, regardless of tier or other flags
  5. Unparseable keys are kept, not silently dropped
"""

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.evaluate_simq import _select_scenarios  # noqa: E402


_KEYS = [
    "dungeon_crawl_seed42_200t",
    "dungeon_crawl_seed42_500t",
    "dungeon_crawl_seed42_1000t",
    "dungeon_crawl_seed42_2000t",
    "urban_political_seed123_500t",
]


class TestDefaultScopesToFastTier:
    def test_default_excludes_slow_tier_keys(self):
        result = _select_scenarios(_KEYS, scenario=None, dry_run=False, include_slow=False)
        assert "dungeon_crawl_seed42_1000t" not in result
        assert "dungeon_crawl_seed42_2000t" not in result

    def test_default_includes_fast_tier_keys(self):
        result = _select_scenarios(_KEYS, scenario=None, dry_run=False, include_slow=False)
        assert "dungeon_crawl_seed42_200t" in result
        assert "dungeon_crawl_seed42_500t" in result
        assert "urban_political_seed123_500t" in result

    def test_default_500t_boundary_is_inclusive(self):
        result = _select_scenarios(
            ["x_seed1_500t", "x_seed1_501t"], scenario=None, dry_run=False, include_slow=False
        )
        assert "x_seed1_500t" in result
        assert "x_seed1_501t" not in result


class TestIncludeSlowRestoresFullList:
    def test_include_slow_returns_every_key(self):
        result = _select_scenarios(_KEYS, scenario=None, dry_run=False, include_slow=True)
        assert set(result) == set(_KEYS)


class TestDryRunNeverTierFiltered:
    def test_dry_run_returns_every_key_even_without_include_slow(self):
        result = _select_scenarios(_KEYS, scenario=None, dry_run=True, include_slow=False)
        assert set(result) == set(_KEYS)


class TestScenarioAlwaysWins:
    def test_scenario_overrides_default_scoping(self):
        result = _select_scenarios(
            _KEYS, scenario="dungeon_crawl_seed42_2000t", dry_run=False, include_slow=False
        )
        assert result == ["dungeon_crawl_seed42_2000t"]

    def test_scenario_overrides_dry_run_and_include_slow(self):
        result = _select_scenarios(
            _KEYS, scenario="dungeon_crawl_seed42_200t", dry_run=True, include_slow=True
        )
        assert result == ["dungeon_crawl_seed42_200t"]


class TestUnparseableKeysKept:
    def test_unparseable_key_kept_in_default_fast_mode(self):
        keys = ["dungeon_crawl_seed42_200t", "not_a_valid_run_key_shape"]
        result = _select_scenarios(keys, scenario=None, dry_run=False, include_slow=False)
        assert "not_a_valid_run_key_shape" in result
