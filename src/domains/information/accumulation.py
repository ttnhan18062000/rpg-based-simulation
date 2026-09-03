"""
src/domains/information/accumulation.py
───────────────────────────────────────────────────────────────────────────────
TCK-20260903-INFORMATION-HUB-ACCUMULATION — Information Hub Knowledge Accumulation.

Applies a knowledge_accumulated increment + knowledge_age freshness reset to an
InformationProviderState in response to a quest report-back (e.g. a quest the
provider assigned being reported back by the entity who completed it).

Decision-only: returns a replacement InformationProviderState, does not mutate
state. The caller (QuestResolutionSystem.enforce()) is responsible for writing
the replacement into StateUpdate.information_providers_update.

Logic ID: INFO-HUB-001
"""
from __future__ import annotations

from dataclasses import replace

from src.domains.information.providers import InformationProviderState


class InformationAccumulationService:
    """Applies a knowledge_accumulated increment + knowledge_age freshness reset to an
    InformationProviderState in response to a quest report-back. Decision-only: returns a
    replacement InformationProviderState, does not mutate state."""

    @staticmethod
    def record_quest_reported_back(provider: InformationProviderState) -> InformationProviderState:
        return replace(
            provider,
            knowledge_accumulated=provider.knowledge_accumulated + 1,
            knowledge_age=0,
        )
