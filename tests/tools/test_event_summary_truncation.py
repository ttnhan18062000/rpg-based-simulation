"""Regression tests for TCK-20260915-EVENT-SUMMARY-TRUNCATION.

Static, raw-source-text-parsing tests against `.claude/workflows/implement-ticket.js` — follows
tests/tools/test_monitoring_bypass_fix.py's established pattern of `Path.read_text()` against this
non-Python source file (no JS test runner exists in this repo for `.claude/workflows/*.js`).

Covers: `pushEvent`'s silent `.slice(0, 200)` (no marker) was replaced with a `truncateSummary()`
helper that appends a visible `' […]'` marker only when an actual cut occurs, applied uniformly at
every summary-truncation call site in the file (not only `pushEvent`'s own internal slice) so a
reader can always tell a truncated summary from a complete one.
"""
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_IMPLEMENT_TICKET_PATH = _REPO_ROOT / ".claude" / "workflows" / "implement-ticket.js"


def _read() -> str:
    return _IMPLEMENT_TICKET_PATH.read_text(encoding="utf-8")


def test_truncate_summary_helper_defined():
    text = _read()
    assert "const truncateSummary = (s) => {" in text


def test_truncate_summary_caps_at_200_with_trailing_marker():
    text = _read()
    assert "str.slice(0, 196) + ' […]'" in text, (
        "truncateSummary must cut to 196 chars + a 4-char marker, keeping the total at 200"
    )


def test_push_event_uses_truncate_summary_not_raw_slice():
    text = _read()
    push_event_idx = text.find("const pushEvent = (")
    assert push_event_idx != -1
    close_idx = text.find("\n}\n", push_event_idx)
    push_event_block = text[push_event_idx:close_idx]
    assert "summary: truncateSummary(summary)," in push_event_block
    assert ".slice(0, 200)" not in push_event_block


def test_no_raw_200_char_slices_remain_anywhere_in_file():
    # Every original call site (pushEvent's own slice, 2 shadow-call object literals, and 8
    # pre-slicing call sites feeding pushEvent) must be gone -- a reintroduced raw slice would
    # silently drop the visible-truncation marker at that one site.
    text = _read()
    assert ".slice(0, 200)" not in text


def test_shadow_call_sites_use_truncate_summary():
    text = _read()
    assert "summary: truncateSummary(archVerifyShadow.summary)," in text
    assert "summary: truncateSummary(securityReviewShadow.summary)," in text
