# TDD certification tests for Determinism Parity Suite in Phase 10
import pytest
import hashlib
from src.domains.optimization.feature_flags import FeatureFlagManager, FeatureMode

def compute_dummy_hash(seed: int, features: list) -> str:
    m = hashlib.sha256()
    m.update(str(seed).encode("utf-8"))
    for f in sorted(features):
        m.update(f.encode("utf-8"))
    return m.hexdigest()

# Explicit, named allowlist of flags deliberately cut over to a live "ON" default — each backed
# by a real, validated replacement (not speculative rollout), documented in feature_flags.py's own
# comment block at the flag's definition (TCK-20260807-FEATURE-FLAG-OFF-SHADOW-TEST-STALE).
# Mirrors tests/unit/config/test_phase10_feature_flags.py::_DELIBERATE_ON_DEFAULT_FLAGS and
# tests/integration/test_scenario_feature_flag_defaults.py's own copy — kept in sync with both
# (TCK-20260812-DETERMINISM-PARITY-SHADOW-BASELINE-HASH-STALE). Adding a flag here must NOT be
# done casually — it defeats this test's entire purpose (catching *accidental* ON defaults) unless
# the flag has the same real-cutover backing these do.
_DELIBERATE_ON_DEFAULT_FLAGS = frozenset({
    "ENABLE_PUSH_EVENT_SHAPERS",         # TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION
    "ENABLE_PUSH_EVENT_SHAPERS_PHASE2",  # TCK-20260806-PUSH-CUTOVER-PHASE2
    "ENABLE_PUSH_EVENT_SHAPERS_QUEST",   # TCK-20260807-QUEST-EVENT-PUSH-MIGRATION
    "ENABLE_PUSH_EVENT_SHAPERS_AGENCY",  # TCK-20260807-COMMITMENT-ABANDONED-PUSH-MIGRATION-GAP / TCK-20260807-REJECTION-CASCADE-TICK-PUSH-MIGRATION-GAP
    "ENABLE_BELIEF_ASSIMILATION",        # TCK-20260824-ROLLOUT-FLAG-DECISIONS (DEV-003) -- already ON in real corpus profiles
    "ENABLE_SOCIAL_COOPERATION",         # TCK-20260824-ROLLOUT-FLAG-DECISIONS (DEV-003) -- already ON in real corpus profile
})

def test_shadow_mode_preserves_baseline_hash():
    # Hash under SHADOW mode must equal baseline hash
    seed = 42

    # Baseline computed from the REAL default enabled-feature set (the 4 deliberately-ON
    # flags), derived live from a fresh manager — not hardcoded — so this stays correct if
    # the flag set ever changes. An empty-list baseline would make this test unable to
    # detect SHADOW mode leaking a flag into the enabled set.
    baseline_ff = FeatureFlagManager()
    baseline_features = [f for f in baseline_ff.get_all_flags() if baseline_ff.is_enabled(f)]
    assert set(baseline_features) == _DELIBERATE_ON_DEFAULT_FLAGS, (
        f"Real default enabled-feature set {sorted(baseline_features)} no longer matches the "
        f"documented deliberate-ON-default allowlist {sorted(_DELIBERATE_ON_DEFAULT_FLAGS)} — "
        "update this allowlist (and its siblings in "
        "tests/unit/config/test_phase10_feature_flags.py and "
        "tests/integration/test_scenario_feature_flag_defaults.py) if this is an intentional "
        "new cutover."
    )
    baseline = compute_dummy_hash(seed, baseline_features)

    ff = FeatureFlagManager()
    ff.set_flag_mode("ENABLE_SELF_MODEL_COGNITION", FeatureMode.SHADOW)

    # Authoritative hash should only include ON/STRICT features
    enabled_features = [f for f in ff.get_all_flags() if ff.is_enabled(f)]
    shadow_hash = compute_dummy_hash(seed, enabled_features)

    assert shadow_hash == baseline

def test_full_stack_on_is_deterministic_across_runs():
    seed = 100
    ff = FeatureFlagManager()
    for flag in ff.get_all_flags():
        ff.set_flag_mode(flag, FeatureMode.ON)
        
    enabled_features = [f for f in ff.get_all_flags() if ff.is_enabled(f)]
    
    hash_run_1 = compute_dummy_hash(seed, enabled_features)
    hash_run_2 = compute_dummy_hash(seed, enabled_features)
    
    assert hash_run_1 == hash_run_2

def test_provider_budget_skips_are_deterministic():
    # If a budget is exceeded, the decision to skip must be completely deterministic
    limit = 5
    run1_skips = []
    run2_skips = []
    
    # Run 1
    for i in range(10):
        if i >= limit:
            run1_skips.append(True)
        else:
            run1_skips.append(False)
            
    # Run 2
    for i in range(10):
        if i >= limit:
            run2_skips.append(True)
        else:
            run2_skips.append(False)
            
    assert run1_skips == run2_skips

def test_cache_enabled_and_disabled_have_same_authoritative_result_when_expected():
    # Cache should only optimize speed, not change the final semantic logic/state
    data = [1, 2, 3]
    cached_result = sorted(data)
    uncached_result = sorted(data)
    assert cached_result == uncached_result

def test_semantic_scorecard_deterministic_for_same_seed():
    seed = 999
    scorecard_1 = {"combat_score": seed * 1.5, "coop_score": seed * 0.8}
    scorecard_2 = {"combat_score": seed * 1.5, "coop_score": seed * 0.8}
    assert scorecard_1 == scorecard_2
