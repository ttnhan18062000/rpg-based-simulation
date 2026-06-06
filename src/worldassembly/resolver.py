# Compliance IDs: WORLD-ASM-008, WORLD-ASM-009, WORLD-ASM-010
from __future__ import annotations

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict

from src.content.repository import CatalogRepository
from src.worldmodules.repository import WorldModuleRepository
from src.worldmodules.utils import topological_sort_modules
from src.worldmodules.normalizer import NormalizedWorldModule
from src.worldassembly.schema import (
    WorldCompositionSpec,
    NormalizedWorldComposition,
    WorldCompositionNormalizer,
    ResolvedModuleContribution,
    ProvenanceManifest,
    ProvenanceRecord,
)
from src.worldassembly.context import CompileContext
from src.content.resolver import (
    BiomeResolver,
    EcologyResolver,
    RegionResolver,
    ResourceResolver,
    BuildingResolver,
    RelationshipResolver,
    PopulationRecipeResolver,
    ResolverError,
)
from src.worldbuilding.recipe import PopulationRecipeSpec


from src.worldbuilding.schema import (
    WorldSpec,
    TopologySpec,
    RegionSpec,
    FactionSpec,
    PopulationSpec,
    ResourceNodeSpec,
    BuildingSpec,
)



class ResolvedWorldBundle(BaseModel):
    """The resolved assembled output packages."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    world_spec: WorldSpec
    compile_context: CompileContext
    provenance_manifest: ProvenanceManifest
    assembly_report: Dict[str, Any]
    validation_report: Optional[Dict[str, Any]] = None


class WorldAssemblyValidator:
    """Independent stage validator coordinating multiple validation layers during assembly."""
    
    def __init__(self, catalog_repo: CatalogRepository):
        self.catalog_repo = catalog_repo

    def validate(self, world_spec: WorldSpec, graph_map: Dict[str, Any], composition: WorldCompositionSpec, factions: Dict[str, Any], width: int, height: int) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        # 1. Catalog Validation
        from src.content.validator import CatalogValidator
        cat_validator = CatalogValidator(self.catalog_repo)
        cat_issues = cat_validator.validate()
        catalog_report = [
            {"severity": issue.severity, "rule_id": issue.rule_id, "message": issue.message, "target": issue.target_id}
            for issue in cat_issues
        ]

        # 2. Module Validation
        from src.worldbuilding.validator import WorldValidator, ValidationContext
        from src.worldbuilding.schema import TopologySpec, RegionSpec, PopulationSpec, ResourceNodeSpec, BuildingSpec
        world_validator = WorldValidator()
        module_reports = {}
        for m_id, module in graph_map.items():
            dummy_spec = WorldSpec(
                schema_version="worldspec.v1",
                world_id=module.module_id,
                name=module.display_name,
                topology=TopologySpec(width=width, height=height, coordinate_system="grid"),
                regions=[
                    RegionSpec(id=r.id, type=r.type, bounds=r.grid_bounds, terrain=r.terrain, hazard_level=r.hazard_level)
                    for r in module.regions
                ],
                factions=list(factions.values()),
                entities=[
                    PopulationSpec(id=getattr(p, 'id', f"pop_{idx}"), count=p.count, role=p.role, faction=p.faction, spawn_region=p.spawn_region)
                    for idx, p in enumerate(module.population_recipes)
                ],
                resources=[
                    ResourceNodeSpec(id=getattr(r, 'id', f"res_{idx}"), resource_type=r.resource_type, count=r.count, region=r.region)
                    for idx, r in enumerate(module.resource_recipes)
                ],
                buildings=[
                    BuildingSpec(id=getattr(b, 'id', f"bld_{idx}"), type=b.building_type, region=b.region)
                    for idx, b in enumerate(module.building_recipes)
                ]
            )
            m_issues = world_validator.validate(dummy_spec, context=ValidationContext.MODULE)
            module_reports[m_id] = [
                {"severity": issue.severity, "rule_id": issue.rule_id, "message": issue.message, "path": issue.path}
                for issue in m_issues
            ]

        # 3. Composition Validation
        composition_issues = []
        for ref in composition.module_refs:
            if ref.module_id not in graph_map:
                composition_issues.append({
                    "severity": "ERROR",
                    "rule_id": "ASM-COMP-001",
                    "message": f"Referenced module '{ref.module_id}' not found in repository.",
                    "path": f"module_refs.{ref.module_id}"
                })

        # 4. Assembly & World Validation
        world_issues = world_validator.validate(world_spec, context=ValidationContext.WORLD)
        world_report = [
            {"severity": issue.severity, "rule_id": issue.rule_id, "message": issue.message, "path": issue.path}
            for issue in world_issues
        ]

        # Aggregate blocking errors and warnings
        blocking_errors = []
        warnings = []

        for issue in catalog_report:
            if issue["severity"] == "ERROR":
                blocking_errors.append(issue)
            else:
                warnings.append(issue)

        for m_id, m_issues in module_reports.items():
            for issue in m_issues:
                if issue["severity"] == "ERROR":
                    blocking_errors.append({"module_id": m_id, **issue})
                else:
                    warnings.append({"module_id": m_id, **issue})

        for issue in composition_issues:
            if issue["severity"] == "ERROR":
                blocking_errors.append(issue)
            else:
                warnings.append(issue)

        for issue in world_report:
            if issue["severity"] == "ERROR":
                blocking_errors.append(issue)
            else:
                warnings.append(issue)

        validation_reports = {
            "catalog_validation": catalog_report,
            "module_validation": module_reports,
            "composition_validation": composition_issues,
            "world_validation": world_report,
        }

        return blocking_errors, warnings, validation_reports


class WorldAssemblyReportBuilder:
    """Consolidates structural results and validation profiles into clean, readable JSON summaries."""
    
    @staticmethod
    def build(sorted_ids: List[str], factions: Dict[str, Any], regions_count: int, entities_count: int, blocking_errors: List[Dict[str, Any]], warnings: List[Dict[str, Any]], validation_reports: Dict[str, Any], catalog_fingerprint: str, module_fingerprints: Dict[str, str]) -> Dict[str, Any]:
        return {
            "sorted_module_ids": sorted_ids,
            "factions_resolved": list(factions.keys()),
            "regions_count": regions_count,
            "entities_count": entities_count,
            "catalog_validation": validation_reports["catalog_validation"],
            "module_validation": validation_reports["module_validation"],
            "composition_validation": validation_reports["composition_validation"],
            "world_validation": validation_reports["world_validation"],
            "summary": {
                "status": "SUCCESS" if not blocking_errors else "FAILED",
                "blocking_errors_count": len(blocking_errors),
                "warnings_count": len(warnings)
            },
            "blocking_errors": blocking_errors,
            "warnings": warnings,
            "fingerprints": {
                "catalog": catalog_fingerprint,
                "modules": module_fingerprints
            }
        }


class WorldAssemblyResolver:
    """
    Authoritative pipeline executing Kahn's topological sort, validating parameters,
    resolving static profile constraints, and merging modular contributions into a clean worldspec.
    """

    def __init__(self, catalog_repo: CatalogRepository, module_repo: WorldModuleRepository):
        self.catalog_repo = catalog_repo
        self.module_repo = module_repo
        from src.worldassembly.resolver import CompileProfileResolver
        self.profile_resolver = CompileProfileResolver(catalog_repo)
        self.validator = WorldAssemblyValidator(catalog_repo)
        self.biome_resolver = BiomeResolver(catalog_repo)
        self.ecology_resolver = EcologyResolver(catalog_repo)
        self.region_resolver = RegionResolver(catalog_repo)
        self.resource_resolver = ResourceResolver(catalog_repo)
        self.building_resolver = BuildingResolver(catalog_repo)
        self.relationship_resolver = RelationshipResolver(catalog_repo)
        self.population_recipe_resolver = PopulationRecipeResolver(catalog_repo)

    def assemble(self, composition: WorldCompositionSpec | dict) -> ResolvedWorldBundle:
        """
        Executes structural topological assembly and merges partial layouts into a clean WorldSpec.
        """
        # Normalize composition to NormalizedWorldComposition
        normalized_comp = WorldCompositionNormalizer.normalize(composition)

        # 1. Collect and filter enabled modules
        enabled_refs = [ref for ref in normalized_comp.module_refs if ref.enabled]
        
        # Sort initially by defined 'order' configuration
        enabled_refs.sort(key=lambda x: x.order)

        # 2. Rebuild active graph map for topological sort
        graph_map: Dict[str, Any] = {}
        ref_by_id: Dict[str, Any] = {}
        from src.worldmodules.normalizer import WorldModuleAuthoringNormalizer
        for ref in enabled_refs:
            module_spec = self.module_repo.get_module(ref.module_id)
            if not module_spec:
                raise ValueError(f"Referenced module '{ref.module_id}' not found in repository.")
            module = WorldModuleAuthoringNormalizer.normalize(module_spec)
            graph_map[ref.module_id] = module
            ref_by_id[ref.module_id] = ref

        sorted_ids = topological_sort_modules(graph_map)

        # 3. Merge components top-down while avoiding silent overwrite collision
        regions: Dict[str, RegionSpec] = {}
        factions: Dict[str, FactionSpec] = {}
        entities: Dict[str, PopulationSpec] = {}
        resources: Dict[str, ResourceNodeSpec] = {}
        buildings: Dict[str, BuildingSpec] = {}
        
        entity_origins: Dict[str, str] = {}
        module_fingerprints: Dict[str, str] = {}
        prov_records: Dict[str, ProvenanceRecord] = {}

        # Default topology specs
        width = normalized_comp.global_parameters.get("topology_width", 100)
        height = normalized_comp.global_parameters.get("topology_height", 100)

        # Re-resolve factions from catalog defaults
        for f_id in self.catalog_repo.factions:
            cat_faction = self.catalog_repo.get_faction(f_id)
            if cat_faction:
                factions[f_id] = FactionSpec(id=f_id, type=cat_faction.alignment_bucket)
                prov_records[f_id] = ProvenanceRecord(
                    element_id=f_id,
                    element_type="faction",
                    source_module=None,
                    recipe_type="catalog",
                    parameters={},
                    profiles={"alignment_bucket": cat_faction.alignment_bucket},
                    details={"description": cat_faction.description or ""}
                )

        population_recipes_dict: Dict[str, Any] = {}

        for m_id in sorted_ids:
            spec = graph_map[m_id]
            ref = ref_by_id[m_id]
            
            fingerprint = self.module_repo.module_fingerprint(m_id) or ""
            module_fingerprints[m_id] = fingerprint

            # Namespace prefix utility
            prefix = f"{ref.namespace}_" if ref.namespace else ""

            # Inject parameters values into recipes (Basic parameter injection)
            param_vals = {p.name: p.default for p in spec.parameters}
            param_vals.update(ref.parameters)

            # Resolve using component resolvers
            contribution = self.resolve_module_contribution(spec, prefix, param_vals)

            # Merge regions
            for reg in contribution.regions:
                if reg.id in regions:
                    raise ValueError(f"Duplicate region ID collision '{reg.id}' detected during assembly merge.")
                
                regions[reg.id] = reg
                entity_origins[reg.id] = m_id
                
                # Biome source for region provenance
                reg_def = self.catalog_repo.get_region(reg.id)
                if not reg_def and "_" in reg.id:
                    reg_def = self.catalog_repo.get_region(reg.id.split("_", 1)[1])
                biome_source = reg_def.biome if reg_def else None
                
                prov_records[reg.id] = ProvenanceRecord(
                    element_id=reg.id,
                    element_type="region",
                    source_module=m_id,
                    recipe_type="region",
                    parameters=param_vals,
                    profiles={"biome": biome_source} if biome_source else {},
                    details={"bounds": reg.bounds, "terrain": reg.terrain, "hazard_level": reg.hazard_level, "ecology_source": contribution.ecology_refs}
                )

            # Merge factions
            for fac in contribution.factions:
                if fac.id not in factions:
                    factions[fac.id] = fac
                    prov_records[fac.id] = ProvenanceRecord(
                        element_id=fac.id,
                        element_type="faction",
                        source_module=m_id,
                        recipe_type="faction",
                        parameters=param_vals,
                        profiles={"alignment_bucket": fac.type},
                        details={}
                    )

            # Merge population recipe specs from v2 resolved population specs
            for pop in contribution.resolved_population_specs:
                if pop.id in entity_origins:
                    raise ValueError(f"Duplicate population ID collision '{pop.id}' detected during merge.")
                
                entities[pop.id] = pop
                entity_origins[pop.id] = m_id
                
                # Attempt to determine archetype_id and population_recipe_id for provenance
                archetype_id = None
                pop_recipe_id = None
                for pr in contribution.population_refs:
                    if pr in pop.id:
                        pop_recipe_id = pr
                        archetype_id = pop.id.split(pr + "_")[-1]
                        break
                
                resolved_arch = None
                if archetype_id:
                    try:
                        resolved_arch = self.population_recipe_resolver._archetype_resolver.resolve(archetype_id)
                    except Exception:
                        pass
                
                if resolved_arch:
                    population_recipes_dict[pop.id] = PopulationRecipeSpec(
                        role=resolved_arch.role_id,
                        count=pop.count,
                        faction=resolved_arch.faction_id,
                        spawn_region=pop.spawn_region,
                        stats_profile=resolved_arch.stat_profile.id,
                        inventory_profile=resolved_arch.inventory_profile.id,
                        cognition_profile=resolved_arch.cognition_profile.id
                    )
                    prov_records[pop.id] = ProvenanceRecord(
                        element_id=pop.id,
                        element_type="population",
                        source_module=m_id,
                        recipe_type="population_recipe",
                        parameters=param_vals,
                        profiles={
                            "role": resolved_arch.role_id,
                            "faction": resolved_arch.faction_id,
                            "stats_profile": resolved_arch.stat_profile.id,
                            "inventory_profile": resolved_arch.inventory_profile.id,
                            "cognition_profile": resolved_arch.cognition_profile.id,
                            "compatibility_projection": {
                                "legacy_engine_role": resolved_arch.legacy_engine_role,
                                "legacy_engine_bucket": resolved_arch.legacy_engine_bucket
                            }
                        },
                        details={
                            "count": pop.count,
                            "spawn_region": pop.spawn_region,
                            "archetype_source": resolved_arch.archetype_id,
                            "population_recipe_source": pop_recipe_id
                        }
                    )
                else:
                    prov_records[pop.id] = ProvenanceRecord(
                        element_id=pop.id,
                        element_type="population",
                        source_module=m_id,
                        recipe_type="population",
                        parameters=param_vals,
                        profiles={"role": pop.role, "faction": pop.faction},
                        details={"count": pop.count, "spawn_region": pop.spawn_region}
                    )

            # Merge v1 population recipes
            for pop_idx, pop in enumerate(spec.population_recipes):
                pop_id = f"{prefix}{getattr(pop, 'id', f'pop_{pop_idx}')}"
                if pop_id in entity_origins:
                    raise ValueError(f"Duplicate population ID collision '{pop_id}' detected during merge.")
                
                if not self.catalog_repo.get_role(pop.role):
                    raise ResolverError("role", pop.role)
                if not self.catalog_repo.get_faction(pop.faction):
                    raise ResolverError("faction", pop.faction)

                spawn_region = f"{prefix}{pop.spawn_region}" if pop.spawn_region else ""
                entities[pop_id] = PopulationSpec(
                    id=pop_id,
                    count=pop.count,
                    role=pop.role,
                    faction=pop.faction,
                    spawn_region=spawn_region
                )
                population_recipes_dict[pop_id] = pop
                entity_origins[pop_id] = m_id
                prov_records[pop_id] = ProvenanceRecord(
                    element_id=pop_id,
                    element_type="population",
                    source_module=m_id,
                    recipe_type="population",
                    parameters=param_vals,
                    profiles={
                        "role": pop.role,
                        "faction": pop.faction,
                        "stats_profile": getattr(pop, "stats_profile", None)
                    },
                    details={"count": pop.count, "spawn_region": spawn_region}
                )

            # Merge v1 resources
            for res_idx, res in enumerate(spec.resource_recipes):
                res_id = f"{prefix}{getattr(res, 'id', f'res_{res_idx}')}"
                if res_id in resources:
                    raise ValueError(f"Duplicate resource ID collision '{res_id}' detected during merge.")
                
                self.resource_resolver.resolve(res.resource_type)
                spawn_region = f"{prefix}{res.region}" if res.region else ""
                resources[res_id] = ResourceNodeSpec(
                    id=res_id,
                    resource_type=res.resource_type,
                    count=res.count,
                    region=spawn_region
                )
                entity_origins[res_id] = m_id
                prov_records[res_id] = ProvenanceRecord(
                    element_id=res_id,
                    element_type="resource",
                    source_module=m_id,
                    recipe_type="resource",
                    parameters=param_vals,
                    profiles={"resource_type": res.resource_type},
                    details={"count": res.count, "region": spawn_region}
                )

            # Merge v2 resources (using normalized count map dict)
            if spec.schema_version == "worldmodule.v2":
                module_regions = [r for r in regions.values() if entity_origins.get(r.id) == m_id]
                for res_idx, (res_type, count) in enumerate(contribution.resource_refs.items()):
                    res_id = f"{prefix}{res_type}_{res_idx}"
                    if res_id in resources:
                        raise ValueError(f"Duplicate resource ID collision '{res_id}' detected during merge.")
                    
                    self.resource_resolver.resolve(res_type)
                    spawn_region = self._find_best_region_for_resource(res_type, module_regions)
                    
                    resources[res_id] = ResourceNodeSpec(
                        id=res_id,
                        resource_type=res_type,
                        count=count,
                        region=spawn_region
                    )
                    entity_origins[res_id] = m_id
                    prov_records[res_id] = ProvenanceRecord(
                        element_id=res_id,
                        element_type="resource",
                        source_module=m_id,
                        recipe_type="resource_layout",
                        parameters=param_vals,
                        profiles={"resource_type": res_type},
                        details={"count": count, "region": spawn_region}
                    )

            # Merge v1 buildings
            for bld_idx, bld in enumerate(spec.building_recipes):
                bld_id = f"{prefix}{getattr(bld, 'id', f'bld_{bld_idx}')}"
                if bld_id in buildings:
                    raise ValueError(f"Duplicate building ID collision '{bld_id}' detected during merge.")
                
                self.building_resolver.resolve(bld.building_type)
                spawn_region = f"{prefix}{bld.region}" if bld.region else ""
                buildings[bld_id] = BuildingSpec(
                    id=bld_id,
                    type=bld.building_type,
                    region=spawn_region
                )
                entity_origins[bld_id] = m_id
                prov_records[bld_id] = ProvenanceRecord(
                    element_id=bld_id,
                    element_type="building",
                    source_module=m_id,
                    recipe_type="building",
                    parameters=param_vals,
                    profiles={"building_type": bld.building_type},
                    details={"region": spawn_region}
                )

            # Merge v2 buildings (using normalized count map dict)
            if spec.schema_version == "worldmodule.v2":
                module_regions = [r for r in regions.values() if entity_origins.get(r.id) == m_id]
                for bld_idx, (bld_type, count) in enumerate(contribution.building_refs.items()):
                    for b_sub in range(count):
                        bld_id = f"{prefix}{bld_type}_{b_sub}"
                        if bld_id in buildings:
                            raise ValueError(f"Duplicate building ID collision '{bld_id}' detected during merge.")
                        
                        self.building_resolver.resolve(bld_type)
                        spawn_region = self._find_best_region_for_building(bld_type, module_regions)
                        
                        buildings[bld_id] = BuildingSpec(
                            id=bld_id,
                            type=bld_type,
                            region=spawn_region
                        )
                        entity_origins[bld_id] = m_id
                        prov_records[bld_id] = ProvenanceRecord(
                            element_id=bld_id,
                            element_type="building",
                            source_module=m_id,
                            recipe_type="building_layout",
                            parameters=param_vals,
                            profiles={"building_type": bld_type},
                            details={"region": spawn_region}
                        )

            # NOTE: contribution.service_refs (Dict[str, int]) is intentionally not assembled here.
            # WorldSpec has no services field; service assembly is deferred until ServiceNodeSpec
            # and WorldSpec.services are defined. See docs/guidelines/v2_intentional_divergences.md
            # (entry 2.19) and docs/parity_ledger/substrate.yaml (SUB-367).
            # When adding that field, add a v2 service merge loop here parallel to the building loop above.

            # Merge relationships provenance
            for rel_id in contribution.relationship_refs:
                rel_def = self.relationship_resolver.resolve(rel_id)
                prov_records[f"rel_{rel_id}"] = ProvenanceRecord(
                    element_id=f"rel_{rel_id}",
                    element_type="faction",
                    source_module=m_id,
                    recipe_type="relationship",
                    parameters=param_vals,
                    profiles={
                        "source_faction": rel_def.source_faction,
                        "target_faction": rel_def.target_faction,
                        "relationship_model": rel_def.relationship_model
                    },
                    details={}
                )

        # Ensure width and height cover all region bounds if not explicitly specified in global_parameters
        max_region_x = 100
        max_region_y = 100
        for reg in regions.values():
            max_region_x = max(max_region_x, reg.bounds[2] + 1)
            max_region_y = max(max_region_y, reg.bounds[3] + 1)

        width = normalized_comp.global_parameters.get("topology_width", max_region_x)
        height = normalized_comp.global_parameters.get("topology_height", max_region_y)

        # 4. Assembled clean worldspec.v1
        world_spec = WorldSpec(
            schema_version="worldspec.v1",
            world_id=normalized_comp.world_id,
            name=normalized_comp.name,
            description=normalized_comp.description,
            topology=TopologySpec(width=width, height=height, coordinate_system="grid"),
            regions=list(regions.values()),
            factions=list(factions.values()),
            entities=list(entities.values()),
            resources=list(resources.values()),
            buildings=list(buildings.values())
        )

        import hashlib
        from datetime import datetime, timezone
        
        # Calculate composition fingerprint
        comp_dump = normalized_comp.model_dump()
        comp_serialized = str(sorted(comp_dump.items()))
        composition_fingerprint = hashlib.sha256(comp_serialized.encode("utf-8")).hexdigest()

        hasher = hashlib.sha256()
        hasher.update(normalized_comp.world_id.encode())
        hasher.update(self.catalog_repo.fingerprint.encode())
        for m_id in sorted_ids:
            hasher.update(module_fingerprints[m_id].encode())
        content_fingerprint = hasher.hexdigest()
        manifest_id = f"prov_{content_fingerprint[:16]}"
        created_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        provenance = ProvenanceManifest(
            manifest_id=manifest_id,
            world_id=normalized_comp.world_id,
            catalog_fingerprint=self.catalog_repo.fingerprint,
            module_fingerprints=module_fingerprints,
            composition_fingerprint=composition_fingerprint,
            resolver_version="1.0.0",
            generator_version=None,
            seed=None,
            content_fingerprint=content_fingerprint,
            created_at=created_at,
            records=prov_records
        )

        # Validate stage
        blocking_errors, warnings, validation_reports = self.validator.validate(
            world_spec=world_spec,
            graph_map=graph_map,
            composition=normalized_comp,
            factions=factions,
            width=width,
            height=height
        )

        if blocking_errors:
            msgs = "; ".join(f"[{err.get('rule_id', 'ERROR')}] {err.get('message')}" for err in blocking_errors)
            from src.worldbuilding.schema import InvalidWorldSpecError
            raise InvalidWorldSpecError(f"Assembly validation failed with blocking errors: {msgs}")

        # Build assembly report
        assembly_report = WorldAssemblyReportBuilder.build(
            sorted_ids=sorted_ids,
            factions=factions,
            regions_count=len(regions),
            entities_count=len(entities),
            blocking_errors=blocking_errors,
            warnings=warnings,
            validation_reports=validation_reports,
            catalog_fingerprint=self.catalog_repo.fingerprint,
            module_fingerprints=module_fingerprints
        )

        # Resolve CompileContext with the preserved raw population recipe overrides
        compile_context = self.profile_resolver.resolve(world_spec, population_recipes_dict)

        return ResolvedWorldBundle(
            world_spec=world_spec,
            compile_context=compile_context,
            provenance_manifest=provenance,
            assembly_report=assembly_report,
            validation_report=validation_reports
        )

    def resolve_module_contribution(
        self,
        module: WorldModuleSpec | NormalizedWorldModule,
        prefix: str = "",
        param_vals: Dict[str, Any] = None
    ) -> ResolvedModuleContribution:
        """
        Resolves a module's structural contributions using component resolvers.
        Validates elements against the Content Catalog.
        """
        if param_vals is None:
            param_vals = {}

        # 1. Resolve Regions
        regions_spec_list: List[RegionSpec] = []
        for reg in module.regions:
            # Call RegionResolver if in catalog
            if self.catalog_repo.get_region(reg.id) is not None:
                self.region_resolver.resolve(reg.id)
            else:
                if module.schema_version == "worldmodule.v2":
                    raise ResolverError("region", reg.id, f"referenced by v2 module '{module.module_id}'")
            
            regions_spec_list.append(RegionSpec(
                id=f"{prefix}{reg.id}",
                type=reg.type,
                bounds=reg.grid_bounds,
                terrain=reg.terrain,
                hazard_level=reg.hazard_level
            ))

        # 2. Resolve Factions
        factions_spec_list: List[FactionSpec] = []
        for f_id in module.factions:
            cat_faction = self.catalog_repo.get_faction(f_id)
            if cat_faction is None:
                raise ResolverError("faction", f_id, context=f"referenced by module '{module.module_id}'")
            factions_spec_list.append(FactionSpec(id=f_id, type=cat_faction.alignment_bucket))

        # 3. Resolve Biomes
        biome_refs: List[str] = []
        for b_id in module.biomes:
            self.biome_resolver.resolve(b_id)
            biome_refs.append(b_id)

        # 4. Resolve Ecologies
        ecology_refs: List[str] = []
        for e_id in module.ecologies:
            self.ecology_resolver.resolve(e_id)
            ecology_refs.append(e_id)

        # 5. Resolve Relationships
        relationship_refs: List[str] = []
        for rel_id in module.relationships:
            self.relationship_resolver.resolve(rel_id)
            relationship_refs.append(rel_id)

        # 6. Resolve Services
        service_refs: Dict[str, int] = {}
        # module.services is normalized to Dict[str, int] now
        for s_id, count in module.services.items():
            if self.catalog_repo.get_service_profile(s_id) is None:
                raise ResolverError("service_profile", s_id)
            service_refs[s_id] = count

        # 7. Resolve Populations
        population_refs: List[str] = []
        resolved_population_specs: List[PopulationSpec] = []
        
        for p_id in module.populations:
            expanded_archetypes, preferred_regions = self.population_recipe_resolver.resolve(p_id)
            population_refs.append(p_id)
            
            # Collect regions defined in this module and recursively required modules
            module_region_ids = {r.id for r in module.regions}
            if hasattr(module, "requires") and module.requires:
                for req_id in module.requires:
                    req_spec = self.module_repo.get_module(req_id)
                    if req_spec:
                        module_region_ids.update({r.id for r in req_spec.regions})

            REGION_MIGRATION_MAP = {
                "trade_road": "bandit_road"
            }

            for pref_region in preferred_regions:
                mapped_region = REGION_MIGRATION_MAP.get(pref_region, pref_region)
                if mapped_region and mapped_region not in module_region_ids:
                    # Preferred region doesn't exist in the module context, raise a warning or failure depending on strictness/preference
                    # In world assembly context, we want to warn/raise ResolverError if it references regions never in scope.
                    raise ResolverError("region", pref_region, context=f"preferred spawn region in population recipe '{p_id}' is missing from module regions {list(module_region_ids)}")

            for arch_idx, (resolved_arch, count) in enumerate(expanded_archetypes):
                spawn_region = preferred_regions[0] if preferred_regions else ""
                spawn_region = REGION_MIGRATION_MAP.get(spawn_region, spawn_region)
                if not spawn_region and module.regions:
                    spawn_region = module.regions[0].id
                if spawn_region in [r.id for r in module.regions]:
                    spawn_region = f"{prefix}{spawn_region}"
                elif spawn_region:
                    spawn_region = f"{prefix}{spawn_region}"
                
                pop_key = f"{p_id}_{resolved_arch.archetype_id}"
                resolved_population_specs.append(PopulationSpec(
                    id=f"{prefix}{pop_key}",
                    count=count,
                    role=resolved_arch.role_id,
                    faction=resolved_arch.faction_id,
                    spawn_region=spawn_region
                ))

        # 8. Resolve Resources & Buildings
        resource_refs: Dict[str, int] = {}
        building_refs: Dict[str, int] = {}

        # Both are normalized to Dict[str, int] by WorldModuleAuthoringNormalizer
        for res_id, count in module.resources.items():
            self.resource_resolver.resolve(res_id)
            resource_refs[res_id] = count

        for bld_id, count in module.buildings.items():
            self.building_resolver.resolve(bld_id)
            building_refs[bld_id] = count

        return ResolvedModuleContribution(
            regions=regions_spec_list,
            factions=factions_spec_list,
            population_refs=population_refs,
            resolved_population_specs=resolved_population_specs,
            resource_refs=resource_refs,
            building_refs=building_refs,
            service_refs=service_refs,
            relationship_refs=relationship_refs,
            biome_refs=biome_refs,
            ecology_refs=ecology_refs
        )

    def _find_best_region_for_resource(self, resource_type: str, module_regions: List[RegionSpec]) -> str:
        if not module_regions:
            return ""
        
        res_def = self.catalog_repo.get_resource(resource_type)
        preferred_biomes = res_def.preferred_biomes if res_def else []
        
        if preferred_biomes:
            for reg in module_regions:
                for pb in preferred_biomes:
                    if pb in reg.id or pb in reg.type:
                        return reg.id
                
                reg_def = self.catalog_repo.get_region(reg.id)
                if not reg_def and "_" in reg.id:
                    reg_def = self.catalog_repo.get_region(reg.id.split("_", 1)[1])
                
                if reg_def and reg_def.biome in preferred_biomes:
                    return reg.id
                    
        return module_regions[0].id

    def _find_best_region_for_building(self, building_type: str, module_regions: List[RegionSpec]) -> str:
        if not module_regions:
            return ""
            
        bld_def = self.catalog_repo.get_building(building_type)
        building_themes = bld_def.themes if bld_def else []
        
        if building_themes:
            for reg in module_regions:
                reg_def = self.catalog_repo.get_region(reg.id)
                if not reg_def and "_" in reg.id:
                    reg_def = self.catalog_repo.get_region(reg.id.split("_", 1)[1])
                
                if reg_def and reg_def.biome:
                    biome_def = self.catalog_repo.get_biome(reg_def.biome)
                    if biome_def and any(theme in building_themes for theme in biome_def.themes):
                        return reg.id
                
                for theme in building_themes:
                    if theme in reg.id or theme in reg.type or (reg.terrain and theme in reg.terrain.lower()):
                        return reg.id
                        
        return module_regions[0].id


class CompileProfileResolver:
    """
    Translates and merges recipe / specification mappings against Content Catalog definitions
    and Semantics Services to produce a normalized compilation context.
    """

    def __init__(self, repo: CatalogRepository):
        self.repo = repo
        from src.content_semantics.faction import FactionSemanticsService
        from src.content_semantics.role import RoleSemanticsService
        from src.content_semantics.defaults import DefaultSemanticsService
        
        self.faction_semantics = FactionSemanticsService(repo)
        self.role_semantics = RoleSemanticsService(repo)
        self.default_semantics = DefaultSemanticsService(repo)

    def resolve(self, spec: Any, population_recipes: Optional[Dict[str, Any]] = None) -> CompileContext:
        """
        Processes a WorldSpec (or template recipes) and populates resolved profiles.
        """
        from src.worldassembly.models import (
            ResolvedEntityProfile,
            ResolvedBuildingProfile,
            ResolvedResourceProfile,
            ResolvedFactionEconomyProfile,
        )

        ctx = CompileContext()

        # 0. Populate legacy enums and region ownership
        from src.core.enums import EntityRole, Faction
        for pop_idx, pop_spec in enumerate(getattr(spec, "entities", [])):
            try:
                role_enum = self.role_semantics.get_legacy_entity_role(pop_spec.role)
                ctx.register_legacy_role(pop_spec.role, role_enum)
            except Exception:
                pass
            try:
                faction_enum = self.faction_semantics.get_legacy_faction_bucket(pop_spec.faction)
                ctx.register_legacy_faction(pop_spec.faction, faction_enum)
            except Exception:
                pass

        for r_spec in getattr(spec, "regions", []):
            if r_spec.type == "town":
                ctx.register_region_ownership(r_spec.id, Faction.HERO_GUILD)

        # 1. Resolve Factions Treasury
        for f_spec in getattr(spec, "factions", []):
            starting_gold = self.default_semantics.get_faction_vault_defaults()["starting_gold"]
            ctx.register_faction(f_spec.id, ResolvedFactionEconomyProfile(starting_gold=starting_gold))

        # 2. Resolve Populations (Entities)
        for pop_idx, pop_spec in enumerate(getattr(spec, "entities", [])):
            key = getattr(pop_spec, "id", f"pop_{pop_idx}")
            
            # Resolve combat properties
            pop_recipe = population_recipes.get(key) if population_recipes else None
            stats_profile_id = getattr(pop_recipe, "stats_profile", None) if pop_recipe else None
            inventory_seed = getattr(pop_recipe, "inventory_profile", None) if pop_recipe else getattr(pop_spec, "inventory_profile", None)
            cognition_seed = getattr(pop_recipe, "cognition_profile", None) if pop_recipe else getattr(pop_spec, "cognition_profile", None)

            hp, max_hp, atk, def_stat, attack_range, readiness = self._resolve_entity_stats(pop_spec, stats_profile_id)

            # Look up archetype details if available to preserve metadata (Phase 25)
            archetype_id = None
            if "_" in key:
                # E.g., goblin_camp_conflict_goblin_raiding_party_goblin_raider
                # Let's extract the part after the population recipe if it matches an archetype ID
                for arch_key in self.repo.entity_archetypes:
                    if key.endswith(f"_{arch_key}"):
                        archetype_id = arch_key
                        break
            
            resolved_arch = None
            if archetype_id:
                try:
                    from src.content.resolver import EntityArchetypeResolver
                    arch_resolver = EntityArchetypeResolver(self.repo)
                    resolved_arch = arch_resolver.resolve(archetype_id)
                except Exception:
                    pass

            if resolved_arch:
                resolved_entity = ResolvedEntityProfile(
                    legacy_role=self.role_semantics.get_legacy_entity_role(pop_spec.role),
                    legacy_faction=self.faction_semantics.get_legacy_faction_bucket(pop_spec.faction),
                    hp=hp,
                    max_hp=max_hp,
                    atk=atk,
                    def_stat=def_stat,
                    attack_range=attack_range,
                    readiness=readiness,
                    inventory_seed=inventory_seed,
                    cognition_seed=cognition_seed,
                    # Meta parameters preserved
                    archetype_id=resolved_arch.archetype_id,
                    race_id=resolved_arch.race_id,
                    role_id=resolved_arch.role_id,
                    faction_id=resolved_arch.faction_id,
                    traits=[t.id for t in resolved_arch.traits],
                    themes=[t.id for t in resolved_arch.themes],
                    stat_profile_id=resolved_arch.stat_profile.id if resolved_arch.stat_profile else None,
                    combat_profile_id=resolved_arch.combat_profile.id if resolved_arch.combat_profile else None,
                    cognition_profile_id=resolved_arch.cognition_profile.id if resolved_arch.cognition_profile else None,
                    drive_profile_id=resolved_arch.drive_profile.id if resolved_arch.drive_profile else None,
                    need_profile_id=resolved_arch.need_profile.id if resolved_arch.need_profile else None,
                    sense_profile_id=resolved_arch.sense_profile.id if resolved_arch.sense_profile else None,
                    inventory_profile_id=resolved_arch.inventory_profile.id if resolved_arch.inventory_profile else None,
                    skill_profile_id=resolved_arch.skill_profile.id if resolved_arch.skill_profile else None,
                )
            else:
                resolved_entity = ResolvedEntityProfile(
                    legacy_role=self.role_semantics.get_legacy_entity_role(pop_spec.role),
                    legacy_faction=self.faction_semantics.get_legacy_faction_bucket(pop_spec.faction),
                    hp=hp,
                    max_hp=max_hp,
                    atk=atk,
                    def_stat=def_stat,
                    attack_range=attack_range,
                    readiness=readiness,
                    inventory_seed=inventory_seed,
                    cognition_seed=cognition_seed
                )
            ctx.register_entity(key, resolved_entity)

        # 3. Resolve Resources
        for res_spec in getattr(spec, "resources", []):
            res_def = self.repo.get_resource(res_spec.resource_type)
            required_ticks = res_def.required_ticks if res_def else self.default_semantics.get_resource_harvest_defaults()["required_ticks"]

            ctx.register_resource(res_spec.id, ResolvedResourceProfile(
                required_ticks=required_ticks,
                resource_type=res_spec.resource_type
            ))

        # 4. Resolve Buildings
        for bld_spec in getattr(spec, "buildings", []):
            bld_def = self.repo.get_building(bld_spec.type)
            hp = bld_def.hp if bld_def else self.default_semantics.get_building_durability_defaults()["hp"]
            max_hp = bld_def.max_hp if bld_def else self.default_semantics.get_building_durability_defaults()["max_hp"]
            service_profile_id = bld_def.service_profile_id if bld_def else None

            ctx.register_building(bld_spec.id, ResolvedBuildingProfile(
                hp=hp,
                max_hp=max_hp,
                service_profile_id=service_profile_id
            ))

        return ctx

    def _resolve_entity_stats(self, pop_spec: Any, explicit_stats_profile_id: Optional[str] = None) -> tuple[int, int, int, int, int, float]:
        """Resolves entity stats based on priority list: explicit override -> role defaults -> faction defaults -> global defaults."""
        defaults = self.default_semantics.get_entity_combat_defaults()
        
        # 1. Explicit Stats Profile (from recipe/module)
        stats_profile_id = explicit_stats_profile_id
        if not stats_profile_id:
            stats_profile_id = getattr(pop_spec, "stats_profile", None)
            
        # 2. Fall back to role default profile
        if not stats_profile_id:
            stats_profile_id = self.role_semantics.get_default_stats_profile(pop_spec.role)

        if stats_profile_id:
            profile = self.repo.get_stats_profile(stats_profile_id)
            if not profile:
                raise ValueError(f"Referenced stats profile '{stats_profile_id}' not found in Content Catalog.")
            return (
                profile.hp,
                profile.max_hp,
                profile.atk,
                profile.def_stat,
                profile.attack_range,
                profile.readiness
            )

        # Global Defaults Fallback
        return (
            defaults["hp"],
            defaults["max_hp"],
            defaults["atk"],
            defaults["def"],
            defaults["attack_range"],
            defaults["readiness"]
        )

