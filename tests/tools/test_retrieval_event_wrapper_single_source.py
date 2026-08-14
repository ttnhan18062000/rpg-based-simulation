"""Architecture guards for tools/retrieval_events.py (TCK-20260729-RETRIEVAL-EVENT-SCHEMA-EMIT).

Mirrors, but deliberately does NOT extend, tests/tools/test_monitoring_writer_single_source.py's
assertions — that file's `_CALL_SITES` list stays exactly 3 entries
(post_tool_hook.py/record_run.py/record_events.py); tools/retrieval_events.py gets its own,
separate guard here instead (AC4's "mirroring test_monitoring_writer_single_source.py's
assertions" requirement, without redefining what "the 3 call sites" means for that file).

Also covers AC6's structural guard: tools/retrieval_events.py must never reference any
.claude/workflows/*.js file or a known pipeline entry-point string.
"""
from pathlib import Path

_RETRIEVAL_EVENTS_PATH = Path(__file__).parent.parent.parent / "tools" / "retrieval_events.py"


def test_module_does_not_import_fcntl():
    source = _RETRIEVAL_EVENTS_PATH.read_text()
    assert "import fcntl" not in source
    assert "from fcntl" not in source


def test_module_does_not_implement_its_own_lock_file_open():
    source = _RETRIEVAL_EVENTS_PATH.read_text()
    assert "O_EXCL" not in source


def test_module_imports_shared_writer():
    source = _RETRIEVAL_EVENTS_PATH.read_text()
    assert "from writer import write_lines" in source


def test_module_never_references_workflow_files_or_pipeline_entry_points():
    source = _RETRIEVAL_EVENTS_PATH.read_text()
    forbidden = (
        ".claude/workflows",
        "pushEvent",
        "writeSidecar",
        "implement-ticket.js",
        "implement-epic.js",
        "create-tickets.js",
        "simq-audit.js",
    )
    for needle in forbidden:
        assert needle not in source, f"tools/retrieval_events.py must never reference '{needle}'"
