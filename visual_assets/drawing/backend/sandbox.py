"""Run the Aseprite binary inside a bwrap sandbox: no network, read-only system, one job directory."""

from __future__ import annotations

import subprocess
from pathlib import Path

from visual_assets.drawing import config
from visual_assets.drawing.errors import AdapterError


def bwrap(job: Path, argv: list[str]) -> subprocess.CompletedProcess:
    home = "/home/sandbox"
    cmd = [
        "bwrap",
        "--unshare-all",  # includes network
        "--die-with-parent",
        "--new-session",
        "--clearenv",
        "--setenv", "HOME", home,
        "--setenv", "PATH", "/usr/bin",
        "--ro-bind", "/usr", "/usr",
        "--symlink", "usr/lib", "/lib",
        "--symlink", "usr/lib64", "/lib64",
        "--symlink", "usr/bin", "/bin",
        "--ro-bind", "/etc/ld.so.cache", "/etc/ld.so.cache",
        "--proc", "/proc",
        "--dev", "/dev",
        "--tmpfs", "/tmp",
        "--tmpfs", home,
        "--ro-bind", str(config.LUA_PATH.parent), "/lua",
        "--bind", str(job), "/job",
        "--chdir", "/job",
        config.ASEPRITE, "-b", *argv,
    ]
    try:
        return subprocess.run(
            cmd, capture_output=True, timeout=config.JOB_TIMEOUT_S, stdin=subprocess.DEVNULL
        )
    except subprocess.TimeoutExpired as exc:
        raise AdapterError(f"aseprite timed out after {config.JOB_TIMEOUT_S}s") from exc
