"""`python -m visual_assets.store`: exit codes and output (0 passed, 1 quarantined, 2 refused/error)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from tests.visual_assets.store import builders as b
from visual_assets.store import cli

REPO = Path(__file__).resolve().parents[4]


@pytest.fixture(autouse=True)
def fixed_clock(monkeypatch):
    monkeypatch.setattr(cli, "_now", lambda: "2026-03-03T03:03:03Z")


@pytest.fixture
def good(tmp_path):
    package, source, preview = b.good_files()
    return b.write_dir(tmp_path / "good", package, source, preview)


@pytest.fixture
def bad(tmp_path):
    return b.write_dir(tmp_path / "bad", *b.bad_files())


def test_intake_exit_codes(good, bad, roots, capsys):
    assert cli.main(["intake", str(good)]) == 0
    assert "PASSED" in capsys.readouterr().out
    assert cli.main(["intake", str(bad)]) == 1
    out = capsys.readouterr().out
    assert "QUARANTINED" in out and "SOURCE_BAD_MAGIC" in out
    assert cli.main(["intake", str(good.parent / "missing")]) == 2
    assert "error: not_found" in capsys.readouterr().err


def test_the_clock_is_read_only_here(good, roots, capsys):
    cli.main(["intake", str(good)])
    intake_id = capsys.readouterr().out.split()[0]
    cli.main(["show", intake_id])
    assert intake_id in capsys.readouterr().out
    from visual_assets.store.intake import show

    assert show(intake_id).created_at == "2026-03-03T03:03:03Z"


def test_list_show_and_review(good, bad, roots, capsys):
    cli.main(["intake", str(good)])
    good_id = capsys.readouterr().out.split()[0]
    cli.main(["intake", str(bad)])
    bad_id = capsys.readouterr().out.split()[0]
    assert cli.main(["list"]) == 0
    listing = capsys.readouterr().out
    assert good_id in listing and bad_id in listing and "UNREADABLE" not in listing
    assert cli.main(["show", bad_id]) == 0 and "SOURCE_BAD_MAGIC" in capsys.readouterr().out
    assert cli.main(["review", good_id]) == 0
    assert str(roots[1] / good_id) in capsys.readouterr().out
    assert cli.main(["review", bad_id]) == 2 and "not_passed" in capsys.readouterr().err
    assert cli.main(["show", "in-0000000000000000"]) == 2
    assert cli.main(["review", "../x"]) == 2


def test_unknown_commands_and_missing_arguments_are_usage_errors(capsys):
    for argv in ([], ["adopt", "x"], ["intake"], ["revoke"], ["gc"], ["build"]):
        with pytest.raises(SystemExit) as err:
            cli.main(argv)
        assert err.value.code == 2


def test_the_module_runs_as_a_script_and_has_no_gate_commands():
    env = {**os.environ, "PYTHONPATH": str(REPO)}  # inherit: user-site packages (pydantic) must stay importable
    run = subprocess.run([sys.executable, "-m", "visual_assets.store", "--help"], capture_output=True, text=True, env=env, cwd=REPO)
    assert run.returncode == 0
    for command in ("intake", "review", "list", "show"):
        assert command in run.stdout
    for gate in ("adopt", "revoke", "build", "release", "gc", "verify"):
        assert gate not in run.stdout.split("positional arguments")[-1].split("options")[0], gate
