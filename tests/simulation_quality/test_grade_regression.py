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
  0. Anchors are MEASURED UNDER ``audit_mode`` (``evaluate_simq`` and ``calibrate_simq --audit-mode``), so a value does not depend on host speed. Never
     re-anchor from a throttled run. Record them with ``python -m tools.test_architecture.simq_reanchor`` from two isolated audit_mode runs per key that are
     identical on every pillar (a non-identical pair is a determinism finding, not an anchor); it writes the fixture and the before/after table, and the
     change needs an owner ruling and a provenance file (docs/plans/test_architecture/reference/baseline_change_policy.md; the worked record is
     agent-working/stored_artifacts/TCK-20261011-SIMQ-GRADE-ANCHORS-RUN-UNDER-AUDIT-MODE/reanchor_provenance.md). The steps below are the manual equivalent.
  1. Re-run calibration: ``make evaluate-full`` (re-runs the engine for all fast/<=500t
     scenarios and populates ``data/calibration/``; add ``--include-slow`` via
     ``tools/evaluate_simq.py --include-slow`` for the 1000t/2000t anchors too), or
     per-scenario via ``tools/calibrate_simq.py --ticks ... --seed ... --name ...``
     (``make calibrate`` does not exist as a Makefile target -- do not use it)
  2. Inspect new grades/scores in ``data/calibration/<run_key>/quality_report.json``
     (use ``normalized_score``, not ``raw_score``)
  3. Edit ``tests/simulation_quality/fixtures/grade_anchors.json`` with new
     ``{"grade": ..., "score": ...}`` values (a pillar the scorer reports as ``no-data`` is anchored as
     ``{"status": "no-data", "reason": "below_min_events", "min_events": k}``, never with a grade or score; a change of
     status is a moved row that needs an owner ruling, ``simq_reanchor`` writes both shapes)
  4. Run this file to confirm all pass
  5. Commit both fixture and calibration data together

CI note (TCK-20260903-WORLD-COMPILE-REPORT-BASELINE-STALENESS): this file's own anchor
tests only compare against ``data/calibration/`` (gitignored, developer-machine-local) --
they silently ``pytest.skip()`` whenever that directory is absent, which is every real CI
run today (no CI job populates it). The "SimQ grade-anchor drift (informational)" job in
``.github/workflows/test.yml`` runs ``make simq-full-audit-full`` on push-to-main to
actually populate ``data/calibration/`` and surface real drift for human review --
non-blocking by design, since committed anchors can already be behind current `main`
(known drift is tracked, not silently re-accepted as passing).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from tools.test_architecture.simq_pillar_compare import BAND, SCORE, compare_report, parse_anchor, parse_report_pillar

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

GRADE_ORDER = ["F", "D", "C", "B", "A", "S"]  # ascending quality; index distance = band distance

SCORE_TOLERANCE_ABS_FLOOR = 0.05
SCORE_TOLERANCE_REL_PCT = 0.20

# Per-(run_key, pillar) score-tolerance overrides. Empty since TCK-20261011-SIMQ-GRADE-ANCHORS-RUN-UNDER-AUDIT-MODE: the anchors are measured under
# audit_mode, where two isolated runs are identical, so no anchor needs a tolerance widened to absorb host speed. The five widenings that stood here
# (urban_political_seed123_1000t ECONOMY/NARRATIVE/COGNITION/SOCIAL and frontier_marches_seed42_200t NARRATIVE) were each derived from independent
# throttled draws (TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP, TCK-20260716-SIMQ-URBAN-POLITICAL-FULL-PILLAR-SWEEP); their derivation stays in those stored
# artifacts. Add an entry only with a stated audit_mode reason.
SCORE_TOLERANCE_OVERRIDES: dict[tuple[str, str], float] = {}


def _score_tolerance_kwargs(run_key: str, pillar: str) -> dict[str, float]:
    """Return abs_floor override kwargs for _within_score_tolerance, or {} for the
    global default (SCORE_TOLERANCE_ABS_FLOOR/SCORE_TOLERANCE_REL_PCT)."""
    abs_floor = SCORE_TOLERANCE_OVERRIDES.get((run_key, pillar))
    return {"abs_floor": abs_floor} if abs_floor is not None else {}


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "grade_anchors.json"

