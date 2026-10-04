# Compliance IDs: WORLD-ASM-006, WORLD-ASM-007
"""File and repository I/O around resolving a `worldcomposition.v1` world.

Loads and validates a composition source file, loads the catalog and module repositories a resolve
reads from, resolves the composition into a bundle together with the exact `world.resolved.yaml`
text it serializes to, and writes the five `resolved/` artifacts. The resolve CLI and the guard that
compares a committed snapshot against a fresh resolve both go through these functions, so neither can
drift in how a resolved world is serialized.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import yaml

from src.content.paths import ContentPathConfig
from src.content.repository import CatalogRepository
from src.worldassembly.resolver import ResolvedWorldBundle, WorldAssemblyResolver
from src.worldassembly.schema import WorldCompositionSpec
from src.worldmodules.repository import WorldModuleRepository

RESOLVED_DIRNAME = "resolved"
RESOLVED_WORLD_FILENAME = "world.resolved.yaml"


def render_resolved_world_yaml(bundle: ResolvedWorldBundle) -> str:
    """Serializes a resolved bundle's world spec exactly as the committed snapshot stores it."""
    return yaml.safe_dump(
        bundle.world_spec.model_dump(exclude_none=True),
        sort_keys=False,
        allow_unicode=True,
    )


def load_content_repositories(
    catalog_root: str = "data/content",
    world_modules_dir: Optional[str] = None,
) -> tuple[CatalogRepository, WorldModuleRepository]:
    """Loads the catalog and module repositories a resolve reads from."""
    cat_repo = CatalogRepository(catalog_root)
    cat_repo.load_all()
    mod_repo = WorldModuleRepository(world_modules_dir or ContentPathConfig().world_modules_dir)
    mod_repo.load_all()
    return cat_repo, mod_repo


def resolve_composition(
    composition: WorldCompositionSpec,
    catalog: CatalogRepository,
    module_repo: WorldModuleRepository,
) -> tuple[ResolvedWorldBundle, str]:
    """
    Resolves an already-validated composition into its bundle and the rendered
    `world.resolved.yaml` text.

    Returning the rendered text alongside the bundle is deliberate: the resolve CLI and the
    architecture guard that compares a committed snapshot against a fresh resolve must not be
    able to drift in serialization, or a byte comparison between them proves nothing.
    """
    bundle = WorldAssemblyResolver(catalog, module_repo).assemble(composition)
    return bundle, render_resolved_world_yaml(bundle)


def load_composition_spec(yaml_path: Path) -> WorldCompositionSpec:
    """Reads and validates a `worldcomposition.v1` source file."""
    with open(yaml_path, "r", encoding="utf-8") as f:
        raw_data = yaml.safe_load(f)

    schema_version = raw_data.get("schema_version", "")
    if "worldcomposition" not in schema_version:
        raise ValueError(
            f"File at '{yaml_path}' is not a worldcomposition.v1 composition "
            f"(got schema: '{schema_version}')."
        )
    try:
        return WorldCompositionSpec.model_validate(raw_data)
    except Exception as e:
        world_id_val = raw_data.get("world_id", "<unknown>")
        raise ValueError(
            f"Validation failed for composition '{world_id_val}' in family "
            f"'world_compositions' at '{yaml_path}': {e}"
        ) from e


def resolve_composition_file(
    yaml_path: Path,
    catalog_root: str = "data/content",
    world_modules_dir: Optional[str] = None,
) -> tuple[ResolvedWorldBundle, str]:
    """Path-loading wrapper over `resolve_composition` for callers that start from disk."""
    composition = load_composition_spec(yaml_path)
    catalog, module_repo = load_content_repositories(catalog_root, world_modules_dir)
    return resolve_composition(composition, catalog, module_repo)


def write_resolved_artifacts(
    world_dir: Path,
    bundle: ResolvedWorldBundle,
    rendered_world_yaml: str,
) -> dict[str, Path]:
    """Writes the five `resolved/` sidecars and returns their paths by artifact name."""
    resolved_dir = world_dir / RESOLVED_DIRNAME
    resolved_dir.mkdir(parents=True, exist_ok=True)

    paths = {
        "world": resolved_dir / RESOLVED_WORLD_FILENAME,
        "compile_context": resolved_dir / "compile_context.json",
        "provenance": resolved_dir / "provenance_manifest.json",
        "assembly_report": resolved_dir / "assembly_report.json",
        "validation_report": resolved_dir / "validation_report.json",
    }

    paths["world"].write_text(rendered_world_yaml, encoding="utf-8")
    with open(paths["compile_context"], "w", encoding="utf-8") as f:
        json.dump(bundle.compile_context.to_dict(), f, indent=2)
    with open(paths["provenance"], "w", encoding="utf-8") as f:
        json.dump(bundle.provenance_manifest.model_dump(exclude_none=True), f, indent=2)
    with open(paths["assembly_report"], "w", encoding="utf-8") as f:
        json.dump(bundle.assembly_report, f, indent=2)
    with open(paths["validation_report"], "w", encoding="utf-8") as f:
        json.dump(bundle.validation_report, f, indent=2)

    return paths
