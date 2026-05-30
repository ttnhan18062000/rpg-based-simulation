"""
tests/unit/domains/progression/test_phase6_reward_ledger_service.py

Phase 6 — RewardLedgerService tests.
"""

import pytest
from src.domains.progression.schema import RewardLedgerComponent
from src.domains.progression.ledger import RewardLedgerService


def test_reward_ledger_records_item_gain():
    ledger = RewardLedgerComponent()
    ledger = RewardLedgerService.record_entry(ledger, tick=5, kind="item", subject="iron_ore", quantity=1)
    
    assert len(ledger.entries) == 1
    assert ledger.entries[0].kind == "item"
    assert ledger.entries[0].subject == "iron_ore"


def test_reward_ledger_capacity_is_bounded():
    ledger = RewardLedgerComponent()
    for i in range(25):
        ledger = RewardLedgerService.record_entry(ledger, tick=i, kind="gold", subject="quest", quantity=1)
    
    # MAX_ENTRIES is 20, so older entries should be trimmed
    assert len(ledger.entries) == 20
    assert ledger.entries[0].tick == 5  # Entries 0-4 are trimmed
    assert ledger.entries[-1].tick == 24


def test_reward_ledger_entry_can_be_marked_consumed():
    ledger = RewardLedgerComponent()
    ledger = RewardLedgerService.record_entry(ledger, tick=10, kind="xp", subject="kill", quantity=100)
    
    assert ledger.entries[0].consumed_by_plan is False
    ledger = RewardLedgerService.mark_consumed(ledger, 0)
    assert ledger.entries[0].consumed_by_plan is True
