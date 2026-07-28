"""Tests for TCK-20260720-CREATE-TICKETS-TAG-SCOPE-FIX.

Asserts create-tickets.js's Structure-phase prompt no longer cites the stale
TCK-20260705-TAG-REGISTRY-QUERY ticket as justification for restricting batch-created
tickets to Process/Skill-signal tags only, and instead follows the full 5-category
tag_taxonomy.md model gated by an evidence guardrail (files_found/domain must support
a Subsystem/Topic tag, not a guess from the title).
"""

from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_CREATE_TICKETS_JS = _REPO_ROOT / ".claude" / "workflows" / "create-tickets.js"


def _read_source() -> str:
    return _CREATE_TICKETS_JS.read_text(encoding="utf-8")


def test_stale_tag_registry_query_citation_is_gone():
    source = _read_source()
    assert "TCK-20260705-TAG-REGISTRY-QUERY" not in source


def test_blanket_do_not_assign_restriction_is_gone():
    source = _read_source()
    assert "Do NOT assign Subsystem/Topic" not in source


def test_full_taxonomy_guidance_present():
    source = _read_source()
    assert "tag_taxonomy.md" in source
    assert "full 5-category model" in source


def test_evidence_guardrail_present():
    source = _read_source()
    assert "files_found" in source
    assert "clearly indicates one" in source
    assert "Do not guess a tag from the title alone if files_found doesn't support it" in source


def test_process_skill_signal_mapping_table_still_present_unchanged():
    source = _read_source()
    assert "api-design  -> /api-design-principles" in source
    assert "Do not invent mappings for tags outside this 4-entry table" in source
