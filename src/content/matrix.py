from __future__ import annotations

from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, FrozenSet

class ContentFamilyMatrixEntry(BaseModel):
    """
    Represents the status of a content family.
    POLICY NOTE: YAML comments (e.g. # STATE: ...) are planning notes only.
    They must never be parsed by validators or the engine. Implementation status
    is tracked solely by implementation_state at the family level.
    """
    model_config = ConfigDict(frozen=True)

    file_path: str = Field(..., description="File path relative to data/content/")
    schema_class: Optional[str] = Field(None, description="Pydantic schema class name")
    repository_index: Optional[str] = Field(None, description="Target field in CatalogRepository or WorldModuleRepository")
    validator_coverage: Optional[str] = Field(None, description="Validator checks covering this family")
    resolver_component: Optional[str] = Field(None, description="Component resolving this family")
    compile_runtime_consumer: Optional[str] = Field(None, description="Runtime or compile consumer component")
    test_coverage: str = Field(..., description="Key test file path/pattern targeting this family")
    evidence_tests: Optional[str] = Field(None, description="Test cases demonstrating actual executable flow for states above VALIDATED_ONLY")
    resolver_evidence: Optional[str] = Field(None, description="Resolver evidence text or None")
    runtime_consumer_evidence: Optional[str] = Field(None, description="Runtime consumer evidence text or None")
    implementation_state: str = Field(..., description="Standardized usage state")
    content_maturity: str = Field(..., description="YAML comment content maturity classification")


