"""Run the five adopted tools over `src/` and turn their output into `Finding` records.

`run_scan` writes each tool's raw JSON into one directory; `collect_findings` reads that directory
through the adapters. They are separate so the ratchet can be tested on captured output and a
scan can be reused (`python3 -m codebase.health check --from DIR`).

Tools are found next to the running interpreter first (the project environment), then on PATH.
ruff ships a `__main__`, so it is started as `python -m ruff`, which always uses the interpreter's
own environment; complexipy has no `__main__` and is only a console script, so it is looked up
beside the interpreter, falling back to PATH.
jscpd is a Node tool: it runs through `npx` at the version pinned by `JSCPD_VERSION` in the
Makefile, the one place that pin lives.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any, Collection, Sequence

from codebase.health import adapters
from codebase.health.findings import Finding
from codebase.health.line_count import load_thresholds, measure_paths, report_to_dict

SCAN_ROOT = "src"
RUFF_JSON = "ruff.json"
COMPLEXIPY_JSON = "complexipy.json"
LINE_COUNT_JSON = "line_count.json"
AST_GREP_JSON = "ast_grep.json"
AST_GREP_CONFIG = "codebase/rules/sgconfig.yml"
JSCPD_DIR = "jscpd"
JSCPD_REPORT = "jscpd-report.json"
JSCPD_CONFIG = "codebase/config/.jscpd.json"
DEFAULT_COMPLEXITY_LIMIT = 15

# jscpd needs npx and the npm registry; the others are Python tools in the project environment.
# `OFFLINE_TOOLS` is what the codebase-health snapshot uses, so a snapshot never needs the network.
TOOL_JSCPD_NAME = "jscpd"
TOOL_AST_GREP_NAME = "ast_grep"
ALL_TOOLS = ("ruff", "complexipy", TOOL_JSCPD_NAME, "line_count", TOOL_AST_GREP_NAME)
# ast-grep is a local binary from the `lint` dependency group, so it needs no network. A snapshot without it
# fails (`ToolUnavailableError`); it must never record 0 for the ast-grep keys, which would read as debt paid.
OFFLINE_TOOLS = ("ruff", "complexipy", "line_count", TOOL_AST_GREP_NAME)


class ToolUnavailableError(RuntimeError):
    """A required tool could not be started or produced no output."""


def jscpd_version(makefile: Path) -> str:
    """The version `JSCPD_VERSION ?= x.y.z` pins in the Makefile."""
    match = re.search(r"^JSCPD_VERSION\s*\??=\s*(\S+)", makefile.read_text(encoding="utf-8"), re.M)
    if match is None:
        raise ToolUnavailableError(f"{makefile}: no JSCPD_VERSION assignment found")
    return match.group(1)


def complexity_limit(pyproject: Path) -> int:
    """`max-complexity-allowed` from `[tool.complexipy]`; the default if there is no such file or table."""
    if not pyproject.is_file():
        return DEFAULT_COMPLEXITY_LIMIT
    with pyproject.open("rb") as handle:
        table = tomllib.load(handle).get("tool", {}).get("complexipy", {})
    return int(table.get("max-complexity-allowed", DEFAULT_COMPLEXITY_LIMIT))


def find_tool(name: str) -> str:
    """The path of the project-environment tool `name` (beside this Python, else on PATH); raises `ToolUnavailableError`."""
    beside = Path(sys.executable).parent / name
    found = str(beside) if beside.exists() else shutil.which(name)
    if found is None:
        raise ToolUnavailableError(f"{name} not found: install the project environment (uv sync)")
    return found


def _run(command: Sequence[str], root: Path, ok_codes: Sequence[int]) -> subprocess.CompletedProcess[str]:
    try:
        done = subprocess.run(command, cwd=root, capture_output=True, text=True, check=False)
    except OSError as exc:
        raise ToolUnavailableError(f"{command[0]}: {exc}") from exc
    if done.returncode not in ok_codes:
        raise ToolUnavailableError(f"{' '.join(command)} exited {done.returncode}: {done.stderr.strip()}")
    return done


def _scan_ruff(root: Path, out_dir: Path) -> None:
    ruff = _run([sys.executable, "-m", "ruff", "check", SCAN_ROOT, "--output-format", "json"], root, (0, 1))
    (out_dir / RUFF_JSON).write_text(ruff.stdout, encoding="utf-8")


def _scan_complexipy(root: Path, out_dir: Path) -> None:
    # The path is given explicitly: complexipy stops with an error if neither it nor a config names one.
    command = [find_tool("complexipy"), SCAN_ROOT, "-q", "--output-format", "json", "--output", str(out_dir / COMPLEXIPY_JSON)]
    _run(command, root, (0, 1))


def _scan_ast_grep(root: Path, out_dir: Path) -> None:
    # The binary is `ast-grep`, never `sg` (on Linux `sg` is shadow-utils' switch-group command).
    command = [find_tool("ast-grep"), "scan", "--config", AST_GREP_CONFIG, SCAN_ROOT, "--json=compact"]
    done = _run(command, root, (0, 1))
    (out_dir / AST_GREP_JSON).write_text(done.stdout or "[]", encoding="utf-8")


def _scan_jscpd(root: Path, out_dir: Path) -> None:
    version = jscpd_version(root / "Makefile")
    command = ["npx", "--yes", f"jscpd@{version}", SCAN_ROOT, "--config", JSCPD_CONFIG, "--output", str(out_dir / JSCPD_DIR)]
    _run(command, root, (0,))


def _scan_line_count(root: Path, out_dir: Path) -> None:
    report = measure_paths([root / SCAN_ROOT], load_thresholds(root / "pyproject.toml"), relative_to=root)
    (out_dir / LINE_COUNT_JSON).write_text(json.dumps(report_to_dict(report), indent=1), encoding="utf-8")


_SCANNERS = {
    "ruff": _scan_ruff,
    "complexipy": _scan_complexipy,
    TOOL_JSCPD_NAME: _scan_jscpd,
    "line_count": _scan_line_count,
    TOOL_AST_GREP_NAME: _scan_ast_grep,
}


def run_scan(
    root: Path, out_dir: Path, tools: Sequence[str] = ALL_TOOLS, skippable: Collection[str] = ()
) -> tuple[str, ...]:
    """Run `tools` (default: all five) over `src/`, writing each one's raw JSON to `out_dir`.

    A tool in `skippable` that cannot run is skipped, not fatal: its name is returned (callers must treat it as
    "not measured") and the scan goes on. Any other tool that cannot run raises `ToolUnavailableError`.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    skipped: list[str] = []
    for name in tools:
        try:
            _SCANNERS[name](root, out_dir)
        except ToolUnavailableError:
            if name not in skippable:
                raise
            skipped.append(name)
    return tuple(skipped)


def _load(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ToolUnavailableError(f"{path}: {exc}") from exc


def collect_findings(
    out_dir: Path, root: Path, scan_root: str = SCAN_ROOT, tools: Sequence[str] = ALL_TOOLS
) -> list[Finding]:
    """The adapters' findings for the raw output of `tools` in `out_dir`; `scan_root` is what was scanned."""
    findings: list[Finding] = []
    if "ruff" in tools:
        findings += adapters.adapt_ruff(_load(out_dir / RUFF_JSON), str(root))
    if "complexipy" in tools:
        findings += adapters.adapt_complexipy(_load(out_dir / COMPLEXIPY_JSON), complexity_limit(root / "pyproject.toml"))
    if TOOL_JSCPD_NAME in tools:
        findings += adapters.adapt_jscpd(_load(out_dir / JSCPD_DIR / JSCPD_REPORT), scan_root)
    if "line_count" in tools:
        findings += adapters.adapt_line_count(_load(out_dir / LINE_COUNT_JSON))
    if TOOL_AST_GREP_NAME in tools:
        findings += adapters.adapt_ast_grep(_load(out_dir / AST_GREP_JSON), str(root))
    return findings
