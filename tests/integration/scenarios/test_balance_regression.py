"""
tests/integration/scenarios/test_balance_regression.py

Epic 1.2C — Balance regression test suite.

Anchors the E12A measured baseline (urban_political, seed=42, 100 ticks,
ENABLE_ADVENTURE_ROUTING=ON) so future changes that break combat or scoring
balance are caught automatically.

Ticket: TCK-20260619-E12C-BALANCE-TESTS
Audit:  docs/audits/D04_balance_tuning.md §6
"""
from __future__ import annotations

import pytest
from dataclasses import replace

# ── E12A-measured constants ───────────────────────────────────────────────────
# Source: TCK-20260619-E12A-BALANCE-MEASURE, urban_political seed=42, 100-tick run
# with ENABLE_ADVENTURE_ROUTING=ON.
ATTRITION_CAP = 0.60          # E12A: 46.7% (14/30 dead) — 13.3% headroom above measured
ATTRITION_FLOOR = 0.00        # Non-negative sanity bound
ECONOMIC_GOLD_FLOOR = 0.0     # E12A: 0.0 gold — economic pipeline blocked (routing/nodes)
BLOCKER_FREQUENCY_E12A = 0.0  # E12A: 0.0 — no blocked routes observed
# Scoring formula constants (docs/mechanics/04_strategic_cognition.md §6.4, GATHER_RESOURCE/greed)
CONFIDENCE_BONUS_WEIGHT = 0.15
PERSONALITY_BIAS_WEIGHT = 0.50  # E11C (2026-06-28): raised from 0.25 -- see §6.4 calibration history
BLOCKER_PENALTY = 2.0
SEED = 42
WORLD_ID = "urban_political"
TICKS = 100


# ── Helpers ───────────────────────────────────────────────────────────────────

def _build_kernel(enable_routing: bool = False):
    """Load urban_political and return a ready Kernel."""
    from src.worldbuilding.repository import WorldRepository
    from src.worldbuilding.compiler import WorldCompiler
    from src.engine.kernel import Kernel
    from src.config.profiles import RuntimeProfile, HardwareClass
    from src.platform.rng import DeterministicRNG

    repo = WorldRepository("data/worlds")
    spec = repo.load_world(WORLD_ID)
    state, _ = WorldCompiler.compile(spec, seed=SEED)

    if enable_routing:
        flags = dict(state.feature_flags)
        flags["ENABLE_ADVENTURE_ROUTING"] = 1.0
        state = replace(state, feature_flags=flags)

    profile = RuntimeProfile(
        name="balance-regression",
        hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=2048,
        max_cpu_percent=100.0,
        max_worker_count=1,
        max_queue_depth=2000,
        max_replay_buffer_kb=0,
        max_observability_budget_percent=0.0,
        max_tick_budget_ms=500.0,
    )
    return Kernel(profile=profile, state=state, rng=DeterministicRNG(SEED))


def _make_entity(greed: float = 0.0, bravery: float = 0.5):
    """Build a minimal EntityState for scoring unit tests."""
    from src.core.builder import V2EntityBuilder
    from src.core.state import CombatComponent, BiologicalComponent, PersonalityComponent
    from src.core.self_model import (
        SelfModelBundle,
        SelfAwarenessComponent,
        NeedInterpretationComponent,
        KnowledgeModelComponent,
    )

    b = V2EntityBuilder(1)
    b.replace_combat(CombatComponent(hp=100, max_hp=100, atk=10, def_stat=2))
    b.replace_biological(BiologicalComponent(hunger=0.0, sleep_debt=0.0))
    p = PersonalityComponent(greed=greed, bravery=bravery, sociability=0.0, industry=0.0)
    b.identity(evolution_level=1, personality=p)
    bundle = SelfModelBundle(
        self_awareness=SelfAwarenessComponent(
            perceived_condition={"health": 1.0},
            perceived_weaknesses=(),
        ),
        needs=NeedInterpretationComponent(active_needs={}, dominant_need=None),
        knowledge=KnowledgeModelComponent(unknowns={}),
    )
    b.replace_self_model(bundle)
    return b.build()


# ── Test 1: Combat attrition ──────────────────────────────────────────────────

@pytest.mark.slow
@pytest.mark.integration
def test_combat_attrition_urban_in_band():
    """
    Combat attrition at tick 100 in urban_political must stay below 60%.

    E12A baseline: 46.7% attrition (14/30 dead).
    Cap: 60% (13.3% headroom). Catches combat lethality regressions.
    """
    kernel = _build_kernel(enable_routing=False)
    entity_count_start = sum(
        1 for e in kernel.state.entities.values() if e.combat.alive
    )
    assert entity_count_start > 0, "urban_political must spawn at least 1 entity"

    try:
        for _ in range(TICKS):
            kernel.tick_once()
    finally:
        kernel.shutdown()

    dead_count = sum(1 for e in kernel.state.entities.values() if not e.combat.alive)
    attrition_rate = dead_count / max(1, entity_count_start)

    assert ATTRITION_FLOOR <= attrition_rate < ATTRITION_CAP, (
        f"Combat attrition {attrition_rate:.1%} out of band [{ATTRITION_FLOOR:.0%}, {ATTRITION_CAP:.0%}). "
        f"{dead_count}/{entity_count_start} entities dead at tick {TICKS}. "
        f"E12A baseline was 46.7%. If this regresses above 60%, investigate recent "
        f"combat formula or world content changes in urban_political."
    )


# ── Test 2: Feature flag default ──────────────────────────────────────────────

