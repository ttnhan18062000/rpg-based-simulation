import pytest
from src.core.cognition import CommitmentEntry, CommitmentModel

def test_commitment_entry_serialization():
    entry = CommitmentEntry(
        id="quest_1",
        kind="escort",
        target_id="npc_2",
        strength=0.8,
        deadline_tick=100,
        created_tick=10
    )
    assert entry.id == "quest_1"
    assert entry.kind == "escort"
    assert entry.strength == 0.8
    assert entry.deadline_tick == 100
