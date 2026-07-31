"""Structural guard for TCK-20260720-TAG-RELEVANCE-VERIFY's drift-check Finalize wiring.

`check_tag_drift()` (tools/gate_checks/done_checker_static.py) must be invoked from
`.claude/workflows/implement-ticket.js`'s Finalize phase in its own `bash()` block, positioned
*after* `writeMonitoring('DONE')` and the existing `check_monitoring_write_recorded` block, and it
must never change the final `return` object's `status` field away from `'DONE'`. Mirrors
`test_classify_checklist_failure_js_mirror.py`'s established pattern: raw-source-text parsing
against this non-Python workflow file, since no JS test runner exists in this repo for
`.claude/workflows/*.js`.
"""

from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_WORKFLOW_PATH = _REPO_ROOT / ".claude" / "workflows" / "implement-ticket.js"

_SOURCE = _WORKFLOW_PATH.read_text(encoding="utf-8")


def test_check_tag_drift_call_site_present():
    assert "check_tag_drift" in _SOURCE
    assert "TAG_DRIFT_CHECK_JSON:" in _SOURCE


def test_tag_drift_block_positioned_after_monitoring_write_and_its_check():
    write_monitoring_index = _SOURCE.index("await writeMonitoring('DONE')")
    monitoring_check_index = _SOURCE.index("check_monitoring_write_recorded")
    tag_drift_index = _SOURCE.index("check_tag_drift")
    final_return_index = _SOURCE.rindex("return {\n  status: 'DONE',")

    assert write_monitoring_index < monitoring_check_index < tag_drift_index < final_return_index


def test_tag_drift_never_conditions_final_status():
    final_return_block_start = _SOURCE.rindex("return {\n  status: 'DONE',")
    final_return_block = _SOURCE[final_return_block_start:]
    # The final return's `status` literal must stay unconditional — no ternary/variable involving
    # tagDriftCheck may appear anywhere in the returned object.
    assert "status: 'DONE'," in final_return_block
    assert "tagDriftCheck" not in final_return_block


def test_tag_drift_flagged_result_only_logs_and_pushes_event_never_blocks():
    tag_drift_block_start = _SOURCE.index("const tagDriftCheckOutput")
    final_return_block_start = _SOURCE.rindex("return {\n  status: 'DONE',")
    tag_drift_block = _SOURCE[tag_drift_block_start:final_return_block_start]

    assert "log(" in tag_drift_block
    assert "pushEvent(" in tag_drift_block
    assert "'FLAGGED'" in tag_drift_block
    # Must never reference a blocking status like FINALIZE_INCOMPLETE.
    assert "FINALIZE_INCOMPLETE" not in tag_drift_block
