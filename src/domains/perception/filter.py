"""
src/domains/perception/filter.py
───────────────────────────────────────────────────────────────────────────────
Phase 12 — PerceptionFilterService

Filters and budget-clamps raw scoped world signals into perceived signals
stored under the PerceptionModel.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Sequence, Tuple, Dict, Any, List

from src.core.state import EntityState
from src.core.cognition import (
    PerceptionModel,
    PerceivedEntity,
    PerceivedResource,
    PerceivedService,
    PerceivedThreat,
    PerceivedOpportunity,
    IgnoredSignal
)
from src.domains.perception.salience import WorldSignal, SignalSalienceEvaluator
from src.domains.perception.service import AttentionFocusService


@dataclass(frozen=True, slots=True)
class PerceptionBudget:
    max_perceived: int = 10
    max_ignored_to_record: int = 5


@dataclass(frozen=True, slots=True)
class PerceptionUpdate:
    perceived_entities: Dict[int, PerceivedEntity]
    perceived_resources: Dict[str, PerceivedResource]
    perceived_services: Dict[str, PerceivedService]
    perceived_threats: Dict[str, PerceivedThreat]
    perceived_opportunities: Dict[str, PerceivedOpportunity]
    ignored_signals: Tuple[IgnoredSignal, ...]


class PerceptionFilterService:
    """Selects, orders, and limits signals to fit dynamic entity capacity limitations."""

    @staticmethod
    def filter(
        entity: EntityState,
        candidate_signals: Sequence[WorldSignal],
        budget: PerceptionBudget,
        tick: int = 0
    ) -> PerceptionUpdate:
        # 1. Get attention focus biases
        attention_focus = AttentionFocusService.get_attention_focus(entity)

        # 2. Evaluate salience for all candidates
        scored_signals: List[Tuple[WorldSignal, float]] = []
        for signal in candidate_signals:
            salience = SignalSalienceEvaluator.evaluate(entity, signal, attention_focus)
            scored_signals.append((signal, salience))

        # 3. Sort by salience descending
        scored_signals.sort(key=lambda x: x[1], reverse=True)

        # 4. Partition into perceived and ignored under budget
        perceived_ents: Dict[int, PerceivedEntity] = {}
        perceived_res: Dict[str, PerceivedResource] = {}
        perceived_serv: Dict[str, PerceivedService] = {}
        perceived_thr: Dict[str, PerceivedThreat] = {}
        perceived_opps: Dict[str, PerceivedOpportunity] = {}
        ignored_list: List[IgnoredSignal] = []

        perceived_count = 0

        for signal, salience in scored_signals:
            # Drop zero salience elements entirely
            if salience <= 0.0:
                continue

            if perceived_count < budget.max_perceived:
                # Add to appropriate typed container
                if signal.kind == "entity" or signal.kind == "HERO" or signal.kind == "MONSTER":
                    # Convert id to int securely
                    try:
                        ent_id = int(signal.signal_id)
                    except ValueError:
                        ent_id = hash(signal.signal_id)
                    perceived_ents[ent_id] = PerceivedEntity(
                        entity_id=ent_id,
                        kind=signal.kind,
                        position=signal.position,
                        salience=salience
                    )
                elif signal.kind in ("healing_resource", "food_source", "crafting_material"):
                    perceived_res[signal.signal_id] = PerceivedResource(
                        node_id=hash(signal.signal_id),
                        kind=signal.kind,
                        position=signal.position,
                        salience=salience
                    )
                elif signal.kind in ("blacksmith", "town_inn", "guild_intel", "shop_merchant"):
                    perceived_serv[signal.signal_id] = PerceivedService(
                        service_id=signal.signal_id,
                        position=signal.position,
                        salience=salience
                    )
                elif signal.kind == "threat":
                    perceived_thr[signal.signal_id] = PerceivedThreat(
                        threat_id=signal.signal_id,
                        position=signal.position,
                        salience=salience,
                        threat_level=signal.danger_level
                    )
                else:
                    perceived_opps[signal.signal_id] = PerceivedOpportunity(
                        opportunity_id=signal.signal_id,
                        kind=signal.kind,
                        salience=salience
                    )
                perceived_count += 1
            else:
                # Bounded record of ignored high-salience signals
                if len(ignored_list) < budget.max_ignored_to_record:
                    ignored_list.append(
                        IgnoredSignal(
                            signal_id=signal.signal_id,
                            reason="capacity_limit",
                            tick=tick
                        )
                    )

        return PerceptionUpdate(
            perceived_entities=perceived_ents,
            perceived_resources=perceived_res,
            perceived_services=perceived_serv,
            perceived_threats=perceived_thr,
            perceived_opportunities=perceived_opps,
            ignored_signals=tuple(ignored_list)
        )
