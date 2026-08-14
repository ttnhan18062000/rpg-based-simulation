"""No-live-consent-dependency architecture guard (TCK-20260730-CODEX-RUNTIME-SHADOW, Step 11).

Proves this package's entire test suite runs unconditionally — no live-consent env var gate is
needed, since nothing in tools/agent_codex_runtime_shadow/ ever invokes a real Codex CLI process.
Contrast with tests/agent_replay_codex/'s ~5-6 tests that require
CODEX_REPLAY_PARITY_LIVE_CONSENT=1 (via its conftest.py's `real_codex_replay` session fixture) and
skip cleanly otherwise — that pattern is the anti-pattern to avoid copying into this package's
tests, not a precedent to mirror here.

Deliberately scans only actual code shapes that could gate a test (`skipif`/`skip` decorators,
`os.environ.get`/`os.getenv` calls) rather than every string constant in the file — a blanket
string-constant scan would false-positive on this very file's own docstring, which necessarily
names the marker it is proving absent from actual gating code.
"""
from __future__ import annotations

import ast
from pathlib import Path

_TEST_DIR = Path(__file__).resolve().parent

_FORBIDDEN_CONSENT_MARKERS = ("CODEX_REPLAY_PARITY_LIVE_CONSENT", "LIVE_CONSENT")
_ENV_LOOKUP_CALL_TAILS = {("os", "environ", "get"), ("os", "getenv")}


def _test_py_files() -> list[Path]:
    files = sorted(_TEST_DIR.glob("test_*.py"))
    assert files, f"no test_*.py files found under {_TEST_DIR} — scan would be vacuous"
    return files


def _dotted_name(node: ast.expr) -> str | None:
    parts: list[str] = []
    current = node
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if isinstance(current, ast.Name):
        parts.append(current.id)
        return ".".join(reversed(parts))
    return None


def test_new_package_test_suite_never_requires_live_consent():
    for path in _test_py_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                for decorator in node.decorator_list:
                    decorator_src = ast.dump(decorator)
                    for marker in _FORBIDDEN_CONSENT_MARKERS:
                        assert marker not in decorator_src, (
                            f"{path}: {node.name} is gated on a live-consent marker "
                            f"{marker!r} — this package's suite must run unconditionally"
                        )
            if isinstance(node, ast.Call):
                dotted = _dotted_name(node.func)
                if dotted in ("os.environ.get", "os.getenv", "environ.get", "getenv"):
                    for arg in node.args:
                        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                            for marker in _FORBIDDEN_CONSENT_MARKERS:
                                assert marker not in arg.value, (
                                    f"{path}: {dotted}({arg.value!r}) reads a live-consent env "
                                    "var — this package's suite must run unconditionally"
                                )


def test_no_conftest_fixture_requiring_live_consent_exists_in_this_package():
    conftest_path = _TEST_DIR / "conftest.py"
    assert not conftest_path.exists(), (
        "tests/agent_codex_runtime_shadow/ must not define its own conftest.py fixture requiring "
        "live consent — unlike tests/agent_replay_codex/conftest.py's real_codex_replay fixture, "
        "no fixture in this package should ever gate on a real Codex invocation"
    )
