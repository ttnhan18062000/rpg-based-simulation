"""Run the four adopted tools over `src/` and turn their output into `Finding` records.

`run_scan` writes each tool's raw JSON into one directory; `collect_findings` reads that directory
through the adapters. They are separate so the ratchet can be tested on captured output and a
scan can be reused (`python3 -m tools.code_health check --from DIR`).

Tools are found next to the running interpreter first (the project environment), then on PATH.
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
from typing import Any, Sequence

from tools.code_health import adapters
from tools.code_health.findings import Finding
from tools.code_health.line_count import load_thresholds, measure_paths, report_to_dict

SCAN_ROOT = "src"
RUFF_JSON = "ruff.json"
COMPLEXIPY_JSON = "complexipy.json"
LINE_COUNT_JSON = "line_count.json"
JSCPD_DIR = "jscpd"
JSCPD_REPORT = "jscpd-report.json"
DEFAULT_COMPLEXITY_LIMIT = 15


class ToolUnavailableError(RuntimeError):
    """A required tool could not be started or produced no output."""


def jscpd_version(makefile: Path) -> str:
    """The version `JSCPD_VERSION ?= x.y.z` pins in the Makefile."""
    match = re.search(r"^JSCPD_VERSION\s*\??=\s*(\S+)", makefile.read_text(encoding="utf-8"), re.M)
    if match is None:
        raise ToolUnavailableError(f"{makefile}: no JSCPD_VERSION assignment found")
    return match.group(1)


def complexity_limit(pyproject: Path) -> int:
    """`max-complexity-allowed` from `[tool.complexipy]`."""
    with pyproject.open("rb") as handle:
        table = tomllib.load(handle).get("tool", {}).get("complexipy", {})
    return int(table.get("max-complexity-allowed", DEFAULT_COMPLEXITY_LIMIT))


def _find(name: str) -> str:
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


def run_scan(root: Path, out_dir: Path) -> None:
    """Run ruff, complexipy, jscpd and the line-count report over `src/`, writing raw JSON to `out_dir`."""
    out_dir.mkdir(parents=True, exist_ok=True)
    ruff = _run([sys.executable, "-m", "ruff", "check", SCAN_ROOT, "--output-format", "json"], root, (0, 1))
    (out_dir / RUFF_JSON).write_text(ruff.stdout, encoding="utf-8")
    _run([_find("complexipy"), "-q", "--output-format", "json", "--output", str(out_dir / COMPLEXIPY_JSON)],
         root, (0, 1))
    version = jscpd_version(root / "Makefile")
    _run(["npx", "--yes", f"jscpd@{version}", SCAN_ROOT, "--config", ".jscpd.json",
          "--output", str(out_dir / JSCPD_DIR)], root, (0,))
    report = measure_paths([root / SCAN_ROOT], load_thresholds(root / "pyproject.toml"), relative_to=root)
    (out_dir / LINE_COUNT_JSON).write_text(json.dumps(report_to_dict(report), indent=1), encoding="utf-8")


def _load(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ToolUnavailableError(f"{path}: {exc}") from exc


def collect_findings(out_dir: Path, root: Path, scan_root: str = SCAN_ROOT) -> list[Finding]:
    """Every adapter's findings for the raw output in `out_dir`; `scan_root` is the directory that was scanned."""
    limit = complexity_limit(root / "pyproject.toml")
    return [
        *adapters.adapt_ruff(_load(out_dir / RUFF_JSON), str(root)),
        *adapters.adapt_complexipy(_load(out_dir / COMPLEXIPY_JSON), limit),
        *adapters.adapt_jscpd(_load(out_dir / JSCPD_DIR / JSCPD_REPORT), scan_root),
        *adapters.adapt_line_count(_load(out_dir / LINE_COUNT_JSON)),
    ]
