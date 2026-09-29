"""AC5: docs/ai/ticket-lifecycle.md carries the offer-not-invoke rule for /create-tickets and
/implement-epic (TCK-20260929-OPEN-TICKET-DUPLICATE-SCAN-AND-WORKFLOW-OFFER).
"""
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_TICKET_LIFECYCLE_PATH = _REPO_ROOT / "docs" / "ai" / "ticket-lifecycle.md"


def test_offer_not_invoke_rule_present_near_epic_batch_workflow_section():
    text = _TICKET_LIFECYCLE_PATH.read_text(encoding="utf-8")
    epic_batch_idx = text.find("## Epic Batch Workflow")
    offer_rule_idx = text.find("Offering is not invoking")
    assert epic_batch_idx != -1, "## Epic Batch Workflow section not found — has it moved?"
    assert offer_rule_idx != -1, (
        "the offer-not-invoke rule is missing — see TCK-20260929-OPEN-TICKET-DUPLICATE-SCAN-AND-WORKFLOW-OFFER"
    )
    # within a few hundred chars of the section heading -- "next to line 632" per the ticket.
    assert 0 <= offer_rule_idx - epic_batch_idx < 500

    section = text[offer_rule_idx:offer_rule_idx + 700]
    assert "/create-tickets" in section
    assert "/implement-epic" in section
    assert "never start" in section or "can never start" in section
