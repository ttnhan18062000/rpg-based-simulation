"""Regression tests for TCK-20260915-SIBLING-WORKFLOW-SUMMARY-TRUNCATION-MARKERS.

Static, raw-source-text-parsing tests against `.claude/workflows/create-tickets.js`,
`.claude/workflows/simq-audit.js`, and `.claude/workflows/implement-epic.js` — mirrors
`tests/tools/test_event_summary_truncation.py`'s own established pattern for
`implement-ticket.js` (no JS test runner exists in this repo for `.claude/workflows/*.js`).

Covers: each file's own silent `.slice(0, 200)` (no marker) was replaced with a local
`truncateSummary()` helper (same shape as `implement-ticket.js`'s own, duplicated per-file since
no shared module exists between these standalone workflow scripts) that appends a visible
`' […]'` marker only when an actual cut occurs.
"""
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).parent.parent.parent
_WORKFLOWS_DIR = _REPO_ROOT / ".claude" / "workflows"

_FILES_WITH_PUSH_EVENT = ["create-tickets.js", "simq-audit.js"]
_ALL_FILES = ["create-tickets.js", "simq-audit.js", "implement-epic.js"]


def _read(filename: str) -> str:
    return (_WORKFLOWS_DIR / filename).read_text(encoding="utf-8")


@pytest.mark.parametrize("filename", _ALL_FILES)
def test_truncate_summary_helper_defined(filename):
    text = _read(filename)
    assert "const truncateSummary = (s) => {" in text


@pytest.mark.parametrize("filename", _ALL_FILES)
def test_truncate_summary_caps_at_200_with_trailing_marker(filename):
    text = _read(filename)
    assert "str.slice(0, 196) + ' […]'" in text, (
        "truncateSummary must cut to 196 chars + a 4-char marker, keeping the total at 200"
    )


@pytest.mark.parametrize("filename", _ALL_FILES)
def test_no_raw_200_char_slices_remain_anywhere_in_file(filename):
    text = _read(filename)
    assert ".slice(0, 200)" not in text


@pytest.mark.parametrize("filename", _FILES_WITH_PUSH_EVENT)
def test_push_event_uses_truncate_summary_not_raw_slice(filename):
    text = _read(filename)
    push_event_idx = text.find("const pushEvent = (")
    assert push_event_idx != -1
    close_idx = text.find("\n}\n", push_event_idx)
    push_event_block = text[push_event_idx:close_idx]
    assert "summary: truncateSummary(summary)," in push_event_block
    assert ".slice(0, 200)" not in push_event_block


def test_implement_epic_direct_assignment_site_uses_truncate_summary():
    # implement-epic.js's own single summary-producing site has no pushEvent wrapper at all
    # (a direct object-literal assignment inside batchEvents) — the ticket's own named shape.
    text = _read("implement-epic.js")
    assert "summary: truncateSummary(r.implementation_summary || r.message || r.status || '')," in text


def test_create_tickets_link_epic_pre_slice_site_uses_raw_text_not_pre_sliced():
    # The redundant pre-slice at create-tickets.js's own link-epic pushEvent call site is gone --
    # pushEvent's own truncateSummary now handles it, so the raw (unsliced) linkText is passed
    # through, letting the visible marker apply if a real cut happens.
    text = _read("create-tickets.js")
    assert "linkText.slice(0, 200)" not in text
    assert "linkText || `Linked to ${epicId}`" in text


@pytest.mark.parametrize(
    "filename,var_names",
    [
        ("simq-audit.js", ["recalText", "syncDocsText", "parityText"]),
    ],
)
def test_simq_audit_pre_slice_sites_use_raw_text_not_pre_sliced(filename, var_names):
    text = _read(filename)
    for var in var_names:
        assert f"{var}.slice(0, 200)" not in text, (
            f"{var}'s own redundant pre-slice must be gone -- pushEvent's truncateSummary "
            "already handles truncation with a visible marker"
        )
