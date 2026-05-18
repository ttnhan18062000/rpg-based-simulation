# Compliance IDs: API-001, API-009, API-013, API-018, API-019, API-020, API-021, API-022, API-023, API-024, DATA-023, DATA-041, DATA-045, DATA-129, DATA-130, DATA-131, DATA-132, DATA-133, DATA-134, DATA-135, INFRA-019, INFRA-056, INFRA-057, INFRA-167, INFRA-180, RES-021, STRAT-035, STRAT-044, STRAT-060, STRAT-068, WORLD-015
from __future__ import annotations
from typing import Dict, Any, List
from src.core.state import AuthoritativeState, EntityState, RegionState

class StatePresenter:
    """
    Transforms authoritative state into read-only API models.
    M12 Law: API presenters MUST NOT mutate authoritative state.
    VERIFIED v2: observability_from_results
    """

    @staticmethod
    def present_minimal(state: AuthoritativeState) -> Dict[str, Any]:
        """Summarized world view."""
        return {
            "tick": state.tick,
            "world_time": state.world_time,
            "entities_count": len(state.entities),
            "maturity": state.maturity,
            "seed": state.seed
        }

    @staticmethod
    def present_full(state: AuthoritativeState) -> Dict[str, Any]:
        """Complete inspectable world view."""
        return {
            "tick": state.tick,
            "world_time": state.world_time,
            "maturity": state.maturity,
            "entities": [StatePresenter.present_entity(e) for e in state.entities.values()],
            "regions": [StatePresenter.present_region(r) for r in state.regions.values()],
            "global_resources": state.global_resources,
            "transaction_trace": state.transaction_trace,
            "status": "ACTIVE"
        }

    @staticmethod
    def present_entity(entity: EntityState) -> Dict[str, Any]:
        """Detailed entity model."""
        from src.core.quests import QuestState
        
        return {
            "id": entity.id,
            "kind": entity.kind,
            "position": entity.position,
            "readiness": entity.readiness,
            "combat": {
                "hp": entity.combat.hp,
                "max_hp": entity.combat.max_hp,
                "atk": entity.combat.atk,
                "def": entity.combat.def_stat,
                "alive": entity.combat.alive,
                "tactical_role": entity.combat.tactical_role,
                "last_legality_result": entity.combat.latest_result.reason if entity.combat.latest_result else None,
                "damage_trace": {} # Trace removed in V2 to save memory
            },
            "inventory": {
                "gold": entity.inventory.gold,
                "item_count": len(entity.inventory.items),
                "items": [
                    {"id": i.item_id, "quantity": i.quantity, "metadata": i.metadata}
                    for i in entity.inventory.items
                ]
            },
            "strategic": {
                "current_project": entity.strategic.current_project_id,
                "current_objective": entity.strategic.current_objective_id,
                "project_count": len(entity.strategic.projects),
                "boredom": entity.strategic.boredom,
                "primary_overload": entity.strategic.primary_overload_source,
                "blockers": [
                    {"id": b.id, "kind": b.kind, "subject": b.subject, "severity": b.severity, "resolved": b.resolved}
                    for b in entity.strategic.blockers.values()
                ],
                "leads": [
                    {"id": l.id, "kind": l.kind, "subject": l.subject, "certainty": l.certainty.value if hasattr(l.certainty, 'value') else l.certainty, "tested": l.tested}
                    for l in entity.strategic.leads.values()
                ],
                "contracts": [
                    {"id": c.id, "kind": c.kind.value if hasattr(c.kind, 'value') else c.kind, "status": c.status.value if hasattr(c.status, 'value') else c.status, "target_id": c.target_id}
                    for c in entity.strategic.contracts.values()
                ]
            },
            "quests": [
                {
                    "id": q.id,
                    "name": q.name,
                    "kind": q.quest_kind.name if hasattr(q.quest_kind, 'name') else str(q.quest_kind),
                    "status": q.quest_status.name if hasattr(q.quest_status, 'name') else str(q.quest_status),
                    "progress": q.progress_ratio,
                    "reward": {"xp": q.reward.xp, "gold": q.reward.gold, "items": q.reward.items}
                }
                for q in entity.strategic.projects.values() if isinstance(q, QuestState)
            ],
            "social": {
                "trust": {str(k): v for k, v in entity.social.trust_history.items()},
                "public_reputation": entity.social.public_reputation,
                "heroism": entity.social.heroism_score,
                "notoriety": entity.social.notoriety_score,
                "betrayals": entity.social.betrayal_count
            },
            "navigation": {
                "target": entity.navigation.target,
                "moved_recently": entity.navigation.moved_recently,
                "wait_count": entity.navigation.wait_count,
                "oscillation_count": entity.navigation.oscillation_count,
                "last_failure": entity.navigation.last_failure_reason,
                "mode": entity.navigation.movement_mode.name if hasattr(entity.navigation.movement_mode, 'name') else str(entity.navigation.movement_mode)
            },
            "biological": {
                "sleep_debt": entity.biological.sleep_debt,
                "hunger": entity.biological.hunger
            },
            "identity": {
                "faction": entity.identity.faction,
                "role": entity.identity.role,
                "level": entity.identity.evolution_level,
                "class": entity.identity.class_id
            },
            "intent_results": [
                {
                    "accepted": r.accepted,
                    "reason": r.reason,
                    "source": f"{r.source_kind}:{r.source_id}",
                    "transaction_id": r.transaction_id
                } for r in entity.identity.latest_intent_results
            ]
        }

    @staticmethod
    def present_region(region: RegionState) -> Dict[str, Any]:
        """Detailed regional model."""
        return {
            "id": region.id,
            "name": region.name,
            "owner": region.owner_faction_id,
            "influence": region.influence,
            "hazard": region.hazard_level,
            "kind": region.kind,
            "weather": region.weather
        }
