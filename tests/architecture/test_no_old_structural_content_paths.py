"""
Architecture guard: no hardcoded old content catalog paths in src/.

Forbidden patterns (catalog input paths, not compiled-world output):
  - "data/world_modules" as a literal string
  - WorldModuleRepository("data/world_modules") direct instantiation
  - load_all_compositions("data/worlds") — "data/worlds" used as a composition source

Allowed:
  - WorldRepository("data/worlds") — compiled world output repo, not the catalog
  - Any file in tests/ named legacy_* or containing "# legacy fixture"
  - Docstrings and comments that only describe the old path (not call it)
"""
from __future__ import annotations

import re
from pathlib import Path

_SRC_ROOT = Path(__file__).parent.parent.parent / "src"

# Patterns that are forbidden in non-allowlisted src/ files.
_FORBIDDEN: list[tuple[str, re.Pattern[str]]] = [
    (
        "hardcoded data/world_modules path",
        re.compile(r'"data/world_modules"'),
    ),
    (
        "WorldModuleRepository with hardcoded data/world_modules",
        re.compile(r'WorldModuleRepository\s*\(\s*"data/world_modules"\s*\)'),
    ),
    (
        "load_all_compositions with hardcoded data/worlds (composition source)",
        re.compile(r'load_all_compositions\s*\(\s*"data/worlds"\s*\)'),
    ),
]

# WorldRepository("data/worlds") is the compiled-world output repo — NOT forbidden.
# We do not flag it.


def _is_allowlisted(path: Path) -> bool:
    """Return True for files that are explicitly exempt from this guard."""
    name = path.name
    if name.startswith("legacy_"):
        return True
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return False
    if "# legacy fixture" in text:
        return True
    return False


def test_no_hardcoded_old_content_paths_in_src() -> None:
    violations: list[str] = []

    for py_file in sorted(_SRC_ROOT.rglob("*.py")):
        if _is_allowlisted(py_file):
            continue

        try:
            source = py_file.read_text(encoding="utf-8")
        except OSError:
            continue

        for description, pattern in _FORBIDDEN:
            for match in pattern.finditer(source):
                # Compute line number for readability
                line_no = source.count("\n", 0, match.start()) + 1
                rel = py_file.relative_to(_SRC_ROOT.parent)
                violations.append(f"{rel}:{line_no} — {description}: {match.group()!r}")

    assert not violations, (
        "Hardcoded old content catalog paths found in src/.\n"
        "Use ContentPathConfig() from src.content.paths instead.\n\n"
        + "\n".join(f"  {v}" for v in violations)
    )
