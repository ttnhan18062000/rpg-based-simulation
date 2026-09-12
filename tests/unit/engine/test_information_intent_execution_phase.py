"""
tests/unit/engine/test_information_intent_execution_phase.py

Unit tests for InformationIntentExecutionPhase (TCK-20260713-SIMQ-COGNITION-PIPELINE-WIRE):
- executes the ActionIntent routed into EntityUpdate.pending_action_intent this tick.
- leaves EntityUpdate.intent_results (typed for IntentResult) untouched -- Branch B no
  longer ever writes an ActionIntent there (TCK-20260912-ACTIONINTENT-WRONG-TYPE-IN-
  LATEST-INTENT-RESULTS-CRASHES-STRATEGIC-WORK-QUEUE).
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


def test_action_intent_execution_phase_noop_when_no_pending_action_intent():
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


def test_action_intent_execution_phase_executes_pending_action_intent_alongside_real_intent_results():
    actor = _entity(1)
    state = _state([actor])

    real_intent_result = IntentResult(
        transaction_id="tx1", accepted=True, reason=None,
        source_kind="RESOURCE_TRANSFER", source_id=99,
    )
    action_intent = _move_intent(actor.id)
    update = StateUpdate(entity_updates={
        actor.id: EntityUpdate(
            entity_id=actor.id,
            intent_results=[real_intent_result],
            pending_action_intent=action_intent,
        ),
    })

    ActionIntentAdapter.clear_traces()
    InformationIntentExecutionPhase.execute(state, update)
    traces = ActionIntentAdapter.get_traces()
    assert len(traces) == 1
    assert traces[0].actor_id == actor.id
    assert traces[0].intent_kind == "MOVE_TO"


def test_action_intent_execution_phase_clears_pending_action_intent_after_execution():
    """TCK-20260912-ACTIONINTENT-WRONG-TYPE-IN-LATEST-INTENT-RESULTS-CRASHES-STRATEGIC-WORK-QUEUE.

    Branch B now writes its routed ActionIntent to the dedicated pending_action_intent
    field, never to intent_results (typed for IntentResult only) -- so a raw ActionIntent
    can no longer reach entity.identity.latest_intent_results and crash
    StrategicWorkQueue.build() (which reads .accepted unconditionally off every entry, a
    field only real IntentResult objects have) by construction, regardless of whether
    this phase runs. This phase's own job is only to consume and clear the field once
    executed.
    """
    actor = _entity(1)
    state = _state([actor])

    action_intent = _move_intent(actor.id)
    update = StateUpdate(entity_updates={
        actor.id: EntityUpdate(entity_id=actor.id, pending_action_intent=action_intent),
    })

    result = InformationIntentExecutionPhase.execute(state, update)

    assert result.entity_updates[actor.id].pending_action_intent is None


def test_action_intent_execution_phase_leaves_intent_results_untouched():
    actor = _entity(1)
    state = _state([actor])

    real_intent_result = IntentResult(
        transaction_id="tx1", accepted=True, reason=None,
        source_kind="RESOURCE_TRANSFER", source_id=99,
    )
    action_intent = _move_intent(actor.id)
    update = StateUpdate(entity_updates={
        actor.id: EntityUpdate(
            entity_id=actor.id,
            intent_results=[real_intent_result],
            pending_action_intent=action_intent,
        ),
    })

    result = InformationIntentExecutionPhase.execute(state, update)

    surviving = result.entity_updates[actor.id].intent_results
    assert not any(isinstance(r, ActionIntent) for r in surviving), (
        "an ActionIntent must never appear in intent_results -- StrategicWorkQueue.build() "
        "reads .accepted unconditionally off every intent_results entry"
    )
    assert real_intent_result in surviving


def test_action_intent_execution_phase_preserves_deterministic_entity_order():
    entities = [_entity(30), _entity(5), _entity(17)]
    state = _state(entities)

    update = StateUpdate(entity_updates={
        e.id: EntityUpdate(entity_id=e.id, pending_action_intent=_move_intent(e.id))
        for e in entities
    })

    ActionIntentAdapter.clear_traces()
    InformationIntentExecutionPhase.execute(state, update)
    traces = ActionIntentAdapter.get_traces()
    assert [t.actor_id for t in traces] == [5, 17, 30]
