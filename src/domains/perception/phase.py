"""
src/domains/perception/phase.py
───────────────────────────────────────────────────────────────────────────────
Phase 12 — PerceptionUpdatePhase

Orchestrates the perception tick updates inside the authoritative pipeline loop.
"""

from __future__ import annotations
from typing import Sequence, List
from dataclasses import replace

from src.core.state import EntityState
from src.domains.perception.salience import WorldSignal
from src.domains.perception.filter import PerceptionFilterService, PerceptionBudget
from src.domains.perception.service import AttentionFocusService
from src.core.cognition import PerceptionModel

class PerceptionUpdatePhase:
    """The engine phase that updates each active entity's perception metrics."""

    def __init__(self, budget: PerceptionBudget = PerceptionBudget()) -> None:
        self.budget = budget

    def run(
        self,
        entities: Sequence[EntityState],
        world_signals: Sequence[WorldSignal],
        tick: int = 0
    ) -> List[EntityState]:
        updated_entities: List[EntityState] = []

        for entity in entities:
            # 1. Skip checks: dead/inactive entities
            if not entity.lifecycle.active or not entity.combat.alive:
                updated_entities.append(entity)
                continue

            # 2. Extract attention focus tags
            focus = AttentionFocusService.get_attention_focus(entity)

            # 3. Filter world signals for this entity
            percept_update = PerceptionFilterService.filter(
                entity=entity,
                candidate_signals=world_signals,
                budget=self.budget,
                tick=tick
            )

            # 4. Construct updated PerceptionModel
            new_perception = PerceptionModel(
                attention_focus=focus,
                perceived_entities=percept_update.perceived_entities,
                perceived_resources=percept_update.perceived_resources,
                perceived_services=percept_update.perceived_services,
                perceived_threats=percept_update.perceived_threats,
                perceived_opportunities=percept_update.perceived_opportunities,
                ignored_signals=percept_update.ignored_signals,
                last_updated_tick=tick
            )

            # 5. Pack back into the cognition.subjective model structure
            new_subjective = replace(entity.cognition.subjective, perception=new_perception)
            new_cognition = replace(entity.cognition, subjective=new_subjective)
            new_entity = replace(entity, cognition=new_cognition)

            updated_entities.append(new_entity)

        return updated_entities
