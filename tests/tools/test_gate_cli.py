"""TCK-20261009-NATIVE-ATTESTED-COMMAND-TRANSPORT-LOSSY: the short gate command lines and the git-derived file list.

``tools/gate_checks/gate_cli.py`` replaces the inline ``python3 -c`` gate sites of ``implement-ticket.js``. These tests
hold three things: every site's command stays under a recorded length (the payload an agent has to copy), the changed
files are derived from git (not carried in the command), and each sub-command prints what the script parses."""

from __future__ import annotations

import base64
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "tools"))

from gate_checks import gate_cli  # noqa: E402

SCRIPT = REPO_ROOT / ".claude" / "workflows" / "implement-ticket.js"
_NODE = shutil.which("node")
needs_node = pytest.mark.skipif(_NODE is None, reason="node not installed")

# Base64 characters of the command handed to the agent. Measured 120-316 for the reference ticket below (the inline forms
# were 288-1932 and grew with the file count); 400 leaves room for a longer pytest command or docs list.
GATE_CMD_BOUND = 400
TID = "TCK-20261009-MAIN-INTEGRITY-REPORT-SILENT-TORN-RUN-EVENT-LINES"
SHA = "0123456789abcdef0123456789abcdef01234567"


def _site_commands(**override) -> dict:
    text = SCRIPT.read_text(encoding="utf-8")
    block = text[text.index("// GATE-CMD-BEGIN"):text.index("// GATE-CMD-END")]
    pytest_command = override.get("pytest_command", "python -m pytest tests/tools/ tests/unit/core tests/unit/systems tests/unit/combat -q -p no:cacheprovider")
    program = block + f"""
const out = {{
  tag_check: gateCmd.tagCheck(['agent-monitoring', 'data-quality', 'ai', 'testing']),
  plan_unresolved: gateCmd.planUnresolved({json.dumps(TID)}),
  doc_staleness: gateCmd.docStaleness({json.dumps(SHA)}, true, ['docs/agent-monitoring/README.md', 'docs/guides/delivery_process.md', 'docs/engine/kernel.md']),
  test_scope: gateCmd.testScope({json.dumps(SHA)}, {json.dumps(pytest_command)}),
  data_runs_cleanup: gateCmd.dataRunsCleanup('2026-10-09T01:54:36Z'),
  p0_scan: gateCmd.p0Scan({json.dumps(SHA)}),
  parity_xref: gateCmd.parityXref({json.dumps(SHA)}),
  finalize_selfcheck: gateCmd.finalizeSelfcheck({json.dumps(TID)}, 'standard'),
}};
process.stdout.write(JSON.stringify(out));"""
    proc = subprocess.run([_NODE, "-e", program], capture_output=True, text=True, timeout=30)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


@needs_node
def test_every_attested_site_command_stays_under_the_recorded_bound():
    for site, cmd in _site_commands().items():
        assert len(base64.b64encode(cmd.encode())) <= GATE_CMD_BOUND, f"{site}: {cmd}"


@needs_node
def test_the_command_length_does_not_grow_with_the_number_of_changed_files():
    """The list is derived from git inside gate_cli, so no site's command can carry a path list."""
    assert all("--start-sha" in cmd or site in {"tag_check", "plan_unresolved", "data_runs_cleanup", "finalize_selfcheck"}
               for site, cmd in _site_commands().items())
    assert not any(".py" in cmd.replace("gate_cli.py", "") for cmd in _site_commands().values())


@needs_node
def test_a_pytest_command_with_a_single_quote_survives_shell_quoting():
    cmd = _site_commands(pytest_command="python -m pytest tests/tools/ -k 'a or b'")["test_scope"]
    parsed = subprocess.run(["bash", "-c", f"set -- {cmd.split('gate_cli.py ', 1)[1]}; for a in \"$@\"; do printf '%s\\n' \"$a\"; done"],
                            capture_output=True, text=True, check=True).stdout.splitlines()
    assert "--pytest-command=python -m pytest tests/tools/ -k 'a or b'" in parsed


def test_no_attested_gate_site_in_the_script_still_builds_inline_python():
    text = SCRIPT.read_text(encoding="utf-8")
    for match in __import__("re").finditer(r"shAttested\(\s*(.*?),\s*'([a-z0-9_]+)'", text, __import__("re").S):
        body, gate = match.groups()
        assert "python3 -c" not in body, gate


