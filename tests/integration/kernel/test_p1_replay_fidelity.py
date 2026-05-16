from dataclasses import replace

from src.core.builder import V2EntityBuilder
from src.core.models.inventory import ItemStack
from src.core.state import AuthoritativeState, ResourceNodeState
from src.core.strategic import (
    LeadCertainty,
    LeadState,
    ProjectState,
    ProjectStatus,
)
from src.core.updates import (
    EntityUpdate,
    StateUpdate,
)
from src.core.state import IntentResult
from src.core.update_models.resources import ResourceTransferIntent
from src.engine.apply import ApplyPath
from src.engine.pipeline import AuthoritativeApplyPipeline
from src.systems.strategic_systems.intelligence import StrategicIntelligenceSystem
from src.systems.strategic_systems.detour import DetourSuggestionSystem


def replace_entity(state: AuthoritativeState, entity_id: int, updated_entity):
    """
    Return a new AuthoritativeState with one entity replaced.

    AuthoritativeState.entities is intentionally read-only. Tests must not
    mutate it directly with:

        state.entities[entity_id] = updated_entity

    because that bypasses the same immutability law used by the runtime.

    This helper keeps tests aligned with the current V2 state model.
    """
    return replace(
        state,
        entities={
            **dict(state.entities),
            entity_id: updated_entity,
        },
    )


def create_mock_entity(entity_id: int, pos: tuple[float, float] = (0.0, 0.0)):
    """
    Build a valid V2 entity for replay-fidelity tests.

    V2 model note:
        EntityState no longer accepts legacy top-level fields such as:
            - position
            - readiness
            - active

        These now live in components:
            - navigation.position
            - combat.readiness
            - lifecycle.active
    """
    from src.core.enums import EntityRole, Faction

    return (
        V2EntityBuilder(entity_id)
        .kind("ACTOR")
        .location(float(pos[0]), float(pos[1]))
        .identity(
            faction=Faction.HERO_GUILD,
            role=EntityRole.HERO,
        )
        .combat(
            hp=100,
            max_hp=100,
            atk=10,
            attack_range=1,
            alive=True,
            readiness=100.0,
        )
        .inventory(
            max_slots=10,
            max_weight=100.0,
        )
        .strategic()
        .task()
        .lifecycle(active=True)
        .build()
    )


