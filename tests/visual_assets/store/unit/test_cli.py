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
    from tests.visual_assets.store.adoption_support import FakeRenderer

    monkeypatch.setattr(cli, "_renderer", lambda: FakeRenderer())  # deterministic: never the real Aseprite


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
    for argv in ([], ["adopt", "x"], ["intake"], ["revoke"], ["release"], ["frobnicate"], ["gc", "--bogus"]):
        with pytest.raises(SystemExit) as err:
            cli.main(argv)
        assert err.value.code == 2


def test_the_module_runs_as_a_script_and_only_adopt_and_revoke_are_human_only():
    env = {**os.environ, "PYTHONPATH": str(REPO)}  # inherit: user-site packages (pydantic) must stay importable
    run = subprocess.run([sys.executable, "-m", "visual_assets.store", "--help"], capture_output=True, text=True, env=env, cwd=REPO)
    assert run.returncode == 0
    commands = run.stdout.split("positional arguments")[-1].split("options")[0]
    for command in ("intake", "review", "list", "show", "audit", "verify", "build", "release", "gc", "adopt", "revoke"):
        assert command in commands, command
    assert commands.count("HUMAN ONLY") == 2  # adopt and revoke say so in their own help
    assert "activate" not in commands and "publish" not in commands  # nothing in this foundation activates anything (D6)


# --------------------------------------------------------------------------- review with the store's render, and build / release / verify / gc


def test_review_exits_1_when_the_preview_does_not_match_the_source(env, monkeypatch, capsys):
    from tests.visual_assets.store.adoption_support import MismatchRenderer, make_intake

    result = make_intake(env.tmp, reviewed=False)
    monkeypatch.setattr(cli, "_renderer", lambda: MismatchRenderer())
    assert cli.main(["review", result.intake_id]) == 1
    out = capsys.readouterr().out
    assert "DOES NOT MATCH" in out and str(env.review / result.intake_id) in out


def test_review_without_a_renderer_exits_0_and_says_nothing_was_verified(env, monkeypatch, capsys):
    from tests.visual_assets.store.adoption_support import make_intake

    result = make_intake(env.tmp, reviewed=False)
    monkeypatch.setattr(cli, "_renderer", lambda: None)
    assert cli.main(["review", result.intake_id]) == 0
    assert "UNVERIFIED" in capsys.readouterr().out


def test_build_release_verify_and_gc_at_the_command_line(env, monkeypatch, capsys):
    from tests.visual_assets.store import adoption_support as s

    s.adopted_tree(env, build=False)
    s.write_registry(env.catalog, [s.key_for("hero"), s.key_for("rock")])
    monkeypatch.setattr(cli, "_renderer", lambda: s.HashRenderer())
    assert cli.main(["build"]) == 0
    out = capsys.readouterr().out
    assert "hero--x1 r0001" in out and "built" in out
    assert cli.main(["build", "hero"]) == 0 and "unchanged" in capsys.readouterr().out
    assert cli.main(["release", "--catalog-id", "main"]) == 2  # the committed registry rules: fixture keys are refused by the CLI
    assert "registry_invalid" in capsys.readouterr().err
    assert cli.main(["verify"]) == 1  # the same fixture registry fails verification without the opt-in
    assert "REGISTRY_INVALID" in capsys.readouterr().out
    assert cli.main(["gc"]) == 0 and "generated" not in capsys.readouterr().out  # only review exports of adopted intakes are listed
    (env.catalog / "generated" / "hero--x1" / ("d" * 64 + ".png")).write_bytes(b"orphan")
    assert cli.main(["gc"]) == 0 and "would delete generated" in capsys.readouterr().out
    assert (env.catalog / "generated" / "hero--x1" / ("d" * 64 + ".png")).exists()
    assert cli.main(["gc", "--delete"]) == 0 and "deleted generated" in capsys.readouterr().out
    assert not (env.catalog / "generated" / "hero--x1" / ("d" * 64 + ".png")).exists()


def test_build_without_aseprite_exits_2_with_its_own_code(env, monkeypatch, capsys):
    monkeypatch.setattr(cli, "_renderer", lambda: None)
    from visual_assets.store.build import exporter

    monkeypatch.setattr(exporter, "default_renderer", lambda: None)
    assert cli.main(["build"]) == 2 and "renderer_unavailable" in capsys.readouterr().err