# --- the git-derived list ---------------------------------------------------------------------------------------------

def _git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True,
                          env={"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
                               "GIT_COMMITTER_EMAIL": "t@t", "PATH": "/usr/bin:/bin:/usr/local/bin", "HOME": str(repo)}).stdout.strip()


def _w(repo, rel, text="x\n"):
    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


@pytest.fixture
def repo(tmp_path, monkeypatch):
    _git(tmp_path, "init", "-q", "-b", "main")
    _w(tmp_path, "tools/old.py")
    _w(tmp_path, "tools/earlier_ticket.py")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "base")
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_the_list_is_the_working_tree_against_the_start_commit_plus_untracked_files(repo):
    start = _git(repo, "rev-parse", "HEAD")
    _w(repo, "tools/earlier_ticket.py", "committed after the start commit\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "committed after the start commit")
    _w(repo, "tools/old.py", "edited, uncommitted\n")
    _w(repo, "tests/tools/test_new.py")
    assert gate_cli.derive_changed_files(start) == ["tests/tools/test_new.py", "tools/earlier_ticket.py", "tools/old.py"]


def test_work_committed_before_the_start_commit_is_not_this_tickets_change(repo):
    """On a batch branch earlier tickets' commits sit below the start commit, so they must not enter the list."""
    _w(repo, "tools/previous_ticket.py")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "previous ticket")
    start = _git(repo, "rev-parse", "HEAD")
    _w(repo, "tools/this_ticket.py")
    assert gate_cli.derive_changed_files(start) == ["tools/this_ticket.py"]


def test_bookkeeping_paths_the_run_writes_are_left_out(repo):
    start = _git(repo, "rev-parse", "HEAD")
    for rel in ("agent-working/agent-monitoring/data/2026-W41/x.runs.jsonl", "data/runs/run_1/manifest.json",
                "reports/release_proof/p/out.json", "graphify-out/graph.json", "tools/__pycache__/m.pyc",
                "tests/.pytest_cache/v/cache", ".claude/current_run.abc"):
        _w(repo, rel)
    _w(repo, "tools/real.py")
    assert gate_cli.derive_changed_files(start) == ["tools/real.py"]


def test_a_deleted_tracked_file_is_a_change(repo):
    start = _git(repo, "rev-parse", "HEAD")
    (repo / "tools" / "old.py").unlink()
    assert gate_cli.derive_changed_files(start) == ["tools/old.py"]


# --- what each sub-command prints -------------------------------------------------------------------------------------

def test_test_scope_prints_the_derived_list_then_the_check_json(repo, capsys):
    start = _git(repo, "rev-parse", "HEAD")
    _w(repo, "tools/agent-monitoring/main_integrity_report.py")
    assert gate_cli.main(["test_scope", "--start-sha", start, "--pytest-command=python -m pytest tests/tools/ -q"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert json.loads(lines[0].removeprefix("DERIVED_FILES_JSON:")) == ["tools/agent-monitoring/main_integrity_report.py"]
    assert json.loads(lines[1].removeprefix("TEST_SCOPE_CHECK_JSON:"))[0]["status"] == "PASS"


def test_test_scope_reports_the_gap_the_failed_native_run_was_meant_to_catch(repo, capsys):
    start = _git(repo, "rev-parse", "HEAD")
    _w(repo, "tools/agent-monitoring/main_integrity_report.py")
    gate_cli.main(["test_scope", "--start-sha", start, "--pytest-command=python -m pytest tests/tools/test_x.py -q"])
    results = json.loads(capsys.readouterr().out.splitlines()[1].removeprefix("TEST_SCOPE_CHECK_JSON:"))
    assert results[0]["status"] == "FAIL" and "tests/tools/" in results[0]["condition"]


def test_p0_scan_and_tag_check_and_finalize_print_the_markers_the_script_parses(repo, capsys):
    start = _git(repo, "rev-parse", "HEAD")
    assert gate_cli.main(["p0_scan", "--start-sha", start]) == 0
    assert capsys.readouterr().out.splitlines()[0] in {"P0_NO_INTERSECTION", "P0_INTERSECTION_FOUND"}
    assert gate_cli.main(["tag_check", "no-such-tag-xyz"]) == 0
    assert json.loads(capsys.readouterr().out.removeprefix("TAG_CHECK_JSON:")) == ["no-such-tag-xyz"]