# Calibration root relative to repo root (tests run from repo root).
_CALIBRATION_ROOT = Path("data/calibration")

FAST_ANCHOR_KEYS = [
    "simq_scale_stress_seed42_seed42_200t",
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
    # new — TCK-20260808-LIFECYCLE-FULL-COVERAGE-WORLD added this anchor entry (grade_anchors.json
    # count 80 -> 81) but never registered it here, so it went ungated until
    # TCK-20260811-ADVENTURE-SHADOW-MIGRATION-GATE's SimQ audit (SIMQ-AUDIT-20260811T111151Z)
    # caught it as an UNCOVERED_ANCHOR_KEY and registered it (fast tier: 200t <= 500t).
    "lifecycle_full_coverage_world_seed42_200t",
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


def _ceiling_note(run_key: str, pillar: str) -> str:
    """The known-ceiling annotation for a score failure (``simq_ceiling``), or ''."""
    import sys as _sys
    from pathlib import Path as _Path

    _sys.path.insert(0, str(_Path(__file__).resolve().parents[2] / "tools"))
    from simq_ceiling import lookup_ceiling  # noqa: E402

    ceiling = lookup_ceiling(run_key, pillar)
    if ceiling is None:
        return ""
    return f" [known {ceiling.ceiling_kind}: {ceiling.reason}" + (f" — {ceiling.since_ticket}" if ceiling.since_ticket else "") + "]"


def _pillar_failures(run_key: str, anchors: dict, report: dict[str, Any]) -> tuple[list[str], list[str], list[str]]:
    """Compare every anchored pillar of ``run_key`` with ``report`` through ``simq_pillar_compare`` (TCK-20261013-SIMQ-NO-DATA-PILLAR-IN-GRADE-REGRESSION).

    Returns ``(band_failures, score_failures, other_failures)``. A pillar missing from the report, a pillar that lost or gained its data, a changed ``min_events``
    and a malformed pillar are ``other_failures``: there is no default grade or score, so none of them can read as a pass. Anchor ok / live ok keeps the band check
    and the score tolerance (with the per-row override) exactly as before. A run with no-data pillars warns, naming them, so no-data cannot grow unseen."""
    import warnings

    verdicts, sets = compare_report(
        run_key, anchors, report, floor_overrides={(run_key, p): v for (k, p), v in SCORE_TOLERANCE_OVERRIDES.items() if k == run_key},
    )
    band, score, other = [], [], []
    for verdict in verdicts:
        if verdict.ok:
            continue
        if verdict.code == BAND:
            band.append(f"  {verdict.message}")
        elif verdict.code == SCORE:
            pillar = verdict.message.split(":", 1)[0]
            score.append(f"  {verdict.message}{_ceiling_note(run_key, pillar)}")
        else:
            other.append(f"  {verdict.message}")
    if sets["anchor_no_data"] or sets["live_no_data"]:
        warnings.warn(f"{run_key}: no-data pillars: anchor={sets['anchor_no_data']} live={sets['live_no_data']}", stacklevel=2)
    return band, score, other


def _assert_pillars(run_key: str, anchors: dict, report: dict[str, Any]) -> None:
    band, score, other = _pillar_failures(run_key, anchors, report)
    assert not other, f"{run_key} — {len(other)} pillar(s) missing, malformed or changed their data status:\n" + "\n".join(other)
    assert not band, f"{run_key} — {len(band)} pillar(s) drifted beyond anchor band:\n" + "\n".join(band)
    assert not score, f"{run_key} — {len(score)} pillar(s) drifted beyond score tolerance:\n" + "\n".join(score)


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

    _assert_pillars(run_key, grade_anchors[run_key], report)


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

    _assert_pillars(run_key, grade_anchors[run_key], report)


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
    calibration — COGNITION anchors at S (self_model_updated fires every tick).

    INFORMATION fires independently of ENABLE_BELIEF_ASSIMILATION: SelfModelUpdatePhase's
    own Knowledge Assimilation step (self_model_phase.py:103-141) is gated only by
    ENABLE_SELF_MODEL_COGNITION and unconditionally assimilates this world's single seeded
    pending_self_model_information_events entry. TCK-20260829-SELFMODEL-PROBE-GRADE-ANCHOR-
    DRIFT-INVESTIGATION confirmed this was the anchor's original assumption error, not a
    regression, and re-anchored INFORMATION to B/0.2 (event_count=1) for this run key
    accordingly."""
    run_key = "urban_political_selfmodel_probe_seed42_200t"
    if run_key not in grade_anchors:
        pytest.skip(f"No anchor entry for {run_key!r} in grade_anchors.json")

    report = _load_calibration_report(run_key)
    if report is None:
        pytest.skip(f"Calibration report not found: data/calibration/{run_key}/quality_report.json")

    _assert_pillars(run_key, grade_anchors[run_key], report)  # a missing or no-data COGNITION fails here, naming it
    assert parse_report_pillar("COGNITION", report["pillars"]["COGNITION"]).grade == "S"


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

    _assert_pillars(run_key, grade_anchors[run_key], report)


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

    Each entry must have exactly 10 pillars, each an anchor of exactly one of two shapes
    (``simq_pillar_compare.parse_anchor``): ``{"grade", "score"}`` (``"status": "ok"`` allowed) with grade in GRADE_ORDER and a numeric
    normalized_score, or ``{"status": "no-data", "reason": "below_min_events", "min_events": k}`` with no grade or score.
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
            parse_anchor(f"{run_key}/{pillar}", value)  # exactly one of the two anchor shapes (ok {grade, score}, or no-data {status, reason, min_events}); raises otherwise

    # Field-confusion guard: catches an implementer wiring raw_score instead of
    # normalized_score into the "score" field (the two differ by an order of magnitude).
    #
    # Re-pointed from hero_guild_routing_seed42_1000t/NARRATIVE (SimQ audit 2026-08-07):
    # that anchor's own S grade was itself a corrupted value — event_extractor.py mislabeled
    # every non-quest AI project start as quest_event before TCK-20260807-QUEST-EVENT-TYPE-
    # FILTER-BUG fixed it, artificially inflating NARRATIVE's quest_active score across the
    # corpus. Re-pointed to urban_political_selfmodel_execution_probe_seed42_200t/COGNITION,
    # a real, unaffected S-grade anchor (raw_score=5579.0 vs normalized_score=27.895 in the
    # live report -- confirmed genuinely distinct, not a coincidental match) so the guard keeps
    # testing its own purpose (catching raw_score/normalized_score field confusion) rather than
    # asserting a value that needed correcting for an unrelated reason.
    guard_run_key = "urban_political_selfmodel_execution_probe_seed42_200t"
    guard_pillar = "COGNITION"
    guard_entry = grade_anchors[guard_run_key][guard_pillar]
    assert guard_entry["grade"] == "S"
    assert guard_entry["score"] > 2.0
    guard_report = _load_calibration_report(guard_run_key)
    if guard_report is None:
        pytest.skip(f"Calibration report not found: data/calibration/{guard_run_key}/quality_report.json")
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

    81 real scenario entries as of TCK-20260808-LIFECYCLE-FULL-COVERAGE-WORLD, which added
    lifecycle_full_coverage_world_seed42_200t (1 new entry, 80 -> 81) — previously 80 as of
    TCK-20260808-SIMQ-LARGE-SCALE-WORLD-VALIDATION, which added
    simq_scale_stress_seed42_seed42_200t (1 new entry, 79 -> 80) — previously 79 as of
    TCK-20260805-SIMQ-CORPUS-QUEST-DENSITY-DECOUPLE, which added
    quest_dense_frontier_seed{42,123,456}_200t (3 new entries, 76 -> 79).
    """
    metadata_keys = {"_note", "_instructions", "_grade_order"}
    scenario_keys = set(grade_anchors.keys()) - metadata_keys
    assert len(scenario_keys) == 81, (
        f"Expected 81 real scenario entries, found {len(scenario_keys)} — "
        "an anchor entry may have been silently dropped or duplicated"
    )


def test_score_tolerance_override_table_is_empty_because_anchors_are_measured_under_audit_mode() -> None:
    """Anti-drift guard (TCK-20261011-SIMQ-GRADE-ANCHORS-RUN-UNDER-AUDIT-MODE): the five throttle-absorbing widenings are gone, because two isolated audit_mode runs
    are identical. An entry may come back only with a stated audit_mode reason, and then this test is changed with it, in review."""
    assert SCORE_TOLERANCE_OVERRIDES == {}
    anchors = json.loads(FIXTURE_PATH.read_text())
    assert _score_tolerance_kwargs(next(iter(k for k in anchors if not k.startswith("_"))), "COGNITION") == {}


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


# ---------------------------------------------------------------------------
# TCK-20261013-SIMQ-NO-DATA-PILLAR-IN-GRADE-REGRESSION: the comparison on synthetic reports (these need no data/calibration, so they run in the blocking suite)
# ---------------------------------------------------------------------------

_ND_ANCHOR = {"status": "no-data", "reason": "below_min_events", "min_events": 3}
_ND_LIVE = {"status": "no-data", "grade": None, "normalized_score": None, "event_count": 1, "min_events": 3, "reason": "below_min_events"}


def test_a_pillar_missing_from_the_report_fails_naming_it_not_reading_as_c() -> None:
    anchors = {"COMBAT": {"grade": "C", "score": 0.0}, "FACTION": {"grade": "C", "score": 0.0}}
    report = {"pillars": {"COMBAT": {"grade": "C", "normalized_score": 0.0}}}
    with pytest.raises(AssertionError, match="FACTION: pillar missing from the report"):
        _assert_pillars("k", anchors, report)


def test_status_less_reports_compare_as_before() -> None:
    anchors = {"COMBAT": {"grade": "B", "score": 1.0}, "FACTION": {"grade": "A", "score": 2.0}}
    ok = {"pillars": {"COMBAT": {"grade": "A", "normalized_score": 1.1}, "FACTION": {"grade": "A", "normalized_score": 2.0}}}
    _assert_pillars("k", anchors, ok)
    band = {"pillars": {"COMBAT": {"grade": "D", "normalized_score": 1.0}, "FACTION": {"grade": "A", "normalized_score": 2.0}}}
    with pytest.raises(AssertionError, match="outside ±1 band"):
        _assert_pillars("k", anchors, band)
    score = {"pillars": {"COMBAT": {"grade": "B", "normalized_score": 1.0}, "FACTION": {"grade": "A", "normalized_score": 3.5}}}
    with pytest.raises(AssertionError, match="outside tolerance"):
        _assert_pillars("k", anchors, score)


def test_no_data_pillars_pass_only_as_still_no_data_and_are_listed() -> None:
    anchors = {"INFORMATION": _ND_ANCHOR, "COMBAT": {"grade": "B", "score": 1.0}}
    good = {"pillars": {"INFORMATION": _ND_LIVE, "COMBAT": {"grade": "B", "normalized_score": 1.0}}}
    with pytest.warns(UserWarning, match=r"no-data pillars: anchor=\['INFORMATION'\] live=\['INFORMATION'\]"):
        _assert_pillars("k", anchors, good)
    lost = {"pillars": {"INFORMATION": {"grade": "B", "normalized_score": 1.0}, "COMBAT": _ND_LIVE}}
    with pytest.raises(AssertionError) as exc:
        _assert_pillars("k", anchors, lost)
    assert "COMBAT: pillar lost its data" in str(exc.value) and "INFORMATION: pillar gained data" in str(exc.value)
    with pytest.raises(AssertionError, match="threshold changed"):
        _assert_pillars("k", {"INFORMATION": _ND_ANCHOR}, {"pillars": {"INFORMATION": {**_ND_LIVE, "min_events": 5}}})
    with pytest.raises(AssertionError, match="no-data must carry no grade or score"):
        _assert_pillars("k", {"INFORMATION": _ND_ANCHOR}, {"pillars": {"INFORMATION": {**_ND_LIVE, "grade": "C"}}})


def test_a_report_with_no_grade_for_an_ok_looking_pillar_is_a_contract_failure_not_a_default() -> None:
    with pytest.raises(AssertionError, match="contract"):
        _assert_pillars("k", {"COMBAT": {"grade": "C", "score": 0.0}}, {"pillars": {"COMBAT": {"normalized_score": 0.0}}})


def test_a_known_ceiling_still_annotates_a_score_failure() -> None:
    _band, score, _other = _pillar_failures("k", {"COMBAT": {"grade": "B", "score": 1.0}}, {"pillars": {"COMBAT": {"grade": "B", "normalized_score": 9.0}}})
    assert score and "outside tolerance of anchor_score=1.0" in score[0]