CONTENT_USAGE_MATRIX: Dict[str, ContentFamilyMatrixEntry] = {
    # 1. Foundation
    "foundation/materials": ContentFamilyMatrixEntry(
        file_path="foundation/materials.yaml",
        schema_class="MaterialDefinition",
        repository_index="materials",
        validator_coverage="CAT-REL-018, CAT-REL-019",
        resolver_component="FoundationResolver",
        compile_runtime_consumer="CompileContext, WorldCompiler",
        test_coverage="tests/unit/content/test_catalog.py, tests/unit/content/test_layered_catalog.py",
        evidence_tests="tests/unit/content/test_resolvers.py::TestFoundationResolverSingle",
        resolver_evidence="FoundationResolver resolves materials correctly",
        runtime_consumer_evidence="CompileContext handles material compilation",
        implementation_state="RESOLVED_PARTIALLY",
        content_maturity="REDESIGNED-CORE",
    ),
    "foundation/traits": ContentFamilyMatrixEntry(
        file_path="foundation/traits.yaml",
        schema_class="TraitDefinition",
        repository_index="traits",
        validator_coverage="CAT-REL-001, CAT-REL-011, CAT-REL-017",
        resolver_component="FoundationResolver",
        compile_runtime_consumer="CompileContext, WorldCompiler",
        test_coverage="tests/unit/content/test_catalog.py, tests/unit/content/test_layered_catalog.py",
        evidence_tests="tests/unit/content/test_resolvers.py::TestFoundationResolverSingle",
        resolver_evidence="FoundationResolver resolves traits correctly",
        runtime_consumer_evidence="CompileContext and WorldCompiler use traits for validation and archetypes",
        implementation_state="RESOLVED_PARTIALLY",
        content_maturity="REDESIGNED-CORE",
    ),
    "foundation/themes": ContentFamilyMatrixEntry(
        file_path="foundation/themes.yaml",
        schema_class="ThemeDefinition",
        repository_index="themes",
        validator_coverage="CAT-REL-011, CAT-REL-018",
        resolver_component="FoundationResolver",
        compile_runtime_consumer="CompileContext",
        test_coverage="tests/unit/content/test_catalog.py, tests/unit/content/test_layered_catalog.py",
        evidence_tests="tests/unit/content/test_resolvers.py::TestFoundationResolverSingle",
        resolver_evidence="FoundationResolver resolves themes correctly",
        runtime_consumer_evidence="CompileContext captures themes during module compilation",
        implementation_state="RESOLVED_PARTIALLY",
        content_maturity="REDESIGNED-CORE",
    ),
    "foundation/relationship_axes": ContentFamilyMatrixEntry(
        file_path="foundation/relationship_axes.yaml",
        schema_class="RelationshipAxisDefinition",
        repository_index="relationship_axes",
        validator_coverage="CAT-REL-012",
        resolver_component="FoundationResolver",
        compile_runtime_consumer="CompileContext",
        test_coverage="tests/unit/content/test_catalog.py, tests/unit/content/test_layered_catalog.py",
        evidence_tests="tests/unit/content/test_resolvers.py::TestFoundationResolverSingle",
        resolver_evidence="FoundationResolver resolves axes correctly",
        runtime_consumer_evidence="CompileContext aggregates relationship axes",
        implementation_state="RESOLVED_PARTIALLY",
        content_maturity="REDESIGNED-CORE",
    ),
    "foundation/attributes": ContentFamilyMatrixEntry(
        file_path="foundation/attributes.yaml",
        schema_class="AttributeDefinition",
        repository_index="attributes",
        validator_coverage="None",
        resolver_component="FoundationResolver",
        compile_runtime_consumer="CompileContext",
        test_coverage="tests/unit/content/test_catalog.py, tests/unit/content/test_layered_catalog.py",
        evidence_tests="tests/unit/content/test_resolvers.py::TestFoundationResolverSingle",
        resolver_evidence="FoundationResolver resolves attributes correctly",
        runtime_consumer_evidence="CompileContext uses attributes",
        implementation_state="RESOLVED_PARTIALLY",
        content_maturity="REDESIGNED-CORE",
    ),
    "foundation/elements": ContentFamilyMatrixEntry(
        file_path="foundation/elements.yaml",
        schema_class="ElementDefinition",
        repository_index="elements",
        validator_coverage="None",
        resolver_component="FoundationResolver",
        compile_runtime_consumer="CompileContext",
        test_coverage="tests/unit/content/test_catalog.py, tests/unit/content/test_layered_catalog.py",
        evidence_tests="tests/unit/content/test_resolvers.py::TestFoundationResolverSingle",
        resolver_evidence="FoundationResolver resolves elements correctly",
        runtime_consumer_evidence="CompileContext uses elements",
        implementation_state="RESOLVED_PARTIALLY",
        content_maturity="REDESIGNED-CORE",
    ),

    # 2. Living
    "living/races": ContentFamilyMatrixEntry(
        file_path="living/races.yaml",
        schema_class="RaceDefinition",
        repository_index="races",
        validator_coverage="CAT-REL-011, CAT-REL-017",
        resolver_component="LivingDefaultsResolver",
        compile_runtime_consumer="CompileContext, WorldCompiler",
        test_coverage="tests/unit/content/test_catalog.py, tests/unit/content/test_layered_catalog.py",
        evidence_tests="tests/unit/content/test_resolvers.py::TestLivingDefaultsResolver",
        resolver_evidence="LivingDefaultsResolver fetches race defaults",
        runtime_consumer_evidence="CompileContext, WorldCompiler use race definitions during compilation",
        implementation_state="RESOLVED_PARTIALLY",
        content_maturity="REDESIGNED-CORE",
    ),
    "living/need_profiles": ContentFamilyMatrixEntry(
        file_path="living/need_profiles.yaml",
        schema_class="NeedProfileDefinition",
        repository_index="need_profiles",
        validator_coverage="CAT-REL-017",
        resolver_component="LivingDefaultsResolver",
        compile_runtime_consumer="CompileContext, WorldCompiler",
        test_coverage="tests/unit/content/test_catalog.py, tests/unit/content/test_layered_catalog.py",
        evidence_tests="tests/unit/content/test_resolvers.py::TestLivingDefaultsResolver",
        resolver_evidence="LivingDefaultsResolver fetches need profiles",
        runtime_consumer_evidence="None yet",
        implementation_state="RESOLVED_PARTIALLY",
        content_maturity="REDESIGNED-CORE",
    ),
    "living/sense_profiles": ContentFamilyMatrixEntry(
        file_path="living/sense_profiles.yaml",
        schema_class="SenseProfileDefinition",
        repository_index="sense_profiles",
        validator_coverage="CAT-REL-017",
        resolver_component="LivingDefaultsResolver",
        compile_runtime_consumer="CompileContext, WorldCompiler",
        test_coverage="tests/unit/content/test_catalog.py, tests/unit/content/test_layered_catalog.py",
        evidence_tests="tests/unit/content/test_resolvers.py::TestLivingDefaultsResolver",
        resolver_evidence="LivingDefaultsResolver fetches sense profiles",
        runtime_consumer_evidence="None yet",
        implementation_state="RESOLVED_PARTIALLY",
        content_maturity="REDESIGNED-CORE",
    ),
    "living/body_models": ContentFamilyMatrixEntry(
        file_path="living/body_models.yaml",
        schema_class="BodyModelDefinition",
        repository_index="body_models",
        validator_coverage="CAT-REL-017",
        resolver_component="LivingDefaultsResolver",
        compile_runtime_consumer="CompileContext, WorldCompiler",
        test_coverage="tests/unit/content/test_catalog.py, tests/unit/content/test_layered_catalog.py",
        evidence_tests="tests/unit/content/test_resolvers.py::TestLivingDefaultsResolver",
        resolver_evidence="LivingDefaultsResolver fetches body models",
        runtime_consumer_evidence="None yet",
        implementation_state="RESOLVED_PARTIALLY",
        content_maturity="REDESIGNED-CORE",
    ),
    "living/drive_profiles": ContentFamilyMatrixEntry(
        file_path="living/drive_profiles.yaml",
        schema_class="DriveProfileDefinition",
        repository_index="drive_profiles",
        validator_coverage="CAT-REL-017",
        resolver_component="LivingDefaultsResolver",
        compile_runtime_consumer="CompileContext, WorldCompiler",
        test_coverage="tests/unit/content/test_catalog.py, tests/unit/content/test_layered_catalog.py",
        evidence_tests="tests/unit/content/test_resolvers.py::TestLivingDefaultsResolver",
        resolver_evidence="LivingDefaultsResolver fetches drive profiles",
        runtime_consumer_evidence="None yet",
        implementation_state="RESOLVED_PARTIALLY",
        content_maturity="REDESIGNED-CORE",
    ),
    "living/cognition_profiles": ContentFamilyMatrixEntry(
        file_path="living/cognition_profiles.yaml",
        schema_class="CognitionProfileDefinition",
        repository_index="cognition_profiles",
        validator_coverage="CAT-REL-003, CAT-REL-011, CAT-REL-017",
        resolver_component="LivingDefaultsResolver",
        compile_runtime_consumer="CompileContext, WorldCompiler",
        test_coverage="tests/unit/content/test_catalog.py, tests/unit/content/test_layered_catalog.py",
        evidence_tests="tests/unit/content/test_resolvers.py::TestLivingDefaultsResolver",
        resolver_evidence="LivingDefaultsResolver fetches cognition profiles",
        runtime_consumer_evidence="None yet",
        implementation_state="RESOLVED_PARTIALLY",
        content_maturity="REDESIGNED-CORE",
    ),

    # 3. Social
    "social/roles": ContentFamilyMatrixEntry(
        file_path="social/roles.yaml",
        schema_class="RoleDefinition",
        repository_index="roles",
        validator_coverage="CAT-REL-001, CAT-REL-002, CAT-REL-003, CAT-REL-011, CAT-REL-017",
        resolver_component="SocialDefaultsResolver",
        compile_runtime_consumer="CompileContext, WorldCompiler",
        test_coverage="tests/unit/content/test_catalog.py, tests/unit/content/test_layered_catalog.py",
        evidence_tests="tests/unit/content/test_resolvers.py::TestSocialDefaultsResolver",
        resolver_evidence="SocialDefaultsResolver fetches role defaults",
        runtime_consumer_evidence="CompileContext and WorldCompiler resolve role dependencies",
        implementation_state="RESOLVED_PARTIALLY",
        content_maturity="REDESIGNED-CORE",
    ),
    "social/factions": ContentFamilyMatrixEntry(
        file_path="social/factions.yaml",
        schema_class="FactionDefinition",
        repository_index="factions",
        validator_coverage="CAT-REL-011, CAT-REL-012, CAT-REL-013, CAT-REL-018, CAT-REL-019",
        resolver_component="SocialDefaultsResolver",
        compile_runtime_consumer="CompileContext, WorldCompiler",
        test_coverage="tests/unit/content/test_catalog.py, tests/unit/content/test_layered_catalog.py",
        evidence_tests="tests/unit/content/test_resolvers.py::TestSocialDefaultsResolver",
        resolver_evidence="SocialDefaultsResolver fetches faction defaults",
        runtime_consumer_evidence="CompileContext and WorldCompiler resolve faction dependencies",
        implementation_state="RESOLVED_PARTIALLY",
        content_maturity="REDESIGNED-CORE",
    ),
    "social/perspectives": ContentFamilyMatrixEntry(
        file_path="social/perspectives.yaml",
        schema_class="PerspectiveDefinition",
        repository_index="perspectives",
        validator_coverage="CAT-REL-013",
        resolver_component="SocialDefaultsResolver",
        compile_runtime_consumer="RelationProjectionService",
        test_coverage="tests/unit/content/test_catalog.py, tests/unit/content/test_layered_catalog.py",
        evidence_tests="tests/unit/content_semantics/test_semantics.py::test_relation_projection_clean",
        resolver_evidence="SocialDefaultsResolver resolves perspectives",
        runtime_consumer_evidence="RelationProjectionService maps perspectives to relationships",
        implementation_state="RESOLVED_PARTIALLY",
        content_maturity="REDESIGNED-CORE",
    ),
    "social/faction_relationships": ContentFamilyMatrixEntry(
        file_path="social/faction_relationships.yaml",
        schema_class="FactionRelationshipDefinition",
        repository_index="faction_relationships",
        validator_coverage="CAT-REL-012",
        resolver_component="SocialDefaultsResolver",
        compile_runtime_consumer="RelationProjectionService",
        test_coverage="tests/unit/content/test_catalog.py, tests/unit/content/test_layered_catalog.py",
        evidence_tests="tests/unit/content_semantics/test_semantics.py::test_relation_projection_clean",
        resolver_evidence="SocialDefaultsResolver resolves relationship vectors",
        runtime_consumer_evidence="RelationProjectionService projects relationships to combat checks",
        implementation_state="RESOLVED_PARTIALLY",
        content_maturity="REDESIGNED-CORE",
    ),

    # 4. Entities
    "entities/stat_profiles": ContentFamilyMatrixEntry(
        file_path="entities/stat_profiles.yaml",
        schema_class="StatsProfileDefinition",
        repository_index="stats_profiles",
        validator_coverage="CAT-REL-001, CAT-REL-011",
        resolver_component="CompileProfileResolver",
        compile_runtime_consumer="CompileContext, WorldCompiler",
        test_coverage="tests/unit/content/test_catalog.py, tests/unit/content/test_layered_catalog.py",
        evidence_tests="tests/unit/worldassembly/test_assembly.py::test_resolved_bundle_includes_compile_context_and_preserves_profiles",
        resolver_evidence="CompileProfileResolver fetches stat profiles",
        runtime_consumer_evidence="CompileContext captures stats for entity spawning",
        implementation_state="RESOLVED_PARTIALLY",
        content_maturity="REDESIGNED-CORE",
    ),
    "entities/combat_profiles": ContentFamilyMatrixEntry(
        file_path="entities/combat_profiles.yaml",
        schema_class="CombatProfileDefinition",
        repository_index="combat_profiles",
        validator_coverage="CAT-REL-011",
        resolver_component="CompileProfileResolver",
        compile_runtime_consumer="CompileContext, WorldCompiler",
        test_coverage="tests/unit/content/test_catalog.py, tests/unit/content/test_layered_catalog.py",
        evidence_tests="tests/unit/worldassembly/test_assembly.py::test_resolved_bundle_includes_compile_context_and_preserves_profiles",
        resolver_evidence="CompileProfileResolver fetches combat profiles",
        runtime_consumer_evidence="CompileContext captures combat rules for entity spawning",
        implementation_state="RESOLVED_PARTIALLY",
        content_maturity="REDESIGNED-CORE",
    ),
    "entities/inventory_profiles": ContentFamilyMatrixEntry(
        file_path="entities/inventory_profiles.yaml",
        schema_class="InventoryProfileDefinition",
        repository_index="inventory_profiles",
        validator_coverage="CAT-REL-002, CAT-REL-011",
        resolver_component="CompileProfileResolver",
        compile_runtime_consumer="CompileContext, WorldCompiler",
        test_coverage="tests/unit/content/test_catalog.py, tests/unit/content/test_layered_catalog.py",
        evidence_tests="tests/unit/worldassembly/test_assembly.py::test_resolved_bundle_includes_compile_context_and_preserves_profiles",
        resolver_evidence="CompileProfileResolver fetches inventory profiles",
        runtime_consumer_evidence="CompileContext captures inventory items for entity spawning",
        implementation_state="RESOLVED_PARTIALLY",
        content_maturity="REDESIGNED-CORE",
    ),
    "entities/skill_profiles": ContentFamilyMatrixEntry(
        file_path="entities/skill_profiles.yaml",
        schema_class="SkillProfileDefinition",
        repository_index="skill_profiles",
        validator_coverage="CAT-REL-011",
        resolver_component="CompileProfileResolver",
        compile_runtime_consumer="CompileContext, WorldCompiler",
        test_coverage="tests/unit/content/test_catalog.py, tests/unit/content/test_layered_catalog.py",
        evidence_tests="tests/unit/worldassembly/test_assembly.py::test_resolved_bundle_includes_compile_context_and_preserves_profiles",
        resolver_evidence="CompileProfileResolver fetches skill profiles",
        runtime_consumer_evidence="CompileContext captures skills for entity spawning",
        implementation_state="RESOLVED_PARTIALLY",
        content_maturity="REDESIGNED-CORE",
    ),
    "entities/populations": ContentFamilyMatrixEntry(
        file_path="entities/populations.yaml",
        schema_class="PopulationRecipeDefinition",
        repository_index="populations",
        validator_coverage="CAT-REL-019",
        resolver_component="PopulationRecipeResolver",
        compile_runtime_consumer="WorldAssemblyResolver",
        test_coverage="tests/unit/content/test_catalog.py, tests/unit/content/test_layered_catalog.py",
        evidence_tests="tests/unit/content/test_resolvers.py::TestPopulationRecipeResolver",
        resolver_evidence="PopulationRecipeResolver expands recipes to archetypes",
        runtime_consumer_evidence="WorldAssemblyResolver resolves population spawners",
        implementation_state="RESOLVED_PARTIALLY",
        content_maturity="REDESIGNED-CORE",
    ),
    "entities/entity_archetypes": ContentFamilyMatrixEntry(
        file_path="entities/entity_archetypes.yaml",
        schema_class="EntityArchetypeDefinition",
        repository_index="entity_archetypes",
        validator_coverage="CAT-REL-011, CAT-REL-014, CAT-REL-016",
        resolver_component="ResolvedEntityArchetype",
        compile_runtime_consumer="PopulationRecipeResolver, WorldAssemblyResolver",
        test_coverage="tests/unit/content/test_catalog.py, tests/unit/content/test_layered_catalog.py",
        evidence_tests="tests/unit/content/test_resolvers.py::TestEntityArchetypeResolver",
        resolver_evidence="EntityArchetypeResolver resolves archetype composition",
        runtime_consumer_evidence="PopulationRecipeResolver and WorldAssemblyResolver use archetypes",
        implementation_state="RESOLVED_PARTIALLY",
        content_maturity="REDESIGNED-CORE",
    ),

    # 5. World
    "world/buildings": ContentFamilyMatrixEntry(
        file_path="world/buildings.yaml",
        schema_class="BuildingDefinition",
        repository_index="buildings",
        validator_coverage="CAT-REL-004",
        resolver_component="BuildingResolver",
        compile_runtime_consumer="BuildingRegistry, WorldCompiler",
        test_coverage="tests/unit/content/test_catalog.py, tests/unit/content/test_layered_catalog.py",
        evidence_tests="tests/unit/core/test_registry_adapters.py::test_service_adapter_happy_path",
        resolver_evidence="BuildingResolver resolves building templates",
        runtime_consumer_evidence="BuildingRegistry registers buildings in simulation runtime",
        implementation_state="RUNTIME_AUTHORITATIVE",
        content_maturity="REDESIGNED-CORE",
    ),
    "world/terrain": ContentFamilyMatrixEntry(
        file_path="world/terrain.yaml",
        schema_class="TerrainDefinition",
        repository_index="terrain",
        validator_coverage="None",
        resolver_component="RegionResolver",
        compile_runtime_consumer="RegionRegistry, WorldCompiler",
        test_coverage="tests/unit/content/test_catalog.py, tests/unit/content/test_layered_catalog.py",
        evidence_tests="tests/unit/core/test_registry_adapters.py::test_region_adapter_happy_path",
        resolver_evidence="RegionResolver resolves terrain types",
        runtime_consumer_evidence="RegionRegistry loads terrain info for simulation cells",
        implementation_state="RUNTIME_AUTHORITATIVE",
        content_maturity="REDESIGNED-CORE",
    ),
    "world/services": ContentFamilyMatrixEntry(
        file_path="world/services.yaml",
        schema_class="ServiceProfileDefinition",
        repository_index="services",
        validator_coverage="CAT-REL-004, CAT-REL-015",
        resolver_component="ServiceResolver",
        compile_runtime_consumer="ServiceRegistry, WorldCompiler",
        test_coverage="tests/unit/content/test_catalog.py, tests/unit/content/test_layered_catalog.py",
        evidence_tests="tests/unit/core/test_registry_adapters.py::test_service_adapter_happy_path",
        resolver_evidence="ServiceResolver resolves service properties",
        runtime_consumer_evidence="ServiceRegistry registers available services at runtime",
        implementation_state="RUNTIME_AUTHORITATIVE",
        content_maturity="REDESIGNED-CORE",
    ),
    "world/runtime_regions": ContentFamilyMatrixEntry(
        file_path="world/runtime_regions.yaml",
        schema_class="RuntimeRegionDefinition",
        repository_index="regions",
        validator_coverage="CAT-REL-014, CAT-REL-016",
        resolver_component="RegionResolver",
        compile_runtime_consumer="RegionRegistry, WorldCompiler",
        test_coverage="tests/unit/content/test_catalog.py, tests/unit/content/test_layered_catalog.py",
        evidence_tests="tests/unit/core/test_registry_adapters.py::test_region_adapter_happy_path",
        resolver_evidence="RegionResolver resolves structural regions",
        runtime_consumer_evidence="RegionRegistry populates runtime region layouts",
        implementation_state="RUNTIME_AUTHORITATIVE",
        content_maturity="REDESIGNED-CORE",
    ),
    "world/recipes": ContentFamilyMatrixEntry(
        file_path="world/recipes.yaml",
        schema_class="RecipeDefinition",
        repository_index="recipes",
        validator_coverage="CAT-REL-015",
        resolver_component="RecipeResolver",
        compile_runtime_consumer="RecipeRegistry, WorldCompiler",
        test_coverage="tests/unit/content/test_catalog.py, tests/unit/content/test_layered_catalog.py",
        evidence_tests="tests/unit/core/test_registry_adapters.py::test_recipe_adapter_happy_path",
        resolver_evidence="RecipeResolver resolves crafting recipes",
        runtime_consumer_evidence="RecipeRegistry records crafting recipes for agents",
        implementation_state="RUNTIME_AUTHORITATIVE",
        content_maturity="REDESIGNED-CORE",
    ),
    "world/resources": ContentFamilyMatrixEntry(
        file_path="world/resources.yaml",
        schema_class="ResourceDefinition",
        repository_index="resources",
        validator_coverage="CAT-REL-019",
        resolver_component="ResourceResolver",
        compile_runtime_consumer="ResourceRegistry, WorldCompiler",
        test_coverage="tests/unit/content/test_catalog.py, tests/unit/content/test_layered_catalog.py",
        evidence_tests="tests/unit/core/test_registry_adapters.py::test_resource_adapter_happy_path",
        resolver_evidence="ResourceResolver resolves resource nodes",
        runtime_consumer_evidence="ResourceRegistry monitors resource extraction at runtime",
        implementation_state="RUNTIME_AUTHORITATIVE",
        content_maturity="REDESIGNED-CORE",
    ),
    "world/items": ContentFamilyMatrixEntry(
        file_path="world/items.yaml",
        schema_class="ItemDefinition",
        repository_index="items",
        validator_coverage="CAT-REL-014, CAT-REL-015",
        resolver_component="ItemResolver",
        compile_runtime_consumer="ItemRegistry, WorldCompiler",
        test_coverage="tests/unit/content/test_catalog.py, tests/unit/content/test_layered_catalog.py",
        evidence_tests="tests/unit/core/test_registry_adapters.py::test_item_adapter_happy_path",
        resolver_evidence="ItemResolver resolves item properties",
        runtime_consumer_evidence="ItemRegistry loads item catalog for agents",
        implementation_state="RUNTIME_AUTHORITATIVE",
        content_maturity="REDESIGNED-CORE",
    ),
    "world/biomes": ContentFamilyMatrixEntry(
        file_path="world/biomes.yaml",
        schema_class="BiomeDefinition",
        repository_index="biomes",
        validator_coverage="CAT-REL-018, CAT-REL-019",
        resolver_component="BiomeResolver",
        compile_runtime_consumer="RegionRegistry, WorldCompiler",
        test_coverage="tests/unit/content/test_catalog.py, tests/unit/content/test_layered_catalog.py",
        evidence_tests="tests/unit/core/test_registry_adapters.py::test_region_adapter_happy_path",
        resolver_evidence="BiomeResolver resolves biome definitions",
        runtime_consumer_evidence="RegionRegistry checks biomes for weather/spawning",
        implementation_state="RUNTIME_AUTHORITATIVE",
        content_maturity="REDESIGNED-CORE",
    ),
    "world/ecologies": ContentFamilyMatrixEntry(
        file_path="world/ecologies.yaml",
        schema_class="EcologyDefinition",
        repository_index="ecologies",
        validator_coverage="CAT-REL-019",
        resolver_component="EcologyResolver",
        compile_runtime_consumer="RegionRegistry, WorldCompiler",
        test_coverage="tests/unit/content/test_catalog.py, tests/unit/content/test_layered_catalog.py",
        evidence_tests="tests/unit/core/test_registry_adapters.py::test_region_adapter_happy_path",
        resolver_evidence="EcologyResolver resolves ecology cycles",
        runtime_consumer_evidence="RegionRegistry operates ecology cycles at runtime",
        implementation_state="RUNTIME_AUTHORITATIVE",
        content_maturity="REDESIGNED-CORE",
    ),

    # 6. Root & Legacy
    "defaults": ContentFamilyMatrixEntry(
        file_path="defaults.yaml",
        schema_class="DefaultCompileProfile",
        repository_index="defaults",
        validator_coverage="CAT-DEF-001",
        resolver_component="CompileProfileResolver",
        compile_runtime_consumer="CompileContext",
        test_coverage="tests/unit/content/test_catalog.py",
        evidence_tests="tests/unit/worldassembly/test_assembly.py::test_resolved_bundle_includes_compile_context_and_preserves_profiles",
        resolver_evidence="CompileProfileResolver resolves compilation defaults",
        runtime_consumer_evidence="CompileContext holds defaults during build phase",
        implementation_state="RESOLVED_PARTIALLY",
        content_maturity="REDESIGNED-CORE",
    ),
    "spawn_tables": ContentFamilyMatrixEntry(
        file_path="spawn_tables.yaml",
        schema_class="SpawnTableDefinition",
        repository_index="spawn_tables",
        validator_coverage="None",
        resolver_component="None (Design-Only)",
        compile_runtime_consumer="None",
        test_coverage="tests/unit/content/test_catalog.py",
        evidence_tests="tests/unit/content/test_catalog.py",
        resolver_evidence="None",
        runtime_consumer_evidence="None",
        implementation_state="PROJECTED_TO_LEGACY",
        content_maturity="COMPATIBILITY",
    ),

    # 7. Compatibility
    "compatibility/legacy_enemy_projection": ContentFamilyMatrixEntry(
        file_path="compatibility/legacy_enemy_projection.yaml",
        schema_class="LegacyEnemyProjectionDefinition",
        repository_index="legacy_enemy_projections",
        validator_coverage="CAT-REL-014, CAT-REL-016",
        resolver_component="None",
        compile_runtime_consumer="EnemyRegistry",
        test_coverage="tests/unit/content/test_catalog.py, tests/unit/content/test_runtime_catalog.py",
        evidence_tests="tests/unit/core/test_registry_adapters.py::test_enemy_adapter_happy_path",
        resolver_evidence="None",
        runtime_consumer_evidence="EnemyRegistry projects to legacy combat types",
        implementation_state="PROJECTED_TO_LEGACY",
        content_maturity="COMPATIBILITY",
    ),

    # 8. Extra Structural layouts / Scenarios
    "world_modules": ContentFamilyMatrixEntry(
        file_path="world_modules",
        schema_class="WorldModuleSpec",
        repository_index="modules",
        validator_coverage="WorldValidator, WorldAssemblyValidator",
        resolver_component="WorldAssemblyResolver",
        compile_runtime_consumer="WorldCompiler",
        test_coverage="tests/unit/worldassembly/test_assembly.py",
        evidence_tests="tests/unit/worldassembly/test_assembly.py::test_structural_world_assembly_resolver",
        resolver_evidence="WorldAssemblyResolver resolves module configurations",
        runtime_consumer_evidence="WorldCompiler uses resolved modules for region expansion",
        implementation_state="RESOLVED_PARTIALLY",
        content_maturity="REDESIGNED-CORE",
    ),
    "world_compositions": ContentFamilyMatrixEntry(
        file_path="world_compositions",
        schema_class="WorldCompositionSpec",
        repository_index="None",
        validator_coverage="WorldAssemblyValidator",
        resolver_component="WorldAssemblyResolver",
        compile_runtime_consumer="WorldCompiler",
        test_coverage="tests/unit/worldassembly/test_assembly.py",
        evidence_tests="tests/unit/worldassembly/test_assembly.py::test_structural_world_assembly_resolver",
        resolver_evidence="WorldAssemblyResolver normalizes compositions and parses module refs",
        runtime_consumer_evidence="WorldCompiler uses compositions to bundle multiple modules",
        implementation_state="RESOLVED_PARTIALLY",
        content_maturity="REDESIGNED-CORE",
    ),
    "simulation_scenarios": ContentFamilyMatrixEntry(
        file_path="simulation_scenarios",
        schema_class="ScenarioSpec",
        repository_index="None",
        validator_coverage="ScenarioLabValidator",
        resolver_component="None (Design-Only)",
        compile_runtime_consumer="ScenarioLabOrchestrator",
        test_coverage="tests/unit/lab/test_variant_matrix_builder.py",
        evidence_tests="tests/unit/lab/test_variant_matrix_builder.py",
        resolver_evidence="None",
        runtime_consumer_evidence="ScenarioLabOrchestrator loads scenarios",
        implementation_state="DESIGN_ONLY",
        content_maturity="REDESIGNED-CORE",
    ),
    "compatibility/migration_map": ContentFamilyMatrixEntry(
        file_path="compatibility/migration_map.yaml",
        schema_class=None,
        repository_index="None",
        validator_coverage="None",
        resolver_component="None",
        compile_runtime_consumer="None",
        test_coverage="tests/unit/content/test_content_usage_matrix.py",
        evidence_tests=None,
        resolver_evidence="None",
        runtime_consumer_evidence="Machine-readable legacy-to-catalog migration status map",
        implementation_state="DESIGN_ONLY",
        content_maturity="COMPATIBILITY",
    ),
    "packs/swamp_border_pack": ContentFamilyMatrixEntry(
        file_path="packs/swamp_border_pack.yaml",
        schema_class=None,
        repository_index="None",
        validator_coverage="None",
        resolver_component="None",
        compile_runtime_consumer="None",
        test_coverage="tests/unit/content/test_content_usage_matrix.py",
        evidence_tests=None,
        resolver_evidence="None",
        runtime_consumer_evidence="Optional content pack (swamp border terrain extension)",
        implementation_state="DESIGN_ONLY",
        content_maturity="ADDITIONAL",
    ),
    "packs/frontier_extended_pack": ContentFamilyMatrixEntry(
        file_path="packs/frontier_extended_pack.yaml",
        schema_class=None,
        repository_index="None",
        validator_coverage="None",
        resolver_component="None",
        compile_runtime_consumer="None",
        test_coverage="tests/unit/content/test_content_usage_matrix.py",
        evidence_tests=None,
        resolver_evidence="None",
        runtime_consumer_evidence="Optional content pack (frontier extended region definitions)",
        implementation_state="DESIGN_ONLY",
        content_maturity="ADDITIONAL",
    ),
    "social/personality_bias": ContentFamilyMatrixEntry(
        file_path="social/personality_bias.yaml",
        schema_class=None,
        repository_index="None",
        validator_coverage="None",
        resolver_component="None (read directly by WorldCompiler, not CatalogRepository)",
        compile_runtime_consumer="None (Design-Only)",
        test_coverage="tests/unit/worldbuilding/test_world_compiler.py",
        evidence_tests="tests/unit/worldbuilding/test_world_compiler.py::test_personality_bias_config_loads_from_real_data_file",
        resolver_evidence="None",
        runtime_consumer_evidence="WorldCompiler.compile() reads bravery_bias_by_alignment_bucket and action_style_thresholds directly (outside the CatalogRepository/resolver system) to bias per-entity personality/ActionStyle at generation",
        implementation_state="DESIGN_ONLY",
        content_maturity="REDESIGNED-CORE",
    ),
}


