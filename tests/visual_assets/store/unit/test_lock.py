"""ADR D24: one advisory store lock per data root; a second writer refuses at once; read-only commands take none; the kernel releases it on a kill."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

from tests.visual_assets.store.unit.conftest import snapshot
from visual_assets.store import cli, lock
from visual_assets.store.errors import GateError

REPO = Path(__file__).resolve().parents[4]
NOW = "2026-02-01T00:00:00Z"


def start_holder(env) -> subprocess.Popen:
    (env.tmp / "quarantine").mkdir(exist_ok=True)
    child = subprocess.Popen([sys.executable, "-m", "tests.visual_assets.store.kill_helper", "hold", "x", str(env.tmp)], cwd=REPO,
                             stdout=subprocess.PIPE, text=True)
    assert child.stdout.readline().strip() == "ready"
    return child


def _hang_guard(seconds: int = 10):
    """A regression to a WAITING lock would hang this test for the holder's whole sleep: turn it into a failure instead."""
    def fire(*_):
        raise TimeoutError("the lock waited instead of refusing")

    signal.signal(signal.SIGALRM, fire)
    signal.alarm(seconds)


def test_a_second_writer_is_refused_at_once_naming_the_holder(env):
    child = start_holder(env)
    _hang_guard()
    try:
        started = time.monotonic()
        with pytest.raises(GateError) as err, lock.store_write_lock("gc", started_at=NOW):
            pass
        assert time.monotonic() - started < 2  # refuses, never waits
        assert err.value.code == "store_locked"
        assert f"pid {child.pid}" in str(err.value) and "`hold`" in str(err.value)
    finally:
        signal.alarm(0)
        child.kill()
        child.wait()


def test_the_kernel_releases_the_lock_when_the_holder_is_killed(env):
    child = start_holder(env)
    os.kill(child.pid, signal.SIGKILL)
    child.wait()
    with lock.store_write_lock("gc", started_at=NOW):  # immediately, no cleanup step
        pass


def test_the_cli_refuses_a_writing_command_while_another_holds_the_lock_and_changes_nothing(env, capsys):
    child = start_holder(env)
    _hang_guard()
    try:
        before = snapshot(env.catalog)
        assert cli.main(["gc", "--delete"]) == 2
        assert "store_locked" in capsys.readouterr().err
        assert cli.main(["build"]) == 2
        assert snapshot(env.catalog) == before
    finally:
        signal.alarm(0)
        child.kill()
        child.wait()


def test_read_only_commands_take_no_lock(env, capsys):
    child = start_holder(env)
    try:
        for argv in (["list"], ["audit"], ["verify"], ["gc"], ["deletions"], ["draft", "verify"]):
            assert cli.main(argv) in (0, 1), argv  # never 2 for a lock refusal
            assert "store_locked" not in capsys.readouterr().err, argv
    finally:
        child.kill()
        child.wait()


def test_a_nested_acquire_in_the_same_process_refuses(env):
    with lock.store_write_lock("outer", started_at=NOW), pytest.raises(GateError) as err, lock.store_write_lock("inner", started_at=NOW):
        pass
    assert err.value.code == "store_locked"


def test_the_holder_text_is_the_last_writers_and_survives_release(env):
    with lock.store_write_lock("gc", started_at=NOW):
        pass
    assert lock.lock_path().read_text().startswith('{"command":"gc","pid":')
    child = start_holder(env)  # a stale file from the previous holder is overwritten by the new one
    try:
        with pytest.raises(GateError) as err, lock.store_write_lock("gc", started_at=NOW):
            pass
        assert str(os.getpid()) not in str(err.value)
    finally:
        child.kill()
        child.wait()


@pytest.mark.parametrize("content", [b"not json", b'{"pid": "1; rm -rf /", "command": "x"}', b'{"pid": 5, "command": "evil\\u001b[2Jcmd"}', b"\xff\xfe", b'{"pid": -3, "command": "gc"}'])
def test_untrusted_holder_text_is_never_echoed(content):
    assert lock._holder_text(content) == "the last holder is unknown"


def test_a_symlinked_lock_file_is_refused_and_its_target_untouched(env):
    target = env.tmp / "elsewhere"
    target.write_text("keep")
    lock.lock_path().symlink_to(target)
    with pytest.raises(GateError) as err, lock.store_write_lock("gc", started_at=NOW):
        pass
    assert err.value.code == "lock_file" and target.read_text() == "keep"


def test_a_directory_in_place_of_the_lock_file_is_refused(env):
    lock.lock_path().mkdir()
    with pytest.raises(GateError) as err, lock.store_write_lock("gc", started_at=NOW):
        pass
    assert err.value.code == "lock_file"


def test_a_missing_store_is_refused_not_created(tmp_path, monkeypatch):
    from visual_assets.store import config

    monkeypatch.setattr(config, "CATALOG_ROOT", tmp_path / "nope")
    with pytest.raises(GateError) as err, lock.store_write_lock("gc", started_at=NOW):
        pass
    assert err.value.code == "store_missing" and not (tmp_path / "nope").exists()


