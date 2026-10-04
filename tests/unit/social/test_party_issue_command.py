from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole, Faction
from src.core.strategic import DirectivePriority
from src.core.updates import StrategicUpdate
from src.systems.social_systems.party import PartyCoordinationSystem


def _leader():
    return (
        V2EntityBuilder(1)
        .kind("hero")
        .location(0, 0)
        .identity(role=EntityRole.HERO, faction=Faction.HERO_GUILD)
        .combat(hp=100, max_hp=100, alive=True, readiness=100.0)
        .inventory(gold=10)
        .build()
    )


def test_issue_party_command_builds_a_critical_directive():
    """Regression: `StrategicUpdate` was never imported, so this raised NameError on first call."""
    update = PartyCoordinationSystem.issue_party_command(_leader(), "REGROUP", (3.0, 4.0), tick=7)

    assert isinstance(update, StrategicUpdate)
    assert len(update.directives_add_or_update) == 1
    directive = update.directives_add_or_update[0]
    assert directive.id == "party_cmd_REGROUP_7"
    assert directive.kind == "REGROUP"
    assert directive.target == "(3.0, 4.0)"
    assert directive.priority == DirectivePriority.CRITICAL
    assert directive.created_tick == 7
