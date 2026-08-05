"""Grade regression anchors for canonical simulation scenarios.

Tests compare per-pillar grades and scores in committed calibration reports against
anchors stored in tests/simulation_quality/fixtures/grade_anchors.json. Each anchor
entry is ``{"grade": "S", "score": 2.87}``, where ``score`` is the pillar's
``normalized_score`` (not ``raw_score`` — the two differ by an order of magnitude).
Two independent regressions are flagged:

Band tolerance rule (±1 letter):
  anchor=B → accepts A, B, C — fails on D or S
  anchor=A → accepts S, A, B — fails on C or D
  GRADE_ORDER (ascending quality): F < D < C < B < A < S

Score tolerance rule (independent of the letter band):
  abs(actual_score - anchor_score) <= max(SCORE_TOLERANCE_ABS_FLOOR,
                                            SCORE_TOLERANCE_REL_PCT * abs(anchor_score))
  Catches within-band magnitude regressions the letter-only check cannot see (e.g. an
  S-graded pillar's score cut in half but still >2.0, still graded S).

Fast tests (200t / 500t runs) run in the standard suite.
Slow tests (1000t runs) require ``pytest -m slow`` or omit ``-m "not slow"``.

To update anchors after an intentional scoring change:
  1. Re-run calibration: ``make calibrate`` (or per-scenario variant)
  2. Inspect new grades/scores in ``data/calibration/<run_key>/quality_report.json``
     (use ``normalized_score``, not ``raw_score``)
  3. Edit ``tests/simulation_quality/fixtures/grade_anchors.json`` with new
     ``{"grade": ..., "score": ...}`` values
  4. Run this file to confirm all pass
  5. Commit both fixture and calibration data together
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

GRADE_ORDER = ["F", "D", "C", "B", "A", "S"]  # ascending quality; index distance = band distance

SCORE_TOLERANCE_ABS_FLOOR = 0.05
SCORE_TOLERANCE_REL_PCT = 0.20

# Evidence-derived per-(run_key, pillar) score-tolerance overrides for anchors with
# confirmed real-world single-draw variance exceeding the global default width.
# The first two entries' values are reused verbatim from the corresponding
# tests/unit/worldassembly/test_corpus_diversity.py `*_grade_stability` guard's own
# `abs_floor` — see stored_artifacts/TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP/
# repro_sweep.md Section 8 for derivation. Section 8 shows both floors were widened
# against independent single fresh-draw samples (not only 3-trial means: e.g. ECONOMY's
# floor was set after two independent single-draw evaluate_simq.py runs, not a trial
# mean), so no additional single-draw safety multiplier is applied on top of the guards'
# committed value — TCK-20260715-SIMQ-CORPUS-DIVERSITY-SESSION-LOAD-FLAKE investigation.
#
# urban_political_seed123_1000t/NARRATIVE has no corresponding grade_stability guard to
# reuse a floor from (it was never in that anchor's originally-scoped pillar set). Its
# abs_floor=0.3197 is instead derived directly from 6 independent fresh calibration
# draws (3 from TCK-20260715-SIMQ-CORPUS-DIVERSITY-SESSION-LOAD-FLAKE, 3 fresh this
# session) using the same 1.3x max-observed-deviation formula: max deviation 0.2459,
# round(1.3 * 0.2459, 4) = 0.3197. The anchor is NOT re-centered (matches the ECONOMY
# precedent, not the frontier_marches-NARRATIVE re-centered precedent) — see
# staging_artifacts/TCK-20260716-SIMQ-URBAN-POLITICAL-NARRATIVE-TOLERANCE/investigation.md
# for the full 6-draw table and derivation.
#
# urban_political_seed123_1000t/SOCIAL: abs_floor=5.003 is derived from 11 independent
# fresh draws combined across two sessions (3 historical from
# TCK-20260716-SIMQ-URBAN-POLITICAL-NARRATIVE-TOLERANCE, 8 fresh from
# TCK-20260716-SIMQ-URBAN-POLITICAL-FULL-PILLAR-SWEEP), not this latter session's 8 draws
# alone (which alone would show max deviation 3.2135, under the then-and-now-unchanged
# default width of 3.5931). The max deviation across the combined 11 draws is 3.8485,
# from one of the 3 historical draws: round(1.3 * 3.8485, 4) = 5.003. The anchor is NOT
# re-centered (matches the ECONOMY/NARRATIVE precedent on this same anchor) — see
# stored_artifacts/TCK-20260716-SIMQ-URBAN-POLITICAL-FULL-PILLAR-SWEEP/investigation.md
# for the full 8-draw table and combined-evidence derivation.
#
# urban_political_seed123_1000t/COGNITION: abs_floor=2.0435 is derived from 8 independent
# fresh draws this session (TCK-20260716-SIMQ-URBAN-POLITICAL-FULL-PILLAR-SWEEP), max
# observed deviation 1.5719 (draw6): round(1.3 * 1.5719, 4) = 2.0435. The anchor is NOT
# re-centered. This floor is wide relative to the anchor (0.0440) because COGNITION's
# `decision_divergence_detected` event has no dedup gate and can refire every tick
# (src/observability/event_extractor.py:477-496), so the floor bounds this session's
# observed spikes but is not a hard ceiling on the mechanism's worst case — see
# stored_artifacts/TCK-20260716-SIMQ-URBAN-POLITICAL-FULL-PILLAR-SWEEP/investigation.md
# Risks and Open Questions #1 for the full reasoning.
SCORE_TOLERANCE_OVERRIDES: dict[tuple[str, str], float] = {
    ("urban_political_seed123_1000t", "ECONOMY"): 0.2878,
    ("frontier_marches_seed42_200t", "NARRATIVE"): 0.3351,
    ("urban_political_seed123_1000t", "NARRATIVE"): 0.3197,
    ("urban_political_seed123_1000t", "COGNITION"): 2.0435,
    ("urban_political_seed123_1000t", "SOCIAL"): 5.003,
}


def _score_tolerance_kwargs(run_key: str, pillar: str) -> dict[str, float]:
    """Return abs_floor override kwargs for _within_score_tolerance, or {} for the
    global default (SCORE_TOLERANCE_ABS_FLOOR/SCORE_TOLERANCE_REL_PCT)."""
    abs_floor = SCORE_TOLERANCE_OVERRIDES.get((run_key, pillar))
    return {"abs_floor": abs_floor} if abs_floor is not None else {}


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "grade_anchors.json"

# Calibration root relative to repo root (tests run from repo root).
_CALIBRATION_ROOT = Path("data/calibration")

FAST_ANCHOR_KEYS = [
    "sandbox_world_seed42_200t",
    "sandbox_world_seed137_200t",
    "sandbox_world_seed999_200t",
    "dungeon_crawl_seed42_200t",
    "urban_political_seed42_200t",
    "simq_routing_test_seed42_500t",
    # new — simq_routing_test additional seeds
    "simq_routing_test_seed123_500t",
    "simq_routing_test_seed456_500t",
    # new — dungeon_crawl 500t
    "dungeon_crawl_seed42_500t",
    "dungeon_crawl_seed123_500t",
    "dungeon_crawl_seed456_500t",
    # new — urban_political 500t
    "urban_political_seed42_500t",
    "urban_political_seed123_500t",
    "urban_political_seed456_500t",
    # new — TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS: 5 newly-anchored worlds, 3 seeds each
    "frontier_extended_seed42_200t",
    "frontier_extended_seed123_200t",
    "frontier_extended_seed456_200t",
    "frontier_living_world_seed42_200t",
    "frontier_living_world_seed123_200t",
    "frontier_living_world_seed456_200t",
    "wilderness_survival_seed42_200t",
    "wilderness_survival_seed123_200t",
    "wilderness_survival_seed456_200t",
    "highland_traverse_seed42_200t",
    "highland_traverse_seed123_200t",
    "highland_traverse_seed456_200t",
    "swamp_border_world_seed42_200t",
    "swamp_border_world_seed123_200t",
    "swamp_border_world_seed456_200t",
    # new — TCK-20260704-SIMQ-CORPUS-UNIT-WORLDS-FACTION-INFO: 2 unit-tier worlds, 3 seeds each
    "unit_faction_tension_seed42_200t",
    "unit_faction_tension_seed123_200t",
    "unit_faction_tension_seed456_200t",
    "unit_information_source_seed42_200t",
    "unit_information_source_seed123_200t",
    "unit_information_source_seed456_200t",
    # new — TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-SELFMODEL-PILOT: 1 unit-tier world, 3 seeds
    "unit_selfmodel_pilot_seed42_200t",
    "unit_selfmodel_pilot_seed123_200t",
    "unit_selfmodel_pilot_seed456_200t",
    # new — TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY: 1 unit-tier world, 3 seeds, 500t
    "hero_guild_routing_seed42_500t",
    "hero_guild_routing_seed123_500t",
    "hero_guild_routing_seed456_500t",
    # new — TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS: 3 stress-tier worlds, 3 seeds each, 200t
    "crowded_frontier_seed42_200t",
    "crowded_frontier_seed123_200t",
    "crowded_frontier_seed456_200t",
    "resource_dense_basin_seed42_200t",
    "resource_dense_basin_seed123_200t",
    "resource_dense_basin_seed456_200t",
    "frontier_marches_seed42_200t",
    "frontier_marches_seed123_200t",
    "frontier_marches_seed456_200t",
    # new — TCK-20260707-SIMQ-GENERATED-FRONTIER-BASELINE-ANCHORS
    "generated_frontier_3_42_seed42_200t",
    "generated_frontier_3_42_seed123_200t",
    "generated_frontier_3_42_seed456_200t",
    # new — TCK-20260713-SIMQ-SCORE-CEILING-FIX: unit-tier INFORMATION event-density probe,
    # complementary to unit_information_source (3 belief_assimilated events/run instead of 1),
    # added because INFORMATION's positive weight raise alone could not reach grade A on any
    # existing 1-event corpus scenario without a per-event weight large enough to dominate
    # the pillar on its own.
    "unit_information_density_seed42_200t",
    "unit_information_density_seed123_200t",
    "unit_information_density_seed456_200t",
    # new — TCK-20260805-SIMQ-CORPUS-QUEST-DENSITY-DECOUPLE: stress-tier world closing the named
    # scale-diversity gap of no world deliberately decoupling quest-def count from entity count
    # (6 entities, 6 quest_definitions, ratio 1.0 -- beyond the corpus's prior incidental max of
    # 0.636, wilderness_survival, which was not authored for this purpose), 3 seeds, 200t
    "quest_dense_frontier_seed42_200t",
    "quest_dense_frontier_seed123_200t",
    "quest_dense_frontier_seed456_200t",
]

SLOW_ANCHOR_KEYS = [
    "dungeon_crawl_seed42_1000t",
    "sandbox_world_seed42_1000t",
    # new — dungeon_crawl 1000t
    "dungeon_crawl_seed123_1000t",
    "dungeon_crawl_seed456_1000t",
    # new — urban_political 1000t
    "urban_political_seed42_1000t",
    "urban_political_seed123_1000t",
    "urban_political_seed456_1000t",
    # new — dungeon_crawl 2000t
    "dungeon_crawl_seed42_2000t",
    "dungeon_crawl_seed123_2000t",
    "dungeon_crawl_seed456_2000t",
    # new — sandbox_world 2000t
    "sandbox_world_seed42_2000t",
    # new — TCK-20260707-SIMQ-LONGRUN-HOTPILLAR-ANCHORS
    "unit_selfmodel_pilot_seed42_1000t",
    "hero_guild_routing_seed42_1000t",
    "simq_routing_test_seed42_1000t",
    "unit_faction_tension_seed42_1000t",
    "unit_faction_tension_seed42_2000t",
    "urban_political_seed42_2000t",
    # new — TCK-20260707-SIMQ-GENERATED-FRONTIER-BASELINE-ANCHORS
    "generated_frontier_3_42_seed42_1000t",
]

MINIMUM_FAST_ANCHORS = set(FAST_ANCHOR_KEYS)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _within_band(actual: str, anchor: str, tolerance: int = 1) -> bool:
    """Return True if *actual* grade is within *tolerance* positions of *anchor*.

    Uses GRADE_ORDER (ascending quality: F=0, D=1, C=2, B=3, A=4, S=5).
    Both grades must be valid members of GRADE_ORDER; unknown grades return False.
    """
    if actual not in GRADE_ORDER or anchor not in GRADE_ORDER:
        return False
    return abs(GRADE_ORDER.index(actual) - GRADE_ORDER.index(anchor)) <= tolerance


def _within_score_tolerance(
    actual_score: float,
    anchor_score: float,
    abs_floor: float = SCORE_TOLERANCE_ABS_FLOOR,
    rel_pct: float = SCORE_TOLERANCE_REL_PCT,
) -> bool:
    """Return True if *actual_score* is within tolerance of *anchor_score*.

    Passes if the delta is within either the absolute floor or the relative
    percentage of the anchor's magnitude, whichever tolerance is wider — see
    module docstring and investigation.md's trial-pair variance dataset for
    derivation of the default constants.
    """
    return abs(actual_score - anchor_score) <= max(abs_floor, rel_pct * abs(anchor_score))


def _extract_pillar_grades(report: dict[str, Any]) -> dict[str, str]:
    """Extract ``{PILLAR: grade}`` mapping from a quality_report.json dict."""
    return {
        pillar: data["grade"]
        for pillar, data in report.get("pillars", {}).items()
    }


def _extract_pillar_scores(report: dict[str, Any]) -> dict[str, float]:
    """Extract ``{PILLAR: normalized_score}`` mapping from a quality_report.json dict."""
    return {
        pillar: data["normalized_score"]
        for pillar, data in report.get("pillars", {}).items()
    }


def _load_calibration_report(run_key: str) -> dict[str, Any] | None:
    """Load ``data/calibration/{run_key}/quality_report.json``.

    Returns None if the file does not exist (allows pytest.skip downstream).
    """
    path = _CALIBRATION_ROOT / run_key / "quality_report.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def grade_anchors() -> dict[str, Any]:
    """Load the committed grade anchor fixture (module-scoped, loaded once)."""
    return json.loads(FIXTURE_PATH.read_text())


# ---------------------------------------------------------------------------
# Fast anchor tests — 200t / 500t runs (excluded from slow CI mark)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("run_key", FAST_ANCHOR_KEYS)
def test_grade_within_anchor_band(run_key: str, grade_anchors: dict) -> None:
    """Each pillar grade must be within ±1 letter of the committed anchor, and its
    normalized_score must stay within the documented score tolerance — two
    independent checks (see module docstring).

    Reads the current calibration report from data/calibration/{run_key}/quality_report.json.
    Skips if the calibration file is not present (calibration not yet run for this key).
    """
    if run_key not in grade_anchors:
        pytest.skip(f"No anchor entry for {run_key!r} in grade_anchors.json")

    report = _load_calibration_report(run_key)
    if report is None:
        pytest.skip(f"Calibration report not found: data/calibration/{run_key}/quality_report.json")

    anchors = grade_anchors[run_key]
    actual_grades = _extract_pillar_grades(report)
    actual_scores = _extract_pillar_scores(report)

    band_failures: list[str] = []
    score_failures: list[str] = []
    for pillar, anchor in anchors.items():
        anchor_grade = anchor["grade"]
        anchor_score = anchor["score"]
        actual_grade = actual_grades.get(pillar, "C")
        actual_score = actual_scores.get(pillar, 0.0)
        if not _within_band(actual_grade, anchor_grade):
            band_failures.append(
                f"  {pillar}: actual={actual_grade!r} is outside ±1 band of anchor={anchor_grade!r}"
            )
        if not _within_score_tolerance(
            actual_score, anchor_score, **_score_tolerance_kwargs(run_key, pillar)
        ):
            score_failures.append(
                f"  {pillar}: actual_score={actual_score!r} is outside tolerance of "
                f"anchor_score={anchor_score!r}"
            )

    assert not band_failures, (
        f"{run_key} — {len(band_failures)} pillar(s) drifted beyond anchor band:\n"
        + "\n".join(band_failures)
    )
    assert not score_failures, (
        f"{run_key} — {len(score_failures)} pillar(s) drifted beyond score tolerance:\n"
        + "\n".join(score_failures)
    )


# ---------------------------------------------------------------------------
# Slow anchor tests — 1000t long runs
# ---------------------------------------------------------------------------

@pytest.mark.slow
@pytest.mark.parametrize("run_key", SLOW_ANCHOR_KEYS)
def test_grade_within_anchor_band_long_run(run_key: str, grade_anchors: dict) -> None:
    """Long-run anchor check (1000t). Marked slow — excluded from fast CI.

    Each pillar grade must be within ±1 letter of the committed anchor, and its
    normalized_score must stay within the documented score tolerance — two
    independent checks (see module docstring).

    Reads data/calibration/{run_key}/quality_report.json.
    Skips if the calibration file is not present.
    """
    if run_key not in grade_anchors:
        pytest.skip(f"No anchor entry for {run_key!r} in grade_anchors.json")

    report = _load_calibration_report(run_key)
    if report is None:
        pytest.skip(f"Calibration report not found: data/calibration/{run_key}/quality_report.json")

    anchors = grade_anchors[run_key]
    actual_grades = _extract_pillar_grades(report)
    actual_scores = _extract_pillar_scores(report)

    band_failures: list[str] = []
    score_failures: list[str] = []
    for pillar, anchor in anchors.items():
        anchor_grade = anchor["grade"]
        anchor_score = anchor["score"]
        actual_grade = actual_grades.get(pillar, "C")
        actual_score = actual_scores.get(pillar, 0.0)
        if not _within_band(actual_grade, anchor_grade):
            band_failures.append(
                f"  {pillar}: actual={actual_grade!r} is outside ±1 band of anchor={anchor_grade!r}"
            )
        if not _within_score_tolerance(
            actual_score, anchor_score, **_score_tolerance_kwargs(run_key, pillar)
        ):
            score_failures.append(
                f"  {pillar}: actual_score={actual_score!r} is outside tolerance of "
                f"anchor_score={anchor_score!r}"
            )

    assert not band_failures, (
        f"{run_key} — {len(band_failures)} pillar(s) drifted beyond anchor band:\n"
        + "\n".join(band_failures)
    )
    assert not score_failures, (
        f"{run_key} — {len(score_failures)} pillar(s) drifted beyond score tolerance:\n"
        + "\n".join(score_failures)
    )


# ---------------------------------------------------------------------------
# Structural sanity test
# ---------------------------------------------------------------------------

def test_urban_political_selfmodel_cognition_isolated_grade_anchor(grade_anchors: dict) -> None:
    """Grade-anchor probe for the permanent
    config/simulation_quality/profiles/urban_political_selfmodel_probe.yaml fixture
    (formalized by TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE, originally the
    investigation-scoped _investigation_probe_urban_political_selfmodel_only.yaml from
    TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE). This profile isolates
    ENABLE_SELF_MODEL_COGNITION materialization from ENABLE_BELIEF_ASSIMILATION routing
    (the latter stays OFF), so Branch B's InformationBeliefPhase never runs in this
    calibration — COGNITION anchors at S (self_model_updated fires every tick) and
    INFORMATION anchors at C (zero belief_*/route_new_query events), independent of
    this ticket's routing fix (re-measured post-fix, not copied blindly from the pre-fix
    baseline — confirmed unchanged since this profile never activates Branch B)."""
    run_key = "urban_political_selfmodel_probe_seed42_200t"
    if run_key not in grade_anchors:
        pytest.skip(f"No anchor entry for {run_key!r} in grade_anchors.json")

    report = _load_calibration_report(run_key)
    if report is None:
        pytest.skip(f"Calibration report not found: data/calibration/{run_key}/quality_report.json")

    pillars = report.get("pillars", {})
    assert pillars["COGNITION"]["grade"] == "S"
    assert pillars["INFORMATION"]["grade"] == "C"
    assert pillars["INFORMATION"]["event_count"] == 0, (
        "expected zero belief_*/route_new_query events — ENABLE_BELIEF_ASSIMILATION stays "
        "OFF in this probe profile, so InformationBeliefPhase's Branch A/B never run"
    )

    actual_grades = _extract_pillar_grades(report)
    actual_scores = _extract_pillar_scores(report)
    anchors = grade_anchors[run_key]
    band_failures = [
        f"  {pillar}: actual={actual_grades.get(pillar, 'C')!r} outside ±1 band of "
        f"anchor={anchor['grade']!r}"
        for pillar, anchor in anchors.items()
        if not _within_band(actual_grades.get(pillar, "C"), anchor["grade"])
    ]
    score_failures = [
        f"  {pillar}: actual_score={actual_scores.get(pillar, 0.0)!r} outside tolerance of "
        f"anchor_score={anchor['score']!r}"
        for pillar, anchor in anchors.items()
        if not _within_score_tolerance(actual_scores.get(pillar, 0.0), anchor["score"])
    ]
    assert not band_failures, f"{run_key} — pillar(s) drifted beyond anchor band:\n" + "\n".join(band_failures)
    assert not score_failures, f"{run_key} — pillar(s) drifted beyond score tolerance:\n" + "\n".join(score_failures)


def test_urban_political_selfmodel_execution_isolated_grade_anchor(grade_anchors: dict) -> None:
    """Grade-anchor probe for the permanent config/simulation_quality/profiles/
    urban_political_selfmodel_execution_probe.yaml fixture
    (TCK-20260713-SIMQ-COGNITION-PIPELINE-WIRE). This profile turns
    ENABLE_SELF_MODEL_COGNITION, ENABLE_BELIEF_ASSIMILATION, AND the new
    ENABLE_INFORMATION_INTENT_EXECUTION all ON — a superset of the sibling
    urban_political_selfmodel_probe.yaml (which leaves the latter two OFF).

    Honest scope note (verified directly, not assumed): urban_political's real compiled
    state does not have InformationBeliefPhase Branch B route a query within this 200-tick
    window at seed 42 (matches INFRA-266's "does NOT generalize" finding for this specific
    corpus/seed — INFRA-267's fallback fix makes Branch B *correct*, not *guaranteed to
    fire* in every corpus). Confirmed via a direct in-process ActionIntentAdapter.get_traces()
    check against this exact profile/world/seed/tick combination: 0 traces. This anchor test
    therefore proves the new phase does not regress the calibration pipeline (grades/costs
    stable with the phase wired in and gated ON), not that it fires in this specific corpus.
    The deterministic, guaranteed proof that ActionIntentAdapter.execute() fires through a
    real Kernel.tick_once() loop is test_information_intent_execution_fires_through_kernel_tick_once
    below, using a minimal hand-built scenario where Branch B is guaranteed to route."""
    run_key = "urban_political_selfmodel_execution_probe_seed42_200t"
    if run_key not in grade_anchors:
        pytest.skip(f"No anchor entry for {run_key!r} in grade_anchors.json")

    report = _load_calibration_report(run_key)
    if report is None:
        pytest.skip(f"Calibration report not found: data/calibration/{run_key}/quality_report.json")

    actual_grades = _extract_pillar_grades(report)
    actual_scores = _extract_pillar_scores(report)
    anchors = grade_anchors[run_key]
    band_failures = [
        f"  {pillar}: actual={actual_grades.get(pillar, 'C')!r} outside ±1 band of "
        f"anchor={anchor['grade']!r}"
        for pillar, anchor in anchors.items()
        if not _within_band(actual_grades.get(pillar, "C"), anchor["grade"])
    ]
    score_failures = [
        f"  {pillar}: actual_score={actual_scores.get(pillar, 0.0)!r} outside tolerance of "
        f"anchor_score={anchor['score']!r}"
        for pillar, anchor in anchors.items()
        if not _within_score_tolerance(actual_scores.get(pillar, 0.0), anchor["score"])
    ]
    assert not band_failures, f"{run_key} — pillar(s) drifted beyond anchor band:\n" + "\n".join(band_failures)
    assert not score_failures, f"{run_key} — pillar(s) drifted beyond score tolerance:\n" + "\n".join(score_failures)


def test_information_intent_execution_fires_through_kernel_tick_once() -> None:
    """Direct, deterministic proof of Acceptance Criterion 2: with
    ENABLE_INFORMATION_INTENT_EXECUTION deliberately ON (alongside ENABLE_SELF_MODEL_COGNITION
    and ENABLE_BELIEF_ASSIMILATION), ActionIntentAdapter.execute() fires through a real
    Kernel.tick_once() loop — not just direct test-harness invocation of .execute() in
    isolation. Uses a minimal hand-built state (not the urban_political corpus, which does
    not route Branch B within a 200-tick window at seed 42 — see the isolated_grade_anchor
    test above) so routing is guaranteed and this test stays fast/deterministic."""
    from dataclasses import replace as dataclass_replace

    from src.config.profiles import PROD_SMALL
    from src.core.builder import V2EntityBuilder
    from src.core.self_model import KnowledgeModelComponent, SelfModelBundle, UnknownFact
    from src.core.state import AuthoritativeState, BiologicalComponent, CombatComponent, PersonalityComponent
    from src.domains.information.schema import InformationSourceProfile
    from src.domains.optimization.feature_flags import FeatureMode
    from src.engine.intent.action_intent import ActionIntentAdapter
    from src.engine.kernel import Kernel
    from src.platform.rng import DeterministicRNG

    unk = UnknownFact(subject="iron_ore", reason="test_unk", recorded_tick=0)
    b = V2EntityBuilder(1)
    b.replace_combat(CombatComponent(hp=100, max_hp=100, atk=10, def_stat=2))
    b.replace_biological(BiologicalComponent(hunger=0.0, sleep_debt=0.0))
    b.identity(evolution_level=1, personality=PersonalityComponent(greed=0.5, bravery=0.5, sociability=0.5, industry=0.5))
    b.location(0.0, 0.0)
    b.lifecycle(active=True)
    b.replace_self_model(SelfModelBundle(knowledge=KnowledgeModelComponent(unknowns={"iron_ore": unk})))
    actor = b.build()

    state = AuthoritativeState(tick=0, seed=42, entities={actor.id: actor})
    state = dataclass_replace(
        state,
        information_source_profiles=[
            InformationSourceProfile(
                source_id="town_notice_board", source_kind="guide",
                knowledge_scopes=("common_resource_sources",),
                accuracy=0.4, freshness=0.6, cost_gold=0,
            )
        ],
        feature_flags={
            "ENABLE_SELF_MODEL_COGNITION": FeatureMode.ON,
            "ENABLE_BELIEF_ASSIMILATION": FeatureMode.ON,
            "ENABLE_INFORMATION_INTENT_EXECUTION": FeatureMode.ON,
        },
    )

    ActionIntentAdapter.clear_traces()
    kernel = Kernel(profile=PROD_SMALL, state=state, rng=DeterministicRNG(42), flags={"no_frame_pacing": True})
    try:
        kernel.tick_once()
    finally:
        kernel.shutdown()

    traces = ActionIntentAdapter.get_traces()
    assert traces, "expected ActionIntentAdapter.execute() to fire through Kernel.tick_once()"
    assert any(t.actor_id == actor.id and t.intent_kind == "ASK_INFORMATION" for t in traces)


def test_grade_anchor_file_exists_and_valid(grade_anchors: dict) -> None:
    """grade_anchors.json must exist and contain at least all fast anchor run keys.

    Each entry must have exactly 10 pillars, each pillar an object with exactly
    ``{"grade", "score"}`` — grade in GRADE_ORDER, score a numeric normalized_score.
    """
    assert FIXTURE_PATH.exists(), f"Grade anchors fixture missing: {FIXTURE_PATH}"

    missing_keys = MINIMUM_FAST_ANCHORS - set(grade_anchors.keys())
    assert not missing_keys, f"grade_anchors.json missing required run keys: {missing_keys}"

    for run_key in MINIMUM_FAST_ANCHORS:
        entry = grade_anchors[run_key]
        assert len(entry) == 10, (
            f"{run_key}: expected 10 pillars, got {len(entry)}: {list(entry.keys())}"
        )
        for pillar, value in entry.items():
            assert isinstance(value, dict) and set(value.keys()) == {"grade", "score"}, (
                f"{run_key}/{pillar}: expected {{'grade', 'score'}} object, got {value!r}"
            )
            assert value["grade"] in GRADE_ORDER, (
                f"{run_key}/{pillar}: grade {value['grade']!r} not in GRADE_ORDER {GRADE_ORDER}"
            )
            assert isinstance(value["score"], (int, float)), (
                f"{run_key}/{pillar}: score {value['score']!r} is not numeric"
            )

    # Field-confusion guard: catches an implementer wiring raw_score instead of
    # normalized_score into the "score" field (the two differ by an order of magnitude).
    guard_run_key = "hero_guild_routing_seed42_1000t"
    guard_pillar = "NARRATIVE"
    guard_entry = grade_anchors[guard_run_key][guard_pillar]
    assert guard_entry["grade"] == "S"
    assert guard_entry["score"] > 2.0
    guard_report = _load_calibration_report(guard_run_key)
    assert guard_entry["score"] != guard_report["pillars"][guard_pillar]["raw_score"], (
        f"{guard_run_key}/{guard_pillar}: anchor 'score' matches raw_score — "
        "normalized_score should have been persisted, not raw_score"
    )


def test_score_tolerance_catches_within_band_regression() -> None:
    """Before/after proof: a within-band score regression is caught by the new
    score-tolerance check, and would NOT have been caught by the old letter-only check.

    Synthetic anchor: S-graded pillar at normalized_score=4.5. Synthetic live value:
    2.25 (exactly half, still >2.0 so still grade S — same letter band as the anchor).
    """
    anchor_grade, anchor_score = "S", 4.5
    live_grade, live_score = "S", 2.25  # cut in half; still S-band (>2.0)

    # OLD mechanism: letter-band check alone sees no regression.
    assert _within_band(live_grade, anchor_grade) is True

    # NEW mechanism: score-tolerance check catches the magnitude regression.
    assert _within_score_tolerance(live_score, anchor_score) is False
    assert abs(live_score - anchor_score) > max(
        SCORE_TOLERANCE_ABS_FLOOR, SCORE_TOLERANCE_REL_PCT * abs(anchor_score)
    )


def test_grade_order_includes_f_band() -> None:
    """TCK-20260805-SIMQ-GRADE-ORDER-F-BAND-GAP: `_assign_grade()` in quality_report.py has a
    real 6th band, F (everything below the D cutoff) — GRADE_ORDER previously excluded it,
    silently mismatching `_within_band`'s ordinal comparison for any real F occurrence.

    `_within_band` previously returned False unconditionally for F (treated as "unknown grade",
    same code path as a typo) rather than a graded ordinal distance — this is the regression this
    fix closes.
    """
    assert "F" in GRADE_ORDER
    assert GRADE_ORDER.index("F") == 0  # F is the lowest band, ascending quality order

    # D vs F: adjacent bands, distance 1 — within default tolerance.
    assert _within_band("F", "D", tolerance=1) is True
    assert _within_band("D", "F", tolerance=1) is True

    # F vs S: maximum possible distance (5), never within any real tolerance window.
    assert _within_band("F", "S", tolerance=1) is False
    assert abs(GRADE_ORDER.index("F") - GRADE_ORDER.index("S")) == 5


def test_within_band_default_tolerance_unchanged() -> None:
    """Anti-drift guard: `_within_band`'s default tolerance must stay 1 (±1 letter band).

    A silent widening/narrowing of this default would change every anchor's regression
    sensitivity without any other test noticing, since all call sites rely on the default.
    """
    assert _within_band.__defaults__ == (1,)


def test_grade_anchors_entry_count_unchanged(grade_anchors: dict) -> None:
    """Anti-drift guard: the migration (bare string -> {grade, score}) must not silently
    drop or duplicate a scenario entry.

    79 real scenario entries as of TCK-20260805-SIMQ-CORPUS-QUEST-DENSITY-DECOUPLE, which
    added quest_dense_frontier_seed{42,123,456}_200t (3 new entries, 76 -> 79).
    """
    metadata_keys = {"_note", "_instructions", "_grade_order"}
    scenario_keys = set(grade_anchors.keys()) - metadata_keys
    assert len(scenario_keys) == 79, (
        f"Expected 79 real scenario entries, found {len(scenario_keys)} — "
        "an anchor entry may have been silently dropped or duplicated"
    )


def test_score_tolerance_override_table_scoped_to_named_pillars() -> None:
    """Anti-drift guard: the override table contains exactly the 5 evidence-derived
    entries and each entry widens -- never narrows -- the tolerance relative to the
    global default for that anchor's committed score."""
    assert set(SCORE_TOLERANCE_OVERRIDES.keys()) == {
        ("urban_political_seed123_1000t", "ECONOMY"),
        ("frontier_marches_seed42_200t", "NARRATIVE"),
        ("urban_political_seed123_1000t", "NARRATIVE"),
        ("urban_political_seed123_1000t", "COGNITION"),
        ("urban_political_seed123_1000t", "SOCIAL"),
    }
    anchors = json.loads(FIXTURE_PATH.read_text())
    for (run_key, pillar), abs_floor in SCORE_TOLERANCE_OVERRIDES.items():
        anchor_score = anchors[run_key][pillar]["score"]
        default_width = max(
            SCORE_TOLERANCE_ABS_FLOOR, SCORE_TOLERANCE_REL_PCT * abs(anchor_score)
        )
        assert abs_floor > default_width, (
            f"{run_key}/{pillar}: override abs_floor {abs_floor} does not widen the "
            f"default tolerance {default_width}"
        )


def test_score_tolerance_overrides_do_not_affect_unlisted_anchors(grade_anchors: dict) -> None:
    """Anti-drift guard: for every (run_key, pillar) NOT in SCORE_TOLERANCE_OVERRIDES
    (including urban_political_seed123_1000t/COMBAT), the lookup helper must fall through
    to the global defaults -- byte-identical to calling _within_score_tolerance with no
    kwargs at all."""
    checked = 0
    for run_key, anchors in grade_anchors.items():
        for pillar in anchors:
            if (run_key, pillar) in SCORE_TOLERANCE_OVERRIDES:
                continue
            assert _score_tolerance_kwargs(run_key, pillar) == {}, (
                f"{run_key}/{pillar} unexpectedly has a tolerance override"
            )
            checked += 1
    assert checked > 0