def test_non_linux_is_refused_at_acquire_time_not_at_import(env, monkeypatch):
    monkeypatch.setattr(sys, "platform", "darwin")
    with pytest.raises(GateError) as err, lock.store_write_lock("gc", started_at=NOW):
        pass
    assert err.value.code == "lock_unsupported" and not lock.lock_path().exists()
    assert "import fcntl" not in Path(lock.__file__).read_text().split("def ")[0]  # fcntl is imported inside the acquire, so importing the module works anywhere


def test_a_bad_holder_name_or_timestamp_is_refused(env):
    for name, started in (("GC; rm", NOW), ("gc", "yesterday")):
        with pytest.raises(Exception), lock.store_write_lock(name, started_at=started):
            pass


def test_each_data_root_has_its_own_lock(env, tmp_path, monkeypatch):
    from visual_assets.store import config

    other = tmp_path / "other-catalog"
    other.mkdir()
    with lock.store_write_lock("gc", started_at=NOW):
        monkeypatch.setattr(config, "CATALOG_ROOT", other)
        with lock.store_write_lock("gc", started_at=NOW):  # another checkout's store is not blocked by this one
            assert (other / lock.LOCK_NAME).is_file()


def test_every_cli_command_is_classified_exactly_once():
    commands = set(cli._parser()._subparsers._group_actions[0].choices)
    groups = (cli.WRITING_COMMANDS, cli.READ_ONLY_COMMANDS, cli.CONDITIONAL_COMMANDS)
    assert set().union(*groups) == commands
    assert sum(len(g) for g in groups) == len(commands)  # no command in two groups


@pytest.mark.parametrize("argv, expected", [
    (["intake", "d"], "intake"), (["review", "in-0123456789abcdef"], "review"), (["build"], "build"), (["release", "--catalog-id", "c", "--release-id", "rc-0001"], "release"),
    (["export-runtime", "--catalog-id", "c", "--release-id", "rc-0001", "--out", "o"], "export-runtime"),
    (["gc", "--delete"], "gc"), (["gc"], None), (["deletions"], None), (["deletions", "--archive"], "deletions"),
    (["draft", "keep", "in-0123456789abcdef", "--set", "s", "--as", "k"], "draft keep"), (["draft", "verify"], None),
    (["list"], None), (["show", "x"], None), (["audit"], None), (["verify"], None),
])
def test_which_invocations_take_the_lock(argv, expected):
    args = cli._parser().parse_args(argv)
    assert cli.lock_name(args) == expected


def test_draft_export_and_draft_drop_take_the_lock():
    parser = cli._parser()
    for sub in ("export", "drop", "keep"):
        assert sub in cli._LOCKED_DRAFT
    assert parser.parse_args(["draft", "verify"]).draft_command == "verify" and "verify" not in cli._LOCKED_DRAFT


def test_a_writing_command_really_holds_the_lock_while_it_runs(env, monkeypatch):
    seen = {}

    def probe(args):
        try:
            with lock.store_write_lock("probe", started_at=NOW):
                seen["free"] = True
        except GateError:
            seen["free"] = False
        return 0

    monkeypatch.setattr(cli, "_run", probe)
    for argv in (["gc", "--delete"], ["build"], ["export-runtime", "--catalog-id", "c", "--release-id", "rc-0001", "--out", "o"], ["draft", "export", "s", "o"]):
        seen.clear()
        try:
            cli.main(argv)
        except SystemExit:
            continue
        assert seen == {"free": False}, argv
    seen.clear()
    cli.main(["audit"])
    assert seen == {"free": True}


def test_human_gated_refusals_leave_no_lock_file(env, capsys, monkeypatch):
    monkeypatch.setattr(cli, "_stdin_is_tty", lambda: False)
    assert cli.main(["revoke", "in-0123456789abcdef", "--reason", "x", "--approver", "a", "--approver-role", "r"]) == 2
    assert not lock.lock_path().exists()


def test_the_mcp_submit_takes_the_lock(env, monkeypatch):
    from visual_assets.drawing.server import store_readonly_tools as tools

    seen = {}
    monkeypatch.setattr(tools.handoff, "handoff_directory", lambda _id: env.tmp)

    def fake_intake(directory, created_at):
        try:
            with lock.store_write_lock("probe", started_at=NOW):
                seen["free"] = True
        except GateError:
            seen["free"] = False
        raise GateError("stop", "stop here")

    monkeypatch.setattr(tools.intake_api, "intake", fake_intake)
    with pytest.raises(ValueError):
        tools.submit_candidate.fn("hf-x") if hasattr(tools.submit_candidate, "fn") else tools.submit_candidate("hf-x")
    assert seen == {"free": False}


def test_snapshot_helper_hides_only_the_lock_file(env):
    (env.catalog / ".store.lock").write_text("x")
    (env.catalog / "other").write_text("y")
    assert set(snapshot(env.catalog)) == {"other"}
