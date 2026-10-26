"""tools/graphify_shim.py: link ~/.local/bin/graphify to the pinned venv graphify, and the SessionStart advisory.

Fixtures are fake venvs (a script whose shebang is a stub `python` that prints a version), never the host's graphify.
"""

from __future__ import annotations

import os
import stat
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from tools import graphify_shim as gs  # noqa: E402

PIN = "0.9.70"


def _exe(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)
    return path


def _fake_python(path: Path, version: str | None) -> Path:
    body = f"#!/bin/sh\necho {version}\n" if version else "#!/bin/sh\nexit 1\n"
    return _exe(path, body)


@pytest.fixture
def world(tmp_path):
    main = tmp_path / "main"
    (main).mkdir()
    (main / gs.REQUIREMENTS).write_text(f"torch==1\ngraphifyy=={PIN}\n", encoding="utf-8")
    bin_dir = tmp_path / "home" / ".local" / "bin"
    bin_dir.mkdir(parents=True)
    return main, bin_dir, tmp_path


def _venv(main: Path, version: str | None):
    py = _fake_python(main / ".venv-knowledge" / "bin" / "python3", version)
    return _exe(main / ".venv-knowledge" / "bin" / "graphify", f"#!{py}\nfrom graphify.__main__ import main\n")


def _pip_script(bin_dir: Path):
    return _exe(bin_dir / "graphify", "#!/usr/bin/python3\n# -*- coding: utf-8 -*-\nfrom graphify.__main__ import main\n")


def _uv_symlink(tmp: Path, bin_dir: Path):
    real = _exe(tmp / "uv" / "tools" / "graphifyy" / "bin" / "graphify", "#!/x/python\nfrom graphify.__main__ import main\n")
    (bin_dir / "graphify").symlink_to(real)


def test_pin_is_read_from_requirements(world):
    assert gs.pinned_version(world[0]) == PIN
    assert gs.pinned_version(world[0] / "nowhere") is None


def test_absent_target_is_created(world):
    main, bin_dir, _ = world
    venv = _venv(main, PIN)
    code, msg = gs.link(main, main, bin_dir)
    assert code == 0 and "created" in msg
    assert (bin_dir / "graphify").is_symlink() and os.path.realpath(bin_dir / "graphify") == str(venv.resolve())


def test_pip_user_site_script_is_replaceable(world):
    main, bin_dir, _ = world
    _venv(main, PIN)
    _pip_script(bin_dir)
    code, msg = gs.link(main, main, bin_dir)
    assert code == 0 and gs.PIP_SCRIPT in msg and (bin_dir / "graphify").is_symlink()


def test_uv_tool_shim_is_replaceable(world):
    main, bin_dir, tmp = world
    _venv(main, PIN)
    _uv_symlink(tmp, bin_dir)
    code, msg = gs.link(main, main, bin_dir)
    assert code == 0 and gs.UV_TOOL in msg
    assert os.path.realpath(bin_dir / "graphify").endswith(".venv-knowledge/bin/graphify")
    assert (tmp / "uv" / "tools" / "graphifyy" / "bin" / "graphify").is_file()  # the uv tool itself is untouched


def test_uv_tool_script_with_its_interpreter_in_the_shebang_is_replaceable(world):
    main, bin_dir, _ = world
    _venv(main, PIN)
    _exe(bin_dir / "graphify", "#!/h/.local/share/uv/tools/graphifyy/bin/python\nfrom graphify.__main__ import main\n")
    assert gs.link(main, main, bin_dir)[0] == 0


def test_foreign_binary_is_refused_and_left_alone(world):
    main, bin_dir, _ = world
    _venv(main, PIN)
    foreign = _exe(bin_dir / "graphify", "#!/bin/sh\necho some other tool\n")
    code, msg = gs.link(main, main, bin_dir)
    assert code == 3 and "REFUSED" in msg
    assert not foreign.is_symlink() and "some other tool" in foreign.read_text()


def test_foreign_symlink_is_refused(world):
    main, bin_dir, tmp = world
    _venv(main, PIN)
    other = _exe(tmp / "elsewhere" / "graphify", "#!/bin/sh\n")
    (bin_dir / "graphify").symlink_to(other)
    assert gs.link(main, main, bin_dir)[0] == 3
    assert os.path.realpath(bin_dir / "graphify") == str(other.resolve())


def test_already_linked_is_a_no_op(world):
    main, bin_dir, _ = world
    _venv(main, PIN)
    assert gs.link(main, main, bin_dir)[0] == 0
    code, msg = gs.link(main, main, bin_dir)
    assert code == 0 and "already linked" in msg


def test_missing_venv_graphify_fails_loudly_with_the_install_command_and_changes_nothing(world):
    main, bin_dir, _ = world
    pip = _pip_script(bin_dir)
    before = pip.read_text()
    code, msg = gs.link(main, main, bin_dir)
    assert code == 2 and "is not installed" in msg
    assert f"-m pip install graphifyy=={PIN}" in msg and f"uv pip install --python" in msg and str(main / ".venv-knowledge" / "bin" / "python3") in msg
    assert not pip.is_symlink() and pip.read_text() == before


def test_version_mismatch_fails_loudly(world):
    main, bin_dir, _ = world
    _venv(main, "0.8.39")
    _pip_script(bin_dir)
    code, msg = gs.link(main, main, bin_dir)
    assert code == 2 and "0.8.39" in msg and PIN in msg and not (bin_dir / "graphify").is_symlink()


def test_dry_run_changes_nothing(world):
    main, bin_dir, _ = world
    _venv(main, PIN)
    pip = _pip_script(bin_dir)
    code, msg = gs.link(main, main, bin_dir, dry_run=True)
    assert code == 0 and "would replace" in msg and not pip.is_symlink()


def test_advisory_names_a_stray_version_and_is_silent_when_pinned_or_broken(world):
    main, bin_dir, tmp = world
    stray_py = _fake_python(tmp / "stray" / "python", "0.6.7")
    stray = _exe(tmp / "stray" / "graphify", f"#!{stray_py}\n")
    line = gs.advisory_line(main, which=lambda _n: str(stray))
    assert "0.6.7" in line and PIN in line and "make graphify-shim" in line
    ok_py = _fake_python(tmp / "ok" / "python", PIN)
    assert gs.advisory_line(main, which=lambda _n: str(_exe(tmp / "ok" / "graphify", f"#!{ok_py}\n"))) == ""
    assert gs.advisory_line(main, which=lambda _n: None) == ""  # no graphify on PATH
    bad_py = _fake_python(tmp / "bad" / "python", None)
    assert gs.advisory_line(main, which=lambda _n: str(_exe(tmp / "bad" / "graphify", f"#!{bad_py}\n"))) == ""
    assert gs.advisory_line(main / "nowhere", which=lambda _n: str(stray)) == ""  # no pin to compare with
    boom = gs.advisory_line(main, which=lambda _n: (_ for _ in ()).throw(RuntimeError("x")))
    assert boom == ""


def test_a_slow_version_probe_fails_open(world):
    main, _, tmp = world
    slow_py = _exe(tmp / "slow" / "python", "#!/bin/sh\nsleep 5\necho 0.1\n")
    slow = _exe(tmp / "slow" / "graphify", f"#!{slow_py}\n")
    assert gs.advisory_line(main, which=lambda _n: str(slow), timeout=0.3) == ""


def test_settings_json_and_claude_md_do_not_reference_the_shim():
    # the owner decision leaves both governing files untouched
    for name in (".claude/settings.json", "CLAUDE.md"):
        assert "graphify_shim" not in (_ROOT / name).read_text(encoding="utf-8")
