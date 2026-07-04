# Compliance IDs: WORLD-ASM-006, WORLD-ASM-007
from __future__ import annotations

from typing import Optional, Any, Dict, List
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator

from src.worldbuilding.schema import RegionSpec, FactionSpec, PopulationSpec, QuestDefinition, InformationSourceProfileSpec, PendingInformationResponseSpec, PendingSelfModelInformationEventSpec


class ModuleRefSpec(BaseModel):
    """Reference description linking a reusable module to the compositional target."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    module_id: str = Field(..., min_length=1, description="Target module ID")
    enabled: bool = Field(True, description="Whether this module is active in composition")
    order: int = Field(0, description="Evaluation order index (lower executes earlier)")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Custom parameter override values")
    namespace: Optional[str] = Field(None, description="Optional namespace prefix to isolate entity/region IDs")


class WorldCompositionSpec(BaseModel):
    """Pydantic model representing compositional world scenarios (worldcomposition.v1)."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: str = Field(..., description="Schema version specification, strictly 'worldcomposition.v1'")
    world_id: str = Field(..., min_length=1, description="Unique target world identifier")
    name: str = Field(..., min_length=1, description="Composition descriptive name")
    description: Optional[str] = Field(None, description="Detailed layout description")

    catalog_refs: List[str] = Field(default_factory=list, description="Associated static catalog paths relative to data/content/")
    pack_refs: List[str] = Field(default_factory=list, description="Content pack IDs required by this composition (validated at assembly time via ContentPackManifest)")
    module_refs: List[ModuleRefSpec] = Field(default_factory=list, description="Modular components making up the composition")
    modules: Optional[List[str]] = Field(None, description="Shorthand list of module IDs")
    default_perspectives: List[str] = Field(default_factory=list, description="Default perspective IDs")
    provided_features: List[str] = Field(default_factory=list, description="Declarative feature tags this composition provides (e.g. ecology_module, trade_route, settlement). Used by ScenarioWorldFeatureValidator.")

    global_parameters: Dict[str, Any] = Field(default_factory=dict, description="Global configuration variables")
    generation_seed: int = Field(42, description="Seed for deterministic procedural resolution")
    validation_profile: str = Field("local_dev", description="Validation profile budget category (e.g. local_dev, ci)")
    faction_tension_overrides: Dict[str, float] = Field(
        default_factory=dict,
        description="Per-faction initial_tension_level overrides scoped to this composition only. Keys must be catalog-registered faction IDs already present after module merge."
    )
    information_source_profiles: List[InformationSourceProfileSpec] = Field(
        default_factory=list,
        description="Information sources declared directly on this composition (no global catalog exists for this content — see UQ-1 resolution in plan.md). Scoped to this composition only."
    )
    pending_information_responses: List[PendingInformationResponseSpec] = Field(
        default_factory=list,
        description="Compile-time-seeded pending information responses, targeted at a population "
                    "by target_population_id. No global catalog exists for this content (same "
                    "reasoning as information_source_profiles). Scoped to this composition only."
    )
    pending_self_model_information_events: List[PendingSelfModelInformationEventSpec] = Field(
        default_factory=list,
        description="Compile-time-seeded InformationResponse-shaped events for "
                    "SelfModelUpdatePhase's Step 1 (KnowledgeModelService.assimilate()). No global "
                    "catalog exists for this content (same reasoning as "
                    "information_source_profiles/pending_information_responses). Scoped to this "
                    "composition only."
    )

    @model_validator(mode="before")
    @classmethod
    def normalize_modules_shorthand(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        
        modules = data.get("modules")
        module_refs = data.get("module_refs")
        
        if modules is not None and module_refs is not None:
            raise ValueError("Cannot specify both 'modules' shorthand and 'module_refs' structured format in composition.")
        
        if modules is not None:
            normalized_refs = []
            for mod_id in modules:
                if not isinstance(mod_id, str):
                    raise ValueError(f"Module ID in 'modules' list must be a string, got {type(mod_id)}")
                normalized_refs.append({
                    "module_id": mod_id,
                    "enabled": True,
                    "order": 0
                })
            data["module_refs"] = normalized_refs
            data.pop("modules", None)
            
        return data

    @field_validator("schema_version")
    @classmethod
    def validate_schema_version(cls, v: str) -> str:
        if v != "worldcomposition.v1":
            raise ValueError("schema_version must strictly be 'worldcomposition.v1'")
        return v


class ProvenanceRecord(BaseModel):
    """Details the exact origin of a merged world specification asset/element."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    element_id: str = Field(..., description="ID of the merged entity/region/building/resource node")
    element_type: str = Field(..., description="Element category: 'region', 'population', 'entity_group', 'building', 'resource', 'faction', 'profile'")
    source_module: Optional[str] = Field(None, description="Origin module ID contributing this asset")
    recipe_type: Optional[str] = Field(None, description="Recipe category that spawned this asset")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameter settings applied during merge")
    profiles: Dict[str, Any] = Field(default_factory=dict, description="Associated content catalog profile values")
    details: Dict[str, Any] = Field(default_factory=dict, description="Extensible execution details/ranges")


class ProvenanceManifest(BaseModel):
    """Auditable sidecar manifest documenting structural and semantic origins of all resolved assets."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    manifest_id: str = Field(..., description="Unique deterministic identifier hash or uuid for this compilation run")
    world_id: str = Field(..., description="Unique target world identifier")
    source_schema_version: str = Field("provenancemanifest.v1", description="Metadata format version descriptor")
    catalog_fingerprint: str = Field(..., description="Hash/fingerprint of the Content Catalog repository")
    module_fingerprints: Dict[str, str] = Field(default_factory=dict, description="Map of module IDs to their respective source hashes")
    composition_fingerprint: str = Field("", description="Hash/fingerprint of the input compositional specification")
    resolver_version: str = Field("1.0.0", description="Software version index of the world assembly resolver")
    generator_version: Optional[str] = Field(None, description="Procedural generator engine version (Phase 8 placeholder)")
    seed: Optional[int] = Field(None, description="Procedural generation seed (Phase 8 placeholder)")
    content_fingerprint: Optional[str] = Field(None, description="Deterministic content fingerprint")
    created_at: str = Field(..., description="ISO 8601 creation timestamp")
    records: Dict[str, ProvenanceRecord] = Field(default_factory=dict, description="Detailed mappings from element ID to its resolved origin metadata")

    @property
    def entity_origins(self) -> Dict[str, str]:
        """Backward-compatibility mapping of element ID to its source module ID."""
        return {k: v.source_module for k, v in self.records.items() if v.source_module}


class ResolvedModuleContribution(BaseModel):
    """Internal model representing the resolved, normalized structural contributions of a module."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    regions: List[RegionSpec] = Field(default_factory=list)
    factions: List[FactionSpec] = Field(default_factory=list)
    population_refs: List[str] = Field(default_factory=list)
    resolved_population_specs: List[PopulationSpec] = Field(default_factory=list)
    resource_refs: Dict[str, int] = Field(default_factory=dict)
    building_refs: Dict[str, int] = Field(default_factory=dict)
    service_refs: Dict[str, int] = Field(default_factory=dict)
    relationship_refs: List[str] = Field(default_factory=list)
    biome_refs: List[str] = Field(default_factory=list)
    ecology_refs: List[str] = Field(default_factory=list)
    quest_definitions: List[QuestDefinition] = Field(default_factory=list)


class NormalizedWorldComposition(BaseModel):
    """Pydantic model representing normalized composition ready for assembly."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: str = Field(..., description="Schema version specification, strictly 'worldcomposition.v1'")
    world_id: str = Field(..., min_length=1, description="Unique target world identifier")
    name: str = Field(..., min_length=1, description="Composition descriptive name")
    description: Optional[str] = Field(None, description="Detailed layout description")

    catalog_refs: List[str] = Field(default_factory=list, description="Associated static catalog paths relative to data/content/")
    module_refs: List[ModuleRefSpec] = Field(default_factory=list, description="Modular components making up the composition")
    default_perspectives: List[str] = Field(default_factory=list, description="Default perspective IDs")
    provided_features: List[str] = Field(default_factory=list, description="Declarative feature tags this composition provides.")

    global_parameters: Dict[str, Any] = Field(default_factory=dict, description="Global configuration variables")
    generation_seed: int = Field(42, description="Seed for deterministic procedural resolution")
    validation_profile: str = Field("local_dev", description="Validation profile budget category (e.g. local_dev, ci)")
    faction_tension_overrides: Dict[str, float] = Field(
        default_factory=dict,
        description="Per-faction initial_tension_level overrides scoped to this composition only. Keys must be catalog-registered faction IDs already present after module merge."
    )
    information_source_profiles: List[InformationSourceProfileSpec] = Field(
        default_factory=list,
        description="Information sources declared directly on this composition (no global catalog exists for this content — see UQ-1 resolution in plan.md). Scoped to this composition only."
    )
    pending_information_responses: List[PendingInformationResponseSpec] = Field(
        default_factory=list,
        description="Compile-time-seeded pending information responses, targeted at a population "
                    "by target_population_id. No global catalog exists for this content (same "
                    "reasoning as information_source_profiles). Scoped to this composition only."
    )
    pending_self_model_information_events: List[PendingSelfModelInformationEventSpec] = Field(
        default_factory=list,
        description="Compile-time-seeded InformationResponse-shaped events for "
                    "SelfModelUpdatePhase's Step 1 (KnowledgeModelService.assimilate()). No global "
                    "catalog exists for this content (same reasoning as "
                    "information_source_profiles/pending_information_responses). Scoped to this "
                    "composition only."
    )

    @field_validator("schema_version")
    @classmethod
    def validate_schema_version(cls, v: str) -> str:
        if v != "worldcomposition.v1":
            raise ValueError("schema_version must strictly be 'worldcomposition.v1'")
        return v


class WorldCompositionNormalizer:
    @staticmethod
    def normalize(composition: WorldCompositionSpec | dict) -> NormalizedWorldComposition:
        if isinstance(composition, WorldCompositionSpec):
            # Since WorldCompositionSpec itself validates shorthand and converts it,
            # we dump it to a dictionary and populate NormalizedWorldComposition.
            data = composition.model_dump()
            data.pop("modules", None)
            # pack_refs is a pre-assembly validation gate and is intentionally not
            # carried into the normalized compilation context.
            data.pop("pack_refs", None)
        elif isinstance(composition, dict):
            modules = composition.get("modules")
            module_refs = composition.get("module_refs")
            if modules is not None and module_refs is not None:
                raise ValueError("Cannot specify both 'modules' shorthand and 'module_refs' structured format in composition.")

            data = dict(composition)
            if modules is not None:
                normalized_refs = []
                for mod_id in modules:
                    if not isinstance(mod_id, str):
                        raise ValueError(f"Module ID in 'modules' list must be a string, got {type(mod_id)}")
                    normalized_refs.append({
                        "module_id": mod_id,
                        "enabled": True,
                        "order": 0
                    })
                data["module_refs"] = normalized_refs
            data.pop("modules", None)
            # pack_refs is a pre-assembly validation gate and is intentionally not
            # carried into the normalized compilation context.
            data.pop("pack_refs", None)
        else:
            raise TypeError(f"Expected WorldCompositionSpec or dict, got {type(composition)}")

        return NormalizedWorldComposition(**data)

