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

    def get_entity_origin(self, run_id: str, population_id: str) -> Optional[Dict[str, Any]]:
        """
        Lookup the origin metadata for a compiled population group.
        
        Returns:
            A dict containing 'source_module', 'recipe_type', 'parameters', 'profiles', etc.
        """
        manifest = self._load_manifest(run_id)
        if not manifest:
            return None
        
        records = manifest.get("records", {})
        record = records.get(population_id)
        if record:
            return {
                "element_id": population_id,
                "element_type": "population",
                "source_module": record.get("source_module"),
                "recipe_type": record.get("recipe_type"),
                "parameters": record.get("parameters", {}),
                "profiles": record.get("profiles", {}),
                "details": record.get("details", {})
            }
        return None

    def get_region_origin(self, run_id: str, region_id: str) -> Optional[Dict[str, Any]]:
        """Lookup origin metadata for a region."""
        manifest = self._load_manifest(run_id)
        if not manifest:
            return None
        
        records = manifest.get("records", {})
        record = records.get(region_id)
        if record:
            return {
                "element_id": region_id,
                "element_type": "region",
                "source_module": record.get("source_module"),
                "recipe_type": record.get("recipe_type"),
                "parameters": record.get("parameters", {}),
                "profiles": record.get("profiles", {}),
                "details": record.get("details", {})
            }
        return None

    def get_building_origin(self, run_id: str, building_id: str) -> Optional[Dict[str, Any]]:
        """Lookup origin metadata for a building."""
        manifest = self._load_manifest(run_id)
        if not manifest:
            return None
        
        records = manifest.get("records", {})
        record = records.get(building_id)
        if record:
            return {
                "element_id": building_id,
                "element_type": "building",
                "source_module": record.get("source_module"),
                "recipe_type": record.get("recipe_type"),
                "parameters": record.get("parameters", {}),
                "profiles": record.get("profiles", {}),
                "details": record.get("details", {})
            }
        return None

    def get_resource_origin(self, run_id: str, resource_id: str) -> Optional[Dict[str, Any]]:
        """Lookup origin metadata for a resource node."""
        manifest = self._load_manifest(run_id)
        if not manifest:
            return None
        
        records = manifest.get("records", {})
        record = records.get(resource_id)
        if record:
            return {
                "element_id": resource_id,
                "element_type": "resource",
                "source_module": record.get("source_module"),
                "recipe_type": record.get("recipe_type"),
                "parameters": record.get("parameters", {}),
                "profiles": record.get("profiles", {}),
                "details": record.get("details", {})
            }
        return None
