"""
tests/integration/test_world_profile_feature_flag_guardrail.py

Per-world calibration-profile feature-flag/content-field guardrail assertions.

Ticket: TCK-20260704-SIMQ-CORPUS-SCENARIO-FLAG-GUARDRAIL
Source finding: docs/plans/audit_fix_plan.md P2-E ("Feature-gated phases have no
per-scenario default test").

This test closes the calibration-profile half of P2-E. It is distinct from
tests/integration/test_scenario_feature_flag_defaults.py (parity INFRA-221), which
covers the scenario-definition half (data/content/simulation_scenarios/*.yaml,
flag defaults derived from the `perspective` field). This file instead covers
config/simulation_quality/profiles/<world>.yaml — the per-world calibration
profile's optional `feature_flags:` block, applied via
tools/calibrate_simq.py::_load_profile_feature_flags() as `extra_flags` when the
calibration harness invokes the engine. The two subsystems are never merged.

Expected per-world state lives in a checked-in fixture,
tests/simulation_quality/fixtures/expected_world_flag_state.json, mirroring the
existing tests/simulation_quality/fixtures/grade_anchors.json precedent (the
corpus's 17 worlds exceed the ticket's own 15-world hardcode threshold).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Set

import pytest

from tools.calibrate_simq import _resolve_profile, _load_profile_feature_flags


_FIXTURE_PATH = Path("tests/simulation_quality/fixtures/expected_world_flag_state.json")
_WORLDS_DIR = Path("data/worlds")
_GATED_FLAGS = ("ENABLE_ADVENTURE_ROUTING", "ENABLE_BELIEF_ASSIMILATION", "ENABLE_SELF_MODEL_COGNITION")


def _load_fixture() -> Dict[str, Any]:
    with open(_FIXTURE_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def _live_world_names() -> Set[str]:
    return {
        entry.name
        for entry in _WORLDS_DIR.iterdir()
        if entry.is_dir()
    }


_FIXTURE = _load_fixture()


def _world_params() -> List[pytest.param]:
    return [
        pytest.param(name, entry, id=name)
        for name, entry in _FIXTURE["worlds"].items()
    ]


# ---------------------------------------------------------------------------
# T1 — every world resolves to a profile or the default fallback
# ---------------------------------------------------------------------------

@pytest.mark.corpus_flag_guardrail
def test_all_worlds_have_a_resolvable_profile_or_default_fallback():
    """
    Every live world resolves via the real _resolve_profile() to either its own
    profile file or the 'default' fallback, matching the fixture's recorded
    profile_file for that world.
    """
    mismatches = []
    for world_name in sorted(_live_world_names()):
        resolved = _resolve_profile(world_name)
        expected_profile_file = _FIXTURE["worlds"].get(world_name, {}).get("profile_file")
        if resolved == world_name:
            actual_profile_file = f"{world_name}.yaml"
        else:
            actual_profile_file = None
        if actual_profile_file != expected_profile_file:
            mismatches.append(
                f"{world_name}: _resolve_profile() -> {resolved!r} "
                f"(profile_file={actual_profile_file!r}), "
                f"fixture expects profile_file={expected_profile_file!r}"
            )
    assert not mismatches, (
        "Fixture profile_file disagrees with the real _resolve_profile() outcome:\n"
        + "\n".join(mismatches)
    )


# ---------------------------------------------------------------------------
# T2 — resolved flag state matches the fixture, per world
# ---------------------------------------------------------------------------

@pytest.mark.corpus_flag_guardrail
@pytest.mark.parametrize("world_name,entry", _world_params())
def test_flag_state_matches_expected_per_world(world_name: str, entry: Dict[str, Any]):
    """
    _load_profile_feature_flags(_resolve_profile(world_name)) matches the fixture's
    expected ENABLE_ADVENTURE_ROUTING / ENABLE_BELIEF_ASSIMILATION /
    ENABLE_SELF_MODEL_COGNITION state exactly. Absence of a flag key means OFF, per
    FeatureFlagManager's own default.
    """
    resolved = _resolve_profile(world_name)
    flags = _load_profile_feature_flags(resolved)
    for flag in _GATED_FLAGS:
        actual = flags.get(flag, "OFF")
        expected = entry["flags"][flag]
        assert actual == expected, (
            f"[world={world_name!r}] {flag}: expected {expected!r}, got {actual!r} "
            f"(resolved profile={resolved!r})"
        )


# ---------------------------------------------------------------------------
# T3 — AGENCY-DA anti-drift guard
# ---------------------------------------------------------------------------

@pytest.mark.corpus_flag_guardrail
def test_agency_da_anti_drift_guard():
    """
    AGENCY-DA anti-drift guard (TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA): "if any
    calibration world enables ENABLE_ADVENTURE_ROUTING, AGENCY will activate and
    grade anchors must be updated." The 9 originally-non-routing worlds must keep
    ENABLE_ADVENTURE_ROUTING OFF/absent; the 2 purpose-built routing worlds
    (simq_routing_test, hero_guild_routing) must keep it ON. A break here means
    grade anchors are silently stale, not just a flag mismatch.
    """
    non_routing = _FIXTURE["_meta"]["agency_da_non_routing_worlds"]
    for world_name in non_routing:
        flags = _load_profile_feature_flags(_resolve_profile(world_name))
        actual = flags.get("ENABLE_ADVENTURE_ROUTING", "OFF")
        assert actual == "OFF", (
            f"AGENCY-DA anti-drift guard broken: {world_name!r} is a pre-existing "
            f"non-routing world but ENABLE_ADVENTURE_ROUTING resolved to {actual!r}. "
            "AGENCY has silently activated for this world; grade anchors must be "
            "recalibrated before this can ship (TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA)."
        )

    routing = _FIXTURE["_meta"]["agency_da_routing_worlds"]
    for world_name in routing:
        flags = _load_profile_feature_flags(_resolve_profile(world_name))
        actual = flags.get("ENABLE_ADVENTURE_ROUTING", "OFF")
        assert actual == "ON", (
            f"AGENCY-DA anti-drift guard broken: {world_name!r} is a purpose-built "
            f"routing world but ENABLE_ADVENTURE_ROUTING resolved to {actual!r} "
            "instead of 'ON'."
        )


# ---------------------------------------------------------------------------
# T4 — INFORMATION content <-> ENABLE_BELIEF_ASSIMILATION, both directions
# ---------------------------------------------------------------------------

@pytest.mark.corpus_flag_guardrail
@pytest.mark.parametrize("world_name,entry", _world_params())
def test_information_flag_content_pairing_both_directions(world_name: str, entry: Dict[str, Any]):
    """
    information_source_profiles/pending_information_responses seeded <=>
    ENABLE_BELIEF_ASSIMILATION ON. This pair has zero documented exceptions
    (unlike the self-model pair) — holds for all 17 worlds.
    """
    content_seeded = entry["content"]["information_content"]
    flag_on = entry["flags"]["ENABLE_BELIEF_ASSIMILATION"] == "ON"
    if content_seeded and not flag_on:
        pytest.fail(
            f"[world={world_name!r}] INFORMATION content seeded but "
            "ENABLE_BELIEF_ASSIMILATION is OFF — seeding without the flag produces "
            "zero signal."
        )
    if flag_on and not content_seeded:
        pytest.fail(
            f"[world={world_name!r}] ENABLE_BELIEF_ASSIMILATION is ON but no "
            "INFORMATION content is seeded — flag is a no-op for this world."
        )


# ---------------------------------------------------------------------------
# T5 — self-model content <-> ENABLE_SELF_MODEL_COGNITION, both directions,
#      with the one documented urban_political exception
# ---------------------------------------------------------------------------

@pytest.mark.corpus_flag_guardrail
@pytest.mark.parametrize("world_name,entry", _world_params())
def test_self_model_flag_content_pairing_both_directions_with_documented_exception(
    world_name: str, entry: Dict[str, Any]
):
    """
    pending_self_model_information_events seeded <=> ENABLE_SELF_MODEL_COGNITION ON,
    except urban_political, cited to INFRA-259/INFRA-260 (docs/parity_ledger/
    infrastructure.yaml): the field was seeded pre-epic but the flag has never
    shipped ON for this world, by design, verified via a test-scoped override only.
    Any other mismatch not present in the fixture's known_exceptions fails loudly —
    the exception list must not silently grow.
    """
    content_seeded = entry["content"]["self_model_content"]
    flag_on = entry["flags"]["ENABLE_SELF_MODEL_COGNITION"] == "ON"

    exceptions = {
        exc["world"]: exc
        for exc in _FIXTURE["known_exceptions"]["self_model_content_without_flag"]
    }
    if world_name in exceptions:
        exc = exceptions[world_name]
        assert content_seeded is True and flag_on is False, (
            f"[world={world_name!r}] documented exception "
            f"(citation={exc['citation']}) claims content_seeded=True, flag_on=False, "
            f"but actual state is content_seeded={content_seeded!r}, "
            f"flag_on={flag_on!r} — the exception has gone stale and must be "
            "re-verified or removed."
        )
        return

    if content_seeded and not flag_on:
        pytest.fail(
            f"[world={world_name!r}] self-model content seeded but "
            "ENABLE_SELF_MODEL_COGNITION is OFF, and this world is not in the "
            "fixture's known_exceptions allow-list — this is a real, uncited "
            "misconfiguration."
        )
    if flag_on and not content_seeded:
        pytest.fail(
            f"[world={world_name!r}] ENABLE_SELF_MODEL_COGNITION is ON but no "
            "self-model content is seeded — flag is a no-op for this world."
        )


# ---------------------------------------------------------------------------
# T6 — FACTION content has no flag requirement
# ---------------------------------------------------------------------------

@pytest.mark.corpus_flag_guardrail
def test_faction_content_has_no_flag_requirement():
    """
    faction_tension_overrides has no FeatureMode gate at all -- FactionScorer runs
    unconditionally. FACTION-only worlds may correctly have all three gated flags
    OFF. This test exists to stop a future contributor from "fixing" a FACTION-only
    world by adding an unneeded flag.
    """
    faction_only_worlds = [
        name for name, entry in _FIXTURE["worlds"].items()
        if entry["content"]["faction_tension_overrides"]
        and not entry["content"]["information_content"]
        and not entry["content"]["self_model_content"]
    ]
    assert faction_only_worlds, "Expected at least one FACTION-only world in the fixture."
    for world_name in faction_only_worlds:
        entry = _FIXTURE["worlds"][world_name]
        flags = entry["flags"]
        assert flags["ENABLE_ADVENTURE_ROUTING"] == "OFF", (
            f"[world={world_name!r}] FACTION-only world unexpectedly has "
            "ENABLE_ADVENTURE_ROUTING ON in the fixture."
        )
        assert flags["ENABLE_BELIEF_ASSIMILATION"] == "OFF", (
            f"[world={world_name!r}] FACTION-only world unexpectedly has "
            "ENABLE_BELIEF_ASSIMILATION ON in the fixture."
        )
        assert flags["ENABLE_SELF_MODEL_COGNITION"] == "OFF", (
            f"[world={world_name!r}] FACTION-only world unexpectedly has "
            "ENABLE_SELF_MODEL_COGNITION ON in the fixture."
        )


# ---------------------------------------------------------------------------
# T7 — fixture covers every live world exactly
# ---------------------------------------------------------------------------

@pytest.mark.corpus_flag_guardrail
def test_fixture_covers_every_live_world_exactly():
    """
    The fixture's world set matches data/worlds/ exactly. A future 18th world with
    no fixture entry must fail this test immediately instead of silently not being
    covered by the other parametrized tests.
    """
    fixture_worlds = set(_FIXTURE["worlds"].keys())
    live_worlds = _live_world_names()

    missing_from_fixture = live_worlds - fixture_worlds
    stale_in_fixture = fixture_worlds - live_worlds

    assert not missing_from_fixture, (
        f"World(s) present on disk but missing from the fixture (add a fixture "
        f"entry): {sorted(missing_from_fixture)}"
    )
    assert not stale_in_fixture, (
        f"World(s) in the fixture but no longer on disk (stale fixture entry -- "
        f"remove or investigate): {sorted(stale_in_fixture)}"
    )
