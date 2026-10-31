"""The installed-runtime-dependency fingerprint (TCK-20261025-PERF-RECORD-IDENTITY-PINS-INSTALLED-RUNTIME-DEPENDENCIES), against a fake metadata provider."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from src.perf.dependency_fingerprint import (
    MISSING,
    SCHEME,
    InstalledMetadata,
    collect_dependency_fingerprint,
    fingerprint_of,
    project_dependencies,
)


class FakeMetadata:
    """``{name: (version, [Requires-Dist, ...])}``; a name not in it is not installed."""

    def __init__(self, installed: Dict[str, tuple]) -> None:
        self.installed = installed

    def version(self, name: str) -> Optional[str]:
        return self.installed[name][0] if name in self.installed else None

    def requires(self, name: str) -> List[str]:
        return list(self.installed[name][1]) if name in self.installed else []


ROOTS = ["web>=1", "tool[fast]>=2"]


def _env(**overrides: tuple) -> Dict[str, tuple]:
    installed = {
        "web": ("1.0", ["core>=1", "devonly-helper; extra == 'test'"]),
        "core": ("3.0", []),
        "tool": ("2.0", ["fastlib>=1; extra == 'fast'", "slowlib>=1; extra == 'slow'"]),
        "fastlib": ("1.5", []),
        "slowlib": ("1.1", []),
        "devonly-helper": ("9.9", []),
        "pytest": ("8.0", []),
    }
    installed.update(overrides)
    return installed


def _fp(installed: Dict[str, tuple], roots: List[str] = ROOTS) -> str:
    return fingerprint_of(roots, FakeMetadata(installed))[0]


def test_the_value_carries_the_scheme_tag_and_counts_the_hashed_lines() -> None:
    value, count = fingerprint_of(ROOTS, FakeMetadata(_env()))
    assert value.startswith(f"{SCHEME}:") and len(value) == len(SCHEME) + 1 + 64
    assert count == 4  # web, core, tool, fastlib


def test_it_is_stable_for_one_environment() -> None:
    assert _fp(_env()) == _fp(_env())


def test_changing_the_version_of_a_closure_package_changes_it() -> None:
    assert _fp(_env(core=("3.1", []))) != _fp(_env())


def test_a_package_outside_the_closure_does_not_change_it() -> None:
    base = _fp(_env())
    assert _fp(_env(pytest=("9.9", []))) == base  # a dev-only package that nothing in the closure requires
    assert _fp(_env(slowlib=("2.0", []))) == base  # an extra that was not requested
    assert _fp(_env(**{"devonly-helper": ("0.1", [])})) == base  # required only under an extra that was not requested
    extra = dict(_env())
    extra["brand-new-dev-tool"] = ("1.0", [])
    assert _fp(extra) == base


def test_an_uninstalled_required_package_is_a_missing_line_and_changes_it() -> None:
    incomplete = _env()
    del incomplete["core"]
    assert _fp(incomplete) != _fp(_env())
    assert fingerprint_of(ROOTS, FakeMetadata(incomplete))[1] == 4  # the line is still counted, as core==MISSING
    assert MISSING == "MISSING"


def test_a_requested_extras_requirements_are_included() -> None:
    without_extra = _fp(_env(), ["web>=1", "tool>=2"])
    with_extra = _fp(_env(), ["web>=1", "tool[fast]>=2"])
    assert without_extra != with_extra
    assert _fp(_env(fastlib=("1.6", []))) != _fp(_env())  # fastlib is in the closure because the extra was requested


def test_a_marker_that_does_not_hold_for_this_interpreter_drops_the_requirement() -> None:
    gated = _env(web=("1.0", ["core>=1", "winonly>=1; sys_platform == 'win32'"]), winonly=("1.0", []))
    assert _fp(gated) == _fp(_env(web=("1.0", ["core>=1"])))


def test_names_are_canonicalised() -> None:
    assert _fp(_env(), ["Web>=1", "Tool[FAST]>=2"]) == _fp(_env())


def test_a_dependency_cycle_terminates() -> None:
    cyclic = {"a": ("1", ["b"]), "b": ("1", ["a"])}
    assert fingerprint_of(["a"], FakeMetadata(cyclic))[1] == 2


def test_unreadable_pyproject_is_unknown(tmp_path: Path) -> None:
    assert project_dependencies(tmp_path / "missing.toml") is None
    assert collect_dependency_fingerprint(pyproject=tmp_path / "missing.toml", unknown="unknown") == ("unknown", None)


def test_the_real_environment_gives_a_stable_nonempty_fingerprint() -> None:
    first, second = collect_dependency_fingerprint(), collect_dependency_fingerprint()
    assert first == second and first[0].startswith(f"{SCHEME}:") and first[1] and first[1] > 0
    assert InstalledMetadata().version("pyyaml") is not None
