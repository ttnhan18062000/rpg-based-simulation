"""
src/domains/feature_packs/manifest.py
───────────────────────────────────────────────────────────────────────────────
FeaturePackManifest, ExtensionPoint, and CompatibilityResolver — the data model
and dependency resolver for the pluggable feature pack system (E63B).

Manifest YAML schema defined in docs/architecture/feature_pack_architecture.md.
"""

from __future__ import annotations

from collections import deque
from typing import Dict, List, Optional, Set

from pydantic import BaseModel, ConfigDict, Field


class ExtensionPoint(BaseModel):
    """A single domain extension contributed by a feature pack.

    Fields
    ------
    domain:
        Target domain: "adventure_routing", "world_emergence", "faction", "narrative"
    class_path:
        Import path in "module.path:ClassName" format.
    registry_key:
        Key under which the class is registered in the domain's FeatureRegistry.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    domain: str
    class_path: str
    registry_key: str


class FeaturePackManifest(BaseModel):
    """Self-describing manifest for a pluggable feature pack.

    Parsed from YAML at content/packs/{name}/manifest.yaml.
    All fields are required except requires, extension_points, and balance_specs.

    Fields
    ------
    name:
        Unique pack identifier (snake_case).
    version:
        Semantic version string (e.g. "1.0.0").
    requires:
        Dependency pack names. Loaded before this pack. "base" is always implicit.
    extension_points:
        Domain registrations contributed by this pack.
    balance_specs:
        Declarative balance spec IDs declared by this pack (E63D).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(..., min_length=1)
    version: str = Field(..., min_length=1)
    requires: List[str] = Field(default_factory=list)
    extension_points: List[ExtensionPoint] = Field(default_factory=list)
    balance_specs: List[str] = Field(default_factory=list)

    def to_yaml_dict(self) -> dict:
        """Produce a YAML-serialisable dict (for round-trip tests)."""
        return {
            "name": self.name,
            "version": self.version,
            "requires": list(self.requires),
            "extension_points": [
                {
                    "domain": ep.domain,
                    "class_path": ep.class_path,
                    "registry_key": ep.registry_key,
                }
                for ep in self.extension_points
            ],
            "balance_specs": list(self.balance_specs),
        }

    @classmethod
    def from_yaml_dict(cls, d: dict) -> "FeaturePackManifest":
        """Construct from a dict parsed from manifest YAML."""
        return cls(**d)


class PackDependencyError(Exception):
    """Raised by CompatibilityResolver when circular or missing dependencies are found."""


class PackConflictError(Exception):
    """Raised by CompatibilityResolver when two packs register the same registry_key."""


class CompatibilityResolver:
    """Resolve feature pack load order via topological sort (Kahn's algorithm).

    Usage
    -----
    manifests = [base_manifest, faction_manifest, culture_manifest]
    ordered = CompatibilityResolver.resolve(manifests)
    # ordered is sorted: dependencies before dependents
    """

    @staticmethod
    def resolve(manifests: List[FeaturePackManifest]) -> List[FeaturePackManifest]:
        """Return manifests in dependency-resolved load order.

        Raises PackDependencyError on circular or missing dependency.
        Raises PackConflictError when two packs register the same registry_key.

        Algorithm: Kahn's BFS topological sort on the dependency graph.
        Within the same dependency level, packs are sorted lexicographically
        by name for determinism.
        """
        by_name: Dict[str, FeaturePackManifest] = {m.name: m for m in manifests}

        # Check for missing dependencies
        for m in manifests:
            for dep in m.requires:
                if dep not in by_name:
                    raise PackDependencyError(
                        f"Pack '{m.name}' requires '{dep}' which is not in the manifest list."
                    )

        # Build in-degree and adjacency (dep → dependents)
        in_degree: Dict[str, int] = {m.name: 0 for m in manifests}
        dependents: Dict[str, List[str]] = {m.name: [] for m in manifests}
        for m in manifests:
            for dep in m.requires:
                dependents[dep].append(m.name)
                in_degree[m.name] += 1

        # Kahn's BFS: start with all nodes with in_degree == 0
        queue: deque[str] = deque(
            sorted(name for name, deg in in_degree.items() if deg == 0)
        )
        ordered_names: List[str] = []

        while queue:
            name = queue.popleft()
            ordered_names.append(name)
            for dep_name in sorted(dependents[name]):
                in_degree[dep_name] -= 1
                if in_degree[dep_name] == 0:
                    queue.append(dep_name)

        if len(ordered_names) != len(manifests):
            remaining = set(by_name) - set(ordered_names)
            raise PackDependencyError(
                f"Circular dependency detected among packs: {sorted(remaining)}"
            )

        # Check for registry_key conflicts across all packs in load order
        seen_keys: Dict[str, str] = {}  # (domain, registry_key) → pack name
        for name in ordered_names:
            m = by_name[name]
            for ep in m.extension_points:
                conflict_key = f"{ep.domain}::{ep.registry_key}"
                if conflict_key in seen_keys:
                    raise PackConflictError(
                        f"Pack '{name}' and '{seen_keys[conflict_key]}' both register "
                        f"'{ep.registry_key}' in domain '{ep.domain}'."
                    )
                seen_keys[conflict_key] = name

        return [by_name[n] for n in ordered_names]
