"""
src/cognition/self_model_phase.py
───────────────────────────────────────────────────────────────────────────────
Phase 2 — SelfModelUpdatePhase

Orchestrates all four self-model services and emits trace events.
Incorporates a high-performance dirty-check to skip redundant computations.
"""

from __future__ import annotations
import dataclasses
from typing import List, Optional, Tuple, Dict, Any

from src.core.self_model import SelfModelBundle
from src.cognition.self_assessment import SelfAssessmentService
from src.cognition.need_interpretation import NeedInterpretationService
from src.cognition.capability_estimate import CapabilityEstimateService, CapabilityContext
from src.cognition.knowledge_model import KnowledgeModelService

from src.cognition.trace_events import (
    SelfAwarenessUpdatedEvent,
    NeedInterpretedEvent,
    CapabilityEstimateUpdatedEvent,
    KnowledgeFactLearnedEvent,
    KnowledgeUnknownRecordedEvent,
)
class SelfModelUpdatePhase:
    """
    Orchestrates the bottom-up self-model update pipeline.
    """

    @staticmethod
    def apply(
        state: Any,  # AuthoritativeState
        update: Any,  # StateUpdate
    ) -> Any:  # StateUpdate
        """
        Integrated pipeline refined phase apply method mapping to ENABLE_SELF_MODEL_COGNITION aspect.
        """
        new_entity_updates = dict(update.entity_updates)

        for entity_id, entity in state.entities.items():
            if not entity.lifecycle.active or not entity.combat.alive:
                continue

            # Run bottom-up update
            new_bundle = SelfModelUpdatePhase.run(
                entity=entity,
                state=state,
                events=[],
                tick=state.tick
            )

            # Map back to entity update set
            from src.core.updates import EntityUpdate
            entity_up = new_entity_updates.get(entity_id, EntityUpdate(entity_id=entity_id))
            from dataclasses import replace as dataclass_replace
            new_entity_updates[entity_id] = dataclass_replace(
                entity_up,
                self_model_bundle_set=new_bundle
            )

        from dataclasses import replace as dataclass_replace
        return dataclass_replace(update, entity_updates=new_entity_updates)

    @staticmethod
    def run(
        entity: Any,  # EntityState
        state: Optional[Any] = None,  # AuthoritativeState
        events: List[Any] = [],
        tick: int = 0,
        capability_context: Optional[CapabilityContext] = None,
        trace_events_collector: Optional[List[Any]] = None,
    ) -> SelfModelBundle:
        """
        Orchestrates self-model update with dirty checking.
        
        Args:
            entity: The entity state.
            state: Optional world state.
            events: Events emitted in this tick.
            tick: Current simulation tick.
            capability_context: Optional context to scope capability estimates.
            trace_events_collector: Optional list to append trace events to.
        Returns:
            An updated frozen SelfModelBundle.
        """
        if trace_events_collector is None:
            trace_events_collector = []

        old_bundle = entity.self_model if hasattr(entity, "self_model") else SelfModelBundle.empty()

        # ── Step 1: Knowledge Assimilation ──────────────────────────────────
        new_knowledge = old_bundle.knowledge
        has_info_event = False

        for event in events:
            # Detect InformationResponse events via standard answer_kind attribute
            if hasattr(event, "answer_kind"):
                has_info_event = True
                
                # Copy old knowledge component onto a temp entity so service can access it
                temp_entity = dataclasses.replace(entity, self_model=dataclasses.replace(old_bundle, knowledge=new_knowledge))
                new_knowledge = KnowledgeModelService.assimilate(temp_entity, event, tick)

                # Emit trace events for newly learned facts
                for k, new_fact in new_knowledge.facts.items():
                    old_fact = old_bundle.knowledge.facts.get(k)
                    if not old_fact or old_fact.recorded_tick != new_fact.recorded_tick:
                        trace_events_collector.append(
                            KnowledgeFactLearnedEvent(
                                entity_id=entity.id,
                                tick=tick,
                                subject=new_fact.subject,
                                fact_type=new_fact.fact_type,
                                certainty=new_fact.certainty,
                            )
                        )

                # Emit trace events for newly recorded unknowns
                for k, new_unk in new_knowledge.unknowns.items():
                    old_unk = old_bundle.knowledge.unknowns.get(k)
                    if not old_unk or old_unk.recorded_tick != new_unk.recorded_tick:
                        trace_events_collector.append(
                            KnowledgeUnknownRecordedEvent(
                                entity_id=entity.id,
                                tick=tick,
                                subject=new_unk.subject,
                                reason=new_unk.reason,
                            )
                        )

        # ── Step 2: Self-Assessment and Dirty Check ────────────────────────
        new_awareness = SelfAssessmentService.assess(entity, state)
        new_awareness = dataclasses.replace(new_awareness, last_self_check_tick=tick)

        # Dirty check logic
        is_dirty = (
            old_bundle.self_awareness.last_self_check_tick == 0
            or has_info_event
            or new_awareness.perceived_condition != old_bundle.self_awareness.perceived_condition
            or new_awareness.perceived_weaknesses != old_bundle.self_awareness.perceived_weaknesses
            or new_awareness.perceived_strengths != old_bundle.self_awareness.perceived_strengths
        )

        if not is_dirty:
            # Performance budget victory: skip need interpretation and keep old awareness/needs.
            # We still merge new knowledge if it was updated.
            if new_knowledge != old_bundle.knowledge:
                return dataclasses.replace(old_bundle, knowledge=new_knowledge)
            return old_bundle

        # Emit SelfAwarenessUpdatedEvent
        trace_events_collector.append(
            SelfAwarenessUpdatedEvent(
                entity_id=entity.id,
                tick=tick,
                weaknesses=new_awareness.perceived_weaknesses,
                strengths=new_awareness.perceived_strengths,
                confidence=new_awareness.confidence_level,
                stress=new_awareness.stress_level,
            )
        )

        # ── Step 3: Need Interpretation ────────────────────────────────────
        temp_entity = dataclasses.replace(
            entity,
            self_model=SelfModelBundle(
                self_awareness=new_awareness,
                needs=old_bundle.needs,
                capabilities=old_bundle.capabilities,
                knowledge=new_knowledge,
            )
        )
        new_needs = NeedInterpretationService.interpret(temp_entity, new_awareness, state)
        new_needs = dataclasses.replace(new_needs, last_interpreted_tick=tick)

        # Emit NeedInterpretedEvent
        trace_events_collector.append(
            NeedInterpretedEvent(
                entity_id=entity.id,
                tick=tick,
                dominant_need=new_needs.dominant_need or "none",
                needs_summary={k: v.urgency for k, v in new_needs.active_needs.items()},
            )
        )

        # ── Step 4: Capability Estimation ──────────────────────────────────
        new_capabilities = old_bundle.capabilities
        if capability_context is not None:
            new_capabilities = CapabilityEstimateService.estimate(temp_entity, state, capability_context, tick)

            # Emit CapabilityEstimateUpdatedEvent
            trace_events_collector.append(
                CapabilityEstimateUpdatedEvent(
                    entity_id=entity.id,
                    tick=tick,
                    estimates_summary={
                        k: {"estimate": v.estimate, "confidence": v.confidence}
                        for k, v in new_capabilities.estimates.items()
                    },
                )
            )

        return SelfModelBundle(
            self_awareness=new_awareness,
            needs=new_needs,
            capabilities=new_capabilities,
            knowledge=new_knowledge,
        )
