"""Architecture guard for TCK-20260721-MONITORING-WRITER-UNIFICATION's core
claim: post_tool_hook.py, record_run.py, and record_events.py all route their
append step through the one shared tools/agent-monitoring/writer.py module —
not 3 separate ad hoc lock/write implementations.

Fails loudly if a future edit reintroduces a 4th ad hoc writer, or if one of
the 3 call sites regresses back to its own inline fcntl/os.open locking
instead of importing the shared module. Mirrors the AST-scan precedent used
elsewhere in this repo (tests/agent_orchestration/test_validator_no_network_calls.py)
for "no forbidden call/import" guarantees.
"""
from pathlib import Path

_MONITORING_TOOLS_DIR = Path(__file__).parent.parent.parent / "tools" / "agent-monitoring"

_CALL_SITES = [
    _MONITORING_TOOLS_DIR / "post_tool_hook.py",
    _MONITORING_TOOLS_DIR / "record_run.py",
    _MONITORING_TOOLS_DIR / "record_events.py",
    _MONITORING_TOOLS_DIR / "migrate_tools_shards.py",
]


def test_no_call_site_imports_fcntl():
    for path in _CALL_SITES:
        source = path.read_text()
        assert "import fcntl" not in source, f"{path.name} must not import fcntl directly"
        assert "from fcntl" not in source, f"{path.name} must not import fcntl directly"


def test_no_call_site_does_its_own_lock_file_open():
    for path in _CALL_SITES:
        source = path.read_text()
        assert "O_EXCL" not in source, f"{path.name} must not implement its own lock-file protocol"


def test_each_call_site_imports_shared_writer():
    expected_import = {
        "post_tool_hook.py": "write_line",
        "record_run.py": "write_line",
        "record_events.py": "write_lines",
        "migrate_tools_shards.py": "write_lines",
    }
    for path in _CALL_SITES:
        source = path.read_text()
        symbol = expected_import[path.name]
        assert f"from writer import {symbol}" in source, (
            f"{path.name} must import {symbol} from the shared writer module"
        )


def test_writer_module_is_the_only_place_defining_the_lock_protocol():
    writer_source = (_MONITORING_TOOLS_DIR / "writer.py").read_text()
    assert "O_CREAT" in writer_source and "O_EXCL" in writer_source
    for path in _CALL_SITES:
        assert path.read_text() != writer_source
