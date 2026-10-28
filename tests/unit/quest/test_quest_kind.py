from src.core.quests import QuestKind, QuestState


def test_quest_kind_escort_enum_value_is_new_member_only():
    """TCK-20260828-REPUTATION-WITNESSED-EVENT-WIRING: ESCORT is appended, not inserted."""
    assert {k.name for k in QuestKind} == {
        "HUNT", "GATHER", "EXPLORE", "LIBERATE", "BOUNTY", "ESCORT",
    }
    assert QuestState(id="q-default", kind="quest").quest_kind == QuestKind.HUNT
