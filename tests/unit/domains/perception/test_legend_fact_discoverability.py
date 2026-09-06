"""AC4: LegendFact is discoverable via a direct unit-level call to
PerceptionFilterService.filter() -- without wiring PerceptionUpdatePhase into
any live pipeline phase.

Kept separate from test_phase12_perception_filter_service.py so
tests/architecture/test_fame_legend_fact_distinctness.py's guard #4 stays a
clean scan of src/, not test files.
"""

from src.core.state import EntityState
from src.domains.campaigns.state import CampaignState, NarrativeLedgerEntry
from src.domains.chronicle.grouper import ChronicleGrouper
from src.domains.fame.exporter import FameExporter
from src.domains.fame.legend import LegendFactService
from src.domains.perception.filter import PerceptionBudget, PerceptionFilterService


def test_legend_fact_discoverable_via_perception_filter_service():
    state = CampaignState(campaign_id="test", episode_index=0)
    entries = [
        NarrativeLedgerEntry(
            episode=ep,
            tick=ep + 1,
            event_type="quest_completed",
            subject_id="hero_1",
            payload={},
            significance=0.7,
            entry_id=f"{ep}:{ep + 1}:quest_completed:hero_1",
        )
        for ep in range(3)
    ]
    hierarchy = ChronicleGrouper().group(entries)
    FameExporter.export(state, hierarchy, episode_index=2)

    fact = LegendFactService.for_entity(state, "hero_1")
    assert fact is not None
    signal = LegendFactService.to_world_signal(fact)

    entity = EntityState(id=1, kind="HERO")
    update = PerceptionFilterService.filter(entity, [signal], PerceptionBudget())

    assert signal.signal_id in update.perceived_opportunities
    assert update.perceived_opportunities[signal.signal_id].salience > 0.0
