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


def test_skill_mapping_references_live_source_not_embedded_table():
    """TCK-20260720-SKILL-MAPPING-DEDUP removed the embedded skill-mapping table

    in favor of a live lookup against tag_registry.py's skill-mapping CLI
    subcommand, so the old literal table strings must be gone and the new
    live-lookup reference must be present.
    """
    source = _read_source()
    assert "api-design  -> /api-design-principles" not in source
    assert "Do not invent mappings for tags outside this 4-entry table" not in source
    assert "tools/tag_registry.py skill-mapping" in source
    assert "Do not invent mappings for tags outside this live mapping's keys." in source


def test_create_tickets_structure_relevance_self_check_instruction_present():
    """TCK-20260720-TAG-RELEVANCE-VERIFY: the Structure-phase `tags:` prompt block and

    TASK_SCHEMA both gain a `tag_relevance_flags` self-check field, additive to (not replacing)
    the `files_found`-evidence guardrail TCK-20260720-CREATE-TICKETS-TAG-SCOPE-FIX added. The
    companion assertions below confirm that guardrail's exact strings still survive unmodified.
    """
    source = _read_source()

    assert "tag_relevance_flags" in source
    assert "tag_relevance_flags:" in source  # prompt rule block header, not just schema key

    # The pre-existing evidence guardrail must survive byte-for-byte.
    assert "files_found" in source
    assert "clearly indicates one" in source
    assert "Do not guess a tag from the title alone if files_found doesn't support it" in source
