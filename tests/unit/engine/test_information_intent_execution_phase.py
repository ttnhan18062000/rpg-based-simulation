"""
tests/unit/engine/test_information_intent_execution_phase.py

Unit tests for InformationIntentExecutionPhase (TCK-20260713-SIMQ-COGNITION-PIPELINE-WIRE):
- filters out non-ActionIntent entries in intent_results (economy.py/patches.py-shaped
  IntentResult objects sharing the same field must never be treated as ActionIntent).
- iterates entities in sorted-ID order, matching the kernel's determinism law
  (docs/engine/kernel.md line 19).
"""
from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState, CombatComponent, BiologicalComponent, IntentResult
from src.core.updates import EntityUpdate, StateUpdate
from src.engine.intent.action_intent import ActionIntent, ActionIntentAdapter
from src.engine.pipeline_phases.information_intent_execution import InformationIntentExecutionPhase


def _entity(e_id, x=0.0, y=0.0):
    b = V2EntityBuilder(e_id)
    b.replace_combat(CombatComponent(hp=100, max_hp=100, atk=10, def_stat=2))
    b.replace_biological(BiologicalComponent(hunger=0.0, sleep_debt=0.0))
    b.location(x, y)
    return b.build()


def _state(entities) -> AuthoritativeState:
    ent_map = {e.id: e for e in entities}
    return AuthoritativeState(
        tick=1, seed=1, world_time=100, entities=ent_map,
        groups={}, regions={}, resource_nodes={}, buildings={},
        chests={}, ground_items={}, corpses={}, camps={},
        local_scars={}, global_resources={}, town_tiles=(),
        building_tiles=(), terrain=(), home_storage={},
        town_center=(0, 0), periodic_due_ticks={}, work_debt={},
        movement_count=0, maturity=0, last_calamity_tick=0,
        blocked_tiles=(), town_entity_ids=(),
    )


def _move_intent(actor_id: int) -> ActionIntent:
    return ActionIntent(kind="MOVE_TO", actor_id=actor_id, payload={"position": (5.0, 5.0)})


def test_action_intent_execution_phase_filters_non_action_intent_entries():
    actor = _entity(1)
    state = _state([actor])

    real_intent_result = IntentResult(
        transaction_id="tx1", accepted=True, reason=None,
        source_kind="RESOURCE_TRANSFER", source_id=99,
    )
    update = StateUpdate(entity_updates={
        actor.id: EntityUpdate(entity_id=actor.id, intent_results=[real_intent_result]),
    })

    ActionIntentAdapter.clear_traces()
    InformationIntentExecutionPhase.execute(state, update)
    assert ActionIntentAdapter.get_traces() == []


def test_action_intent_execution_phase_only_executes_the_action_intent_entry_in_a_mixed_list():
    actor = _entity(1)
    state = _state([actor])

    real_intent_result = IntentResult(
        transaction_id="tx1", accepted=True, reason=None,
        source_kind="RESOURCE_TRANSFER", source_id=99,
    )
    action_intent = _move_intent(actor.id)
    update = StateUpdate(entity_updates={
        actor.id: EntityUpdate(entity_id=actor.id, intent_results=[real_intent_result, action_intent]),
    })

    ActionIntentAdapter.clear_traces()
    InformationIntentExecutionPhase.execute(state, update)
    traces = ActionIntentAdapter.get_traces()
    assert len(traces) == 1
    assert traces[0].actor_id == actor.id
    assert traces[0].intent_kind == "MOVE_TO"


def test_action_intent_execution_phase_strips_raw_action_intent_after_execution():
    """TCK-20260907-INFORMATION-INTENT-EXECUTION-RESULT-TYPE-MISMATCH regression.

    Before the fix, the raw ActionIntent survived unchanged in the returned
    update's intent_results (EntityUpdate.merge() concatenates additively) and
    later got installed as entity.identity.latest_intent_results --
    StrategicWorkQueue.build() then crashed with AttributeError reading
    .accepted off it (a field only real IntentResult objects have, not
    ActionIntent).
    """
    actor = _entity(1)
    state = _state([actor])

    action_intent = _move_intent(actor.id)
    update = StateUpdate(entity_updates={
        actor.id: EntityUpdate(entity_id=actor.id, intent_results=[action_intent]),
    })

    result = InformationIntentExecutionPhase.execute(state, update)

    surviving = result.entity_updates[actor.id].intent_results
    assert not any(isinstance(r, ActionIntent) for r in surviving), (
        "raw ActionIntent must not survive execution -- StrategicWorkQueue.build() "
        "reads .accepted unconditionally off every intent_results entry"
    )
    for r in surviving:
        assert hasattr(r, "accepted"), "every surviving entry must be a real IntentResult"


def test_action_intent_execution_phase_preserves_real_intent_result_alongside_stripped_action_intent():
    actor = _entity(1)
    state = _state([actor])

    real_intent_result = IntentResult(
        transaction_id="tx1", accepted=True, reason=None,
        source_kind="RESOURCE_TRANSFER", source_id=99,
    )
    action_intent = _move_intent(actor.id)
    update = StateUpdate(entity_updates={
        actor.id: EntityUpdate(entity_id=actor.id, intent_results=[real_intent_result, action_intent]),
    })

    result = InformationIntentExecutionPhase.execute(state, update)

    surviving = result.entity_updates[actor.id].intent_results
    assert not any(isinstance(r, ActionIntent) for r in surviving)
    assert real_intent_result in surviving


def test_action_intent_execution_phase_preserves_deterministic_entity_order():
    entities = [_entity(30), _entity(5), _entity(17)]
    state = _state(entities)

    update = StateUpdate(entity_updates={
        e.id: EntityUpdate(entity_id=e.id, intent_results=[_move_intent(e.id)])
        for e in entities
    })

    ActionIntentAdapter.clear_traces()
    InformationIntentExecutionPhase.execute(state, update)
    traces = ActionIntentAdapter.get_traces()
    assert [t.actor_id for t in traces] == [5, 17, 30]
