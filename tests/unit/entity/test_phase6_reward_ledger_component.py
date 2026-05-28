"""
tests/unit/entity/test_phase6_reward_ledger_component.py

Phase 6 — RewardLedgerComponent dataclass tests.
"""

import pytest
from src.domains.progression.schema import RewardEntry, RewardLedgerComponent


def test_reward_ledger_component_empty_defaults():
    ledger = RewardLedgerComponent()
    assert len(ledger.entries) == 0
    assert ledger.last_processed_tick == 0


def test_reward_entry_fields():
    entry = RewardEntry(
        tick=10,
        kind="gold",
        subject="quest_payment",
        quantity=80,
        source="guild",
    )
    
    assert entry.tick == 10
    assert entry.kind == "gold"
    assert entry.subject == "quest_payment"
    assert entry.quantity == 80
    assert entry.source == "guild"
    assert entry.consumed_by_plan is False