def test_adventure_routing_defaults_off():
    """
    ENABLE_ADVENTURE_ROUTING must default to FeatureMode.OFF.

    Catches accidental flag enablement in feature_flags.py. If this flag is
    enabled by default, the adventure decision pipeline activates for all
    simulation runs — a deliberate policy change that requires updating
    E12A/E12C baseline measurements.
    """
    from src.domains.optimization.feature_flags import FeatureMode, FeatureFlagManager

    manager = FeatureFlagManager()
    default_val = manager.get_flag_mode("ENABLE_ADVENTURE_ROUTING")
    assert default_val == FeatureMode.OFF, (
        f"ENABLE_ADVENTURE_ROUTING must default to FeatureMode.OFF, got {default_val!r}. "
        "If this is intentional, update ATTRITION_CAP and economic baselines in this file, "
        "and re-run tools/balance_measure.py to establish the new E12A baseline."
    )


# ── Test 3: Blocker penalty (skip — E12B decision) ───────────────────────────

@pytest.mark.skip(
    reason=(
        "E12B decision: blocker_penalty=2.0 kept as-is. "
        "E12A measured blocker_frequency=0.0 (< 5% keep-threshold) — no blocked "
        "routes were scored because urban_political has 0 resource nodes and all "
        "adventure routes are DEFER_WITH_REASON. This test requires: (1) resource "
        "nodes added to urban_political, (2) entity navigation.region_id initialized, "
        "and (3) blocker_frequency > 0.05 observed in a controlled run. "
        "Revisit trigger documented in docs/audits/D04_balance_tuning.md §7 and "
        "docs/mechanics/04_strategic_cognition.md §6.5."
    )
)
def test_blocker_penalty_not_near_binary():
    """
    A minor-blocked high-urgency route should outscore a mediocre unblocked route.

    Design intent: graduated penalty so minor obstacles (gold deficit < 5) don't
    universally discard high-urgency routes. Skipped until infrastructure exists
    to produce meaningful non-DEFER routes in urban_political.
    """
    pass


# ── Test 4: Scoring formula constants ─────────────────────────────────────────

def test_scoring_formula_constants_stable():
    """
    Behavioral regression for AdventureRouteScorer formula constants.

    Verifies: confidence_bonus = confidence × 0.15 (weight 0.15), personality_bias
    for greed on GATHER_RESOURCE = greed × 0.50 (weight 0.50, raised from 0.25 by
    E11C -- see docs/mechanics/04_strategic_cognition.md §6.4), and blocker_penalty
    = 2.0 collapses total score to 0.0 when positive terms sum to ~0.65.

    Does NOT run a simulation — pure unit test of the scorer.
    """
    from src.domains.adventure.schema import AdventureRouteOption, RouteFamily
    from src.domains.adventure.scoring import AdventureRouteScorer

    # Entity with greed=1.0, bravery=0.5 (neutral risk profile), no active needs
    entity = _make_entity(greed=1.0, bravery=0.5)

    # Route: GATHER_RESOURCE, confidence=1.0, zero benefit, zero risk, no blockers.
    # Expected score:
    #   urgency          = 0.0   (no active "gold" or "inventory_space" needs)
    #   benefit          = 0.0
    #   personality_bias = greed(1.0) × 0.50 = 0.50
    #   confidence_bonus = 1.0 × 0.15 = 0.15
    #   risk_penalty     = 0.0 × risk_mult × 0.5 = 0.0
    #   blocker_penalty  = 0.0
    #   total            = 0.65
    route_unblocked = AdventureRouteOption(
        family=RouteFamily.GATHER_RESOURCE,
        score=0.0,
        confidence=1.0,
        expected_benefit=0.0,
        expected_risk=0.0,
        blockers=(),
    )
    scored_unblocked = AdventureRouteScorer.score(entity, route_unblocked)
    expected_score = round(
        PERSONALITY_BIAS_WEIGHT * 1.0 + CONFIDENCE_BONUS_WEIGHT * 1.0, 4
    )  # 0.50 + 0.15 = 0.65
    assert abs(scored_unblocked.score - expected_score) < 0.001, (
        f"Expected score {expected_score} (greed×{PERSONALITY_BIAS_WEIGHT} + "
        f"confidence×{CONFIDENCE_BONUS_WEIGHT}), got {scored_unblocked.score}. "
        "Scoring constant weights may have drifted from documented values in "
        "docs/mechanics/04_strategic_cognition.md §6.4."
    )

    # Same route with a blocker: blocker_penalty=2.0 exceeds 0.40 → clamped to 0.0
    route_blocked = AdventureRouteOption(
        family=RouteFamily.GATHER_RESOURCE,
        score=0.0,
        confidence=1.0,
        expected_benefit=0.0,
        expected_risk=0.0,
        blockers=("missing_gold",),
    )
    scored_blocked = AdventureRouteScorer.score(entity, route_blocked)
    assert scored_blocked.score == 0.0, (
        f"Blocked route with blocker_penalty={BLOCKER_PENALTY} should score 0.0 "
        f"(penalty exceeds max positive terms ~{expected_score}), "
        f"got {scored_blocked.score}. Check blocker_penalty constant in scoring.py."
    )

    # Unblocked must always outscore identical blocked route
    assert scored_unblocked.score > scored_blocked.score, (
        "Unblocked route must outscore an otherwise-identical blocked route. "
        f"Got: unblocked={scored_unblocked.score}, blocked={scored_blocked.score}"
    )
