"""Tests for tools/gate_checks/doc_staleness_check.py
(TCK-20260711-DOC-STALENESS-GATE-CHECK).

Coverage-honesty requirement (SEQUENCE.md decision 4, see workflow_meta_conformance's own test
module): the true-positive guard below must reproduce the actual incident shape
(TCK-20260711-EPIC-SCOPE-ORPHAN-FIX / TCK-20260711-EPIC-STALENESS-DEDUPE-CHECK) this check exists
to catch, not just exercise the happy path.
"""

import json
import subprocess
import sys
from pathlib import Path

_TOOLS_DIR = Path(__file__).parent.parent.parent / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from gate_checks.doc_staleness_check import check_doc_staleness  # noqa: E402

_REPO_ROOT = Path(__file__).parent.parent.parent
_MODULE_PATH = _REPO_ROOT / "tools" / "gate_checks" / "doc_staleness_check.py"


# ---------------------------------------------------------------------------
# False-positive guards
# ---------------------------------------------------------------------------


def test_behavior_not_changed_passes_even_with_src_paths():
    results = check_doc_staleness(
        files_changed=["src/systems/foo.py", "tests/test_foo.py"],
        behavior_changed=False,
    )
    assert len(results) == 1
    assert results[0]["status"] == "PASS"


def test_test_only_change_with_behavior_changed_true_passes():
    results = check_doc_staleness(
        files_changed=["tests/tools/test_doc_staleness_check.py"],
        behavior_changed=True,
    )
    assert len(results) == 1
    assert results[0]["status"] == "PASS"


# ---------------------------------------------------------------------------
# True-positive guard — reproduces the actual EPIC-SCOPE-ORPHAN-FIX /
# EPIC-STALENESS-DEDUPE-CHECK incident shape
# ---------------------------------------------------------------------------


def test_src_change_with_behavior_changed_true_and_no_docs_path_fails():
    results = check_doc_staleness(
        files_changed=[
            "src/systems/epic_scope_orphan_check.py",
            "tests/systems/test_epic_scope_orphan_check.py",
        ],
        behavior_changed=True,
    )
    assert len(results) == 1
    assert results[0]["status"] == "FAIL"
    assert "src/systems/epic_scope_orphan_check.py" in results[0]["evidence"]


def test_workflow_js_change_with_behavior_changed_true_and_no_docs_path_fails():
    results = check_doc_staleness(
        files_changed=[".claude/workflows/implement-ticket.js"],
        behavior_changed=True,
    )
    assert len(results) == 1
    assert results[0]["status"] == "FAIL"


# ---------------------------------------------------------------------------
# Happy path guard — same true-positive shape, but WITH a docs/ path present
# ---------------------------------------------------------------------------


def test_src_change_with_behavior_changed_true_and_a_docs_path_passes():
    results = check_doc_staleness(
        files_changed=[
            "src/systems/epic_scope_orphan_check.py",
            "docs/engine/known_limitations.md",
        ],
        behavior_changed=True,
    )
    assert len(results) == 1
    assert results[0]["status"] == "PASS"


def test_workflow_js_change_with_behavior_changed_true_and_a_docs_path_passes():
    results = check_doc_staleness(
        files_changed=[".claude/workflows/implement-ticket.js", "docs/ai/workflows.md"],
        behavior_changed=True,
    )
    assert len(results) == 1
    assert results[0]["status"] == "PASS"


# ---------------------------------------------------------------------------
# Other edge cases
# ---------------------------------------------------------------------------


def test_no_files_changed_passes():
    results = check_doc_staleness(files_changed=[], behavior_changed=True)
    assert results[0]["status"] == "PASS"


def test_non_js_file_under_claude_workflows_does_not_trigger_flag():
    results = check_doc_staleness(
        files_changed=[".claude/workflows/README.md"],
        behavior_changed=True,
    )
    assert results[0]["status"] == "PASS"


# ---------------------------------------------------------------------------
# CLI contract — MARKER:-prefixed JSON line
# ---------------------------------------------------------------------------


def test_cli_entrypoint_prints_marker_prefixed_json():
    proc = subprocess.run(
        [
            sys.executable,
            str(_MODULE_PATH),
            "true",
            "src/systems/foo.py",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    output_line = proc.stdout.strip()
    assert output_line.startswith("MARKER:")
    payload = json.loads(output_line[len("MARKER:"):])
    assert isinstance(payload, list)
    assert payload[0]["status"] == "FAIL"


def test_cli_entrypoint_passes_when_docs_path_included():
    proc = subprocess.run(
        [
            sys.executable,
            str(_MODULE_PATH),
            "true",
            "src/systems/foo.py",
            "docs/engine/known_limitations.md",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    output_line = proc.stdout.strip()
    payload = json.loads(output_line[len("MARKER:"):])
    assert payload[0]["status"] == "PASS"
