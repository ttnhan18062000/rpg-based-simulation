"""Tests for the delivery templates shipped by TCK-20260924-DELIVERY-CONTRACT-AND-TEMPLATES:
.github/pull_request_template.md, tools/delivery/pr_template_spec.json, and .gitmessage.
"""
import json
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_PR_TEMPLATE = _REPO_ROOT / ".github" / "pull_request_template.md"
_SPEC = _REPO_ROOT / "tools" / "delivery" / "pr_template_spec.json"
_GITMESSAGE = _REPO_ROOT / ".gitmessage"

_ATTRIBUTION_MARKERS = ("Co-Authored-By:", "Claude-Session:", "Generated with", "claude.ai/code")


def _pr_template_body_only() -> str:
    """The PR template's real content, excluding its own leading HTML comment block (which
    itself mentions Co-Authored-By/attribution to explain the *rule*, not to violate it)."""
    text = _PR_TEMPLATE.read_text(encoding="utf-8")
    end_of_comment = text.index("-->")
    return text[end_of_comment + len("-->"):]


def test_pr_template_exists_and_has_no_attribution_trailer_in_its_body():
    body = _pr_template_body_only()
    for marker in _ATTRIBUTION_MARKERS:
        assert marker not in body, f"attribution marker {marker!r} found in PR body content"


def test_pr_template_sections_match_plan_order():
    body = _pr_template_body_only()
    headings = ["## What landed", "## Tickets", "## Why", "## Verification", "## Review notes"]
    positions = [body.index(h) for h in headings]
    assert positions == sorted(positions), "PR template sections are out of order"
    assert "Closes:" in body
    assert body.index("## Review notes") < body.index("Closes:")


def test_pr_template_spec_exists_and_is_valid_json():
    spec = json.loads(_SPEC.read_text(encoding="utf-8"))
    assert "sections" in spec
    assert spec["no_attribution_trailer"] is True


def test_pr_template_spec_marks_review_notes_as_the_only_hand_written_section():
    spec = json.loads(_SPEC.read_text(encoding="utf-8"))
    hand_written = [s["heading"] for s in spec["sections"] if not s["rendered"]]
    assert hand_written == ["## Review notes"]


def test_pr_template_spec_section_order_matches_the_actual_template():
    spec = json.loads(_SPEC.read_text(encoding="utf-8"))
    body = _pr_template_body_only()
    heading_sections = [s["heading"] for s in spec["sections"] if s["heading"].startswith("##")]
    positions = [body.index(h) for h in heading_sections]
    assert positions == sorted(positions)


def test_gitmessage_exists_and_is_comment_only():
    text = _GITMESSAGE.read_text(encoding="utf-8")
    real_lines = [line for line in text.splitlines() if line.strip() and not line.startswith("#")]
    assert real_lines == [], (
        f"expected every non-blank .gitmessage line to be a comment, found: {real_lines}"
    )


def test_gitmessage_documents_the_full_contract_shape():
    text = _GITMESSAGE.read_text(encoding="utf-8")
    for fragment in ("TCK-YYYYMMDD-SHORT-SCOPE", "Tests:", "Refs:", "Co-Authored-By:", "Claude-Session:"):
        assert fragment in text
