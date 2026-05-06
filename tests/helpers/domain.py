from __future__ import annotations

from src.core.state import SocialBond
from src.core.strategic import ContractState, ProjectState, SourceTrustEntry
from tests.helpers.entities import make_hero


def make_social_actor(
    entity_id: int = 1,
    *,
    gold: int = 10,
    trust_target_id: int | None = None,
    trust: float | None = None,
    sentiment_target_id: int | None = None,
    sentiment: float | None = None,
    betrayal_count: int | None = None,
    **kwargs,
):
    trust_history = None
    bonds = None

    if trust_target_id is not None and trust is not None:
        trust_history = {trust_target_id: trust}

    if sentiment_target_id is not None and sentiment is not None:
        bonds = {
            sentiment_target_id: SocialBond(
                target_id=sentiment_target_id,
                sentiment=sentiment,
                familiarity=0.5,
            )
        }

    actor = make_hero(
        entity_id,
        gold=gold,
        trust_history=trust_history,
        betrayal_count=betrayal_count,
        **kwargs,
    )

    if bonds is not None:
        from tests.helpers.entities import with_social
        actor = with_social(actor, bonds=bonds)

    return actor


def with_project(entity, project: ProjectState, *, current: bool = True):
    from tests.helpers.entities import with_strategic

    projects = dict(entity.strategic.projects)
    projects[project.id] = project

    changes = {"projects": projects}
    if current:
        changes["current_project_id"] = project.id

    return with_strategic(entity, **changes)


def with_contract(entity, contract: ContractState):
    from tests.helpers.entities import with_strategic

    contracts = dict(entity.strategic.contracts)
    contracts[contract.id] = contract
    return with_strategic(entity, contracts=contracts)


def with_source_trust(entity, source_id: int, entry: SourceTrustEntry):
    from tests.helpers.entities import with_strategic

    source_trust = dict(entity.strategic.source_trust)
    source_trust[source_id] = entry
    return with_strategic(entity, source_trust=source_trust)