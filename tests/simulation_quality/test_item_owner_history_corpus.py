"""Idea 30 (Possessions With History) corpus proof (TCK-20260906-CORPUS-TEST-ZERO-NEW-WORLD-ASSERTIONS).

CORRECTION, found during Investigate: `owner_history: List[str]` accumulates OWNER IDs across
transfers via `ItemInstanceUpdate.owner_history_append` -- it does not, and structurally cannot,
"accumulate all 4 acquired_method values in order" as the ticket's own text describes.
`acquired_method: AcquiredMethod` is set exactly once at `ItemInstanceService.maybe_create_instance()`
construction time and is immutable thereafter -- `ItemInstanceUpdate` (src/core/update_models/
inventory.py:33-49) supports only `owner_history_append`, nothing else. `maybe_create_instance()`'s
own docstring plus a direct grep both confirm zero real production call sites mint or transfer
ItemInstances today (gated behind `ENABLE_ITEM_INSTANCE_HISTORY`, default OFF, never flipped ON by
any real caller) -- this is a fully schema-only, dormant mechanism, a deeper gap than "unscored,"
matching this session's now-repeated "built, not yet visible in play" pattern.

This test proves the real, correct mechanics of the dormant primitive itself: construction with a
real acquired_method (LOOT), then 3 real owner-transfers via the real ApplyPath.apply_partial()
entry point, asserting owner_history accumulates all 4 owner IDs in order -- the actual "history"
the field name promises, not the ticket's own incorrect framing.
"""
from __future__ import annotations

from dataclasses import replace

from src.core.inventory import ItemInstanceService
from src.core.models.inventory import AcquiredMethod
from src.core.state import AuthoritativeState
from src.core.update_models.inventory import ItemInstanceUpdate
from src.core.updates import StateUpdate
from src.engine.apply import ApplyPath


def test_item_instance_owner_history_accumulates_across_real_transfers():
    state = AuthoritativeState(tick=0, seed=1, feature_flags={"ENABLE_ITEM_INSTANCE_HISTORY": "ON"})
    svc = ItemInstanceService(state)

    instance = svc.maybe_create_instance(
        item_id="ancestral_blade", significant=True, owner_entity_id=100,
        tick=0, acquired_method=AcquiredMethod.LOOT, state=state,
    )
    assert instance is not None
    assert instance.acquired_method == AcquiredMethod.LOOT
    assert instance.owner_history == ["100"]

    state = replace(state, item_instances={instance.instance_id: instance})

    for new_owner in ("200", "300", "400"):
        update = StateUpdate(
            item_instance_updates={instance.instance_id: ItemInstanceUpdate(
                instance_id=instance.instance_id, owner_history_append=new_owner,
            )}
        )
        state = ApplyPath.apply_partial(state, update)

    final_instance = state.item_instances[instance.instance_id]
    assert final_instance.owner_history == ["100", "200", "300", "400"], (
        "owner_history must accumulate every real transfer's new owner id in order"
    )
    # acquired_method is immutable at creation -- never flips as ownership changes.
    assert final_instance.acquired_method == AcquiredMethod.LOOT


def test_item_instance_history_disabled_without_the_feature_flag():
    state = AuthoritativeState(tick=0, seed=1)  # ENABLE_ITEM_INSTANCE_HISTORY defaults OFF
    svc = ItemInstanceService(state)

    instance = svc.maybe_create_instance(
        item_id="ancestral_blade", significant=True, owner_entity_id=100,
        tick=0, acquired_method=AcquiredMethod.LOOT, state=state,
    )
    assert instance is None, "maybe_create_instance must no-op when the flag is OFF (the real default)"
