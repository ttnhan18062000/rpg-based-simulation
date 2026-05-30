# Compliance IDs: WORLD-060, WORLD-061, WORLD-062
from __future__ import annotations

import re
import json
import yaml
from pathlib import Path
from datetime import datetime
from src.worldbuilding.schema import WorldSpec, load_world_spec_from_yaml, InvalidWorldSpecError

class WorldRepositoryError(Exception):
    """Base exception for WorldRepository operations."""
    pass

class WorldRepository:
    """
    File-based repository layer for loading, saving, listing, and index-tracking
    world specifications under a safe worlds root directory.
    """

    def __init__(self, worlds_dir: str | Path):
        self.worlds_dir = Path(worlds_dir).resolve()
        self.index_path = self.worlds_dir / "world_index.json"

    def _validate_world_id(self, world_id: str) -> None:
        """Enforces a strict safe pattern on world identifier strings."""
        if not world_id or not re.match(r"^[a-zA-Z0-9_-]+$", world_id):
            raise ValueError(f"Invalid or unsafe world_id pattern: '{world_id}'")

    def _resolve_world_path(self, world_id: str) -> Path:
        """
        Safely resolves a world's target folder and YAML path, blocking path traversal.
        """
        self._validate_world_id(world_id)
        target_dir = (self.worlds_dir / world_id).resolve()
        
        # Verify target is strictly a descendant of worlds_dir
        try:
            if not target_dir.is_relative_to(self.worlds_dir) or target_dir == self.worlds_dir:
                raise PermissionError(f"Path traversal attempt blocked for world_id: '{world_id}'")
        except ValueError as e:
            raise PermissionError(f"Path traversal attempt blocked for world_id: '{world_id}'") from e
            
        return target_dir / "world.yaml"

    def list_worlds(self) -> list[str]:
        """Lists IDs of all available worlds that have a valid directory and world.yaml."""
        if not self.worlds_dir.is_dir():
            return []
        
        worlds = []
        for path in self.worlds_dir.iterdir():
            if path.is_dir():
                try:
                    self._validate_world_id(path.name)
                    if (path / "world.yaml").is_file():
                        worlds.append(path.name)
                except ValueError:
                    continue
        return sorted(worlds)

    def load_world(self, world_id: str) -> WorldSpec:
        """Loads and validates a WorldSpec by its world_id."""
        try:
            yaml_path = self._resolve_world_path(world_id)
        except (ValueError, PermissionError) as e:
            raise WorldRepositoryError(f"Secure path resolution failed for '{world_id}': {e}") from e

        if not yaml_path.is_file():
            raise WorldRepositoryError(f"World spec file not found: '{world_id}'")

        try:
            # Check if this is a composition; if so, redirect to its resolved spec
            with open(yaml_path, "r", encoding="utf-8") as f:
                raw_dict = yaml.safe_load(f)
            if raw_dict and "worldcomposition" in raw_dict.get("schema_version", ""):
                resolved_path = yaml_path.parent / "resolved" / "world.resolved.yaml"
                if resolved_path.is_file():
                    return load_world_spec_from_yaml(resolved_path)
                raise WorldRepositoryError(f"Composition world '{world_id}' has not been resolved. Run resolve first.")

            return load_world_spec_from_yaml(yaml_path)
        except Exception as e:
            if isinstance(e, WorldRepositoryError):
                raise e
            raise WorldRepositoryError(f"Failed to load world '{world_id}': {e}") from e

    def save_world(self, spec: WorldSpec) -> Path:
        """Saves a WorldSpec into its designated world.yaml file."""
        world_id = spec.world_id
        try:
            yaml_path = self._resolve_world_path(world_id)
        except (ValueError, PermissionError) as e:
            raise WorldRepositoryError(f"Secure path resolution failed for '{world_id}': {e}") from e

        try:
            yaml_path.parent.mkdir(parents=True, exist_ok=True)
            spec_dict = spec.model_dump(exclude_none=True)
            
            with open(yaml_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(spec_dict, f, sort_keys=False, allow_unicode=True)
                
            self._update_index_entry(spec, yaml_path)
            return yaml_path
        except Exception as e:
            raise WorldRepositoryError(f"Failed to save world '{world_id}': {e}") from e

    def resolve_asset_path(self, world_id: str, relative_asset_path: str) -> Path:
        """
        Safely resolves an asset path relative to a specific world's directory,
        guaranteeing path-traversal safety.
        """
        try:
            world_yaml_path = self._resolve_world_path(world_id)
        except (ValueError, PermissionError) as e:
            raise WorldRepositoryError(f"Secure path resolution failed for '{world_id}': {e}") from e
            
        world_dir = world_yaml_path.parent
        target_path = (world_dir / relative_asset_path).resolve()
        
        try:
            if not target_path.is_relative_to(world_dir):
                raise PermissionError(f"Path traversal attempt blocked in asset path: '{relative_asset_path}'")
        except ValueError as e:
            raise PermissionError(f"Path traversal attempt blocked in asset path: '{relative_asset_path}'") from e
            
        return target_path

    def _update_index_entry(self, spec: WorldSpec, yaml_path: Path) -> None:
        """Updates a single world entry inside world_index.json."""
        index_data = {}
        if self.index_path.is_file():
            try:
                with open(self.index_path, "r", encoding="utf-8") as f:
                    index_data = json.load(f)
            except Exception:
                index_data = {}

        if "worlds" not in index_data:
            index_data["worlds"] = {}

        now_str = datetime.now().isoformat()
        rel_path = str(yaml_path.relative_to(self.worlds_dir))
        
        existing = index_data["worlds"].get(spec.world_id, {})
        created_at = existing.get("created_at", now_str)

        index_data["worlds"][spec.world_id] = {
            "world_id": spec.world_id,
            "name": spec.name,
            "path": rel_path,
            "schema_version": spec.schema_version,
            "tags": getattr(spec, "tags", []),
            "created_at": created_at,
            "updated_at": now_str,
            "status": "VALIDATED"
        }

        try:
            self.worlds_dir.mkdir(parents=True, exist_ok=True)
            with open(self.index_path, "w", encoding="utf-8") as f:
                json.dump(index_data, f, indent=2)
        except Exception:
            pass

    def rebuild_index(self) -> dict:
        """
        Scans all subdirectories under worlds_dir, loads any valid world.yaml,
        and rewrites a fresh, accurate world_index.json.
        """
        index_data = {"worlds": {}}
        
        existing_worlds = {}
        if self.index_path.is_file():
            try:
                with open(self.index_path, "r", encoding="utf-8") as f:
                    old_data = json.load(f)
                    existing_worlds = old_data.get("worlds", {})
            except Exception:
                pass

        if self.worlds_dir.is_dir():
            for path in self.worlds_dir.iterdir():
                if path.is_dir():
                    yaml_file = path / "world.yaml"
                    if yaml_file.is_file():
                        world_id = path.name
                        try:
                            self._validate_world_id(world_id)
                            # Read raw dict to check schema_version
                            with open(yaml_file, "r", encoding="utf-8") as f:
                                raw_dict = yaml.safe_load(f)
                            
                            schema_ver = raw_dict.get("schema_version", "")
                            if "worldtemplate" in schema_ver:
                                from src.worldbuilding.recipe import WorldTemplateSpec
                                spec = WorldTemplateSpec.model_validate(raw_dict)
                                status_str = "TEMPLATE"
                            elif "worldcomposition" in schema_ver:
                                from src.worldassembly.schema import WorldCompositionSpec
                                spec = WorldCompositionSpec.model_validate(raw_dict)
                                status_str = "COMPOSITION"
                            else:
                                spec = load_world_spec_from_yaml(yaml_file)
                                status_str = "VALIDATED"
                            
                            # Reject duplicate world_id if defined across different directories
                            if spec.world_id in index_data["worlds"]:
                                raise WorldRepositoryError(
                                    f"Duplicate world_id '{spec.world_id}' found in multiple directories."
                                )

                            existing = existing_worlds.get(spec.world_id, {})
                            now_str = datetime.now().isoformat()
                            created_at = existing.get("created_at", now_str)
                            
                            index_data["worlds"][spec.world_id] = {
                                "world_id": spec.world_id,
                                "name": spec.name,
                                "path": str(yaml_file.relative_to(self.worlds_dir)),
                                "schema_version": spec.schema_version,
                                "tags": getattr(spec, "tags", []),
                                "created_at": created_at,
                                "updated_at": now_str,
                                "status": status_str
                            }
                        except Exception as e:
                            if isinstance(e, WorldRepositoryError):
                                raise e
                            now_str = datetime.now().isoformat()
                            existing = existing_worlds.get(world_id, {})
                            created_at = existing.get("created_at", now_str)
                            
                            index_data["worlds"][world_id] = {
                                "world_id": world_id,
                                "name": world_id.replace("_", " ").title(),
                                "path": str(yaml_file.relative_to(self.worlds_dir)),
                                "schema_version": "unknown",
                                "tags": [],
                                "created_at": created_at,
                                "updated_at": now_str,
                                "status": "BROKEN"
                            }

        try:
            self.worlds_dir.mkdir(parents=True, exist_ok=True)
            with open(self.index_path, "w", encoding="utf-8") as f:
                json.dump(index_data, f, indent=2)
        except Exception as e:
            raise WorldRepositoryError(f"Failed to write world_index.json: {e}") from e

        return index_data
