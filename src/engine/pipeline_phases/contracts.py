from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from src.core.strategic import ContractStatus
from src.core.updates import EntityUpdate, StrategicUpdate
from src.systems.social_contract import SocialContractSystem

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState
    from src.core.updates import StateUpdate


class ContractLifecyclePhase:
    """
    Resolves contract expiration and completion lifecycle.
    """

    @staticmethod
    def resolve_expirations(
        state: AuthoritativeState,
        update: StateUpdate,
    ) -> StateUpdate:
        """
        Resolve stale social contracts during authoritative refinement.

        LAW:
            OFFERED / COUNTERED contracts that expire are EXPIRED.

            ACTIVE contracts that reach expiry_tick are treated as successfully
            completed duration contracts and become FULFILLED / COMPLETED.

        Why:
            An ACTIVE recruitment/protection/merchant contract reaching its end date
            is not the same as an unanswered offer expiring. The active obligation
            was honored until its duration ended.

        Effects:
            - ACTIVE -> FULFILLED may create social reputation updates.
            - OFFERED / COUNTERED -> EXPIRED is status-only.
            - No movement, inventory transfer, or world mutation happens here.
        """
        entity_updates = dict(update.entity_updates)

        def _merge_entity_update(entity_id: int, strategic_upd=None, social_upd=None):
            existing = entity_updates.get(
                entity_id,
                EntityUpdate(entity_id=entity_id),
            )

            merged_strategic = existing.strategic
            if strategic_upd is not None:
                merged_strategic = (
                    merged_strategic.merge(strategic_upd)
                    if merged_strategic is not None
                    else strategic_upd
                )

            merged_social = existing.social
            if social_upd is not None:
                merged_social = (
                    merged_social.merge(social_upd)
                    if merged_social is not None
                    else social_upd
                )

            entity_updates[entity_id] = replace(
                existing,
                strategic=merged_strategic,
                social=merged_social,
            )

        for entity_id in sorted(state.entities.keys()):
            entity = state.entities[entity_id]
            for contract_id in sorted(entity.strategic.contracts.keys()):
                contract = entity.strategic.contracts[contract_id]
                if contract.expiry_tick == -1:
                    continue

                if state.tick < contract.expiry_tick:
                    continue

                if contract.status == ContractStatus.ACTIVE:
                    # Active duration completed successfully.
                    strat_upd, social_upd = SocialContractSystem.transition_contract(
                        entity,
                        contract.id,
                        ContractStatus.FULFILLED,
                        state.tick,
                    )

                    if strat_upd.contracts_add_or_update:
                        _merge_entity_update(
                            entity_id,
                            strategic_upd=strat_upd,
                            social_upd=social_upd,
                        )

                elif contract.status in (
                    ContractStatus.OFFERED,
                    ContractStatus.COUNTERED,
                ):
                    expired_contract = replace(
                        contract,
                        status=ContractStatus.EXPIRED,
                    )

                    _merge_entity_update(
                        entity_id,
                        strategic_upd=StrategicUpdate(
                            contracts_add_or_update=[expired_contract],
                        ),
                    )

        return replace(
            update,
            entity_updates=entity_updates,
        )
