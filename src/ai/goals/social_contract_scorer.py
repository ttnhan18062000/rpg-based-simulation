from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple

from src.ai.goals.base import GoalScorer, GoalScore
from src.core.state import EntityState, AuthoritativeState
from src.core.strategic import GoalKind, ContractState, ContractStatus


class SocialContractGoalScorer(GoalScorer):
    """
    GoalScorer wrapper around ContractService.get_project_mapping() (src/systems/social_systems/
    contracts.py), registered under GoalKind.SOCIAL_CONTRACT as one candidate among many in tier 5
    of StrategicIntelligenceSystem.evaluate_strategic_intent()
    (src/systems/strategic_systems/intelligence.py). See plan.md
    TCK-20260811-SOCIAL-CONTRACT-GOAL-SCORER, Design Decision #1: this scorer reads
    entity.strategic.contracts directly and is therefore reachable in live production via
    src/engine/domain/core_actions.py's execute_recruit() (which constructs ACTIVE-status
    RECRUITMENT contracts directly), even though ContractService.accept_contract() itself has no
    production caller.
    """

    def score(self, entity: EntityState, state: AuthoritativeState) -> GoalScore:
        from src.systems.social_systems.contracts import ContractService

        candidates: List[Tuple[float, ContractState, Tuple[Any, Any, str]]] = []
        for contract in entity.strategic.contracts.values():
            if contract.status != ContractStatus.ACTIVE:
                continue
            mapping = ContractService.get_project_mapping(contract)
            if mapping is None:
                # PROTECTION/MERCHANT/POSITION_SWAP: preserve accept_contract()'s pre-existing
                # 2-of-5 coverage -- do not widen (plan.md Scope Guards).
                continue
            raw_score = SocialContractGoalScorer._raw_score(entity, contract, state.tick)
            candidates.append((raw_score, contract, mapping))

        if not candidates:
            return GoalScore(kind=GoalKind.SOCIAL_CONTRACT, utility=0.0, target_id=None)

        # Reduction (Design Decision #4): highest raw_score wins; ties broken by contract id
        # ascending for determinism (entity.strategic.contracts iteration order is not a
        # determinism-safe tie-break source).
        candidates.sort(key=lambda c: (-c[0], c[1].id))
        raw_score, contract, (proj_kind, obj_kind, obj_id_prefix) = candidates[0]

        # MUST be a lazy (function-local) import: mirrors AdventureGoalScorer's own documented
        # reason (src/ai/goals/adventure_scorer.py) -- intelligence.py:78's top-level
        # `from src.ai.goals import GoalRegistry` creates a transitive module-load-order
        # dependency once this module is registered in src/ai/goals/__init__.py.
        from src.systems.strategic_systems.intelligence import (
            _ADVENTURE_ROUTE_SCORE_MAX,
            _GOAL_UTILITY_SCORE_MAX,
        )

        # Design Decision #8: the counterparty's real position, so the materialized objective is
        # tactically resolvable (TacticalDecisionSystem._resolve_target_position() only resolves
        # int-castable targets against state.resource_nodes/state.buildings, never state.entities
        # -- a stringified entity id alone, as accept_contract()'s ORIGINAL ObjectiveState used,
        # was never resolvable). Falls back to None only if the counterparty is genuinely absent.
        source_entity = state.entities.get(contract.source_id)
        target_pos = source_entity.navigation.position if source_entity else None

        utility = (raw_score / _ADVENTURE_ROUTE_SCORE_MAX) * _GOAL_UTILITY_SCORE_MAX

        return GoalScore(
            kind=GoalKind.SOCIAL_CONTRACT,
            utility=utility,
            target_id=str(contract.source_id),
            target_pos=target_pos,
            metadata={
                "contract_id": contract.id,
                "source_id": contract.source_id,
                "raw_score": raw_score,
                "proj_kind": proj_kind,
                "obj_kind": obj_kind,
                "obj_id_prefix": obj_id_prefix,
            },
        )

    @staticmethod
    def _raw_score(entity: EntityState, contract: ContractState, current_tick: int) -> float:
        """
        raw_score = clamp(trust*1.0 + urgency*1.0 + value*0.9 - risk_weight*0.3, 0.0, 2.9)
        Calibrated to the SAME 0-2.9 ceiling _ADVENTURE_ROUTE_SCORE_MAX already declares
        (Design Decision #2 -- reuse, do not extend, _score_scale_max()). See plan.md Design
        Decision #3 for the full per-term rationale and Anti-Drift Notes for the explicit
        disclosure that these weights/baselines are an initial, not empirically validated,
        calibration.
        """
        from src.core.strategic import ContractKind, RiskLevel

        bond = entity.social.bonds.get(contract.source_id)
        if bond:
            trust = (bond.sentiment + 1.0) / 2.0
        else:
            trust = entity.social.trust_history.get(contract.source_id, 0.5)

        duration = contract.terms.get("duration", 0)
        if contract.expiry_tick and contract.expiry_tick > 0 and duration > 0:
            ticks_remaining = max(0, contract.expiry_tick - current_tick)
            urgency = 1.0 - min(1.0, ticks_remaining / duration)
        else:
            urgency = 0.5

        if contract.kind == ContractKind.RECRUITMENT:
            # terms.get("payout", ...) fallback: execute_recruit()-originated contracts use
            # "payout", not "daily_pay" (Design Decision #9) -- disclosed degradation, not a
            # schema unification.
            pay = contract.terms.get("daily_pay", contract.terms.get("payout", 0))
            expected_pay = 10 * max(1, entity.identity.evolution_level)
            value = min(1.0, pay / expected_pay)
            risk = contract.terms.get("risk_level", RiskLevel.NORMAL)
            risk_weight = 1.0 if risk == "HIGH" else (0.5 if risk == "NORMAL" else 0.1)
        elif contract.kind == ContractKind.LOAN:
            amount = contract.terms.get("amount", 0)
            expected_amount = 50 * max(1, entity.identity.evolution_level)
            value = min(1.0, amount / expected_amount)
            risk_weight = 0.0  # LOAN terms carry no risk_level key (contracts.py, confirmed).
        else:
            # Defensively unreachable: score()'s caller already filters to RECRUITMENT/LOAN via
            # get_project_mapping() before calling this. Kept for safety, not exercised by tests.
            value = 0.0
            risk_weight = 0.0

        raw = (trust * 1.0) + (urgency * 1.0) + (value * 0.9) - (risk_weight * 0.3)
        return max(0.0, min(2.9, raw))