def test_event_level_replay_fidelity():
    """
    Law:
        Replaying identical seeds and identical inputs must produce identical
        event sequences and identical strategic state.

    Scope:
        This test verifies deterministic replay fidelity for:
            - resource transaction trace
            - latest intent results
            - blocker inference
            - strategic detour/project state

    Important V2 state rule:
        AuthoritativeState.entities is read-only. The test must update state
        through dataclass replacement, not direct dictionary mutation.

    Fraud this catches:
        - replay trace depends on non-deterministic ordering
        - StrategicUpdate generation is not deterministic
        - IntentResult generation is not deterministic
        - blocker inference produces unstable project/detour state
        - tests accidentally bypass AuthoritativeState immutability
    """

    # ------------------------------------------------------------------
    # 1. Initial state setup
    # ------------------------------------------------------------------
    e1 = create_mock_entity(1, pos=(0.0, 0.0))

    node = ResourceNodeState(
        id=10,
        kind="iron_ore",
        position=(0.0, 0.0),
        remaining_charges=10,
        max_charges=10,
        yields_item="iron_ore",
        required_ticks=1,
    )

    state = AuthoritativeState(
        tick=1,
        seed=42,
        entities={1: e1},
        resource_nodes={10: node},
    )
    
    town_lead = LeadState(
        id="town_info",
        kind="location",
        subject="town",
        detail="(10, 10)",
        certainty=LeadCertainty.PRECISE,
    )

    p_harvest = ProjectState(
        id="p_harvest",
        kind="harvesting",
        status=ProjectStatus.ACTIVE,
    )

    entity_with_project = replace(
        state.entities[1],
        strategic=replace(
            state.entities[1].strategic,
            leads={"town": town_lead},
            projects={"p_harvest": p_harvest},
            current_project_id="p_harvest",
        ),
    )

    state = replace_entity(
        state,
        1,
        entity_with_project,
    )

    # ------------------------------------------------------------------
    # 2. Tick 1: successful harvest
    # ------------------------------------------------------------------
    intent1 = ResourceTransferIntent(
        source_id=10,
        source_kind="NODE",
        items_add=[ItemStack("iron_ore", 1)],
        transfer_kind="HARVEST",
    )

    # Fill 9/10 slots. After the successful Tick 1 harvest, inventory becomes
    # full. Tick 2 can then deterministically fail with INVENTORY_FULL.
    entity_with_nearly_full_inventory = replace(
        state.entities[1],
        inventory=replace(
            state.entities[1].inventory,
            items=[
                ItemStack("junk", 1)
                for _ in range(9)
            ],
        ),
    )

    state = replace_entity(
        state,
        1,
        entity_with_nearly_full_inventory,
    )

    upd1 = StateUpdate(
        entity_updates={
            1: EntityUpdate(
                entity_id=1,
                resource_transfers=[intent1],
            )
        }
    )

    refined1 = AuthoritativeApplyPipeline.refine(state, upd1)

    state_v2 = ApplyPath.apply_generation(
        state,
        refined1,
        next_tick=2,
    )

    trace1 = list(refined1.transaction_trace)
    intent_res1 = state_v2.entities[1].identity.latest_intent_results

    # ------------------------------------------------------------------
    # 3. Tick 2: failed harvest creates blocker and strategic detour
    # ------------------------------------------------------------------
    failure = IntentResult(
        transaction_id="t2",
        accepted=False,
        reason="INVENTORY_FULL",
        source_kind="NODE",
        source_id=10,
    )
    
    identity_with_failure = replace(
        state_v2.entities[1].identity,
        latest_intent_results=[failure],
    )

    entity_with_failure = replace(
        state_v2.entities[1],
        identity=identity_with_failure,
    )

    state_v2 = replace_entity(
        state_v2,
        1,
        entity_with_failure,
    )
    
    current_project = state_v2.entities[1].strategic.projects[
        state_v2.entities[1].strategic.current_project_id
    ]

    upd_blocker = StrategicIntelligenceSystem.infer_blockers(
        entity=state_v2.entities[1],
        last_task="ENTITY_ACT",
        last_payload={
            "action": "INTERACT",
            "target_id": 10,
        },
        current_project=current_project,
    )
    
    assert "blocker_inventory_full" in {
        blocker.id for blocker in upd_blocker.blockers_add_or_update
    }

    entity_with_blocker = replace(
        state_v2.entities[1],
        strategic=replace(
            state_v2.entities[1].strategic,
            blockers={
                blocker.id: blocker
                for blocker in upd_blocker.blockers_add_or_update
            },
        ),
    )

    state_v2 = replace_entity(
        state_v2,
        1,
        entity_with_blocker,
    )

    upd2 = StateUpdate(
        entity_updates={
            1: EntityUpdate(
                entity_id=1,
                resource_transfers=[intent1],
            )
        }
    )

    suggestions = DetourSuggestionSystem.suggest_detours(
        state_v2.entities[1],
        state_v2.tick,
    )

    assert suggestions, (
        "Expected at least one detour suggestion. "
        f"blockers={state_v2.entities[1].strategic.blockers}, "
        f"leads={state_v2.entities[1].strategic.leads}"
    )

    assert suggestions[0].target == "(10, 10)"

    strat_upd = StrategicIntelligenceSystem.evaluate_strategic_intent(
        state_v2,
        state_v2.entities[1],
        force=True
    )
    
    detour_before_apply = next(
        (
            project
            for project in strat_upd.projects_add_or_update
            if project.kind == "detour"
        ),
        None,
    )

    assert detour_before_apply is not None
    assert strat_upd.current_project_id_set == detour_before_apply.id

    refined2 = AuthoritativeApplyPipeline.refine(
        state_v2,
        upd2,
    )

    refined2 = replace(
        refined2,
        entity_updates={
            **dict(refined2.entity_updates),
            1: replace(
                refined2.entity_updates[1],
                strategic=strat_upd,
            ),
        },
    )

    state_v3 = ApplyPath.apply_generation(
        state_v2,
        refined2,
        next_tick=3,
    )

    trace2 = list(refined2.transaction_trace)
    intent_res2 = state_v3.entities[1].identity.latest_intent_results
    strat_state2 = state_v3.entities[1].strategic

    # ------------------------------------------------------------------
    # 4. Replay Tick 1
    # ------------------------------------------------------------------
    refined1_r = AuthoritativeApplyPipeline.refine(
        state,
        upd1,
    )

    state_v2_r = ApplyPath.apply_generation(
        state,
        refined1_r,
        next_tick=2,
    )

    assert list(refined1_r.transaction_trace) == trace1
    assert state_v2_r.entities[1].identity.latest_intent_results == intent_res1

    # ------------------------------------------------------------------
    # 5. Replay Tick 2
    # ------------------------------------------------------------------
    failure_r = IntentResult(
        transaction_id="t2",
        accepted=False,
        reason="INVENTORY_FULL",
        source_kind="NODE",
        source_id=10,
    )
    
    identity_with_failure_r = replace(
        state_v2_r.entities[1].identity,
        latest_intent_results=[failure_r],
    )

    entity_with_failure_r = replace(
        state_v2_r.entities[1],
        identity=identity_with_failure_r,
    )

    state_v2_r = replace_entity(
        state_v2_r,
        1,
        entity_with_failure_r,
    )

    current_project_r = state_v2_r.entities[1].strategic.projects[
        state_v2_r.entities[1].strategic.current_project_id
    ]

    upd_blocker_r = StrategicIntelligenceSystem.infer_blockers(
        entity=state_v2_r.entities[1],
        last_task="ENTITY_ACT",
        last_payload={
            "action": "INTERACT",
            "target_id": 10,
        },
        current_project=current_project_r,
    )
    
    assert "blocker_inventory_full" in {
        blocker.id for blocker in upd_blocker_r.blockers_add_or_update
    }

    entity_with_blocker_r = replace(
        state_v2_r.entities[1],
        strategic=replace(
            state_v2_r.entities[1].strategic,
            blockers={
                blocker.id: blocker
                for blocker in upd_blocker_r.blockers_add_or_update
            },
        ),
    )

    state_v2_r = replace_entity(
        state_v2_r,
        1,
        entity_with_blocker_r,
    )

    upd2_r = StateUpdate(
        entity_updates={
            1: EntityUpdate(
                entity_id=1,
                resource_transfers=[intent1],
            )
        }
    )

    strat_upd_r = StrategicIntelligenceSystem.evaluate_strategic_intent(
        state_v2_r,
        state_v2_r.entities[1],
        force=True
    )

    refined2_r = AuthoritativeApplyPipeline.refine(
        state_v2_r,
        upd2_r,
    )

    refined2_r = replace(
        refined2_r,
        entity_updates={
            **dict(refined2_r.entity_updates),
            1: replace(
                refined2_r.entity_updates[1],
                strategic=strat_upd_r,
            ),
        },
    )

    state_v3_r = ApplyPath.apply_generation(
        state_v2_r,
        refined2_r,
        next_tick=3,
    )

    # ------------------------------------------------------------------
    # 6. Deterministic replay assertions
    # ------------------------------------------------------------------
    assert list(refined2_r.transaction_trace) == trace2
    assert state_v3_r.entities[1].identity.latest_intent_results == intent_res2
    assert state_v3_r.entities[1].strategic == strat_state2

    detour = next(
        (
            project
            for project in state_v3_r.entities[1].strategic.projects.values()
            if project.kind == "detour"
        ),
        None,
    )

    assert detour is not None
    assert state_v3_r.entities[1].strategic.current_project_id == detour.id