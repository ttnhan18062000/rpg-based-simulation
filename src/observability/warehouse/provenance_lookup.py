# Compliance IDs: WORLD-100, WORLD-101
from __future__ import annotations
import os
import json
from typing import Optional, Dict, Any

from src.observability.reporting.artifact_repository import RunArtifactRepository


class ProvenanceLookupService:
    """
    Query-side analytics service allowing post-run tools to join runtime state details
    with resolved World Assembly provenance records and Content Catalog profiles.
    """

    def __init__(self, run_repo: Optional[RunArtifactRepository] = None):
        self.run_repo = run_repo or RunArtifactRepository()

    def _load_manifest(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Safely load the provenance manifest sidecar file for the run."""
        try:
            run_dir = os.path.join(self.run_repo.base_dir, run_id)
            manifest_path = os.path.join(run_dir, "provenance_manifest.json")
            if os.path.exists(manifest_path):
                with open(manifest_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
        return None

    def _resolve_id_key(self, run_id: str, element_id: str, element_type: str) -> str:
        """Resolve a concrete runtime element ID (numeric or string) to its provenance manifest key."""
        # If it's already a key in the records, return it directly
        manifest = self._load_manifest(run_id)
        if manifest and "records" in manifest and element_id in manifest["records"]:
            return element_id
            
        # Try to parse numeric ID
        try:
            target_num_id = int(element_id)
        except ValueError:
            return element_id

        # Load run manifest to find resolved world spec path
        try:
            run_manifest = self.run_repo.read_manifest(run_id)
            resolved_world_path = getattr(run_manifest, "resolved_world_path", None)
            if not resolved_world_path or not os.path.exists(resolved_world_path):
                return element_id
                
            from src.worldbuilding.repository import load_world_spec_from_yaml
            spec = load_world_spec_from_yaml(resolved_world_path)
            regions = {r.id for r in spec.regions}
            
            if element_type == "entity":
                next_id = 1
                for pop_idx, pop_spec in enumerate(spec.entities):
                    region_id = pop_spec.spawn_region
                    if region_id in regions:
                        for _ in range(pop_spec.count):
                            if next_id == target_num_id:
                                return getattr(pop_spec, "id", f"pop_{pop_idx}")
                            next_id += 1
                            
            elif element_type == "building":
                next_id = 20000
                for bld_spec in spec.buildings:
                    region_id = bld_spec.region
                    if region_id in regions:
                        if next_id == target_num_id:
                            return bld_spec.id
                        next_id += 1
                        
            elif element_type == "resource":
                next_id = 10000
                for res_spec in spec.resources:
                    region_id = res_spec.region
                    if region_id in regions:
                        if next_id == target_num_id:
                            return res_spec.id
                        next_id += 1
        except Exception:
            pass
            
        return element_id

    def get_entity_origin(self, run_id: str, population_id: str) -> Optional[Dict[str, Any]]:
        """
        Lookup the origin metadata for a compiled population group or concrete entity ID.
        
        Returns:
            A dict containing 'source_module', 'recipe_type', 'parameters', 'profiles', etc.
        """
        resolved_key = self._resolve_id_key(run_id, population_id, "entity")
        manifest = self._load_manifest(run_id)
        if not manifest:
            return None
        
        records = manifest.get("records", {})
        record = records.get(resolved_key)
        if record:
            res = {
                "element_id": resolved_key,
                "element_type": "population",
                "source_module": record.get("source_module"),
                "recipe_type": record.get("recipe_type"),
                "parameters": record.get("parameters", {}),
                "profiles": dict(record.get("profiles", {}) or {}),
                "details": record.get("details", {})
            }
            try:
                run_manifest = self.run_repo.read_manifest(run_id)
                resolved_world_path = getattr(run_manifest, "resolved_world_path", None)
                if resolved_world_path and os.path.exists(resolved_world_path):
                    from src.worldbuilding.repository import load_world_spec_from_yaml
                    spec = load_world_spec_from_yaml(resolved_world_path)
                    for pop_spec in spec.entities:
                        if getattr(pop_spec, "id", None) == resolved_key:
                            role = getattr(pop_spec, "role", None)
                            faction = getattr(pop_spec, "faction", None)
                            if role:
                                res["profiles"].setdefault("role", role)
                            if faction:
                                res["profiles"].setdefault("faction", faction)
                            break
            except Exception:
                pass
            return res
        return None

    def get_region_origin(self, run_id: str, region_id: str) -> Optional[Dict[str, Any]]:
        """Lookup origin metadata for a region."""
        resolved_key = self._resolve_id_key(run_id, region_id, "region")
        manifest = self._load_manifest(run_id)
        if not manifest:
            return None
        
        records = manifest.get("records", {})
        record = records.get(resolved_key)
        if record:
            return {
                "element_id": resolved_key,
                "element_type": "region",
                "source_module": record.get("source_module"),
                "recipe_type": record.get("recipe_type"),
                "parameters": record.get("parameters", {}),
                "profiles": record.get("profiles", {}),
                "details": record.get("details", {})
            }
        return None

    def get_building_origin(self, run_id: str, building_id: str) -> Optional[Dict[str, Any]]:
        """Lookup origin metadata for a building or building ID."""
        resolved_key = self._resolve_id_key(run_id, building_id, "building")
        manifest = self._load_manifest(run_id)
        if not manifest:
            return None
        
        records = manifest.get("records", {})
        record = records.get(resolved_key)
        if record:
            res = {
                "element_id": resolved_key,
                "element_type": "building",
                "source_module": record.get("source_module"),
                "recipe_type": record.get("recipe_type"),
                "parameters": record.get("parameters", {}),
                "profiles": dict(record.get("profiles", {}) or {}),
                "details": record.get("details", {})
            }
            try:
                run_manifest = self.run_repo.read_manifest(run_id)
                resolved_world_path = getattr(run_manifest, "resolved_world_path", None)
                if resolved_world_path and os.path.exists(resolved_world_path):
                    from src.worldbuilding.repository import load_world_spec_from_yaml
                    spec = load_world_spec_from_yaml(resolved_world_path)
                    for bld_spec in spec.buildings:
                        if getattr(bld_spec, "id", None) == resolved_key:
                            bld_type = getattr(bld_spec, "type", None)
                            if bld_type:
                                res["profiles"].setdefault("building_type", bld_type)
                            break
            except Exception:
                pass
            return res
        return None

    def get_resource_origin(self, run_id: str, resource_id: str) -> Optional[Dict[str, Any]]:
        """Lookup origin metadata for a resource node or resource ID."""
        resolved_key = self._resolve_id_key(run_id, resource_id, "resource")
        manifest = self._load_manifest(run_id)
        if not manifest:
            return None
        
        records = manifest.get("records", {})
        record = records.get(resolved_key)
        if record:
            res = {
                "element_id": resolved_key,
                "element_type": "resource",
                "source_module": record.get("source_module"),
                "recipe_type": record.get("recipe_type"),
                "parameters": record.get("parameters", {}),
                "profiles": dict(record.get("profiles", {}) or {}),
                "details": record.get("details", {})
            }
            try:
                run_manifest = self.run_repo.read_manifest(run_id)
                resolved_world_path = getattr(run_manifest, "resolved_world_path", None)
                if resolved_world_path and os.path.exists(resolved_world_path):
                    from src.worldbuilding.repository import load_world_spec_from_yaml
                    spec = load_world_spec_from_yaml(resolved_world_path)
                    for res_spec in spec.resources:
                        if getattr(res_spec, "id", None) == resolved_key:
                            res_type = getattr(res_spec, "resource_type", None)
                            if res_type:
                                res["profiles"].setdefault("resource_type", res_type)
                            break
            except Exception:
                pass
            return res
        return None
