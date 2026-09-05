"""Tests for .claude/agents/doc-updater.md (TCK-20260803-DOC-UPDATER-CORE-WIRING).

Static, raw-source-text-parsing tests against the agent definition file — reuses
tests/tools/test_doc_staleness_gate_wiring.py's established pattern of Path.read_text() against
non-Python source files. The agent file is never executed by pytest; these tests only verify its
required structure and scope-boundary prose exist.
"""
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_DOC_UPDATER_PATH = _REPO_ROOT / ".claude" / "agents" / "doc-updater.md"


def _read() -> str:
    return _DOC_UPDATER_PATH.read_text(encoding="utf-8")


def test_doc_updater_agent_file_has_required_sections():
    assert _DOC_UPDATER_PATH.exists(), f"{_DOC_UPDATER_PATH} does not exist"
    text = _read()

    assert text.startswith("---\n"), "file must start with a frontmatter block"
    frontmatter_end = text.find("\n---", 4)
    assert frontmatter_end != -1, "frontmatter block is not closed"
    frontmatter = text[:frontmatter_end]
    assert "name: doc-updater" in frontmatter
    assert "description:" in frontmatter

    assert "## Step 0" in text, "missing a Step-0-equivalent orchestrator-injected-context section"
    assert "## What to Do" in text
    assert "## Output" in text

    output_idx = text.find("## Output")
    output_section = text[output_idx:]
    assert "docs_updated" in output_section
    assert "docs_skipped" in output_section
    assert "blocker" in output_section
    assert "verified_by" in output_section

    # docs/architecture/doc_updater_agent.md's Data-flow section uses a literal "Family | Rule"
    # markdown table header — this file must transcribe that table into prose, not copy it verbatim.
    assert "Family | Rule" not in text, (
        "per-family rules must be transcribed as prose instructions, not a copied markdown table"
    )


def test_doc_updater_prompt_includes_self_check_instruction():
    # TCK-20260904-DOC-COVERAGE-REVERSE-CHECK, AC #4: the base prompt must instruct the agent to
    # cross-reference its own touched docs/ paths against Files Changed/Related Docs before
    # returning, and to flag a mismatch same-turn via the existing `blocker` field.
    text = _read()
    what_to_do_idx = text.find("## What to Do")
    output_idx = text.find("## Output")
    assert what_to_do_idx != -1 and output_idx != -1
    section = text[what_to_do_idx:output_idx].lower()
    assert "files changed" in section and "related docs" in section
    assert "blocker" in section


def test_doc_updater_never_edits_parity_ledger_or_audits_scope():
    text = _read()
    assert "docs/parity_ledger/" in text, (
        "agent file must explicitly state docs/parity_ledger/ is out of scope (parity-updater's territory)"
    )
    assert "docs/audits/" in text
    audits_idx = text.find("docs/audits/")
    audits_context = text[max(0, audits_idx - 200):audits_idx + 400].lower()
    assert "cite" in audits_context and ("never edit" in audits_context or "never-edit" in audits_context), (
        "agent file must state docs/audits/ is cite-only and never edited"
    )
