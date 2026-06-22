"""Doc archive validation test (E53Dd).

Verifies that the V1 grand_strategy.md is archived and the V2 faction_contract.md exists.

AC: test_grand_strategy_doc_archived — from TCK-20260619-E53D-HISTORY epic ACs.
"""
import os


def test_grand_strategy_doc_archived():
    """grand_strategy_v1.md must exist in docs/archive/; original must not exist."""
    assert os.path.exists("docs/archive/grand_strategy_v1.md"), (
        "grand_strategy_v1.md must exist in docs/archive/"
    )
    assert not os.path.exists("docs/systems/grand_strategy.md"), (
        "docs/systems/grand_strategy.md must not exist after archival"
    )


def test_faction_contract_exists():
    """docs/systems/faction_contract.md must exist as the authoritative V2 reference."""
    assert os.path.exists("docs/systems/faction_contract.md"), (
        "docs/systems/faction_contract.md must exist"
    )


def test_archived_doc_has_deprecation_notice():
    """Archived doc must contain the deprecation notice linking to faction_contract.md."""
    with open("docs/archive/grand_strategy_v1.md", encoding="utf-8") as f:
        content = f.read()
    assert "ARCHIVED" in content
    assert "faction_contract.md" in content
