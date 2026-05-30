# Compliance IDs: WORLD-ASM-006, WORLD-ASM-007
from __future__ import annotations

from typing import Optional, Any, Dict, List
from pydantic import BaseModel, Field, ConfigDict, field_validator


class ModuleRefSpec(BaseModel):
    """Reference description linking a reusable module to the compositional target."""
    model_config = ConfigDict(frozen=True)

    module_id: str = Field(..., min_length=1, description="Target module ID")
    enabled: bool = Field(True, description="Whether this module is active in composition")
    order: int = Field(0, description="Evaluation order index (lower executes earlier)")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Custom parameter override values")
    namespace: Optional[str] = Field(None, description="Optional namespace prefix to isolate entity/region IDs")


class WorldCompositionSpec(BaseModel):
    """Pydantic model representing compositional world scenarios (worldcomposition.v1)."""
    model_config = ConfigDict(frozen=True)

    schema_version: str = Field(..., description="Schema version specification, strictly 'worldcomposition.v1'")
    world_id: str = Field(..., min_length=1, description="Unique target world identifier")
    name: str = Field(..., min_length=1, description="Composition descriptive name")
    description: Optional[str] = Field(None, description="Detailed layout description")

    catalog_refs: List[str] = Field(default_factory=list, description="Associated static catalog paths relative to data/content/")
    module_refs: List[ModuleRefSpec] = Field(default_factory=list, description="Modular components making up the composition")
    
    global_parameters: Dict[str, Any] = Field(default_factory=dict, description="Global configuration variables")
    generation_seed: int = Field(42, description="Seed for deterministic procedural resolution")
    validation_profile: str = Field("local_dev", description="Validation profile budget category (e.g. local_dev, ci)")

    @field_validator("schema_version")
    @classmethod
    def validate_schema_version(cls, v: str) -> str:
        if v != "worldcomposition.v1":
            raise ValueError("schema_version must strictly be 'worldcomposition.v1'")
        return v


class ProvenanceRecord(BaseModel):
    """Details the exact origin of a merged world specification asset/element."""
    model_config = ConfigDict(frozen=True)

    element_id: str = Field(..., description="ID of the merged entity/region/building/resource node")
    element_type: str = Field(..., description="Element category: 'region', 'population', 'entity_group', 'building', 'resource', 'faction', 'profile'")
    source_module: Optional[str] = Field(None, description="Origin module ID contributing this asset")
    recipe_type: Optional[str] = Field(None, description="Recipe category that spawned this asset")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameter settings applied during merge")
    profiles: Dict[str, Any] = Field(default_factory=dict, description="Associated content catalog profile values")
    details: Dict[str, Any] = Field(default_factory=dict, description="Extensible execution details/ranges")


class ProvenanceManifest(BaseModel):
    """Auditable sidecar manifest documenting structural and semantic origins of all resolved assets."""
    model_config = ConfigDict(frozen=True)

    manifest_id: str = Field(..., description="Unique deterministic identifier hash or uuid for this compilation run")
    world_id: str = Field(..., description="Unique target world identifier")
    source_schema_version: str = Field("provenancemanifest.v1", description="Metadata format version descriptor")
    catalog_fingerprint: str = Field(..., description="Hash/fingerprint of the Content Catalog repository")
    module_fingerprints: Dict[str, str] = Field(default_factory=dict, description="Map of module IDs to their respective source hashes")
    composition_fingerprint: str = Field("", description="Hash/fingerprint of the input compositional specification")
    resolver_version: str = Field("1.0.0", description="Software version index of the world assembly resolver")
    generator_version: Optional[str] = Field(None, description="Procedural generator engine version (Phase 8 placeholder)")
    seed: Optional[int] = Field(None, description="Procedural generation seed (Phase 8 placeholder)")
    created_at: str = Field(..., description="ISO 8601 creation timestamp")
    records: Dict[str, ProvenanceRecord] = Field(default_factory=dict, description="Detailed mappings from element ID to its resolved origin metadata")

    @property
    def entity_origins(self) -> Dict[str, str]:
        """Backward-compatibility mapping of element ID to its source module ID."""
        return {k: v.source_module for k, v in self.records.items() if v.source_module}
