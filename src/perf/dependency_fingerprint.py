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
from typing import Callable, Dict, Iterable, List, Mapping, Optional, Protocol, Set, Tuple

from packaging.requirements import InvalidRequirement, Requirement
from packaging.utils import canonicalize_name

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
        try:
            return metadata.version(name)
        except metadata.PackageNotFoundError:
            return None

    def requires(self, name: str) -> List[str]:
        try:
            return list(metadata.requires(name) or [])
        except metadata.PackageNotFoundError:
            return []


def _applies(requirement: Requirement, extras: Iterable[str]) -> bool:
    """Whether the requirement's marker holds for the running interpreter under any requested extra (or none)."""
    if requirement.marker is None:
        return True
    return any(requirement.marker.evaluate({"extra": extra}) for extra in (*extras, ""))


def _closure(roots: Iterable[str], provider: MetadataProvider) -> Dict[str, Optional[str]]:
    """``{canonical name: installed version or None}`` for the closure of *roots*, with the extras requested along each path."""
    wanted: Dict[str, Set[str]] = {}
    pending: List[Tuple[str, Set[str]]] = []
    for raw in roots:
        try:
            req = Requirement(raw)
        except InvalidRequirement:
            continue
        if _applies(req, ()):
            pending.append((canonicalize_name(req.name), {canonicalize_name(e) for e in req.extras}))
    versions: Dict[str, Optional[str]] = {}
    while pending:
        name, extras = pending.pop()
        known = wanted.setdefault(name, set())
        if name in versions and extras <= known:
            continue
        known |= extras
        versions[name] = provider.version(name)
        if versions[name] is None:
            continue
        for raw in provider.requires(name):
            try:
                child = Requirement(raw)
            except InvalidRequirement:
                continue
            if _applies(child, known):
                pending.append((canonicalize_name(child.name), {canonicalize_name(e) for e in child.extras}))
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
    if roots is None:
        return unknown, None
    return fingerprint_of(roots, provider)
