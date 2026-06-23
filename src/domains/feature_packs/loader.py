"""
src/domains/feature_packs/loader.py
───────────────────────────────────────────────────────────────────────────────
FeaturePackLoader — discovers manifest.yaml files under a directory, filters
by the active RuntimeProfile, resolves load order, imports extension point
classes, and registers them in per-domain FeatureRegistry instances.
"""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Optional

import yaml

from src.domains.feature_packs.manifest import CompatibilityResolver, FeaturePackManifest
from src.domains.feature_packs.profile import RuntimeProfile
from src.domains.feature_packs.registry import FeatureRegistry


class FeaturePackLoader:
    """Loads feature packs from a manifest directory into domain registries.

    Usage
    -----
    registries = FeaturePackLoader.load(profile, Path("content/packs"))
    # registries["adventure_routing"].lookup("ESCORT_DIGNITARY")
    """

    @staticmethod
    def load(
        profile: RuntimeProfile,
        manifest_dir: Path,
        registries: Optional[dict[str, FeatureRegistry]] = None,
    ) -> dict[str, FeatureRegistry]:
        """Discover, filter, resolve, and register feature pack extensions.

        Parameters
        ----------
        profile:
            Declares which pack names are active for this simulation run.
        manifest_dir:
            Root directory whose immediate sub-directories each contain a
            ``manifest.yaml`` file.  Sub-directories without a manifest are
            silently skipped.
        registries:
            Existing domain registries to extend.  Domains absent from this
            dict are created on demand.  Pass ``None`` (default) to start
            with an empty set of registries.

        Returns
        -------
        dict[str, FeatureRegistry]
            One ``FeatureRegistry`` per domain that had at least one extension
            point registered.  Input registries dict is mutated and returned.
        """
        if registries is None:
            registries = {}

        active_names: set[str] = set(profile.active_pack_names)

        # Discover manifest.yaml files; skip packs not in the active profile
        manifests: list[FeaturePackManifest] = []
        if manifest_dir.exists():
            for pack_dir in sorted(manifest_dir.iterdir()):
                if not pack_dir.is_dir():
                    continue
                yaml_path = pack_dir / "manifest.yaml"
                if not yaml_path.exists():
                    continue
                raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
                manifest = FeaturePackManifest.from_yaml_dict(raw)
                if manifest.name not in active_names:
                    continue
                manifests.append(manifest)

        if not manifests:
            return registries

        ordered = CompatibilityResolver.resolve(manifests)

        for manifest in ordered:
            for ep in manifest.extension_points:
                domain = ep.domain
                if domain not in registries:
                    registries[domain] = FeatureRegistry()

                module_path, class_name = ep.class_path.rsplit(":", 1)
                module = importlib.import_module(module_path)
                cls = getattr(module, class_name)
                registries[domain].register(ep.registry_key, cls)

        return registries
