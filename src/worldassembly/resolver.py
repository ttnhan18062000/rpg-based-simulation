# Compliance IDs: WORLD-ASM-008, WORLD-ASM-009, WORLD-ASM-010
from __future__ import annotations

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict

from src.content.repository import CatalogRepository
from src.worldmodules.repository import WorldModuleRepository
from src.worldmodules.utils import topological_sort_modules
from src.worldassembly.schema import WorldCompositionSpec, ProvenanceManifest, ProvenanceRecord
from src.worldassembly.context import CompileContext

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

    def assemble(self, composition: WorldCompositionSpec) -> ResolvedWorldBundle:
        """
        Executes structural topological assembly and merges partial layouts into a clean WorldSpec.
        """
        # 1. Collect and filter enabled modules
        enabled_refs = [ref for ref in composition.module_refs if ref.enabled]
        
        # Sort initially by defined 'order' configuration
        enabled_refs.sort(key=lambda x: x.order)

        # 2. Rebuild active graph map for topological sort
        graph_map: Dict[str, Any] = {}
        ref_by_id: Dict[str, Any] = {}
        for ref in enabled_refs:
            module = self.module_repo.get_module(ref.module_id)
            if not module:
                raise ValueError(f"Referenced module '{ref.module_id}' not found in repository.")
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
        width = composition.global_parameters.get("topology_width", 100)
        height = composition.global_parameters.get("topology_height", 100)

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

            # A. Regions merge
            for reg in spec.regions:
                reg_id = f"{prefix}{reg.id}"
                if reg_id in regions:
                    raise ValueError(f"Duplicate region ID collision '{reg_id}' detected during assembly merge.")
                
                regions[reg_id] = RegionSpec(
                    id=reg_id,
                    type=reg.type,
                    bounds=reg.grid_bounds,
                    terrain=reg.terrain,
                    hazard_level=reg.hazard_level
                )
                entity_origins[reg_id] = m_id
                prov_records[reg_id] = ProvenanceRecord(
                    element_id=reg_id,
                    element_type="region",
                    source_module=m_id,
                    recipe_type="region",
                    parameters=param_vals,
                    profiles={},
                    details={"bounds": reg.grid_bounds, "terrain": reg.terrain, "hazard_level": reg.hazard_level}
                )

            # B. Populations merge
            for pop_idx, pop in enumerate(spec.population_recipes):
                pop_id = f"{prefix}{getattr(pop, 'id', f'pop_{pop_idx}')}"
                if pop_id in entity_origins:
                    raise ValueError(f"Duplicate population ID collision '{pop_id}' detected during merge.")

                # Instantiate clean compiler PopulationSpec
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

            # C. Resources merge
            for res_idx, res in enumerate(spec.resource_recipes):
                res_id = f"{prefix}{getattr(res, 'id', f'res_{res_idx}')}"
                if res_id in resources:
                    raise ValueError(f"Duplicate resource ID collision '{res_id}' detected during merge.")
                
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

            # D. Buildings merge
            for bld_idx, bld in enumerate(spec.building_recipes):
                bld_id = f"{prefix}{getattr(bld, 'id', f'bld_{bld_idx}')}"
                if bld_id in buildings:
                    raise ValueError(f"Duplicate building ID collision '{bld_id}' detected during merge.")

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

        # 4. Assembled clean worldspec.v1
        world_spec = WorldSpec(
            schema_version="worldspec.v1",
            world_id=composition.world_id,
            name=composition.name,
            description=composition.description,
            topology=TopologySpec(width=width, height=height, coordinate_system="grid"),
            regions=list(regions.values()),
            factions=list(factions.values()),
            entities=list(entities.values()),
            resources=list(resources.values()),
            buildings=list(buildings.values())
        )

        import hashlib
        from datetime import datetime, timezone
        hasher = hashlib.sha256()
        hasher.update(composition.world_id.encode())
        hasher.update(self.catalog_repo.fingerprint.encode())
        for m_id in sorted_ids:
            hasher.update(module_fingerprints[m_id].encode())
        content_fingerprint = hasher.hexdigest()
        manifest_id = f"prov_{content_fingerprint[:16]}"
        created_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        provenance = ProvenanceManifest(
            manifest_id=manifest_id,
            world_id=composition.world_id,
            catalog_fingerprint=self.catalog_repo.fingerprint,
            module_fingerprints=module_fingerprints,
            composition_fingerprint="",
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
            composition=composition,
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

