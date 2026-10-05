"""DirtySetBuilder must not decide what to mark from object identity.

TCK-20261005-DIRTY-SET-DEDUPES-UPDATES-BY-ID-SO-RECYCLED-ADDRESSES-DROP-WORK: the builder used to skip an entity
update whose ``id()`` it had already seen. ``id()`` is unique only among live objects, so an update allocated at a
recycled address was silently skipped and its entity never marked dirty, which made strategic scheduling
allocation-dependent. Address reuse cannot be forced portably, so the first test makes every ``id()`` collide:
under the old keying the second entity is never marked, under identity-free marking both are.
"""
from src.core import dirty as dirty_module
from src.core.dirty import DirtySetBuilder
from src.core.state import AuthoritativeState
from src.core.updates import EntityUpdate, StateUpdate, StrategicUpdate


def _strategic_update(entity_id: int) -> EntityUpdate:
    return EntityUpdate(entity_id=entity_id, strategic=StrategicUpdate(current_project_id_set=f"p{entity_id}"))


def _state() -> AuthoritativeState:
    return AuthoritativeState(tick=1, seed=42, world_time=1)


def test_every_entity_update_is_marked_even_when_all_ids_collide(monkeypatch):
    # Shadow the builtin inside src.core.dirty only: every object now has the same "address".
    monkeypatch.setattr(dirty_module, "id", lambda _obj: 1, raising=False)
    builder = DirtySetBuilder()

    builder.mark_from_update(_state(), StateUpdate(entity_updates={1: _strategic_update(1), 2: _strategic_update(2)}))

    assert builder.strategic == {1, 2}  # non-empty before comparing; entity 2 was dropped by the old keying


def test_update_seen_on_an_earlier_call_is_marked_again_without_changing_the_result():
    builder = DirtySetBuilder()
    shared = _strategic_update(7)

    builder.mark_from_update(_state(), StateUpdate(entity_updates={7: shared}))
    first = set(builder.strategic)
    builder.mark_from_update(_state(), StateUpdate(entity_updates={7: shared, 8: _strategic_update(8)}))

    assert first == {7}
    assert builder.strategic == {7, 8}


def test_builder_keeps_no_identity_registry():
    # The fix must not trade the bug for retained references: nothing identity-keyed may be stored.
    assert not hasattr(DirtySetBuilder(), "_processed_upd_ids")