_STRUCTURAL_DIRS: FrozenSet[str] = frozenset(
    {"world_modules", "world_compositions", "simulation_scenarios"}
)


def _auto_discover_extra_entries(
    content_dir: str,
    known_keys: FrozenSet[str],
) -> Dict[str, ContentFamilyMatrixEntry]:
    """Scan *content_dir* for YAML families not already covered by *known_keys*.

    Uses the same directory-walk logic as ``test_matrix_covers_all_content_files``
    so auto-generated keys match exactly what that test expects to find in the
    matrix.  Each discovered key receives a minimal ``DESIGN_ONLY`` placeholder
    entry.  This eliminates the manual ``CONTENT_USAGE_MATRIX`` registration step
    when adding a new content file: the matrix test passes automatically, while
    the ``ValueError: Ignored active YAML files`` guard in
    ``CatalogRepository.load_all(strict=True)`` is unaffected (it checks
    ``CANONICAL_FAMILIES``, not this matrix).

    Args:
        content_dir: Path to the content root directory (e.g. ``"data/content"``).
        known_keys: Set of family keys already present in the matrix — these are
            skipped so hand-crafted entries are never overwritten.

    Returns:
        Dict of newly discovered keys → auto-generated ``DESIGN_ONLY`` entries.
        Empty if *content_dir* does not exist or all files are already registered.
    """
    discovered: Dict[str, ContentFamilyMatrixEntry] = {}
    content_path = Path(content_dir)
    if not content_path.is_dir():
        return discovered

    for item in sorted(content_path.rglob("*")):
        if item.name == ".gitkeep":
            continue

        rel = item.relative_to(content_path)
        parts = rel.parts
        if not parts:
            continue

        top_dir = parts[0]

        if top_dir in _STRUCTURAL_DIRS:
            matrix_key = top_dir
            file_path_val = top_dir
        elif item.is_file() and item.suffix in {".yaml", ".yml"}:
            matrix_key = str(rel.with_suffix("")).replace("\\", "/")
            file_path_val = str(rel).replace("\\", "/")
        else:
            continue

        if matrix_key in known_keys or matrix_key in discovered:
            continue

        discovered[matrix_key] = ContentFamilyMatrixEntry(
            file_path=file_path_val,
            schema_class=None,
            repository_index="None",
            validator_coverage="None",
            resolver_component="None",
            compile_runtime_consumer="None",
            test_coverage="tests/unit/content/test_content_usage_matrix.py",
            evidence_tests=None,
            resolver_evidence="None",
            runtime_consumer_evidence=(
                "Auto-discovered; add a manual entry to CONTENT_USAGE_MATRIX "
                "to declare consumer path and implementation state"
            ),
            implementation_state="DESIGN_ONLY",
            content_maturity="ADDITIONAL",
        )

    return discovered


