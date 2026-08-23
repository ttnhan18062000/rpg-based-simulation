"""Doc-structure tests for the CLAUDE.md pre-scan mandate relaxation draft
(TCK-20260814-KGMCP-PRESCAN-MANDATE-INSTRUCTION-DRAFT).

This ticket produces zero `src/`/`tools/` code and no runtime behavior change: it drafts, but
explicitly does not activate, replacement agent-instruction text for CLAUDE.md's current blanket
"search_docs + graphify before grep" mandate. These tests assert doc *structure* (required
disclaimer fragments, required content coverage) and non-regression of the three live instruction
surfaces this draft must not touch — never runtime behavior — mirroring the static-assertion
pattern `tests/docs/test_redaction_retention_policy_doc.py` uses for its own not-yet-ratified
sibling artifact.

Test 4 verifies the historical fact that TCK-20260814's own commit (`59b4bede`, parent
`12f773c8`) never touched `CLAUDE.md` or `.claude/agents/*.md` — it diffs that pinned commit
range, not the live working tree, so it cannot false-positive on unrelated uncommitted edits to
those files made by other sessions/tickets (see
TCK-20260823-HOTFIX-PRESCAN-DRAFT-TEST-LIVE-DIFF-FALSE-POSITIVE).
"""
from __future__ import annotations

import subprocess
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_DRAFT_DOC = _REPO_ROOT / "docs" / "ai" / "claude_md_prescan_mandate_relaxation_draft.md"
_INVESTIGATOR_MD = _REPO_ROOT / ".claude" / "agents" / "investigator.md"
_SKILL_MD = _REPO_ROOT / ".claude" / "skills" / "implement-ticket" / "SKILL.md"

_INVESTIGATE_MARKER = "2. **Investigate**"
_PLAN_MARKER = "3. **Plan**"


def _read_draft() -> str:
    return _DRAFT_DOC.read_text()


def _investigate_step_text() -> str:
    text = _SKILL_MD.read_text()
    start = text.index(_INVESTIGATE_MARKER)
    end = text.index(_PLAN_MARKER, start)
    return text[start:end]


# ---------------------------------------------------------------------------
# Test 1 — draft exists, labeled not-yet-activated
# ---------------------------------------------------------------------------

def test_draft_instruction_change_artifact_exists_and_is_labeled_not_activated():
    assert _DRAFT_DOC.exists(), f"missing required draft artifact: {_DRAFT_DOC}"
    text = _read_draft()

    assert "for human review only" in text
    assert "not activated" in text or "not applied" in text
    assert "does not itself" in text


# ---------------------------------------------------------------------------
# Test 2 — activation precondition against the hardening ticket
# ---------------------------------------------------------------------------

def test_draft_records_activation_precondition_against_hardening_ticket():
    text = _read_draft()

    assert "TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP" in text
    assert "retro-confirmed" in text or "retro" in text
    assert "pending" in text
    # Must not read as already satisfied.
    assert "precondition is currently satisfied" not in text.lower()
    assert "already retro-confirmed" not in text.lower()


# ---------------------------------------------------------------------------
# Test 3 — live investigator.md / SKILL.md callouts preserved verbatim
# ---------------------------------------------------------------------------

def test_draft_preserves_investigator_and_skill_callouts_verbatim():
    investigator_text = _INVESTIGATOR_MD.read_text()
    assert "mcp__knowledge-search__search_docs" in investigator_text
    assert "graphify" in investigator_text
    assert "does not substitute" in investigator_text

    skill_region = _investigate_step_text()
    assert (
        "Step 0's one-time upfront call does not substitute for this phase-scoped call"
        in skill_region
    )


# ---------------------------------------------------------------------------
# Test 4 — CLAUDE.md and .claude/agents/*.md were byte-unchanged by
# TCK-20260814-KGMCP-PRESCAN-MANDATE-INSTRUCTION-DRAFT's own historical commit
# ---------------------------------------------------------------------------

def test_draft_does_not_modify_claude_md_or_agent_md_files():
    # Pinned to TCK-20260814-KGMCP-PRESCAN-MANDATE-INSTRUCTION-DRAFT's own actual commit,
    # not live HEAD -- see TCK-20260823-HOTFIX-PRESCAN-DRAFT-TEST-LIVE-DIFF-FALSE-POSITIVE
    # for why: checking live uncommitted `git diff HEAD` state made this test fail for any
    # UNRELATED session with an uncommitted edit to these files, which is not what a
    # "this specific ticket didn't touch these files" guarantee should ever assert about.
    _TICKET_COMMIT = "59b4bede"
    _TICKET_COMMIT_PARENT = "12f773c8"
    result = subprocess.run(
        ["git", "diff", "--stat", f"{_TICKET_COMMIT_PARENT}..{_TICKET_COMMIT}",
         "--", "CLAUDE.md", ".claude/agents/*.md"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == "", (
        "TCK-20260814-KGMCP-PRESCAN-MANDATE-INSTRUCTION-DRAFT's own commit must not have "
        f"modified CLAUDE.md or any .claude/agents/*.md file; git diff --stat shows:\n{result.stdout}"
    )


# ---------------------------------------------------------------------------
# Test 5 — required ambient-utility substance from proposal §2.1
# ---------------------------------------------------------------------------

def test_draft_covers_required_ambient_utility_substance():
    text = _read_draft()

    required_fragments = [
        "ambient utility",
        "optional ranking hints",
        "not itself a workflow phase, gate, Definition-of-Done item, or mandatory ticket step",
        "use `rg` for a simple exact text check",
        "use Graphify directly for a focused code-reference or dependency question",
        "use Context Search directly for a focused document lookup",
    ]
    for fragment in required_fragments:
        assert fragment in text, f"draft missing required §2.1 substance fragment: {fragment}"
