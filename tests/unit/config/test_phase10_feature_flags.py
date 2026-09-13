# TDD tests for Phase 10 feature flags
import pytest
from src.domains.optimization.feature_flags import FeatureMode, FeatureFlagManager

# Explicit, named allowlist of flags deliberately cut over to a live "ON" default — each backed
# by a real, validated replacement (not speculative rollout), documented in feature_flags.py's own
# comment block at the flag's definition (TCK-20260807-FEATURE-FLAG-OFF-SHADOW-TEST-STALE).
# Adding a flag here must NOT be done casually — it defeats this test's entire purpose (catching
# *accidental* ON defaults) unless the flag has the same real-cutover backing these two do.
_DELIBERATE_ON_DEFAULT_FLAGS = frozenset({
    "ENABLE_PUSH_EVENT_SHAPERS",         # TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION
    "ENABLE_PUSH_EVENT_SHAPERS_PHASE2",  # TCK-20260806-PUSH-CUTOVER-PHASE2
    "ENABLE_PUSH_EVENT_SHAPERS_QUEST",   # TCK-20260807-QUEST-EVENT-PUSH-MIGRATION
    "ENABLE_PUSH_EVENT_SHAPERS_AGENCY",  # TCK-20260807-COMMITMENT-ABANDONED-PUSH-MIGRATION-GAP / TCK-20260807-REJECTION-CASCADE-TICK-PUSH-MIGRATION-GAP
    "ENABLE_BELIEF_ASSIMILATION",        # TCK-20260824-ROLLOUT-FLAG-DECISIONS -- already ON in real corpus profiles (sandbox_world.yaml, urban_political.yaml)
    "ENABLE_SOCIAL_COOPERATION",         # TCK-20260824-ROLLOUT-FLAG-DECISIONS -- already ON in real corpus profile (urban_political.yaml)
    "ENABLE_GUILD_QUEST_GENERATION",     # TCK-20260912-KNOWLEDGE-INVESTIGATION-LAYER-INERT-NO-FACTS-NO-LEADS -- real before/after SimQ evidence (D-10)
})


def test_all_enhancement_flags_default_to_off_or_shadow():
    manager = FeatureFlagManager()
    # By default, all should be OFF or SHADOW, except the explicit, named, documented exceptions
    # above — a real cutover, not an accidental default.
    for flag in manager.get_all_flags():
        mode = manager.get_flag_mode(flag)
        if flag in _DELIBERATE_ON_DEFAULT_FLAGS:
            assert mode == FeatureMode.ON, (
                f"{flag} is in the deliberate-ON-default allowlist but its actual default is "
                f"{mode} — allowlist entry is now stale, update or remove it."
            )
        else:
            assert mode in (FeatureMode.OFF, FeatureMode.SHADOW)


def test_allowlist_does_not_silently_permit_an_accidental_on_default():
    # Isolated check of the allowlist-gating logic itself (TCK-20260807-FEATURE-FLAG-OFF-SHADOW-
    # TEST-STALE AC2) — a synthetic flag map, not real FeatureFlagManager state, so this can never
    # be satisfied by coincidentally-correct production defaults; it proves the *logic* still
    # rejects a non-allowlisted ON default.
    synthetic_flags = {
        "ENABLE_PUSH_EVENT_SHAPERS": FeatureMode.ON,          # allowlisted — should pass
        "ENABLE_SOME_HYPOTHETICAL_FEATURE": FeatureMode.ON,   # NOT allowlisted — should fail
    }
    failures = [
        flag for flag, mode in synthetic_flags.items()
        if flag not in _DELIBERATE_ON_DEFAULT_FLAGS and mode not in (FeatureMode.OFF, FeatureMode.SHADOW)
    ]
    assert failures == ["ENABLE_SOME_HYPOTHETICAL_FEATURE"]

def test_feature_flag_off_skips_phase():
    manager = FeatureFlagManager()
    manager.set_flag_mode("ENABLE_SELF_MODEL_COGNITION", FeatureMode.OFF)
    assert not manager.is_enabled("ENABLE_SELF_MODEL_COGNITION")
    assert manager.get_flag_mode("ENABLE_SELF_MODEL_COGNITION") == FeatureMode.OFF

def test_feature_flag_shadow_emits_trace_without_state_mutation():
    manager = FeatureFlagManager()
    manager.set_flag_mode("ENABLE_SELF_MODEL_COGNITION", FeatureMode.SHADOW)
    assert manager.is_shadow("ENABLE_SELF_MODEL_COGNITION")
    assert not manager.is_enabled("ENABLE_SELF_MODEL_COGNITION") # Shadow is not ON for state mutation

def test_feature_flag_on_allows_state_update():
    manager = FeatureFlagManager()
    manager.set_flag_mode("ENABLE_SELF_MODEL_COGNITION", FeatureMode.ON)
    assert manager.is_enabled("ENABLE_SELF_MODEL_COGNITION")
    assert not manager.is_shadow("ENABLE_SELF_MODEL_COGNITION")

def test_feature_flag_matrix_is_serialized_in_run_manifest():
    manager = FeatureFlagManager()
    manager.set_flag_mode("ENABLE_SELF_MODEL_COGNITION", FeatureMode.STRICT)
    manifest = manager.serialize()
    assert manifest["ENABLE_SELF_MODEL_COGNITION"] == "STRICT"

def test_new_flag_registered_in_feature_flag_manager():
    manager = FeatureFlagManager()
    assert "ENABLE_INFORMATION_INTENT_EXECUTION" in manager.get_all_flags()
    assert manager.get_flag_mode("ENABLE_INFORMATION_INTENT_EXECUTION") == FeatureMode.OFF
