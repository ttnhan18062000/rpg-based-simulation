"""The fingerprint of the installed runtime dependency closure (TCK-20261025-PERF-RECORD-IDENTITY-PINS-INSTALLED-RUNTIME-DEPENDENCIES).

A benchmark record pins the interpreter but, before this, not the packages the engine can import. The fingerprint is the sha256 of the sorted
``name==version`` lines of the *installed closure* of ``[project].dependencies``: it moves exactly when a package the engine can import moves, and not when a
dev-only or extra-only package does (a hash of ``uv.lock`` would, and would also describe the lock rather than what is installed).

Method (``deps-v1``): start from ``[project].dependencies`` of ``pyproject.toml``; for each requirement whose marker holds for the running interpreter, look up
the installed distribution and walk its own ``requires`` with the extras actually requested (a requirement that names extras brings in those extras'
requirements). Names are PEP 503 canonical. A required distribution that is not installed is a ``name==MISSING`` line, so an incomplete venv does not
match a complete one. The value carries a scheme tag, so a later change of method is itself a visible mismatch.

Known blind spot: a package the engine imports that is not reachable from ``[project].dependencies`` (imported only through an optional extra or a
dependency group) is not in the fingerprint.
"""
from __future__ import annotations

import hashlib
import tomllib
from importlib import metadata
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Protocol, Set, Tuple

try:
    from packaging.requirements import InvalidRequirement, Requirement
    from packaging.utils import canonicalize_name

    PACKAGING_AVAILABLE = True
except ImportError:  # pragma: no cover -- `packaging` is a test-tool dependency, not a runtime one; without it the fingerprint is unknown
    PACKAGING_AVAILABLE = False

SCHEME = "deps-v1"
MISSING = "MISSING"
_PYPROJECT = Path(__file__).resolve().parents[2] / "pyproject.toml"


class MetadataProvider(Protocol):
    """What the closure walk reads from an environment; the default reads ``importlib.metadata``, a test passes a fake."""

    def version(self, name: str) -> Optional[str]:
        """The installed version of *name*, or ``None`` when it is not installed."""

    def requires(self, name: str) -> List[str]:
        """The raw ``Requires-Dist`` strings of installed *name*."""


class InstalledMetadata:
    """``importlib.metadata`` of the running interpreter."""

    def version(self, name: str) -> Optional[str]:
        """The installed version of *name*, or ``None``."""
        try:
            return metadata.version(name)
        except metadata.PackageNotFoundError:
            return None

    def requires(self, name: str) -> List[str]:
        """The raw ``Requires-Dist`` strings of installed *name*."""
        try:
            return list(metadata.requires(name) or [])
        except metadata.PackageNotFoundError:
            return []


def _applies(requirement: Requirement, extras: Iterable[str]) -> bool:
    """Whether the requirement's marker holds for the running interpreter under any requested extra (or none)."""
    if requirement.marker is None:
        return True
    return any(requirement.marker.evaluate({"extra": extra}) for extra in (*extras, ""))


def _parse(raw: str, extras_in_scope: Iterable[str]) -> Optional[Tuple[str, Set[str]]]:
    """``(canonical name, requested extras)`` of requirement string *raw*, or ``None`` when it is invalid or its marker does not hold."""
    try:
        req = Requirement(raw)
    except InvalidRequirement:
        return None
    if not _applies(req, extras_in_scope):
        return None
    return canonicalize_name(req.name), {canonicalize_name(e) for e in req.extras}


def _visit(
    name: str, extras: Set[str], wanted: Dict[str, Set[str]], versions: Dict[str, Optional[str]], provider: MetadataProvider
) -> List[Tuple[str, Set[str]]]:
    """Record *name* with *extras*; return the requirements to visit next (none when it was already visited with these extras, or is not installed)."""
    known = wanted.setdefault(name, set())
    if name in versions and extras <= known:
        return []
    known |= extras
    versions[name] = provider.version(name)
    if versions[name] is None:
        return []
    return [p for p in (_parse(raw, known) for raw in provider.requires(name)) if p is not None]


def _closure(roots: Iterable[str], provider: MetadataProvider) -> Dict[str, Optional[str]]:
    """``{canonical name: installed version or None}`` for the closure of *roots*, with the extras requested along each path."""
    pending = [parsed for parsed in (_parse(raw, ()) for raw in roots) if parsed is not None]
    wanted: Dict[str, Set[str]] = {}
    versions: Dict[str, Optional[str]] = {}
    while pending:
        name, extras = pending.pop()
        pending.extend(_visit(name, extras, wanted, versions, provider))
    return versions


def fingerprint_of(roots: Iterable[str], provider: Optional[MetadataProvider] = None) -> Tuple[str, int]:
    """``(deps-v1:<sha256 hex>, number of lines hashed)`` for the closure of the requirement strings *roots*."""
    versions = _closure(roots, provider or InstalledMetadata())
    lines = sorted(f"{name}=={version or MISSING}" for name, version in versions.items())
    digest = hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()
    return f"{SCHEME}:{digest}", len(lines)


def project_dependencies(pyproject: Path = _PYPROJECT) -> Optional[List[str]]:
    """``[project].dependencies`` of *pyproject*, or ``None`` when the file is missing or unreadable."""
    try:
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        return list(data["project"]["dependencies"])
    except (OSError, KeyError, tomllib.TOMLDecodeError):
        return None


def collect_dependency_fingerprint(
    provider: Optional[MetadataProvider] = None, pyproject: Path = _PYPROJECT, unknown: str = "unknown"
) -> Tuple[str, Optional[int]]:
    """The fingerprint of this environment, or ``(unknown, None)`` when the project's dependencies cannot be read."""
    roots = project_dependencies(pyproject)
    if roots is None or not PACKAGING_AVAILABLE:
        return unknown, None
    return fingerprint_of(roots, provider)
