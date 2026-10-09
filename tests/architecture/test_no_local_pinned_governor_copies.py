"""Guards against a further local copy of the NORMAL-pinned ``ResourceGovernor``.

TCK-20261009-PINNED-NORMAL-GOVERNOR-SHARED-TEST-HELPER: tests that run a real ``Kernel`` pin the governor to ``RuntimeMode.NORMAL`` (with a no-op
``force_mode``) so the outcome does not depend on host speed. Several files each carried an identical local class; the shared one is
``tests/helpers/kernel_pinning.py::PinnedNormalGovernor``. A subclass is flagged only when it is an exact copy: it subclasses ``ResourceGovernor``,
its ``_get_indicated_mode`` is a single ``return RuntimeMode.NORMAL`` and its ``force_mode`` is a bare ``return None`` / ``return`` / ``pass``.
Overrides with another purpose (a different pinned mode, a recording ``force_mode``) are not flagged.
"""
from __future__ import annotations

import ast
from pathlib import Path

_TESTS_ROOT = Path(__file__).resolve().parents[1]
_HELPERS_DIR = _TESTS_ROOT / "helpers"
_SHARED_HELPER = "tests/helpers/kernel_pinning.py"


def _extends_resource_governor(cls: ast.ClassDef) -> bool:
    for base in cls.bases:
        if isinstance(base, ast.Name) and base.id == "ResourceGovernor":
            return True
        if isinstance(base, ast.Attribute) and base.attr == "ResourceGovernor":
            return True
    return False


def _method(cls: ast.ClassDef, name: str) -> ast.FunctionDef | None:
    for node in cls.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    return None


def _body_without_docstring(fn: ast.FunctionDef) -> list[ast.stmt]:
    body = list(fn.body)
    if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant) and isinstance(body[0].value.value, str):
        body = body[1:]
    return body


def _returns_normal(fn: ast.FunctionDef) -> bool:
    body = _body_without_docstring(fn)
    if len(body) != 1 or not isinstance(body[0], ast.Return) or not isinstance(body[0].value, ast.Attribute):
        return False
    value = body[0].value
    return value.attr == "NORMAL" and isinstance(value.value, ast.Name) and value.value.id == "RuntimeMode"


def _is_noop(fn: ast.FunctionDef) -> bool:
    body = _body_without_docstring(fn)
    if not body:
        return True  # a docstring-only body
    if len(body) != 1:
        return False
    stmt = body[0]
    if isinstance(stmt, ast.Pass):
        return True
    if isinstance(stmt, ast.Return):
        return stmt.value is None or (isinstance(stmt.value, ast.Constant) and stmt.value.value is None)
    return False


def find_pinned_governor_copies(source: str) -> list[str]:
    """Names of classes in ``source`` that are exact copies of the shared NORMAL-pinned governor."""
    found: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.ClassDef) or not _extends_resource_governor(node):
            continue
        indicated = _method(node, "_get_indicated_mode")
        force = _method(node, "force_mode")
        if indicated is not None and force is not None and _returns_normal(indicated) and _is_noop(force):
            found.append(node.name)
    return found


def test_no_test_file_defines_its_own_normal_pinned_governor():
    offenders: list[str] = []
    for path in sorted(_TESTS_ROOT.rglob("*.py")):
        if _HELPERS_DIR in path.parents or path.resolve() == Path(__file__).resolve():
            continue
        source = path.read_text(encoding="utf-8")
        if "ResourceGovernor" not in source:
            continue
        for name in find_pinned_governor_copies(source):
            offenders.append(f"{path.relative_to(_TESTS_ROOT.parent).as_posix()}::{name}")
    assert not offenders, f"Local NORMAL-pinned governor copies found; import PinnedNormalGovernor from {_SHARED_HELPER} instead: {offenders}"


_POSITIVE_COPY = '''
from src.core.governance import RuntimeMode
from src.engine.governor import ResourceGovernor


class _Local(ResourceGovernor):
    """Pins NORMAL."""

    def _get_indicated_mode(self, profile, signals):
        return RuntimeMode.NORMAL

    def force_mode(self, mode, status, current_tick):
        return None  # comment
'''

_POSITIVE_ATTRIBUTE_BASE_AND_PASS = '''
import src.engine.governor as governor_module
from src.core.governance import RuntimeMode


class _Local(governor_module.ResourceGovernor):
    def _get_indicated_mode(self, profile, signals):
        return RuntimeMode.NORMAL

    def force_mode(self, mode, status, current_tick):
        pass
'''

_NEGATIVE_DEGRADED_PIN = '''
from src.core.governance import RuntimeMode
from src.engine.governor import ResourceGovernor


class _Degraded(ResourceGovernor):
    def _get_indicated_mode(self, profile, signals):
        return RuntimeMode.DEGRADED

    def force_mode(self, mode, status, current_tick):
        return None
'''

_NEGATIVE_RECORDING_FORCE_MODE = '''
from src.core.governance import RuntimeMode
from src.engine.governor import ResourceGovernor


class _Recording(ResourceGovernor):
    def __init__(self):
        super().__init__()
        self.forced = []

    def _get_indicated_mode(self, profile, signals):
        return RuntimeMode.NORMAL

    def force_mode(self, mode, status, current_tick):
        self.forced.append(mode)
        return super().force_mode(mode, status, current_tick)
'''

_NEGATIVE_NOT_A_GOVERNOR = '''
from src.core.governance import RuntimeMode


class _Other:
    def _get_indicated_mode(self, profile, signals):
        return RuntimeMode.NORMAL

    def force_mode(self, mode, status, current_tick):
        return None
'''


def test_guard_flags_an_exact_copy():
    assert find_pinned_governor_copies(_POSITIVE_COPY) == ["_Local"]


def test_guard_flags_an_exact_copy_with_a_module_attribute_base_and_a_pass_body():
    assert find_pinned_governor_copies(_POSITIVE_ATTRIBUTE_BASE_AND_PASS) == ["_Local"]


def test_guard_does_not_flag_a_governor_pinned_to_another_mode():
    assert find_pinned_governor_copies(_NEGATIVE_DEGRADED_PIN) == []


def test_guard_does_not_flag_a_recording_force_mode_that_calls_super():
    assert find_pinned_governor_copies(_NEGATIVE_RECORDING_FORCE_MODE) == []


def test_guard_does_not_flag_a_class_that_is_not_a_governor():
    assert find_pinned_governor_copies(_NEGATIVE_NOT_A_GOVERNOR) == []


def test_the_real_negative_files_stay_unflagged_and_the_shared_helper_is_the_only_pin():
    repo_root = _TESTS_ROOT.parent
    for rel in ("tests/integration/world/test_camp_raid_targeting.py", "tests/integration/kernel/test_tick_budget_report_only.py"):
        assert find_pinned_governor_copies((repo_root / rel).read_text(encoding="utf-8")) == [], rel
    assert find_pinned_governor_copies((repo_root / _SHARED_HELPER).read_text(encoding="utf-8")) == ["PinnedNormalGovernor"]
