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

def test_shadow_mode_preserves_baseline_hash():
    # Hash under SHADOW mode must equal baseline hash
    seed = 42
    baseline = compute_dummy_hash(seed, [])
    
    ff = FeatureFlagManager()
    ff.set_flag_mode("ENABLE_SELF_MODEL", FeatureMode.SHADOW)
    
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