# ---------------------------------------------------------------------------
# Auto-discovery: merge any files present on disk but not yet hand-registered.
# This ensures test_matrix_covers_all_content_files passes automatically when
# a new YAML file is added to data/content/ without a manual matrix entry.
# The strict-load ValueError guard in CatalogRepository is NOT affected.
# ---------------------------------------------------------------------------
_auto_discovered = _auto_discover_extra_entries(
    content_dir="data/content",
    known_keys=frozenset(CONTENT_USAGE_MATRIX.keys()),
)
if _auto_discovered:
    CONTENT_USAGE_MATRIX = {**CONTENT_USAGE_MATRIX, **_auto_discovered}


def generate_matrix_report() -> str:
    """Generates a clean markdown table representing the content usage matrix."""
    lines = [
        "# Content Usage Matrix Report",
        "",
        "> [!IMPORTANT]",
        "> POLICY NOTE: YAML comments (e.g. `# STATE: ...`) are planning notes for humans only.",
        "> They are NOT parsed by validators or the engine, nor are they used for per-record validation.",
        "> Implementation status is defined and tracked strictly at the content-family level in this matrix.",
        "",
        "This report is generated dynamically to define the component family contract and engine usage states for all content files in the database.",
        "",
        "| Content Family | File Path / Directory | Schema Class | Repo Index | Validator Coverage | Resolver Component | Compile/Runtime Consumer | Test Coverage | Evidence Tests | Resolver Evidence | Runtime Consumer Evidence | Implementation State | Content Maturity |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]

    for key in sorted(CONTENT_USAGE_MATRIX.keys()):
        entry = CONTENT_USAGE_MATRIX[key]
        lines.append(
            f"| **{key}** | `{entry.file_path}` | `{entry.schema_class or 'None'}` | `{entry.repository_index or 'None'}` | {entry.validator_coverage or 'None'} | {entry.resolver_component or 'None'} | {entry.compile_runtime_consumer or 'None'} | `{entry.test_coverage}` | `{entry.evidence_tests or 'None'}` | {entry.resolver_evidence or 'None'} | {entry.runtime_consumer_evidence or 'None'} | **{entry.implementation_state}** | `{entry.content_maturity}` |"
        )

    return "\n".join(lines) + "\n"
