"""Structural guard: `.claude/workflows/implement-ticket.js`'s `classifyChecklistFailure` mirrors
`tools/gate_checks/done_checker_static.py::classify_checklist_failure`'s TCK-20260720-TAG-
TOUCHPOINT-CLEANUP redesign, not the old evidence-text substring match.

Static, raw-source-text-parsing tests against `.claude/workflows/implement-ticket.js` — reuses
`tests/tools/test_current_run_sidecar_orchestrator.py`'s and
`tests/tools/test_tag_skill_mapping_check.py`'s established pattern of `Path.read_text()` +
regex/string-presence assertions against this non-Python source file. The workflow file is never
executed (no JS test runner exists in this repo for `.claude/workflows/*.js`, confirmed by that
docstring). This is a structural/shape guard, not a full behavioral-equivalence test — true
behavioral parity is verified by the Python-side tests for `_frontmatter_has_unregistered_tags`
(the single source of truth both sides now call into), plus a manual smoke check documented in
this ticket's Completion Summary.
"""
import re
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_WORKFLOW_PATH = _REPO_ROOT / ".claude" / "workflows" / "implement-ticket.js"

_SOURCE = _WORKFLOW_PATH.read_text(encoding="utf-8")


def test_old_marker_string_removed():
    assert "_TAG_REGISTRY_REJECTION_MARKER" not in _SOURCE
    assert "is not in the tag registry" not in _SOURCE


def test_classify_checklist_failure_is_async():
    assert re.search(
        r"const classifyChecklistFailure = async \(checklist, ticketId, ticketTier\) => \{",
        _SOURCE,
    ), "classifyChecklistFailure must be declared async and take (checklist, ticketId, ticketTier)"


def test_classify_checklist_failure_calls_python_reference_helper():
    fn_match = re.search(
        r"const classifyChecklistFailure = async.*?\n(?:.*\n)*?^\}",
        _SOURCE,
        re.MULTILINE,
    )
    assert fn_match, "could not locate classifyChecklistFailure function body"
    body = fn_match.group(0)
    assert "_frontmatter_has_unregistered_tags" in body
    assert "done_checker_static" in body
    assert "TAG_UNREG_JSON:" in body


def test_call_site_passes_tid_and_tier_and_is_awaited():
    call_site_match = re.search(
        r"const reasonCode = (await )?classifyChecklistFailure\(([^)]*)\)", _SOURCE
    )
    assert call_site_match, "could not locate classifyChecklistFailure call site"
    assert call_site_match.group(1) == "await ", "call site must await classifyChecklistFailure"
    args = call_site_match.group(2)
    assert "tid" in args
    assert "tier" in args
