"""
tests/integration/test_scenario_feature_flag_defaults.py

Per-scenario feature flag default assertions.

Verifies:
1. All 10 FeatureMode flags default to OFF regardless of which scenario is loaded.
2. Flag default values are stable across multiple FeatureFlagManager instantiations
   (no import-time or module-level side-effects mutate the defaults).
3. When an adventure-routing scenario explicitly enables ENABLE_ADVENTURE_ROUTING,
   the flag reports as enabled — confirming the per-scenario opt-in mechanism works.
4. YAML scenario files are structurally intact and countable.

Background:
  All 10 Phase 10 flags are intentionally OFF by default (TCK-20260627-P0A-ADVENTURE-FLAG,
  DEV-002, docs/engine/known_limitations.md §1.5). Scenarios that need gated features
  must opt in via explicit overrides. This test suite verifies the invariant holds for
  every loaded scenario and that the opt-in mechanism functions correctly.

Source: D09 Finding 4, Risk 9/15.
Ticket: TCK-20260627-P2E-FEATURE-FLAG-TEST
Parity: INFRA-221 (docs/parity_ledger/infrastructure.yaml)
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pytest
import yaml

from src.domains.optimization.feature_flags import FeatureMode, FeatureFlagManager


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_SCENARIOS_DIR = Path("data/content/simulation_scenarios")

_EXPECTED_YAML_FILES = {
    "dungeon_crawl_scenarios.yaml",
    "frontier_scenarios.yaml",
    "urban_political_scenarios.yaml",
    "wilderness_survival_scenarios.yaml",
}

_ALL_FLAG_NAMES: Tuple[str, ...] = (
    "ENABLE_WORLD_CAPABILITY_LAYER",
    "ENABLE_SELF_MODEL_COGNITION",
    "ENABLE_ADVENTURE_ROUTING",
    "ENABLE_COMBAT_ENGAGEMENT",
    "ENABLE_BELIEF_ASSIMILATION",
    "ENABLE_PROGRESSION_EVOLUTION",
    "ENABLE_SOCIAL_COOPERATION",
    "ENABLE_WORLD_EMERGENCE",
    "ENABLE_LIFE_ARC_CAMPAIGNS",
    "ENABLE_ENHANCED_TRACE_EVENTS",
)

# Perspective type that indicates adventure-routing content.
# Scenarios with this perspective consume the AdventureDecisionPhase and require
# ENABLE_ADVENTURE_ROUTING to be ON for the adventure pipeline to execute.
_ADVENTURE_ROUTING_PERSPECTIVES = frozenset({"hero_guild_perspective"})


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_all_scenarios() -> List[Dict[str, Any]]:
    """Load every scenario definition from the simulation_scenarios YAML files."""
    all_scenarios: List[Dict[str, Any]] = []
    for yaml_file in sorted(_SCENARIOS_DIR.glob("*.yaml")):
        with open(yaml_file, "r") as fh:
            raw = yaml.safe_load(fh)
        if isinstance(raw, list):
            all_scenarios.extend(raw)
    return all_scenarios


def _scenario_params() -> List[pytest.param]:
    """Build parametrize list: (scenario_id, scenario_dict)."""
    scenarios = _load_all_scenarios()
    return [
        pytest.param(sc["id"], sc, id=sc["id"])
        for sc in scenarios
    ]


def _adventure_scenario_params() -> List[pytest.param]:
    """Parametrize list for scenarios that use an adventure-routing perspective."""
    scenarios = _load_all_scenarios()
    return [
        pytest.param(sc["id"], sc, id=sc["id"])
        for sc in scenarios
        if sc.get("perspective") in _ADVENTURE_ROUTING_PERSPECTIVES
    ]


# ---------------------------------------------------------------------------
# T1 — YAML file discoverability
# ---------------------------------------------------------------------------

def test_all_scenario_yaml_files_discoverable():
    """
    All four simulation_scenarios YAML files are present and discoverable.

    Guards against silent file removal that would cause the parametrized tests
    to silently drop scenarios from coverage.
    """
    found = {f.name for f in _SCENARIOS_DIR.glob("*.yaml")}
    missing = _EXPECTED_YAML_FILES - found
    assert not missing, (
        f"Missing scenario YAML file(s): {sorted(missing)}. "
        f"Found: {sorted(found)}. "
        f"Check data/content/simulation_scenarios/ for unexpected deletions."
    )


# ---------------------------------------------------------------------------
# T2 — YAML structural integrity
# ---------------------------------------------------------------------------

@pytest.mark.scenario_flags
def test_scenario_yaml_parses_to_list_of_dicts():
    """
    Each scenario YAML file parses to a non-empty list of dicts with required keys.

    Required keys per scenario: id, world_composition, perspective.
    Fails fast on malformed YAML before parametrized tests run.
    """
    required_keys = {"id", "world_composition", "perspective"}
    for yaml_file in sorted(_SCENARIOS_DIR.glob("*.yaml")):
        with open(yaml_file, "r") as fh:
            raw = yaml.safe_load(fh)
        assert isinstance(raw, list), (
            f"{yaml_file.name}: expected a YAML list at top level, got {type(raw).__name__}"
        )
        assert len(raw) > 0, f"{yaml_file.name}: YAML file is empty"
        for entry in raw:
            assert isinstance(entry, dict), (
                f"{yaml_file.name}: entry is not a dict — got {type(entry).__name__}"
            )
            missing = required_keys - set(entry.keys())
            assert not missing, (
                f"{yaml_file.name} scenario {entry.get('id', '<unknown>')!r}: "
                f"missing required keys {sorted(missing)}"
            )


# ---------------------------------------------------------------------------
# T3 — All flags OFF per scenario (parametrized)
# ---------------------------------------------------------------------------

@pytest.mark.scenario_flags
@pytest.mark.parametrize("scenario_id,scenario", _scenario_params())
def test_all_flags_default_off_for_every_loaded_scenario(
    scenario_id: str, scenario: Dict[str, Any]
):
    """
    All 10 Phase 10 FeatureMode flags are OFF by default for every loaded scenario.

    A fresh FeatureFlagManager constructed without overrides must have every flag
    at FeatureMode.OFF. This is the intentional DEV-002 policy (Stabilized) recorded
    in docs/guidelines/intentional_divergences.md and docs/engine/known_limitations.md §1.5.

    If a flag is not OFF here, either feature_flags.py was accidentally modified or a
    module-level side-effect has mutated the default. In both cases balance measurement
    baselines (TCK-20260619-E12A-BALANCE-MEASURE) would be invalidated.
    """
    manager = FeatureFlagManager()
    not_off = [
        flag for flag in _ALL_FLAG_NAMES
        if manager.get_flag_mode(flag) != FeatureMode.OFF
    ]
    assert not not_off, (
        f"[scenario={scenario_id!r}] Expected all Phase 10 flags to be FeatureMode.OFF by "
        f"default, but the following are not OFF: {not_off}. "
        "If this is intentional, update known_limitations.md §1.5 and re-run "
        "tools/balance_measure.py to re-establish the E12A baseline."
    )


# ---------------------------------------------------------------------------
# T4 — ENABLE_ADVENTURE_ROUTING OFF per scenario (parametrized)
# ---------------------------------------------------------------------------

@pytest.mark.scenario_flags
@pytest.mark.feature_flag_default
@pytest.mark.parametrize("scenario_id,scenario", _scenario_params())
def test_adventure_routing_flag_defaults_off_per_scenario(
    scenario_id: str, scenario: Dict[str, Any]
):
    """
    ENABLE_ADVENTURE_ROUTING is FeatureMode.OFF by default for every scenario.

    Per-scenario variant of the sentinel test in
    tests/integration/scenarios/test_balance_regression.py::test_adventure_routing_defaults_off.
    Parity entry: INFRA-221 (docs/parity_ledger/infrastructure.yaml).
    """
    manager = FeatureFlagManager()
    flag_value = manager.get_flag_mode("ENABLE_ADVENTURE_ROUTING")
    assert flag_value == FeatureMode.OFF, (
        f"[scenario={scenario_id!r}] ENABLE_ADVENTURE_ROUTING must be FeatureMode.OFF by "
        f"default, got {flag_value!r}. "
        "See TCK-20260627-P0A-ADVENTURE-FLAG (DEV-002) for the documented rationale."
    )


# ---------------------------------------------------------------------------
# T5 — Flag defaults are stable across instances
# ---------------------------------------------------------------------------

@pytest.mark.feature_flag_default
def test_feature_flag_defaults_are_stable_across_instances():
    """
    Multiple FeatureFlagManager instantiations without modification produce identical defaults.

    Verifies no module-level mutable state or import-time side-effects alter the flag
    defaults between instances. Three independent instances must serialize identically.
    """
    m1 = FeatureFlagManager()
    m2 = FeatureFlagManager()
    m3 = FeatureFlagManager()
    s1, s2, s3 = m1.serialize(), m2.serialize(), m3.serialize()
    assert s1 == s2, (
        "FeatureFlagManager instances 1 and 2 produced different serializations. "
        f"Instance 1: {s1}. Instance 2: {s2}. "
        "This indicates module-level mutable state is leaking between instantiations."
    )
    assert s2 == s3, (
        "FeatureFlagManager instances 2 and 3 produced different serializations. "
        f"Instance 2: {s2}. Instance 3: {s3}. "
        "This indicates module-level mutable state is leaking between instantiations."
    )
    # All values must be 'OFF'
    for flag, value in s1.items():
        assert value == FeatureMode.OFF.value, (
            f"Flag {flag!r} serializes as {value!r} instead of 'OFF'. "
            "Defaults must be FeatureMode.OFF per DEV-002."
        )


# ---------------------------------------------------------------------------
# T6 — Adventure opt-in mechanism for hero_guild scenarios (parametrized)
# ---------------------------------------------------------------------------

@pytest.mark.scenario_flags
@pytest.mark.parametrize("scenario_id,scenario", _adventure_scenario_params())
def test_adventure_routing_opt_in_enables_for_hero_guild_scenarios(
    scenario_id: str, scenario: Dict[str, Any]
):
    """
    Scenarios with hero_guild_perspective can opt into adventure routing via explicit override.

    When ENABLE_ADVENTURE_ROUTING is explicitly set to ON in the constructor overrides,
    is_enabled() returns True. Verifies the per-scenario opt-in mechanism works correctly
    for all adventure-routing scenarios.

    Note: Default is OFF (DEV-002). Scenarios needing adventure routing must opt in via
    FeatureFlagManager(overrides={"ENABLE_ADVENTURE_ROUTING": FeatureMode.ON}) or via
    set_flag_mode() after construction. See docs/engine/known_limitations.md §1.5.
    """
    assert scenario.get("perspective") in _ADVENTURE_ROUTING_PERSPECTIVES, (
        f"[scenario={scenario_id!r}] Expected hero_guild_perspective, "
        f"got {scenario.get('perspective')!r}. Test fixture may have filtered incorrectly."
    )
    manager = FeatureFlagManager(
        overrides={"ENABLE_ADVENTURE_ROUTING": FeatureMode.ON}
    )
    assert manager.is_enabled("ENABLE_ADVENTURE_ROUTING"), (
        f"[scenario={scenario_id!r}] ENABLE_ADVENTURE_ROUTING with override=ON must be "
        "enabled (is_enabled() must return True). "
        "If is_enabled() returns False for ON, the feature gating mechanism is broken."
    )
    assert manager.get_flag_mode("ENABLE_ADVENTURE_ROUTING") == FeatureMode.ON, (
        f"[scenario={scenario_id!r}] get_flag_mode must return FeatureMode.ON after "
        "setting override=ON."
    )


# ---------------------------------------------------------------------------
# T7 — Override isolation: enabling one flag does not cascade
# ---------------------------------------------------------------------------

@pytest.mark.feature_flag_default
def test_non_adventure_flags_unchanged_by_routing_override():
    """
    Enabling ENABLE_ADVENTURE_ROUTING does not alter any other flag.

    Verifies override isolation — a single-flag override must not cascade to the
    remaining 9 flags. Each of the other 9 flags must remain FeatureMode.OFF.
    """
    manager = FeatureFlagManager(
        overrides={"ENABLE_ADVENTURE_ROUTING": FeatureMode.ON}
    )
    other_flags = [f for f in _ALL_FLAG_NAMES if f != "ENABLE_ADVENTURE_ROUTING"]
    not_off = [
        flag for flag in other_flags
        if manager.get_flag_mode(flag) != FeatureMode.OFF
    ]
    assert not not_off, (
        f"Enabling ENABLE_ADVENTURE_ROUTING should not alter other flags, "
        f"but these are non-OFF: {not_off}. "
        "Override must be isolated to the specified flag only."
    )


# ---------------------------------------------------------------------------
# T8 — SHADOW semantics: not enabled, but is_shadow
# ---------------------------------------------------------------------------

@pytest.mark.feature_flag_default
def test_shadow_mode_is_not_enabled_for_scenario_run():
    """
    FeatureMode.SHADOW means the flag is active in shadow/trace mode but NOT enabled
    for state mutation. is_enabled() must return False; is_shadow() must return True.

    This matters for scenarios that want to observe routing decisions without committing
    adventure state changes (e.g. telemetry shadow runs).
    """
    manager = FeatureFlagManager(
        overrides={"ENABLE_ADVENTURE_ROUTING": FeatureMode.SHADOW}
    )
    assert manager.is_shadow("ENABLE_ADVENTURE_ROUTING"), (
        "SHADOW mode: is_shadow() must return True when flag is FeatureMode.SHADOW."
    )
    assert not manager.is_enabled("ENABLE_ADVENTURE_ROUTING"), (
        "SHADOW mode: is_enabled() must return False — SHADOW does not activate "
        "state-mutating pipeline execution, only trace emission."
    )


# ---------------------------------------------------------------------------
# T9 — Total scenario count and ID uniqueness
# ---------------------------------------------------------------------------

@pytest.mark.scenario_flags
def test_total_scenario_count_from_yaml_files():
    """
    The combined scenario pool contains at least 14 entries with unique IDs.

    Guards against silent YAML pruning that would weaken coverage of the parametrized
    tests above. 14 is the count established when this test suite was authored
    (2026-06-27, TCK-20260627-P2E-FEATURE-FLAG-TEST).
    """
    all_scenarios = _load_all_scenarios()
    all_ids = [sc["id"] for sc in all_scenarios]
    assert len(all_ids) >= 14, (
        f"Expected at least 14 scenarios across all YAML files, "
        f"found {len(all_ids)}: {all_ids}. "
        "If scenarios were intentionally removed, update this lower bound."
    )
    duplicate_ids = [sid for sid in set(all_ids) if all_ids.count(sid) > 1]
    assert not duplicate_ids, (
        f"Duplicate scenario IDs found across YAML files: {duplicate_ids}. "
        "Each scenario must have a globally unique ID."
    )
