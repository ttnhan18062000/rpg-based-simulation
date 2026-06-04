# Investigation: Fail-Closed Schema and Authoring-Form Normalization

## Context & Requirements

1. **Fail-Closed Schema Mode**:
   All active specification schemas (Pydantic models) must reject unknown top-level fields (i.e. `extra="forbid"`).
   - In catalog schemas (`CatalogBaseDefinition` in `src/content/schema.py`), they should support custom metadata under `metadata`, `extension`, and `design_notes` blocks. Since `metadata` already exists, we need to declare `extension` and `design_notes` on the base class.
   - Compatibility models (like `LegacyEnemyProjectionDefinition`) must also enforce this layout.

2. **World Composition Normalization**:
   - `WorldCompositionSpec` currently expects `module_refs` (list of `ModuleRefSpec`).
   - We need to support the author-friendly `modules` shorthand (list of strings representing module IDs) at the top level.
   - We must also allow `default_perspectives` at the top level and ensure it is not silently dropped.
   - If both `modules` and `module_refs` are specified together, it must fail.
   - The normalizer must map the shorthand `modules` to the structured `module_refs` format (each with `enabled=True` and `order=0`).

3. **World Module Normalization**:
   - `WorldModuleSpec` currently expects `schema_version: "worldmodule.v1"`.
   - We need to support `schema_version: "worldmodule.v2"` and add support for the new v2 concepts: `biomes`, `ecologies`, `populations`, `relationships`, `resources`, `buildings`, and `services`.
   - We should define `WorldModuleAuthoringNormalizer` which normalizes `WorldModuleSpec` inputs into `NormalizedWorldModule` internal contributions.
   - Any unknown top-level field in a v2 module must fail.
   - Unsupported `module_type` values must fail unless registered/valid.

## Schema Modifications

### src/content/schema.py
Modify `CatalogBaseDefinition` to add `extra="forbid"`, `extension`, and `design_notes` fields:
```python
class CatalogBaseDefinition(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(..., min_length=1)
    display_name: Optional[str] = Field(None)
    description: Optional[str] = Field(None)
    tags: List[str] = Field(default_factory=list)
    schema_version: Optional[str] = Field(None)
    deprecated: bool = Field(False)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    extension: Dict[str, Any] = Field(default_factory=dict)
    design_notes: Optional[str] = Field(None)
```

### src/worldassembly/schema.py
Add `extra="forbid"` to `WorldCompositionSpec`, `ModuleRefSpec`, `ProvenanceRecord`, and `ProvenanceManifest`.
Add `modules` and `default_perspectives` fields to `WorldCompositionSpec`:
```python
class WorldCompositionSpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    ...
    modules: Optional[List[str]] = Field(None)
    default_perspectives: List[str] = Field(default_factory=list)
```
Add `before` model validator to normalize `modules` to `module_refs`:
```python
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
                    raise ValueError("Module ID in 'modules' list must be a string")
                normalized_refs.append({
                    "module_id": mod_id,
                    "enabled": True,
                    "order": 0
                })
            data["module_refs"] = normalized_refs
            data.pop("modules", None)
            
        return data
```

### src/worldmodules/schema.py
Modify `WorldModuleSpec` to support `worldmodule.v2` and declare the new concepts:
```python
class WorldModuleSpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    ...
    # v2 fields
    biomes: List[Any] = Field(default_factory=list)
    ecologies: List[Any] = Field(default_factory=list)
    populations: List[Any] = Field(default_factory=list)
    relationships: List[Any] = Field(default_factory=list)
    resources: List[Any] = Field(default_factory=list)
    buildings: List[Any] = Field(default_factory=list)
    services: List[Any] = Field(default_factory=list)
```

Allow both `worldmodule.v1` and `worldmodule.v2` schema versions:
```python
    @field_validator("schema_version")
    @classmethod
    def validate_schema_version(cls, v: str) -> str:
        if v not in ("worldmodule.v1", "worldmodule.v2"):
            raise ValueError("schema_version must be 'worldmodule.v1' or 'worldmodule.v2'")
        return v
```

## Normalizer Design

Create `src/worldmodules/normalizer.py` containing `NormalizedWorldModule` and `WorldModuleAuthoringNormalizer`:
```python
@dataclass
class NormalizedWorldModule:
    module_id: str
    schema_version: str
    module_type: str
    display_name: str
    description: Optional[str]
    version: str
    requires: List[str]
    provides: List[str]
    parameters: List[ModuleParameterSpec]
    regions: List[RegionRecipeSpec]
    population_recipes: List[PopulationRecipeSpec]
    resource_recipes: List[ResourceRecipeSpec]
    building_recipes: List[BuildingRecipeSpec]
    biomes: List[Any]
    ecologies: List[Any]
    populations: List[Any]
    relationships: List[Any]
    resources: List[Any]
    buildings: List[Any]
    services: List[Any]
```
The normalizer copies fields deterministically from the Pydantic spec.
