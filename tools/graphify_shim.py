"""Make the `graphify` on PATH the pinned one (TCK-20261024-GRAPHIFY-ON-PATH-IS-NOT-THE-PINNED-VERSION).

`requirements-knowledge.txt` pins graphifyy, and `.venv-knowledge` carries it, but a bare `graphify` resolves to
`~/.local/bin/graphify`: a pip user-site script (host ubuntu, 0.6.7) or a uv-tool shim (host u24desktop, 0.8.39).
The PostToolUse edit hook and every `graphify query` an agent runs therefore use the stray version, and two versions
writing one `graphify-out/` can corrupt it (graphifyy 0.9 re-keys node IDs).

`link` points `~/.local/bin/graphify` at `<main checkout>/.venv-knowledge/bin/graphify`, once per host. It
  * checks first that the venv's graphify exists and reports the pinned version, else fails loudly with the exact
    install command (it never installs anything);
  * replaces only a pip user-site script or a uv-tool graphifyy shim, or nothing, or its own symlink; any other
    file is refused and left alone;
  * writes nothing outside the bin directory (default `~/.local/bin`), and never uses sudo.
`advisory_line` is the SessionStart advisory: one line when the `graphify` on PATH does not report the pin, empty on
any error or slowness (it fails open, like the other SessionStart checks).

Stdlib only.
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

try:
    from tools.handover_home import main_checkout_root
except ImportError:  # run as a script from tools/
    from handover_home import main_checkout_root  # type: ignore[no-redef]

REQUIREMENTS = "requirements-knowledge.txt"
VERSION_TIMEOUT_S = 3
_PIN = re.compile(r"^\s*graphifyy\s*==\s*([0-9][^\s;#]*)", re.MULTILINE)
_VERSION_CODE = "import importlib.metadata as m; print(m.version('graphifyy'))"

# classify() results
ABSENT, SHIM, PIP_SCRIPT, UV_TOOL, FOREIGN = "absent", "shim", "pip-user-site-script", "uv-tool-shim", "foreign"
REPLACEABLE = (PIP_SCRIPT, UV_TOOL)


def pinned_version(repo_root: Path) -> str | None:
    try:
        m = _PIN.search((repo_root / REQUIREMENTS).read_text(encoding="utf-8"))
    except OSError:
        return None
    return m.group(1) if m else None


def venv_graphify(main_root: Path) -> Path:
    return main_root / ".venv-knowledge" / "bin" / "graphify"


def _shebang_python(script: Path) -> Path | None:
    try:
        with open(script, "rb") as fh:
            first = fh.readline(512).decode("utf-8", "replace").strip()
    except OSError:
        return None
    if not first.startswith("#!"):
        return None
    parts = first[2:].split()
    return Path(parts[0]) if parts else None


def installed_version(script: Path, timeout: float = VERSION_TIMEOUT_S) -> str | None:
    """graphifyy version of the interpreter a graphify script runs under; None on any error or timeout."""
    python = _shebang_python(Path(os.path.realpath(script)))
    if python is None or not python.is_file():
        return None
    try:
        out = subprocess.run([str(python), "-c", _VERSION_CODE], capture_output=True, text=True, timeout=timeout,
                             stdin=subprocess.DEVNULL)
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout.strip() or None if out.returncode == 0 else None


def classify(target: Path, venv_script: Path) -> str:
    """What sits at `target`: absent, our shim, a replaceable pip script or uv-tool shim, or something foreign."""
    if not os.path.lexists(target):
        return ABSENT
    resolved = Path(os.path.realpath(target))
    if target.is_symlink():
        if resolved == Path(os.path.realpath(venv_script)):
            return SHIM
        if "/uv/tools/graphifyy/" in resolved.as_posix() + "/" and resolved.name == "graphify":
            return UV_TOOL
        return FOREIGN
    try:
        head = target.read_bytes()[:4096].decode("utf-8", "replace")
    except OSError:
        return FOREIGN
    first = head.splitlines()[0] if head else ""
    if not first.startswith("#!"):
        return FOREIGN
    if "/uv/tools/graphifyy/" in first and "from graphify.__main__ import main" in head:
        return UV_TOOL
    if "from graphify.__main__ import main" in head and "/.venv" not in first:
        return PIP_SCRIPT
    return FOREIGN


def link(main_root: Path, repo_root: Path, bin_dir: Path, dry_run: bool = False) -> tuple[int, str]:
    """(exit code, message). 0 linked or already linked; 2 venv missing or at the wrong version; 3 refused."""
    pin = pinned_version(repo_root)
    venv_script = venv_graphify(main_root)
    if pin is None:
        return 2, f"cannot read the graphifyy pin from {repo_root / REQUIREMENTS}"
    have = installed_version(venv_script) if venv_script.is_file() else None
    if have != pin:
        what = "is not installed" if have is None else f"is {have}, not the pin {pin}"
        return 2, (f"FAILED: graphifyy in {main_root / '.venv-knowledge'} {what}. Nothing was changed. Install it, then rerun:\n"
                   f"  {main_root / '.venv-knowledge' / 'bin' / 'python3'} -m pip install graphifyy=={pin}\n"
                   f"or, when that venv has no pip (built by uv): uv pip install --python "
                   f"{main_root / '.venv-knowledge' / 'bin' / 'python3'} graphifyy=={pin}\n"
                   f"(the full knowledge stack is `pip install -r {REQUIREMENTS}` into the same venv)")
    target = bin_dir / "graphify"
    kind = classify(target, venv_script)
    if kind == SHIM:
        return 0, f"already linked: {target} -> {venv_script} (graphifyy {pin}); nothing changed"
    if kind == FOREIGN:
        return 3, (f"REFUSED: {target} is neither a pip user-site graphify script nor a uv-tool graphifyy shim nor "
                   f"this shim. Left alone; move it aside yourself if it is stale.")
    verb = "would replace" if dry_run else "replaced"
    note = f"{verb} the {kind} at {target}" if kind != ABSENT else f"{'would create' if dry_run else 'created'} {target}"
    if not dry_run:
        bin_dir.mkdir(parents=True, exist_ok=True)
        tmp = bin_dir / f".graphify.shim.{os.getpid()}"
        try:
            os.symlink(venv_script, tmp)
            os.replace(tmp, target)
        finally:
            if os.path.lexists(tmp):
                os.unlink(tmp)
    return 0, f"{note}: {target} -> {venv_script} (graphifyy {pin})"


def advisory_line(repo_root: Path, which=shutil.which, timeout: float = VERSION_TIMEOUT_S) -> str:
    """One line when the `graphify` on PATH is not the pinned version; "" when it is, or on any error."""
    try:
        pin = pinned_version(repo_root)
        found = which("graphify")
        if not pin or not found:
            return ""
        have = installed_version(Path(found), timeout)
        if have is None or have == pin:
            return ""
        return (f"graphify-version: `graphify` on PATH ({found}) is graphifyy {have}, the pin is {pin}. "
                f"Run `make graphify-shim` once on this host (see docs/guidelines/agent_working_environment.md).")
    except Exception:
        return ""


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--bin-dir", type=Path, default=Path.home() / ".local" / "bin")
    ap.add_argument("--dry-run", action="store_true", help="say what would change, change nothing")
    ns = ap.parse_args(argv)
    repo = Path(__file__).resolve().parents[1]
    main_root = main_checkout_root(repo) or repo
    code, msg = link(main_root.resolve(), repo, ns.bin_dir, ns.dry_run)
    print(msg, file=sys.stdout if code == 0 else sys.stderr)
    return code


if __name__ == "__main__":
    sys.exit(main())
