import pytest

import src.content_semantics.personality as personality_module
from src.content_semantics.personality import (
    get_bravery_bias,
    get_action_style_for_bravery,
    build_personality_for_entity,
)
from src.core.enums import ActionStyle


def test_get_bravery_bias_matches_real_alignment_bucket():
    """Mirrors the sibling test in tests/unit/worldbuilding/test_world_compiler.py --
    confirms the shared module (post-extraction) still resolves real content correctly."""
    assert get_bravery_bias("wild_beast_pack") == 0.35
    assert get_bravery_bias("goblin_warband") == 0.25
    assert get_bravery_bias("hero_guild") == 0.05
    assert get_bravery_bias("merchant_league") == 0.0
    assert get_bravery_bias("nonexistent_faction_xyz") == 0.0


def test_get_action_style_for_bravery_thresholds():
    assert get_action_style_for_bravery(0.9) == ActionStyle.AGGRESSIVE
    assert get_action_style_for_bravery(0.5) == ActionStyle.BALANCED
    assert get_action_style_for_bravery(0.1) == ActionStyle.EVASIVE


def test_build_personality_for_entity_is_deterministic():
    """Same (entity_id, faction_id, seed) must produce bit-identical personality --
    TCK-20260809-WORLDENTITYSPAWNER-ZERO-PERSONALITY's own determinism requirement."""
    p1 = build_personality_for_entity(7, "wild_beast_pack", seed=42)
    p2 = build_personality_for_entity(7, "wild_beast_pack", seed=42)
    assert p1 == p2


def test_build_personality_for_entity_race_correlated():
    """A wild_beast_pack entity's real bravery should be measurably higher than a
    merchant_league entity's, on average -- the real gap this ticket closes."""
    predator_bravery = [
        build_personality_for_entity(eid, "wild_beast_pack", seed=42).bravery
        for eid in range(1, 21)
    ]
    civilian_bravery = [
        build_personality_for_entity(eid, "merchant_league", seed=42).bravery
        for eid in range(1, 21)
    ]
    avg_predator = sum(predator_bravery) / len(predator_bravery)
    avg_civilian = sum(civilian_bravery) / len(civilian_bravery)
    assert avg_predator > avg_civilian + 0.2


def test_build_personality_for_entity_handles_none_faction():
    """Must not crash when faction_id is None (real legacy-guard entities may have no
    faction_id set)."""
    p = build_personality_for_entity(1, None, seed=42)
    assert 0.0 <= p.bravery <= 1.0


def test_personality_bias_config_loads_from_real_data_file():
    """The bias/threshold values are read from data/content/social/personality_bias.yaml, not
    the in-code fallback -- confirms the data-driven path is actually exercised, not silently
    falling back. Moved from tests/unit/worldbuilding/test_world_compiler.py
    (TCK-20260809-WORLDENTITYSPAWNER-ZERO-PERSONALITY) since the underlying config-loading
    logic now lives in this module, shared across both real entity-construction paths."""
    personality_module._personality_bias_cache = None  # force a fresh load
    loaded = personality_module._load_personality_bias_config()
    assert loaded is not personality_module._PERSONALITY_BIAS_FALLBACK
    assert loaded["bravery_bias_by_alignment_bucket"]["wild"] == 0.35


def test_personality_bias_config_falls_back_safely_on_bad_file(monkeypatch, tmp_path):
    """A missing or malformed personality_bias.yaml must never crash entity construction --
    falls back to the in-code default values instead. Moved from
    tests/unit/worldbuilding/test_world_compiler.py (TCK-20260809-WORLDENTITYSPAWNER-ZERO-
    PERSONALITY)."""
    bad_path = tmp_path / "does_not_exist.yaml"
    monkeypatch.setattr(personality_module, "Path", lambda _p: bad_path)
    personality_module._personality_bias_cache = None
    loaded = personality_module._load_personality_bias_config()
    assert loaded == personality_module._PERSONALITY_BIAS_FALLBACK
    personality_module._personality_bias_cache = None  # reset cache so later tests reload the real file
