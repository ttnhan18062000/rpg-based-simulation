"""Authoritative service for applying contract-driven social and reputation consequences. [PHASE 3]"""

from __future__ import annotations
import logging
from typing import TYPE_CHECKING

from src_legacy.core.models.enums import StrategicStatus
from src_legacy.ai.strategy.contract_outcome import ContractOutcomeService
from src_legacy.core.logic.relationship_service import RelationshipService
from src_legacy.core.logic.reputation_service import ReputationService
from src_legacy.actions.base import SocialUpdate, ReputationUpdate, StrategicUpdate

if TYPE_CHECKING:
    from src_legacy.core.models.world_state import WorldState
    from src_legacy.core.models.strategy import SocialContractRecord

logger = logging.getLogger(__name__)

class ContractConsequenceService:
    """Orchestrates the authoritative application of contract outcomes."""

    @classmethod
    def apply_resolution(
        cls,
        world: WorldState,
        contract: SocialContractRecord,
        outcome: StrategicStatus,
        tick: int
    ) -> None:
        """Apply all consequences of a contract's resolution (honor or breach)."""
        
        # 1. Generate pure intents
        all_updates = ContractOutcomeService.resolve_contract(contract, outcome, tick)
        
        # 2. Authoritatively apply each intent
        for entity_id, intents in all_updates.items():
            entity = world.get_entity(entity_id)
            if not entity:
                continue

            for intent in intents:
                if isinstance(intent, SocialUpdate):
                    RelationshipService.apply_update(world.social_registry, intent, tick)
                    logger.debug(f"Applied social consequence to {entity_id} from contract {contract.contract_id}")
                
                elif isinstance(intent, ReputationUpdate):
                    ReputationService.apply_update(entity, intent)
                    logger.debug(f"Applied reputation consequence to {entity_id} from contract {contract.contract_id}")
                
                elif isinstance(intent, StrategicUpdate):
                    # Authoritative update of the entity's strategic records
                    cls._apply_strategic_mutation(entity, intent)
                    logger.debug(f"Applied strategic consequence to {entity_id} from contract {contract.contract_id}")

    @classmethod
    def _apply_strategic_mutation(cls, entity: Entity, intent: StrategicUpdate) -> None:
        """Directly mutates the entity's strategic state (Authoritative Path)."""
        if not intent.contracts_add_or_update:
            return
            
        current_contracts = entity.mind.strategic.contracts
        for new_ct in intent.contracts_add_or_update:
            # Find and replace or add
            found = False
            for i, existing in enumerate(current_contracts):
                if existing.contract_id == new_ct.contract_id:
                    current_contracts[i] = new_ct
                    found = True
                    break
            if not found:
                current_contracts.append(new_ct)
