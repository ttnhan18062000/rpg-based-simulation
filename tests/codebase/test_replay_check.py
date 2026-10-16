"""Unit tests for `codebase.reports.replay_check` against a fake CLI (no real simulation)."""

import sys
from pathlib import Path

import pytest

from codebase.reports import replay_check

FAKE_CLI = """
import os, sys, time
from pathlib import Path

mode = os.environ.get("FAKE_MODE", "same")
counter = Path("counter.txt")
n = int(counter.read_text()) + 1 if counter.exists() else 1
counter.write_text(str(n))
with open("contracts.txt", "a") as f:
    f.write(os.environ.get("RPG_SIGNAL_CONTRACT", "<unset>") + "\\n")
Path("data/runs").mkdir(parents=True, exist_ok=True)
Path("data/runs/run_1_2_%d_abc123" % os.getpid()).mkdir()
if mode == "hang":
    time.sleep(60)
if mode == "nohash":
    print("Simulation finished")
    sys.exit(0)
if mode == "crash":
    print("Final State Hash: deadbeef")
    sys.exit(3)
live = os.environ.get("RPG_SIGNAL_CONTRACT") is None
differ = mode == "differ" or (mode == "live_differ" and live)
print("Final State Hash: %s" % ("h%d" % n if differ else "same"))
"""


@pytest.fixture
def fake_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A fake repo root holding a fake CLI script and a foreign run dir."""
    (tmp_path / "fake_cli.py").write_text(FAKE_CLI)
    foreign = tmp_path / "data" / "runs" / "run_9_9_1_ffffff"
    foreign.mkdir(parents=True)
    monkeypatch.delenv("RPG_SIGNAL_CONTRACT", raising=False)
    return tmp_path


def _builder(seed: int, ticks: int) -> list[str]:
    return [sys.executable, "fake_cli.py"]


def _run(repo: Path, *argv: str) -> int:
    return replay_check.main(list(argv), command_builder=_builder, repo_root=repo)


def test_parse_final_hash_takes_last_line_and_ignores_noise() -> None:
    """The hash is the last anchored `Final State Hash:` line; no such line gives None."""
    out = "INFO Final State Hash: nope\nFinal State Hash: aa11\nReplay Artifacts: x\nFinal State Hash:   bb22  \n"
    assert replay_check.parse_final_hash(out) == "bb22"
    assert replay_check.parse_final_hash("Simulation finished\n") is None


def test_match_exits_zero_and_prints_both_hashes(
    fake_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Two equal hashes print MATCH and exit 0."""
    assert _run(fake_repo) == 0
    out = capsys.readouterr().out
    assert out.count("same") == 2
    assert "MATCH" in out and "DIFFER" not in out


def test_differ_exits_one(
    fake_repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Two different hashes print DIFFER and exit 1."""
    monkeypatch.setenv("FAKE_MODE", "differ")
    assert _run(fake_repo) == 1
    assert "DIFFER" in capsys.readouterr().out


@pytest.mark.parametrize("mode", ["crash", "nohash"])
def test_crash_or_missing_hash_exits_two(
    fake_repo: Path, monkeypatch: pytest.MonkeyPatch, mode: str
) -> None:
    """A non-zero exit or a missing hash line is 'could not run', exit 2."""
    monkeypatch.setenv("FAKE_MODE", mode)
    assert _run(fake_repo) == 2


def test_timeout_exits_two_and_cleans_up(
    fake_repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A hung run is killed, reported, exits 2, and its run dir is still removed."""
    monkeypatch.setenv("FAKE_MODE", "hang")
    assert _run(fake_repo, "--timeout", "1") == 2
    assert "timed out" in capsys.readouterr().out
    assert sorted(p.name for p in (fake_repo / "data" / "runs").iterdir()) == [
        "run_9_9_1_ffffff"
    ]


def test_canonical_env_is_set_on_both_runs_and_live_is_off_by_default(
    fake_repo: Path,
) -> None:
    """Both runs get the Canonical env var, and no live pair runs without `--live`."""
    assert _run(fake_repo) == 0
    assert (fake_repo / "contracts.txt").read_text().split() == [
        "canonical",
        "canonical",
    ]


def test_live_prints_label_and_never_changes_exit_code(
    fake_repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """`--live` prints the known-gap label, runs on the unset contract, and exit stays 0."""
    monkeypatch.setenv("FAKE_MODE", "live_differ")
    assert _run(fake_repo, "--live") == 0
    out = capsys.readouterr().out
    assert "expected to differ today (known gap, #585)" in out
    assert (fake_repo / "contracts.txt").read_text().split() == ["canonical"] * 2 + [
        "<unset>"
    ] * 2


def test_canonical_differ_with_live_still_exits_one(
    fake_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The Canonical result alone decides the exit code when `--live` is given."""
    monkeypatch.setenv("FAKE_MODE", "differ")
    assert _run(fake_repo, "--live") == 1


def test_cleanup_removes_only_its_own_run_dirs(fake_repo: Path) -> None:
    """Only dirs whose embedded pid is a child of this check are removed."""
    other = fake_repo / "data" / "runs" / "run_5_5_424242_abcdef"
    other.mkdir()
    assert _run(fake_repo, "--live") == 0
    assert sorted(p.name for p in (fake_repo / "data" / "runs").iterdir()) == [
        "run_5_5_424242_abcdef",
        "run_9_9_1_ffffff",
    ]


def test_own_run_dirs_matches_pid_only(tmp_path: Path) -> None:
    """The pid match is exact: other pids, other names, files and a missing root are ignored."""
    for name in ("run_1_2_77_ab", "run_1_2_770_ab", "run_1_2_77_zz", "other_1_2_77_ab"):
        (tmp_path / name).mkdir()
    (tmp_path / "run_1_2_77_cd").write_text("a file, not a dir")
    assert [p.name for p in replay_check.own_run_dirs(tmp_path, 77)] == [
        "run_1_2_77_ab"
    ]
    assert replay_check.own_run_dirs(tmp_path / "missing", 77) == []
