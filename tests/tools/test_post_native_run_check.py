"""TCK-20260930-NATIVE-PORT-ORCHESTRATOR-BACKSTOP: the post-native-run re-run fails when a gate fails."""
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "gate_checks"))

import post_native_run_check as pnr  # noqa: E402


def test_missing_ticket_fails_without_running_checkers():
    lines = []
    assert pnr.run("TCK-00000000-DOES-NOT-EXIST", out=lines.append) == 1
    assert lines[0].startswith("FAIL ticket_location")


def test_done_ticket_without_working_log_row_fails_naming_the_check(tmp_path):
    # A done ticket whose run never appended a working_log row: the Finalize gate must fail, whatever
    # a native run's agent reported. Run against the real repo with a ticket id that has no row.
    ticket = REPO / "tickets" / "done" / "TCK-99990101-BACKSTOP-FIXTURE.md"
    ticket.write_text(
        "---\nstatus: historical\nlayer: ai\nauthority: P1\naudience: agent\n"
        "ticket_id: TCK-99990101-BACKSTOP-FIXTURE\nphase: done\ndate: 2026-10-01\ntags: []\n---\n\n"
        "# TCK-99990101-BACKSTOP-FIXTURE\n\n## Status\nDONE\n\n## Tier\nhotfix\n\n## Priority\nP3\n",
        encoding="utf-8",
    )
    try:
        lines = []
        assert pnr.run("TCK-99990101-BACKSTOP-FIXTURE", out=lines.append) == 1
        assert "FAIL done_checker_static" in lines
        assert lines[-1].startswith("RESULT: FAIL") and "done_checker_static" in lines[-1]
    finally:
        ticket.unlink()


def test_cli_exit_code_is_nonzero_on_failure():
    proc = subprocess.run([sys.executable, str(REPO / "tools/gate_checks/post_native_run_check.py"),
                           "--ticket-id", "TCK-00000000-DOES-NOT-EXIST"], capture_output=True, text=True, cwd=REPO)
    assert proc.returncode == 1


def test_passes_for_a_real_closed_ticket():
    lines = []
    assert pnr.run("TCK-20260930-IMPLEMENT-TICKET-PARSE-AND-NONDETERMINISM-FIX", out=lines.append) == 0, lines
