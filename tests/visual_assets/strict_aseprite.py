"""Strict mode for the real-Aseprite tests (ADR D10).

`needs_aseprite` tests skip where Aseprite or bwrap is missing (CI). With `VISUAL_ASSETS_REQUIRE_ASEPRITE=1`
(set by `make visual-assets-aseprite-local`) they must fail instead, and the binary must report the pinned
`config.ASEPRITE_VERSION`. Pure functions over injected facts so the rules are unit-tested without a binary.
"""

from __future__ import annotations

import os
import re
import subprocess
from collections.abc import Mapping

ENV_VAR = "VISUAL_ASSETS_REQUIRE_ASEPRITE"


def strict_requested(env: Mapping[str, str] | None = None) -> bool:
    return (os.environ if env is None else env).get(ENV_VAR) == "1"


def parse_version(output: str) -> str | None:
    """`Aseprite 1.3.18.6-x64` -> `1.3.18.6`; None when the output has no such shape."""
    match = re.search(r"Aseprite\s+(\d+(?:\.\d+)+)", output)
    return match.group(1) if match else None


def read_version(binary: str, timeout: float = 15.0) -> str:
    """The raw `--version` output ('' when the binary cannot be run)."""
    try:
        done = subprocess.run([binary, "--version"], capture_output=True, text=True, timeout=timeout, check=False)
    except (OSError, subprocess.SubprocessError):
        return ""
    return (done.stdout + done.stderr).strip()


def strict_problem(*, binary_present: bool, bwrap_present: bool, version_output: str, pinned: str) -> str | None:
    """Why a strict run cannot proceed, or None when it can."""
    if not binary_present:
        return "strict mode: the Aseprite binary is missing (ASEPRITE_MCP_BINARY)"
    if not bwrap_present:
        return "strict mode: bwrap is missing"
    found = parse_version(version_output)
    if found != pinned:
        return f"strict mode: Aseprite reports version {found or version_output!r}, pinned {pinned!r}"
    return None
