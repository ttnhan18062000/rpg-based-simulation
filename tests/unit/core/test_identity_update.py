"""
TCK-20260824-LIFE-STAGE-TRANSITIONS: coverage for IdentityUpdate.life_stage_set.
"""
from src.core.state import LifeStage
from src.core.updates import IdentityUpdate


def test_identity_update_life_stage_set_not_noop():
    """An IdentityUpdate with only life_stage_set populated must not be reported as a no-op --
    otherwise extract_patches() silently discards it before IdentityPatch.apply() ever runs."""
    update = IdentityUpdate(life_stage_set=LifeStage.ELDER)
    assert update.is_noop() is False


def test_identity_update_life_stage_set_merge_last_write_wins():
    base = IdentityUpdate(life_stage_set=LifeStage.CHILD)
    incoming = IdentityUpdate(life_stage_set=LifeStage.ELDER)

    merged = base.merge(incoming)
    assert merged.life_stage_set == LifeStage.ELDER

    preserved = base.merge(IdentityUpdate())
    assert preserved.life_stage_set == LifeStage.CHILD
